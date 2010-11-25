#!/usr/local/bin/perl
# save_net.cgi
# Save global address and topology options

require './bind8-lib.pl';
$access{'defaults'} || &error($text{'net_ecannot'});
&error_setup($text{'net_err'});
&ReadParse();

&lock_file(&make_chroot($config{'named_conf'}));
$conf = &get_config();
$options = &find("options", $conf);
if (!$in{'listen_def'}) {
	for($i=0; defined($addr = $in{"addrs_$i"}); $i++) {
		next if (!$addr);
		local $l = { 'name' => 'listen-on',
			     'type' => 1 };
		if (!$in{"pdef_$i"}) {
			$in{"port_$i"} =~ /^\d+$/ ||
				&error(&text('net_eport', $in{"port_$i"}));
			$l->{'values'} = [ 'port', $in{"port_$i"} ];
			}
		$port = $in{"pdef_$i"} ? 53 : $in{"port_$i"};
		$used{$port}++ && &error(&text('net_eusedport', $port));
		$l->{'members'} =
			[ map { { 'name' => $_ } } split(/\s+/, $addr) ];
		push(@listen, $l);
		}
	}
&save_directive($options, 'listen-on', \@listen, 1);
if (!$in{'saddr_def'}) {
	&check_ipaddress($in{'saddr'}) ||
		&error(&text('net_eaddr', $in{'saddr'}));
	push(@qvals, "address", $in{'saddr'});
	}
if (!$in{'sport_def'}) {
	$in{'sport'} =~ /^\d+$/ || &error(&text('net_eport', $in{'sport'}));
	push(@qvals, "port", $in{'sport'});
	}
if (@qvals) {
	&save_directive($options, 'query-source',
			[ { 'name' => 'query-source',
			    'values' => \@qvals } ], 1);
	}
else {
	&save_directive($options, 'query-source', [ ], 1);
	}
$in{'topology_def'} || $in{'topology'} || &error($text{'net_etopology'});
&save_addr_match('topology', $options, 1);
$in{'allow-recursion_def'} || $in{'allow-recursion'} ||
	&error($text{'net_erecur'});
&save_addr_match('allow-recursion', $options, 1);

&flush_file_lines();
&unlock_file(&make_chroot($config{'named_conf'}));
&webmin_log("net", undef, undef, \%in);
&redirect("");
