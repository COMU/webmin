#!/usr/local/bin/perl
# Change all instances of some IP 

require './bind8-lib.pl';
&ReadParse();
$conf = &get_config();
&error_setup($text{'umass_err'});

# Get the zones
foreach $d (split(/\0/, $in{'d'})) {
	($idx, $viewidx) = split(/\s+/, $d);
	$zone = &get_zone_name($idx, $viewidx);
	$zone || &error($text{'umass_egone'});
	&can_edit_zone($zone) ||
		&error($text{'master_edelete'});
	push(@zones, $zone);
	}
$access{'ro'} && &error($text{'master_ero'});

# Validate inputs
$in{'old'} =~ s/\s+/ /g;
$in{'old_def'} || $in{'old'} || &error($text{'umass_eold'});
$in{'new'} || &error($text{'umass_enew'});
if ($in{'type'} eq 'A') {
	&check_ipaddress($in{'new'}) ||
		&error(&text('edit_eip', $in{'new'}));
	}
elsif ($in{'type'} eq 'AAAA') {
	&check_ip6address($in{'new'}) ||
		&error(&text('edit_eip6', $in{'new'}));
	}
elsif ($in{'type'} eq 'NS') {
	&valname($in{'new'}) ||
		&error(&text('edit_ens', $in{'new'}));
	}
elsif ($in{'type'} eq 'CNAME') {
	&valname($in{'new'}) || $in{'new'} eq '@' ||
		&error(&text('edit_ecname', $in{'new'}));
	}
elsif ($in{'type'} eq 'MX') {
	$in{'new'} =~ /^(\d+)\s+(\S+)$/ && &valname("$2") ||
		&error(&text('emass_emx', $in{'new'}));
	}
elsif ($in{'type'} eq 'TXT' || $in{'type'} eq 'SPF') {
	$in{'new'} = "\"$in{'new'}\"";
	}
elsif ($in{'type'} eq 'PTR') {
	&valname($in{'new'}) ||
		&error(&text('edit_eptr', $in{'new'}));
	}
elsif ($in{'type'} eq 'ttl') {
	$in{'new'} =~ /^\d+$/ || 
		&error(&text('master_edefttl', $in{'new'}));
	}

# Do each one
&ui_print_unbuffered_header(undef, $text{'umass_title'}, "");

foreach $zi (@zones) {
	print &text('umass_doing', "<tt>$zi->{'name'}</tt>"),"<br>\n";
	if ($zi->{'type'} ne 'master') {
		# Skip - not a master zone
		print $text{'umass_notmaster'},"<p>\n";
		next;
		}
	$rcount = 0;
	@recs = &read_zone_file($zi->{'file'}, $zi->{'name'});
	$realfile = &make_chroot(&absolute_path($zi->{'file'}));
	foreach $r (@recs) {
		$v = join(" ", @{$r->{'values'}});
		if ($r->{'type'} eq $in{'type'} &&
		    ($v eq $in{'old'} || $in{'old_def'})) {
			# Found a regular record to fix
			&lock_file($realfile);
			&modify_record($zi->{'file'}, $r, $r->{'name'},
				       $r->{'ttl'}, $r->{'class'}, $r->{'type'},
				       $in{'new'}, $r->{'cmt'});
			$rcount++;
			}
		elsif ($in{'type'} eq 'ttl' && $r->{'defttl'}) {
			# Found default TTL to fix
			&lock_file($realfile);
			&modify_defttl($zi->{'file'}, $r, $in{'new'});
			$rcount++;
			}
		}
	if ($rcount) {
		&bump_soa_record($zi->{'file'}, \@recs);
		&sign_dnssec_zone_if_key($zi, \@recs);
		print &text('umass_done', $rcount, scalar(@recs)),"<p>\n";
		}
	else {
		print &text('umass_none', scalar(@recs)),"<p>\n";
		}
	}

&unlock_all_files();
&webmin_log("update", "zones", scalar(@zones));

&ui_print_footer("", $text{'index_return'});

# valname(name)
sub valname
{
return valdnsname($_[0], 0, $in{'origin'});
}

