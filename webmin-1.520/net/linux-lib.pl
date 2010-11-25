# linux-lib.pl
# Active interface functions for all flavours of linux

# active_interfaces()
# Returns a list of currently ifconfig'd interfaces
sub active_interfaces
{
local(@rv, @lines, $l);
&open_execute_command(IFC, "LC_ALL='' LANG='' ifconfig -a", 1, 1);
while(<IFC>) {
	s/\r|\n//g;
	if (/^\S+/) { push(@lines, $_); }
	else { $lines[$#lines] .= $_; }
	}
  close(IFC);
  foreach $l (@lines) {
	  local %ifc;
	  $l =~ /^([^:\s]+)/; $ifc{'name'} = $1;
	  $l =~ /^(\S+)/; $ifc{'fullname'} = $1;
	  if ($l =~ /^(\S+):(\d+)/) { $ifc{'virtual'} = $2; }
	  if ($l =~ /inet addr:(\S+)/) { $ifc{'address'} = $1; }
	  elsif (!$_[0]) { next; }
	  if ($l =~ /Mask:(\S+)/) { $ifc{'netmask'} = $1; }
	  if ($l =~ /Bcast:(\S+)/) { $ifc{'broadcast'} = $1; }
	  if ($l =~ /HWaddr (\S+)/) { $ifc{'ether'} = $1; }
	  if ($l =~ /MTU:(\d+)/) { $ifc{'mtu'} = $1; }
	  if ($l =~ /P-t-P:(\S+)/) { $ifc{'ptp'} = $1; }
	  $ifc{'up'}++ if ($l =~ /\sUP\s/);
	  $ifc{'promisc'}++ if ($l =~ /\sPROMISC\s/);
	  $ifc{'edit'} = ($ifc{'name'} !~ /^ppp/);
	  $ifc{'index'} = scalar(@rv);
	  push(@rv, \%ifc);


	  # We detect IPV6 adresses. An interface can have multiple IPv6
	  # addresses. So we have to scan the entire line to extract each
	  # of them. 
	  if ($l =~ /inet6 addr:\s+(\S+)\/(\S+)/) { 
		  local($fin)=0;
		  local($ic)=0;
		  local $j=1;
		  while (!$fin) {
			  local %ifc;
			  local $where;
			  $where=index($l,"inet6 addr:",$ic);
			  if ($where != -1) {
				  local $sub_l = substr($l, $where, (length($l) - $where));
				  $sub_l =~ /inet6 addr: (\S+)\/(\S+)/; 
				  $ifc{'address'} = $1; 
				  $ifc{'netmask'} = $2; 
				  $l =~ /^([^:\s]+)/; $ifc{'name'} = $1;

				# An IPv6 address has to be up
				  $ifc{'up'}++;

				# The fe80 type IPV6 adresses and the IPv6 loopback interface address 
				# are set to be non-modifiable (for "security" reason)	
				  if (index($ifc{'address'},"fe80") != -1 ) {
				  } 
				  elsif ($ifc{'address'} eq "::1") {
				  }
				  else {
					  $l =~ /^(\S+)/; $ifc{'fullname'} = $1 . "-IPV6-" . $j;
					  $ifc{'edit'} = ($ifc{'name'} !~ /^ppp/);
				  }
				  $ifc{'ether'}=$rv[-1]{'ether'};
				  #printf "$ifc{'ether'}\n";
				  $ifc{'index'} = scalar(@rv);
				  push(@rv, \%ifc);

# We add an offset to look for another possible IPv6 address ot he interface
				  $ic=$where+1;
				  $j++;
			  } 
			  else 
			  {
				  $fin=1;
			  }
      }
	  }
	}
return @rv;
}

# activate_interface(&details)
# Create or modify an interface
sub activate_interface
{
local $a = $_[0];
if($a->{'vlan'} == 1) {
	local $vconfigCMD = "vconfig add " .
			    $a->{'physical'} . " " . $a->{'vlanid'};
	local $vconfigout = &backquote_logged("$vconfigCMD 2>&1");
	if ($?) { &error($vonconfigout); }
	}

local $cmd;
if (&use_ifup_command($a)) {
	# Use Debian ifup command
        if ($a->{'up'}) { $cmd .= "ifup $a->{'fullname'}"; }
        else { $cmd .= "ifdown $a->{'fullname'}"; }
	}
else {
	# Build ifconfig command manually
	if($a->{'vlan'} == 1) {
		$cmd .= "ifconfig $a->{'physical'}.$a->{'vlanid'}";
		}
	else {
		$cmd .= "ifconfig $a->{'name'}";
		if ($a->{'virtual'} ne "") { $cmd .= ":$a->{'virtual'}"; }
		if (&is_ipv6_address($a->{'address'})) { 
			$cmd .= " inet6 add ";
			if ($a->{'netmask'}) {
				  $a->{'address'} .= "/$a->{'netmask'}";
				  $a->{'netmask'} = ''; 
				}
			} 
		}
	$cmd .= " $a->{'address'}";
	if ($a->{'netmask'}) { $cmd .= " netmask $a->{'netmask'}"; }
	if ($a->{'broadcast'}) { $cmd .= " broadcast $a->{'broadcast'}"; }
	if ($a->{'mtu'} && $a->{'virtual'} eq "") { $cmd .= " mtu $a->{'mtu'}";}
	if ($a->{'up'}) { $cmd .= " up"; }
	else { $cmd .= " down"; }
	}
local $out = &backquote_logged("$cmd 2>&1");
if ($?) { &error($out); }
if ($a->{'ether'} && !&use_ifup_command($a)) {
	# Apply ethernet address
	$out = &backquote_logged(
		"ifconfig $a->{'name'} hw ether $a->{'ether'} 2>&1");
	if ($?) { &error($out); }
	}
}

# deactivate_interface(&details)
# Shutdown some active interface
sub deactivate_interface
{
local $name = $_[0]->{'name'}.
	      ($_[0]->{'virtual'} ne "" ? ":$_[0]->{'virtual'}" : "");
local $address = $_[0]->{'address'}.
        ($_[0]->{'virtual'} ne "" ? ":$_[0]->{'virtual'}" : "");
local $netmask = $_[0]->{'netmask'};
 
if ($_[0]->{'virtual'} ne "") {
	# Shutdown virtual interface by setting address to 0
	local $out = &backquote_logged("ifconfig $name 0 2>&1");
	}
elsif (&is_ipv6_address($address)){
	local $out = &backquote_logged("ifconfig $name inet6 del $address/$netmask 2>&1");
	}
local ($still) = grep { $_->{'fullname'} eq $name } &active_interfaces();
if ($still && !&is_ipv6_address($address)) {
	# Old version of ifconfig or non-virtual interface.. down it
	local $out;
	if (&use_ifup_command($_[0])) {
		$out = &backquote_logged("ifdown $name 2>&1");
		}
	else {
		$out = &backquote_logged("ifconfig $name down 2>&1");
		}
	local ($still) = grep { $_->{'fullname'} eq $name }
		      &active_interfaces();
	if ($still) {
		&error("<pre>$out</pre>");
		}
	if (&iface_type($name) =~ /^(.*) (VLAN)$/) {
		$out = &backquote_logged("vconfig rem $name 2>&1");
		}
	}
}

# use_ifup_command(&iface)
# Returns 1 if the ifup command must be used to bring up some interface.
# True on Debian 5.0+ for non-ethernet, typically bonding ifaces.
sub use_ifup_command
{
local ($iface) = @_;
return $gconfig{'os_type'} eq 'debian-linux' &&
       $gconfig{'os_version'} >= 5 &&
       $iface->{'name'} !~ /^(eth|lo)/ &&
       $iface->{'virtual'} eq '';
}

# iface_type(name)
# Returns a human-readable interface type name
sub iface_type
{
if ($_[0] =~ /^(.*)\.(\d+)$/) {
	return &iface_type("$1")." VLAN";
	}
return "PPP" if ($_[0] =~ /^ppp/);
return "SLIP" if ($_[0] =~ /^sl/);
return "PLIP" if ($_[0] =~ /^plip/);
return "Ethernet" if ($_[0] =~ /^eth/);
return "Wireless Ethernet" if ($_[0] =~ /^(wlan|ath)/);
return "Arcnet" if ($_[0] =~ /^arc/);
return "Token Ring" if ($_[0] =~ /^tr/);
return "Pocket/ATP" if ($_[0] =~ /^atp/);
return "Loopback" if ($_[0] =~ /^lo/);
return "ISDN rawIP" if ($_[0] =~ /^isdn/);
return "ISDN syncPPP" if ($_[0] =~ /^ippp/);
return "CIPE" if ($_[0] =~ /^cip/);
return "VmWare" if ($_[0] =~ /^vmnet/);
return "Wireless" if ($_[0] =~ /^wlan/);
return "Bonded" if ($_[0] =~ /^bond/);
return "OpenVZ" if ($_[0] =~ /^venet/);
return $text{'ifcs_unknown'};
}

# list_routes()
# Returns a list of active routes
sub list_routes
{
local @rv;
&open_execute_command(ROUTES, "netstat -rn", 1, 1);
while(<ROUTES>) {
	s/\s+$//;
	if (/^([0-9\.]+)\s+([0-9\.]+)\s+([0-9\.]+)\s+\S+\s+\S+\s+\S+\s+\S+\s+(\S+)$/) {
		push(@rv, { 'dest' => $1,
			    'gateway' => $2,
			    'netmask' => $3,
			    'iface' => $4 });
		}
	}
close(ROUTES);
&open_execute_command(ROUTES, "netstat -rn -A inet6", 1, 1);
	while(<ROUTES>) {
		s/\s+$//;
		if (/^([0-9a-z:]+)\/([0-9]+)\s+([0-9a-z:]+)\s+\S+\s+\S+\s+\S+\s+\S+\s+(\S+)$/) {
			push(@rv, { 'dest' => $1,
				'gateway' => $3,
				'netmask' => $2,
				'iface' => $4 });
						}
	}

	close(ROUTES);
return @rv;
}

# load_module(&details)
# Load or modify a loaded module
sub load_module
{
local $a = $_[0];
local $cmd = "modprobe bonding";

if($a->{'mode'}) {$cmd .= " mode=" . $a->{'mode'};}
if($a->{'miimon'}) {$cmd .= " miimon=" . $a->{'miimon'};}
if($a->{'downdelay'}) {$cmd .= " downdelay=" . $a->{'downdelay'};}
if($a->{'updelay'}) {$cmd .= " updelay=" . $a->{'updelay'};}

local $out = &backquote_logged("$cmd 2>&1");
if ($?) { &error($out); }
}

# Tries to unload the module
# unload_module(name)
sub unload_module
{
	my ($name) = @_;
	my $cmd = "modprobe -r bonding";
	local $out = &backquote_logged("$cmd 2>&1");
	if($?) { &error($out);}
}

# list_interfaces()
# return a list of interfaces
sub list_interfaces
{
	my @ret;
	$cmd = "ifconfig -a";
	local $out = &backquote_logged("$cmd 2>&1");
	if ($?) { &error($out); }
	
	@lines = split("\n", $out);
	foreach $line(@lines) {
		$line =~ /^([\w|.]*)/m;
		if(($1)) {
			push(@ret, $1);
		}
	}
	return @ret;
}

# create_route(&route)
# Delete one active route, as returned by list_routes. Returns an error message
# on failure, or undef on success
sub delete_route
{
local ($route) = @_;
	local $cmd = "route " . (&is_ipv6_address($route->{'dest'})? "-A inet6 ":"-A inet ") . "del ";
	
	if (!$route->{'dest'} || $route->{'dest'} eq '0.0.0.0' || $route->{'dest'} eq '::') {
	$cmd .= " default";
	}
elsif ($route->{'netmask'} eq '255.255.255.255') {
	$cmd .= " -host $route->{'dest'}";
	}
	elsif (!&is_ipv6_address($route->{'dest'})) {
	$cmd .= " -net $route->{'dest'}";
	if ($route->{'netmask'} && $route->{'netmask'} ne '0.0.0.0') {
		$cmd .= " netmask $route->{'netmask'}";
		}
	}
	else{
		$cmd .= "$route->{'dest'}/$route->{'netmask'}";
	}
if ($route->{'gateway'}) {
	$cmd .= " gw $route->{'gateway'}";
	}
elsif ($route->{'iface'}) {
	$cmd .= " dev $route->{'iface'}";
	}
local $out = &backquote_logged("$cmd 2>&1 </dev/null");
return $? ? $out : undef;
}

# create_route(&route)
# Adds a new active route
sub create_route
{
local ($route) = @_;
	local $cmd = "route " . (&is_ipv6_address($route->{'dest'})? "-A inet6 ":"-A inet ") . "add ";
	
	if (!$route->{'dest'} || $route->{'dest'} eq '0.0.0.0' || $route->{'dest'} eq '::') {
	$cmd .= " default";
	}
	elsif ($route->{'netmask'} eq '255.255.255.255') {
		$cmd .= " -host $route->{'dest'}";
		}
	elsif (!&is_ipv6_address($route->{'dest'})) {
		$cmd .= " -net $route->{'dest'}";
		if ($route->{'netmask'} && $route->{'netmask'} ne '0.0.0.0') {
			$cmd .= " netmask $route->{'netmask'}";
		}
		}
	else{
		$cmd .= "$route->{'dest'}/$route->{'netmask'}";
	}
if ($route->{'gateway'}) {
	$cmd .= " gw $route->{'gateway'}";
	}
	elsif ($route->{'iface'}) {
	$cmd .= " dev $route->{'iface'}";
	}
local $out = &backquote_logged("$cmd 2>&1 </dev/null");
return $? ? $out : undef;
}

# iface_hardware(name)
# Does some interface have an editable hardware address
sub iface_hardware
{
return $_[0] =~ /^eth/;
}

# allow_interface_clash()
# Returns 0 to indicate that two virtual interfaces with the same IP
# are not allowed
sub allow_interface_clash
{
return 0;
}

# get_dns_config()
# Returns a hashtable containing keys nameserver, domain, search & order
sub get_dns_config
{
local $dns;
local $rc;
if ($use_suse_dns && ($rc = &parse_rc_config()) && $rc->{'NAMESERVER'}) {
	# Special case - get DNS settings from SuSE config
	local @ns = split(/\s+/, $rc->{'NAMESERVER'}->{'value'});
	$dns->{'nameserver'} = [ grep { $_ ne "YAST_ASK" } @ns ];
	local $src = $rc->{'SEARCHLIST'};
	$dns->{'domain'} = [ split(/\s+/, $src->{'value'}) ] if ($src);
	$dnsfile = $rc_config;
	}
else {
	&open_readfile(RESOLV, "/etc/resolv.conf");
	while(<RESOLV>) {
		s/\r|\n//g;
		s/#.*$//;
		s/;.*$//;
		if (/nameserver\s+(.*)/) {
			push(@{$dns->{'nameserver'}}, split(/\s+/, $1));
			}
		elsif (/domain\s+(\S+)/) {
			$dns->{'domain'} = [ $1 ];
			}
		elsif (/search\s+(.*)/) {
			$dns->{'domain'} = [ split(/\s+/, $1) ];
			}
		}
	close(RESOLV);
	$dnsfile = "/etc/resolv.conf";
	}
&open_readfile(SWITCH, "/etc/nsswitch.conf");
while(<SWITCH>) {
	s/\r|\n//g;
	if (/^\s*hosts:\s+(.*)/) {
		$dns->{'order'} = $1;
		}
	}
close(SWITCH);
$dns->{'files'} = [ $dnsfile, "/etc/nsswitch.conf" ];
return $dns;
}

# save_dns_config(&config)
# Writes out the resolv.conf and nsswitch.conf files
sub save_dns_config
{
local $rc;
&lock_file($rc_config) if ($suse_dns_config);
if ($use_suse_dns && ($rc = &parse_rc_config()) && $rc->{'NAMESERVER'}) {
	# Update SuSE config file
	&save_rc_config($rc, "NAMESERVER", join(" ", @{$_[0]->{'nameserver'}}));
	&save_rc_config($rc, "SEARCHLIST", join(" ", @{$_[0]->{'domain'}}));
	}
else {
	# Update standard resolv.conf file
	&lock_file("/etc/resolv.conf");
	&open_readfile(RESOLV, "/etc/resolv.conf");
	local @resolv = <RESOLV>;
	close(RESOLV);
	&open_tempfile(RESOLV, ">/etc/resolv.conf");
	foreach (@{$_[0]->{'nameserver'}}) {
		&print_tempfile(RESOLV, "nameserver $_\n");
		}
	if ($_[0]->{'domain'}) {
		if ($_[0]->{'domain'}->[1]) {
			&print_tempfile(RESOLV,
				"search ",join(" ", @{$_[0]->{'domain'}}),"\n");
			}
		else {
			&print_tempfile(RESOLV,
				"domain $_[0]->{'domain'}->[0]\n");
			}
		}
	foreach (@resolv) {
		&print_tempfile(RESOLV, $_)
			if (!/^\s*(nameserver|domain|search)\s+/);
		}
	&close_tempfile(RESOLV);
	&unlock_file("/etc/resolv.conf");
	}

# On Debian, if dns-nameservers are defined in interfaces, update them too
if ($gconfig{'os_type'} eq 'debian-linux' && defined(&get_interface_defs)) {
	local @ifaces = &get_interface_defs();
	foreach my $i (@ifaces) {
		local ($dns) = grep { $_->[0] eq 'dns-nameservers' } @{$i->[3]};
		if ($dns) {
			$dns->[1] = join(' ', @{$_[0]->{'nameserver'}});
			&modify_interface_def($i->[0], $i->[1], $i->[2],
					      $i->[3], 0);
			}
		}
	}

# Update resolution order in nsswitch.conf
&lock_file("/etc/nsswitch.conf");
&open_readfile(SWITCH, "/etc/nsswitch.conf");
local @switch = <SWITCH>;
close(SWITCH);
&open_tempfile(SWITCH, ">/etc/nsswitch.conf");
foreach (@switch) {
	if (/^\s*hosts:\s+/) {
		&print_tempfile(SWITCH, "hosts:\t$_[0]->{'order'}\n");
		}
	else {
		&print_tempfile(SWITCH, $_);
		}
	}
&close_tempfile(SWITCH);
&unlock_file("/etc/nsswitch.conf");

# Update SuSE config file
if ($suse_dns_config && $rc->{'USE_NIS_FOR_RESOLVING'}) {
	if ($_[0]->{'order'} =~ /nis/) {
		&save_rc_config($rc, "USE_NIS_FOR_RESOLVING", "yes");
		}
	else {
		&save_rc_config($rc, "USE_NIS_FOR_RESOLVING", "no");
		}
	}
&unlock_file($rc_config) if ($suse_dns_config);
}

$max_dns_servers = 3;

# order_input(&dns)
# Returns HTML for selecting the name resolution order
sub order_input
{
my @o = split(/\s+/, $_[0]->{'order'});
@o = map { s/nis\+/nisplus/; s/yp/nis/; $_; } @o;
my @opts = ( [ "files", "Hosts" ], [ "dns", "DNS" ], [ "nis", "NIS" ],
	     [ "nisplus", "NIS+" ], [ "ldap", "LDAP" ], [ "db", "DB" ],
	     [ "mdns4", "Multicast DNS" ] );
if (&indexof("mdns4_minimal", @o) >= 0) {
	push(@opts, [ "mdns4_minimal", "Multicast DNS (minimal)" ]);
	}
return &common_order_input("order", join(" ", @o), \@opts);
}

# parse_order(&dns)
# Parses the form created by order_input()
sub parse_order
{
if (defined($in{'order'})) {
	$in{'order'} =~ /\S/ || &error($text{'dns_eorder'});
	$_[0]->{'order'} = $in{'order'};
	}
else {
	local($i, @order);
	for($i=0; defined($in{"order_$i"}); $i++) {
		push(@order, $in{"order_$i"}) if ($in{"order_$i"});
		}
	$_[0]->{'order'} = join(" ", @order);
	}
}

1;

