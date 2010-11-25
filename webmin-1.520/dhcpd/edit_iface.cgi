#!/usr/local/bin/perl
# edit_ifaces.cgi
# Display network interfaces on which the DHCP server is started

require './dhcpd-lib.pl';
%access = &get_module_acl();
$access{'noconfig'} && &error($text{'iface_ecannot'});

# Get the interface
if ($config{'interfaces_type'} eq 'mandrake') {
	if (-r "/etc/conf.linuxconf") {
		# Older mandrake's init script uses a linuxconf setting
		open(FILE, "/etc/conf.linuxconf");
		while(<FILE>) {
			if (/DHCP.interface\s+(.*)/) {
				$iface = $1;
				}
			}
		close(FILE);
		}
	else {
		# Newer use Redhat-style sysconfig file
		&read_env_file("/etc/sysconfig/dhcpd", \%dhcpd);
		$iface = $dhcpd{'INTERFACES'};
		}
	}
elsif ($config{'interfaces_type'} eq 'redhat') {
	# Redhat's init script uses an environment file
	&read_env_file("/etc/sysconfig/dhcpd", \%dhcpd);
	$iface = $dhcpd{'DHCPDARGS'};
	}
elsif ($config{'interfaces_type'} eq 'suse') {
	# SuSE and United use an environment file too
	&read_env_file("/etc/sysconfig/dhcpd", \%dhcpd);
	$iface = $dhcpd{'DHCPD_INTERFACE'};
	}
elsif ($config{'interfaces_type'} eq 'debian') {
	if (-r "/etc/default/dhcp") {
		# New debian uses an environment file
		&read_env_file("/etc/default/dhcp", \%dhcpd);
		$iface = $dhcpd{'INTERFACES'};
		}
	elsif (-r "/etc/default/dhcp3-server") {
		# DHCPd 3 uses a different environment file
		&read_env_file("/etc/default/dhcp3-server", \%dhcpd);
		$iface = $dhcpd{'INTERFACES'};
		}
	else {
		# Old debian has the interface set in the init script!
		$lref = &read_file_lines("/etc/init.d/dhcp");
		for($i=0; $i<@$lref; $i++) {
			if ($lref->[$i] =~ /INTERFACES\s*=\s*'([^']+)'/ ||
			    $lref->[$i] =~ /INTERFACES\s*=\s*"([^"]+)"/ ||
			    $lref->[$i] =~ /INTERFACES\s*=\s*(\S+)/) {
				$iface = $1;
				}
			}
		}
	}
elsif ($config{'interfaces_type'} eq 'caldera') {
	# Interfaces are set in the Caldera daemons directory file
	&read_env_file("/etc/sysconfig/daemons/dhcpd", \%dhcpd);
	@iface = grep { /^(lo|[a-z]+\d+)$/ } split(/\s+/, $dhcpd{'OPTIONS'});
	$iface = join(" ", @iface);
	}
elsif ($config{'interfaces_type'} eq 'gentoo') {
	# Interfaces are set in a file on Gentoo
	&read_env_file("/etc/conf.d/dhcp", \%dhcp);
	$iface = $dhcp{'IFACE'};
	}
else {
	# Just use the configuration
	$iface = $config{'interfaces'};
	}

&ui_print_header(undef, $text{'iface_title'}, "");
print "$text{'iface_desc'}<p>\n";
print "<form action=save_iface.cgi>\n";
print "<table><tr>\n";
print "<td valign=top><b>$text{'iface_listen'}</b></td>\n";
if (&foreign_check("net")) {
	%got = map { $_, 1 } split(/\s+/, $iface);
	&foreign_require("net", "net-lib.pl");
	@ifaces = grep { $_->{'virtual'} eq '' } &net::active_interfaces();
	$sz = scalar(@ifaces);
	print "<td><select name=iface multiple size=$sz>\n";
	foreach $i (@ifaces) {
		$n = $i->{'fullname'};
		printf "<option value=%s %s>%s (%s)\n",
			$n, $got{$n} ? 'selected' : '', $n, &net::iface_type($n);
		}
	print "</select></td>\n";
	}
else {
	print "<td><input name=iface size=30 value='$iface'></td>\n";
	}
print "</tr></table>\n";
print "<input type=submit value='$text{'save'}'></form>\n";

&ui_print_footer("", $text{'listl_return'});

