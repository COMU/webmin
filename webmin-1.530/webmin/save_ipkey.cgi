#!/usr/local/bin/perl
# Save, create or delete an IP-specific SSL key

require './webmin-lib.pl';
&ReadParse();
&get_miniserv_config(\%miniserv);
@ipkeys = &get_ipkeys(\%miniserv);
if (!$in{'new'}) {
	$ipkey = $ipkeys[$in{'idx'}];
	}
else {
	$ipkey = { };
	}

if ($in{'delete'}) {
	# Just remove this entry
	splice(@ipkeys, $in{'idx'}, 1);
	}
else {
	# Validate inputs
	&error_setup($text{'ipkey_err'});
	@ips = split(/\s+/, $in{'ips'});
	foreach $i (@ips) {
		&check_ipaddress($i) ||
			&error(&text('ipkey_eip', $i));
		}
	@ips || &error(&text('ipkey_eips'));
	$ipkey->{'ips'} = \@ips;
	&validate_key_cert($in{'key'}, $in{'cert_def'} ? undef : $in{'cert'});
	$ipkey->{'key'} = $in{'key'};
	$ipkey->{'cert'} = $in{'cert_def'} ? undef : $in{'cert'};

	# Save or add
	if ($in{'new'}) {
		push(@ipkeys, $ipkey);
		}
	}

&save_ipkeys(\%miniserv, \@ipkeys);
&put_miniserv_config(\%miniserv);
&show_restart_page();

