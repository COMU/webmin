#!/usr/local/bin/perl
# save_dns.cgi
# Save DNS client configuration

require './net-lib.pl';
$access{'dns'} == 2 || &error($text{'dns_ecannot'});
&error_setup($text{'dns_err'});
&ReadParse();
$old_hostname = &get_system_hostname();

$in{'hostname'} =~ /^[A-z0-9\.\-]+$/ ||
	&error(&text('dns_ehost', $in{'hostname'}));
$dns = { };
for($i=0; defined($ns = $in{"nameserver_$i"}); $i++) {
	$ns = $in{"nameserver_$i"};
	$ns =~ s/^\s+//; $ns =~ s/\s+$//;
	if ($ns) {
		&check_ipaddress_any($ns) ||
			&error(&text('dns_ens', $ns));
		push(@{$dns->{'nameserver'}}, $ns);
		}
	}
if ($in{'name0'}) {
    my $i = 0 ;
    my $namekey="name$i";
    while ($in{$namekey}) {
	$dns->{'name'}[$i] = $in{$namekey};
	my $nskey = "nameserver$i";
	my $j = -1;
	while (++$j < $max_dns_servers) {
	    $ns = $in{"${nskey}_$j"};
	    $ns =~ s/^\s+//; $ns =~ s/\s+$//;
	    if ($ns) {
		&check_ipaddress_any($ns) ||
		    &error(&text('dns_ens', $ns));
		push(@{$dns->{$nskey}}, $ns);
	    }
	}
	$i++;
	$namekey="name$i";
    }
}
if (!$in{'domain_def'}) {
	@dlist = split(/\s+/, $in{'domain'});
	foreach $d (@dlist) {
		$d =~ /^[A-z0-9\.\-]+$/ ||
			&error(&text('dns_edomain', $d));
		push(@{$dns->{'domain'}}, $d);
		}
	@dlist>0 || &error($text{'dns_esearch'});
	}
&parse_order($dns);
&save_dns_config($dns);
&save_hostname($in{'hostname'});

if ($in{'hosts'} && $in{'hostname'} ne $old_hostname) {
	# Update hostname in /etc/hosts too
	@hosts = &list_hosts();
	foreach $h (@hosts) {
		local $found = 0;
		foreach $n (@{$h->{'hosts'}}) {
			if (lc($n) eq lc($old_hostname)) {
				$n = $in{'hostname'};
				$found++;
				}
			}
		&modify_host($h) if ($found);
		}

	# Update in ipnodes too
	@ipnodes = &list_ipnodes();
	foreach $h (@ipnodes) {
		local $found = 0;
		foreach $n (@{$h->{'ipnodes'}}) {
			if (lc($n) eq lc($old_hostname)) {
				$n = $in{'hostname'};
				$found++;
				}
			}
		&modify_ipnode($h) if ($found);
		}
	}

&webmin_log("dns", undef, undef, \%in);
&redirect("");

