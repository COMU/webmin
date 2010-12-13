#!/usr/local/bin/perl
# save_soa.cgi
# Save changes to an SOA record

require './bind8-lib.pl';
&ReadParse();
&error_setup($text{'master_err2'});
$zone = &get_zone_name($in{'index'}, $in{'view'});
$dom = $zone->{'name'};
&can_edit_zone($zone) ||
	&error($text{'master_ecannot'});
$access{'ro'} && &error($text{'master_ero'});
$access{'params'} || &error($text{'master_esoacannot'});

# Get the SOA and file
@recs = &read_zone_file($zone->{'file'}, $dom);
foreach $r (@recs) {
	$soa = $r if ($r->{'type'} eq "SOA");
	}
$soa || &error($text{'master_esoagone'});
$file = $soa->{'file'};

# check inputs
&valdnsname($in{'master'}, 0, $in{'origin'}) ||
	&error(&text('master_emaster', $in{'master'}));
&valemail($in{'email'}) ||
	&error(&text('master_eemail', $in{'email'}));
$in{'refresh'} =~ /^\d+$/ ||
	&error(&text('master_erefresh', $in{'refresh'}));
$in{'retry'} =~ /^\d+$/ ||
	&error(&text('master_eretry', $in{'retry'}));
$in{'expiry'} =~ /^\d+$/ ||
	&error(&text('master_eexpiry', $in{'expiry'}));
$in{'minimum'} =~ /^\d+$/ ||
	&error(&text('master_eminimum', $in{'minimum'}));
if ($in{'email'} =~ /\@/) {
	$in{'email'} = &email_to_dotted($in{'email'});
	}
$in{'defttl_def'} || $in{'defttl'} =~ /^\d+$/ ||
	&error(&text('master_edefttl', $in{'defttl'}));

&lock_file(&make_chroot($file));
@recs = &read_zone_file($file, $in{'origin'});
$old = $recs[$in{'num'}];
# already set serial if no acl allow it to update or update is disabled
$serial = $old->{'values'}->[2];
if ($config{'updserial_on'}) {
	# automatically handle serial numbers ?
	$serial = &compute_serial($old->{'values'}->[2]);
	}
else {
	$in{'serial'} =~ /^\d+$/ || &error($text{'master_eserial'});
	$serial = $in{'serial'};
	}
$vals = "$in{'master'} $in{'email'} (\n".
	"\t\t\t$serial\n".
	"\t\t\t$in{'refresh'}$in{'refunit'}\n".
	"\t\t\t$in{'retry'}$in{'retunit'}\n".
	"\t\t\t$in{'expiry'}$in{'expunit'}\n".
	"\t\t\t$in{'minimum'}$in{'minunit'} )";
&modify_record($file, $old, $old->{'name'}, $old->{'ttl'},
	       $old->{'class'}, "SOA", $vals);

($defttl) = grep { $_->{'defttl'} } @recs;
if (!$defttl && !$in{'defttl_def'}) {
	&create_defttl($file, $in{'defttl'}.$in{'defttlunit'});
	}
elsif ($defttl && !$in{'defttl_def'}) {
	&modify_defttl($file, $defttl, $in{'defttl'}.$in{'defttlunit'});
	}
elsif ($defttl && $in{'defttl_def'}) {
	&delete_defttl($file, $defttl);
	}

&unlock_file(&make_chroot($file));
&webmin_log("soa", undef, $in{'origin'}, \%in);
&redirect("edit_master.cgi?index=$in{'index'}&view=$in{'view'}");

