#!/usr/local/bin/perl
# list_leases.cgi
# List all active leases
# XXX compute number of available IPs from ranges, and subtract those allocated

require './dhcpd-lib.pl';
require 'timelocal.pl';
&ReadParse();
$timenow = time();

%access = &get_module_acl();
&error_setup($text{'eacl_aviol'});
&error("$text{'eacl_np'} $text{'eacl_psl'}") unless $access{'r_leases'};

if ($in{'network'}) {
	$desc = &text('listl_network', "<tt>$in{'network'}</tt>",
			       "<tt>$in{'netmask'}</tt>");
	}
&ui_print_header($desc, $text{'listl_header'}, "");

# Work out how many IPs we have in our subnet ranges
%ranges = ( );
$conf = &get_config();
@subnets = &find("subnet", $conf);
foreach $shared (&find("shared-network", $conf)) {
	push(@subnets, &find("subnet", $shared->{'members'}));
	}
foreach $subnet (@subnets) {
	if ($in{'network'}) {
		# Only count ranges in specified subnet
		if ($subnet->{'values'}->[0] ne $in{'network'}) {
			next;
			}
		}
	$subnet->{'ips'} = 0;
	@ranges = &find("range", $subnet->{'members'});
	foreach $pool (&find("pool", $subnet->{'members'})) {
		push(@ranges, &find("range", $pool->{'members'}));
		}
	foreach $range (@ranges) {
		local @rv = @{$range->{'values'}};
		shift(@rv) if ($rv[0] eq "dynamic-bootp");
		foreach $ip (&expand_ip_range($rv[0], $rv[1])) {
			if (&within_network($ip)) {
				$ranges{$ip} = $subnet;
				}
			$subnet->{'ips'}++;
			}
		}
	}

if (!-r $config{'lease_file'}) {
	# No leases file
	print "<b>".&text('listl_lfnotexist',$config{'lease_file'})."</b><p>\n";
	}
elsif (!&tokenize_file($config{'lease_file'}, \@tok)) {
	# Leases file is not valid or empty
	print "<b>",&text('listl_lfnotcont',$config{'lease_file'}),"</b><p>\n";
	}
else {
	# Parse lease file
	$i = $j = 0;
	local @nw = split(/\./, $in{'network'});
	local @nm = split(/\./, $in{'netmask'});
	LEASE: while($i < @tok) {
		$lease = &parse_struct(\@tok, \$i, $j++, $config{'lease_file'});
		next if (!$lease || $lease->{'name'} ne 'lease');
		local $mems = $lease->{'members'};
		local $starts = &find('starts', $mems);
		local $ends = &find('ends', $mems);
		$lease->{'stime'} = &lease_time($starts);
		$lease->{'etime'} = &lease_time($ends);
		if ($lease->{'etime'} < $timenow ||
		    $lease->{'stime'} > $timenow) {
			if ($in{'all'}) { $lease->{'expired'}++; }
			else { next; }
			}
		next if (!&within_network($lease->{'values'}->[0]));
		push(@leases, $lease);
		}

	# Show links to select mode, if not showing a single subnet
	if (!$in{'network'}) {
		@links = ( );
		foreach $m (0, 1) {
			$msg = $text{'listl_mode_'.$m};
			if ($m != $in{'bysubnet'}) {
				$msg = "<a href='list_leases.cgi?bysubnet=$m'>".
				       "$msg</a>";
				}
			push(@links, $msg);
			}
		print "<b>$text{'listl_mode'}</b> ",
		      &ui_links_row(\@links),"<br>\n";
		}

	if ($in{'bysubnet'}) {
		# Show table of subnets, with lease usage
		print &ui_columns_start([
			$text{'index_net'}, $text{'index_desc'},
			$text{'listl_size'}, $text{'listl_used'}, 
			$text{'listl_pc'} ], 100);
		foreach $subnet (@subnets) {
			%used = ( );
			foreach $lease (@leases) {
				$r = $ranges{$lease->{'values'}->[0]};
				if ($r eq $subnet && !$lease->{'expired'}) {
					$used{$lease->{'values'}->[0]}++;
					}
				}
			$used = scalar(keys %used);
			print &ui_columns_row([
				$subnet->{'values'}->[0],
				&html_escape($subnet->{'comment'}),
				$subnet->{'ips'},
				$used,
				$subnet->{'ips'} ?
					int(100*$used / $subnet->{'ips'})."%" :
					"",
				]);
			}
		print &ui_columns_end();
		}
	elsif (@leases) {
		# Sort leases by selected type
		if ($in{'sort'} eq 'ipaddr') {
			@leases = sort { &ip_compare($a, $b) } @leases;
			}
		elsif ($in{'sort'} eq 'ether') {
			@leases = sort { &ether_compare($a, $b) } @leases;
			}
		elsif ($in{'sort'} eq 'host') {
			@leases = sort { &hostname_compare($a, $b) } @leases;
			}
		elsif ($in{'sort'} eq 'start') {
			@leases = sort { $a->{'stime'} <=> $b->{'stime'} }
				       @leases;
			}
		elsif ($in{'sort'} eq 'end') {
			@leases = sort { $a->{'etime'} <=> $b->{'etime'} }
				       @leases;
			}
		elsif ($config{'lease_sort'} == 1) {
			@leases = sort { &ip_compare($a, $b) } @leases;
			}
		elsif ($config{'lease_sort'} == 2) {
			@leases = sort { &hostname_compare($a, $b) } @leases;
			}

		# Show available and used
		$leased = 0;
		foreach $lease (@leases) {
			$ip = $lease->{'values'}->[0];
			if ($ranges{$ip} && !$donelease{$ip}++ &&
			    !$lease->{'expired'}) {
				$leased++;
				}
			}
		if (keys %ranges) {
			print &text('listl_allocs',
			    scalar(keys %ranges), $leased,
			    int($leased*100/scalar(keys %ranges))),"<p>\n";
			}

		# Table header, with sorting
		print "<b>$text{'listl_delete2'}</b><br>\n";
		print &ui_columns_start([
			&sort_link("ipaddr"),
			&sort_link("ether"),
			&sort_link("host"),
			&sort_link("start"),
			&sort_link("end"),
			]);

		foreach $lease (@leases) {
			local @cols;
			local $mems = $lease->{'members'};
			local $starts = &find('starts', $mems);
			local $ends = &find('ends', $mems);
			local $ht = $lease->{'expired'} ? "i" : "tt";
			push(@cols, "<$ht><a href='delete_lease.cgi?".
			      "idx=$lease->{'index'}&all=$in{all}&".
			      "network=$in{'network'}&netmask=$in{'netmask'}'>".
			      "$lease->{'values'}->[0]</a></$ht>");
			local $hard = &find('hardware', $mems);
			push(@cols,$hard->{'values'}->[1] ?
				"<tt>$hard->{'values'}->[1]</tt>" :
				 "<i>$text{'listl_unknown'}</i>");
			local $client = &find('client-hostname', $mems);
			push(@cols, $client ? "<tt>".&html_escape(
					      $client->{'values'}->[0])."</tt>"
					    : undef);
			if ($config{'lease_tz'}) {
				local @st = localtime($lease->{'stime'});
				local @et = localtime($lease->{'etime'});
				$s = sprintf "%4.4d/%2.2d/%2.2d %2.2d:%2.2d:%2.2d", $st[5]+1900, $st[4]+1, $st[3], $st[2], $st[1], $st[0];
				$e = sprintf "%4.4d/%2.2d/%2.2d %2.2d:%2.2d:%2.2d", $et[5]+1900, $et[4]+1, $et[3], $et[2], $et[1], $et[0];
				}
			else {
				$s = $starts->{'values'}->[1]." ".
				     $starts->{'values'}->[2];
				$e = $ends->{'values'}->[1]." ".
				     $ends->{'values'}->[2];
				}

			push(@cols, "<tt>$s</tt>");
			push(@cols, "<tt>$e</tt>");
			print &ui_columns_row(\@cols);
			}
		print &ui_columns_end();
		}
	else {
		print "<b>",&text($in{'all'} ? 'listl_lfnotcont' :
				  'listl_lfnotcont2', $config{'lease_file'}),
		      "</b><p>\n";
		}
	if (!$in{'all'} && !$in{'bysubnet'}) {
		print &ui_form_start("list_leases.cgi");
		print &ui_hidden("all", 1);
		print &ui_hidden("network", $in{'network'});
		print &ui_hidden("netmask", $in{'netmask'});
		print &ui_form_end([ [ undef, $text{'listl_all'} ] ]);
		}
	}

&ui_print_footer("", $text{'listl_return'});

sub lease_time
{
local @d = split(/\//, $_[0]->{'values'}->[1]);
local @t = split(/:/, $_[0]->{'values'}->[2]);
local $t;
eval { $t = timegm($t[2], $t[1], $t[0], $d[2], $d[1]-1, $d[0]-1900) };
return $@ ? undef : $t;
}

sub ip_compare
{
$a->{'values'}->[0] =~ /^(\d+)\.(\d+)\.(\d+)\.(\d+)/;
local ($a1, $a2, $a3, $a4) = ($1, $2, $3, $4);
$b->{'values'}->[0] =~ /^(\d+)\.(\d+)\.(\d+)\.(\d+)/;
return	$a1 < $1 ? -1 :
	$a1 > $1 ? 1 :
	$a2 < $2 ? -1 :
	$a2 > $2 ? 1 :
	$a3 < $3 ? -1 :
	$a3 > $3 ? 1 :
	$a4 < $4 ? -1 :
	$a4 > $4 ? 1 : 0;
}

sub hostname_compare
{
local $client_a = &find_value('client-hostname', $a->{'members'});
local $client_b = &find_value('client-hostname', $b->{'members'});
return lc($client_a) cmp lc($client_b);
}

sub ether_compare
{
local $ether_a = &find('hardware', $a->{'members'});
local $ether_b = &find('hardware', $b->{'members'});
return lc($ether_a->{'values'}->[1]) cmp lc($ether_b->{'values'}->[1]);
}

sub sort_link
{
local ($c) = @_;
if ($in{'sort'} eq $c) {
	return $text{'listl_'.$c};
	}
else {
	return "<a href='list_leases.cgi?all=$in{'all'}&network=$in{'network'}&netmask=$in{'netmask'}&sort=$c'>".$text{'listl_'.$c}."</a>";
	}
}

sub within_network
{
local ($ip) = @_;
if ($in{'network'}) {
	# Is lease within network/netmask?
	local @ad = split(/\./, $ip);
	for($k=0; $k<4; $k++) {
		if ((int($ad[$k]) & int($nm[$k])) != int($nw[$k])) {
			return 0;
			}
		}
	}
return 1;
}
