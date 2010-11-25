#!/usr/local/bin/perl
# Delete multiple records from a zone file

require './bind8-lib.pl';
&ReadParse();
&error_setup($text{'drecs_err'});
$zone = &get_zone_name($in{'index'}, $in{'view'});
$dom = $zone->{'name'};
&can_edit_zone($zone) ||
	&error($text{'recs_ecannot'});
&can_edit_type($in{'type'}, \%access) ||
	&error($text{'recs_ecannottype'});

# Find the records
@d = split(/\0/, $in{'d'});
@d || &error($text{'drecs_enone'});

# Check if confirmation is needed
if (!$in{'confirm'} && $config{'confirm_rec'}) {
	# Ask first
	&ui_print_header(undef, $text{'drecs_title'}, "");

	print &ui_confirmation_form("delete_recs.cgi",
		&text('drecs_rusure', scalar(@d), $dom),
		[ [ 'index', $in{'index'} ],
		  [ 'view', $in{'view'} ],
		  [ 'rev', $in{'rev'} ],
		  map { [ 'd', $_ ] } @d ],
		[ [ 'confirm', $text{'drecs_ok'} ] ],
		);

	&ui_print_footer("edit_recs.cgi?index=$in{'index'}&view=$in{'view'}&type=$in{'type'}&sort=$in{'sort'}", $text{'recs_return'});
	}
else {
	# Delete them
	@recs = &read_zone_file($zone->{'file'}, $dom);

	foreach $d (sort { $b <=> $a } @d) {
		$r = $recs[$d];
		if ($in{'rev'}) {
			# Find the reverse
			$fulloldvalue0 = &convert_to_absolute(
						$r->{'values'}->[0], $dom);
			$fulloldname = &convert_to_absolute(
						$r->{'name'}, $dom);
			($orevconf, $orevfile, $orevrec) = &find_reverse(
					$r->{'values'}->[0], $in{'view'});

			if ($orevrec && &can_edit_reverse($orevconf) &&
			    $fulloldname eq $orevrec->{'values'}->[0] &&
			    ($r->{'type'} eq "A" &&
			     $r->{'values'}->[0] eq &arpa_to_ip($orevrec->{'name'}) ||
			     $r->{'type'} eq "AAAA" &&
			     &expandall_ip6($r->{'values'}->[0]) eq &expandall_ip6(&ip6int_to_net($orevrec->{'name'})))) {
				&lock_file(&make_chroot($orevrec->{'file'}));
				&delete_record($orevrec->{'file'} , $orevrec);
				&lock_file(&make_chroot($orevfile));
				@orrecs = &read_zone_file($orevfile, $orevconf->{'name'});
				if (!$bumpedrev{$orevfile}++) {
					&bump_soa_record($orevfile, \@orrecs);
					}
				&sign_dnssec_zone_if_key($orevconf, \@orrecs);
				}
			}

		# Delete the actual record
		&lock_file(&make_chroot($r->{'file'}));
		&delete_record($r->{'file'}, $r);
		splice(@recs, $d, 1);
		}
	&bump_soa_record($zone->{'file'}, \@recs);
	&sign_dnssec_zone_if_key($zone, \@recs);
	&unlock_all_files();

	&webmin_log("delete", "recs", scalar(@d));
	&redirect("edit_recs.cgi?index=$in{'index'}&view=$in{'view'}&type=$in{'type'}&sort=$in{'sort'}");
	}


