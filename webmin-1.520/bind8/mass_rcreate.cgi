#!/usr/local/bin/perl
# Add a record to multiple domains

require './bind8-lib.pl';
&ReadParse();
$conf = &get_config();
&error_setup($text{'rmass_err'});

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
&valdnsname($in{'name'}) || $in{'name'} eq '@' || &error($text{'rmass_ename'});
$in{'name'} =~ /\.$/ && &error($text{'rmass_ename2'});
if ($in{'type'} eq 'A') {
	&check_ipaddress($in{'value'}) ||
		&error(&text('edit_eip', $in{'value'}));
	}
elsif ($in{'type'} eq 'AAAA') {
	&check_ip6address($in{'value'}) ||
		&error(&text('edit_eip6', $in{'value'}));
	}
elsif ($in{'type'} eq 'NS') {
	&valname($in{'value'}) ||
		&error(&text('edit_ens', $in{'value'}));
	}
elsif ($in{'type'} eq 'CNAME') {
	&valname($in{'value'}) || $in{'value'} eq '@' ||
		&error(&text('edit_ecname', $in{'value'}));
	}
elsif ($in{'type'} eq 'MX') {
	$in{'value'} =~ /^(\d+)\s+(\S+)$/ && &valname("$2") ||
		&error(&text('emass_emx', $in{'value'}));
	}
elsif ($in{'type'} eq 'TXT') {
	$in{'value'} = "\"$in{'value'}\"";
	}
elsif ($in{'type'} eq 'PTR') {
	&valname($in{'value'}) ||
		&error(&text('edit_eptr', $in{'value'}));
	}
$in{'ttl_def'} || $in{'ttl'} =~ /^\d+$/ ||
	&error($text{'rmass_ettl'});

# Do each one
&ui_print_unbuffered_header(undef, $text{'rmass_title'}, "");

foreach $zi (@zones) {
	print &text('rmass_doing', "<tt>$zi->{'name'}</tt>"),"<br>\n";
	if ($zi->{'type'} ne 'master') {
		# Skip - not a master zone
		print $text{'umass_notmaster'},"<p>\n";
		next;
		}
	$fullname = $in{'name'} eq '@' ?
			$zi->{'name'}."." :
			$in{'name'}.".".$zi->{'name'}.".";
	@recs = &read_zone_file($zi->{'file'}, $zi->{'name'});
	if ($in{'type'} eq 'CNAME' || $in{'clash'}) {
		# Check if a record with the same name exists
		($clash) = grep { $_->{'name'} eq $fullname &&
				  $_->{'type'} eq $in{'type'} } @recs;
		if ($clash) {
			print &text('rmass_eclash',
			    "<tt>".join(" ", @{$clash->{'values'}})."</tt>"),
			    "<p>\n";
			next;
			}
		}
	# Check if a record with the same name and value exists
	($clash) = grep { $_->{'name'} eq $fullname &&
			  $_->{'type'} eq $in{'type'} &&
			  join(" ", @{$_->{'values'}}) eq $in{'value'} } @recs;
	if ($clash) {
		print &text('rmass_eclash2',
		    "<tt>".join(" ", @{$clash->{'values'}})."</tt>"),"<p>\n";
		next;
		}
	&create_record($zi->{'file'}, $in{'name'}, $in{'ttl'}, "IN",
		       $in{'type'}, $in{'value'});
	&bump_soa_record($zi->{'file'}, \@recs);
	&sign_dnssec_zone_if_key($zi, \@recs);
	print $text{'rmass_done'},"<p>\n";
	}

&unlock_all_files();
&webmin_log("rcreate", "zones", scalar(@zones));

&ui_print_footer("", $text{'index_return'});

# valname(name)
sub valname
{
return valdnsname($_[0], 0, $in{'origin'});
}

