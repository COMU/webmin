# Functions for parsing and updating the LDAP config file

BEGIN { push(@INC, ".."); };
use WebminCore;
&init_config();

@base_types = ("passwd", "shadow", "group", "hosts", "networks", "netmasks",
	       "services", "protocols", "aliases", "netgroup");

# get_config()
# Parses the NSS LDAP config file into a list of names and values
sub get_config
{
local $file = $_[0] || $config{'auth_ldap'};
if (!defined(@get_config_cache)) {
	local $lnum = 0;
	@get_config_cache = ( );
	&open_readfile(CONF, $file);
	while(<CONF>) {
		s/\r|\n//g;
                s/#.*$//;
		if (/^(#?)(\S+)\s*(.*)/) {
			push(@get_config_cache, { 'name' => lc($2),
						  'value' => $3,
						  'enabled' => !$1,
						  'line' => $lnum,
						  'file' => $file });
			}
		$lnum++;
		}
	close(CONF);
	}
return \@get_config_cache;
}

# find(name, &conf, disabled-mode)
sub find
{
local ($name, $conf, $dis) = @_;
local @rv = grep { $_->{'name'} eq $name } @$conf;
if ($dis == 0) {
	# Enabled only
	@rv = grep { $_->{'enabled'} } @rv;
	}
elsif ($dis == 1) {
	# Disabled only
	@rv = grep { !$_->{'enabled'} } @rv;
	}
return wantarray ? @rv : $rv[0];
}

# find_value(name, &conf)
sub find_value
{
local ($name, $conf, $dis) = @_;
local @rv = map { $_->{'value'} } &find($name, $conf, $dis);
return wantarray ? @rv : $rv[0];
}

sub find_svalue
{
local $rv = &find_value(@_);
return $rv;
}

# save_directive(&conf, name, [value])
sub save_directive
{
local ($conf, $name, $value) = @_;
local $old = &find($name, $conf);
local $oldcmt = &find($name, $conf, 1);
local $lref = &read_file_lines($old ? $old->{'file'} :
			       $oldcmt ? $oldcmt->{'file'} :
				         $config{'auth_ldap'});
if (defined($value) && $old) {
	# Just update value
	$old->{'value'} = $value;
	$lref->[$old->{'line'}] = "$name $value";
	}
elsif (defined($value) && $oldcmt) {
	# Add value after commented version
	splice(@$lref, $oldcmt->{'line'}+1, 0, "$name $value");
	&renumber($conf, $oldcmt->{'line'}+1, $oldcmt->{'file'}, 1);
	push(@$conf, { 'name' => $name,
		       'value' => $value,
		       'enabled' => 1,
		       'line' => $oldcmt->{'line'}+1,
		       'file' => $oldcmt->{'file'} });
	}
elsif (!defined($value) && $old) {
	# Delete current value
	splice(@$lref, $old->{'line'}, 1);
	&renumber($conf, $old->{'line'}, $old->{'file'}, -1);
	@$conf = grep { $_ ne $old } @$conf;
	}
elsif ($value) {
	# Add value at end of file
	push(@$conf, { 'name' => $name,
		       'value' => $value,
		       'enabled' => 1,
		       'line' => scalar(@$lref),
		       'file' => $config{'auth_ldap'} });
	push(@$lref, "$name $value");
	}
}

sub renumber
{
local ($conf, $line, $file, $offset) = @_;
foreach my $c (@$conf) {
	if ($c->{'line'} >= $line && $c->{'file'} eq $file) {
		$c->{'line'} += $offset;
		}
	}
}

# get_rootbinddn_secret()
# Returns the password used when the root user connects to the LDAP server
sub get_rootbinddn_secret
{
&open_readfile(SECRET, $config{'secret'}) || return undef;
local $secret = <SECRET>;
close(SECRET);
$secret =~ s/\r|\n//g;
return $secret;
}

# save_rootbinddn_secret(secret)
# Saves the password used when the root user connects to the LDAP server
sub save_rootbinddn_secret
{
if (defined($_[0])) {
	&open_tempfile(SECRET, ">$config{'secret'}");
	&print_tempfile(SECRET, $_[0],"\n");
	&close_tempfile(SECRET);
	&set_ownership_permissions(0, 0, 0600, $config{'secret'});
	}
else {
	&unlink_file($config{'secret'});
	}
}

# ldap_connect(return-error, [&host])
# Connect to the LDAP server and return a handle to the Net::LDAP object
sub ldap_connect
{
# Load the LDAP module
eval "use Net::LDAP";
if ($@) {
	local $err = &text('ldap_emodule', "<tt>Net::LDAP</tt>",
		   "../cpan/download.cgi?source=3&".
		   "cpan=Convert::ASN1%20Net::LDAP&mode=2&".
		   "return=../$module_name/&".
		   "returndesc=".&urlize($module_info{'desc'}));
	if ($_[0]) { return $err; }
	else { &error($err); }
	}
local $err = &generic_ldap_connect($config{'ldap_hosts'}, $config{'ldap_port'},
			     $config{'ldap_tls'}, $config{'ldap_user'},
			     $config{'ldap_pass'});
if (ref($err)) { return $err; }		# Worked
elsif ($_[0]) { return $err; }		# Caller asked for error return
else { &error($err); }			# Caller asked for error() call
}

# generic_ldap_connect([host], [port], [login], [password])
# A generic function for connecting to an LDAP server. Uses the system's
# LDAP client config file if any parameters are missing. Returns the LDAP
# handle on success or an error message on failure.
sub generic_ldap_connect
{
local ($ldap_hosts, $ldap_port, $ldap_ssl, $ldap_user, $ldap_pass) = @_;

# Check for perl module and config file
eval "use Net::LDAP";
if ($@) {
	return &text('ldap_emodule2', "<tt>Net::LDAP</tt>");
	}
if (!-r $config{'auth_ldap'}) {
	$ldap_hosts && $ldap_user ||
		return &text('ldap_econf', "<tt>$config{'auth_ldap'}</tt>");
	}

# Get the host and port
local $conf = &get_config();
local $uri = &find_svalue("uri", $conf);
local ($ldap, $use_ssl, $err);
local $ssl = &find_svalue("ssl", $conf);
local $cafile = &find_svalue("tls_cacertfile", $conf);
local $certfile = &find_svalue("tls_cert", $conf);
local $keyfile = &find_svalue("tls_key", $conf);
local $ciphers = &find_svalue("tls_ciphers", $conf);
if ($ldap_hosts) {
	# Using hosts from parameter
	local @hosts = split(/[ \t,]+/, $ldap_hosts);
	if ($ldap_ssl ne '') {
		$use_ssl = $ldap_ssl;
		}
	else {
		$use_ssl = $ssl eq 'yes' ? 1 :
			   $ssl eq 'start_tls' ? 2 : 0;
		}
	local $port = $ldap_port ||
		      &find_svalue("port", $conf) ||
		      ($use_ssl == 1 ? 636 : 389);
	foreach my $host (@hosts) {
		eval {
			$ldap = Net::LDAP->new($host, port => $port,
				scheme => $use_ssl == 1 ? 'ldaps' : 'ldap',
				inet6 => &should_use_inet6($host));
			};
		if ($@) {
			$err = &text('ldap_econn2',
				     "<tt>$host</tt>", "<tt>$port</tt>",
				     &html_escape($@));
			}
		elsif (!$ldap) {
			$err = &text('ldap_econn',
				     "<tt>$host</tt>", "<tt>$port</tt>");
			}
		else {
			$err = undef;
			last;
			}
		}
	}
elsif ($uri) {
	# Using uri directive
	foreach my $u (split(/\s+/, $uri)) {
		if ($u =~ /^(ldap|ldaps|ldapi):\/\/([a-z0-9\_\-\.]+)(:(\d+))?/) {
			($proto, $host, $port) = ($1, $2, $4);
			if (!$port && $proto eq "ldap") {
				$port = 389;
				}
			elsif (!$port && $proto eq "ldaps") {
				$port = 636;
				}
			$ldap = Net::LDAP->new($host, port => $port,
				       scheme => $proto,
				       inet6 => &should_use_inet6($host));
			if (!$ldap) {
				$err = &text('ldap_econn',
					     "<tt>$host</tt>","<tt>$port</tt>");
				}
			else {
				$err = undef;
				$use_ssl = $proto eq "ldaps" ? 1 :
					   $ssl eq 'start_tls' ? 2 : 0;
				last;
				}
			}
		}
	if (!$ldap && !$err) {
		$err = &text('ldap_eparse', $uri);
		}
	}
else {
	# Using host and port directives
	$use_ssl = $ssl eq 'yes' ? 1 :
		   $ssl eq 'start_tls' ? 2 : 0;
	local @hosts = split(/[ ,]+/, &find_svalue("host", $conf));
	local $port = &find_svalue("port", $conf) ||
		      ($use_ssl == 1 ? 636 : 389);
	@hosts = ( "localhost" ) if (!@hosts);

	foreach $host (@hosts) {
		$ldap = Net::LDAP->new($host, port => $port,
			       scheme => $use_ssl == 1 ? 'ldaps' : 'ldap',
			       inet6 => &should_use_inet6($host));
		if (!$ldap) {
			$err = &text('ldap_econn',
				     "<tt>$host</tt>", "<tt>$port</tt>");
			}
		else {
			$err = undef;
			last;
			}
		}
	}

# Start TLS if configured
if ($use_ssl == 2 && !$err) {
	local $mesg;
	if ($certfile) {
		# Use cert to connect
		eval { $mesg = $ldap->start_tls(
					cafile     => $cafile,
                                        clientcert => $certfile,
                                        clientkey  => $keyfile,
                                        ciphers    => $ciphers
					); };

		}
	else {
		eval { $mesg = $ldap->start_tls(); };
		}
	if ($@ || !$mesg || $mesg->code) {
		$err = &text('ldap_etls', $@ ? $@ : $mesg ? $mesg->error :
					  "Unknown error");
		}
	}

if ($err) {
	return $err;
	}

local ($dn, $password);
local $rootbinddn = &find_svalue("rootbinddn", $conf);
if ($ldap_user) {
	# Use login from config
	$dn = $ldap_user;
	$password = $ldap_pass;
	}
elsif ($rootbinddn) {
	# Use the root login if we have one
	$dn = $rootbinddn;
	$password = &get_rootbinddn_secret();
	}
else {
	# Use the normal login
	$dn = &find_svalue("binddn", $conf);
	$password = &find_svalue("bindpw", $conf);
	}
local $mesg;
if ($password) {
	$mesg = $ldap->bind(dn => $dn, password => $password);
	}
else {
	$mesg = $ldap->bind(dn => $dn, anonymous => 1);
	}
if (!$mesg || $mesg->code) {
	local $err = &text('ldap_elogin', "<tt>$host</tt>",
		     	   $dn || $text{'ldap_anon'},
			   $mesg ? $mesg->error : "Unknown error");
	if ($_[0]) { return $err; }
	else { &error($err); }
	}
return $ldap;
}

# should_use_inet6(host)
# Returns 1 if some host has a v6 address but not v4
sub should_use_inet6
{
local ($host) = @_;
return !&to_ipaddress($host) && &to_ip6address($host);
}

# base_chooser_button(field, node, form)
# Returns HTML for a popup LDAP base chooser button
sub base_chooser_button
{
local ($field, $node, $form) = @_;
$form ||= 0;
local $w = 500;
local $h = 500;
if ($gconfig{'db_sizeusers'}) {
	($w, $h) = split(/x/, $gconfig{'db_sizeusers'});
	}
return "<input type=button onClick='ifield = document.forms[$form].$field; chooser = window.open(\"popup_browser.cgi?node=$node&base=\"+escape(ifield.value), \"chooser\", \"toolbar=no,menubar=no,scrollbars=yes,width=$w,height=$h\"); chooser.ifield = ifield; window.ifield = ifield' value=\"...\">\n";
}

# get_ldap_host()
# Returns the hostname probably used for connecting
sub get_ldap_host
{
local @hosts;
if ($config{'ldap_hosts'}) {
	@hosts = split(/\s+/, $config{'ldap_hosts'});
	}
elsif (!-r $config{'auth_ldap'}) {
	@hosts = ( );
	}
else {
	local $conf = &get_config();
	local $uri = &find_svalue("uri", $conf);
	if ($uri) {
		foreach my $u (split(/\s+/, $uri)) {
			if ($u =~ /^(ldap|ldaps|ldapi):\/\/([a-z0-9\_\-\.]+)(:(\d+))?/) {
				push(@hosts, $2);
				}
			}
		}
	else {
		@hosts = split(/[ ,]+/, &find_svalue("host", $conf));
		}
	if (!@hosts) {
		@hosts = ( "localhost" );
		}
	}
return wantarray ? @hosts : $hosts[0];
}

1;

