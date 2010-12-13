#!/usr/local/bin/perl
# edit_slave.cgi
# Display records and other info for an existing slave or stub zone

require './bind8-lib.pl';
&ReadParse();
if ($in{'zone'}) {
	$zone = &get_zone_name($in{'zone'}, 'any');
	$in{'index'} = $zone->{'index'};
	$in{'view'} = $zone->{'viewindex'};
	}
else {
	$zone = &get_zone_name($in{'index'}, $in{'view'});
	}
$dom = $zone->{'name'};
&can_edit_zone($zone) ||
	&error($text{'slave_ecannot'});

$desc = &ip6int_to_net(&arpa_to_ip($dom));
if ($zone->{'file'}) {
	@st = stat(&make_chroot(&absolute_path($zone->{'file'})));
	$lasttrans = &text('slave_last', @st && $st[7] ? &make_date($st[9])
					     	       : $text{'slave_never'});
	}
&ui_print_header($desc, $0 =~ /edit_slave/ ? $text{'slave_title'}
					   : $text{'stub_title'},
		 "", undef, 0, 0, 0, &restart_links($zone),
		 undef, undef, $lasttrans);

if ($zone->{'file'}) {
	print "<p>\n";
	@recs = &read_zone_file($zone->{'file'}, $dom);
	if ($dom =~ /in-addr\.arpa/i || $dom =~ /\.$ipv6revzone/i) {
		@rcodes = &get_reverse_record_types();
		}
	else {
		@rcodes = &get_forward_record_types();
		}
	foreach $c (@rcodes) { $rnum{$c} = 0; }
	foreach $r (@recs) {
		$rnum{$r->{'type'}}++;
		if ($r->{'type'} eq "SOA") { $soa = $r; }
		}
	if ($config{'show_list'}) {
		# display as list
		$mid = int((@rcodes+1)/2);
		@grid = ( );
		push(@grid, &types_table(@rcodes[0..$mid-1]));
		push(@grid, &types_table(@rcodes[$mid..$#rcodes]));
		print &ui_grid_table(\@grid, 2, 100,
			[ "width=50%", "width=50%" ]);
		}
	else {
		# display as icons
		for($i=0; $i<@rcodes; $i++) {
			push(@rlinks, "edit_recs.cgi?index=$in{'index'}".
				      "&view=$in{'view'}&type=$rcodes[$i]");
			push(@rtitles, $text{"type_$rcodes[$i]"}.
				       " ($rnum{$rcodes[$i]})");
			push(@ricons, "images/$rcodes[$i].gif");
			}
		&icons_table(\@rlinks, \@rtitles, \@ricons);
		}
	$done_recs = 1;
	}

# Shut buttons for editing, options and whois
if ($access{'file'} && $zone->{'file'}) {
	push(@links, "view_text.cgi?index=$in{'index'}&view=$in{'view'}");
	push(@titles, $text{'slave_manual'});
	push(@images, "images/text.gif");
	}
if ($access{'opts'}) {
	push(@links, "edit_soptions.cgi?index=$in{'index'}&view=$in{'view'}");
	push(@titles, $text{'master_options'});
	push(@images, "images/options.gif");
	}
if ($access{'whois'} && &has_command($config{'whois_cmd'}) &&
    $dom !~ /in-addr\.arpa/i) {
	push(@links, "whois.cgi?index=$in{'index'}&view=$in{'view'}");
	push(@titles, $text{'master_whois'});
	push(@images, "images/whois.gif");
	}
if (@links) {
	print &ui_hr() if ($done_recs);
	&icons_table(\@links, \@titles, \@images);
	}

$apply = $access{'apply'} && &has_ndc();
if (!$access{'ro'} && ($access{'delete'} || $apply)) {
	print &ui_hr();
	print &ui_buttons_start();

	# Move to other view
	$conf = &get_config();
	print &move_zone_button($conf, $in{'view'}, $in{'index'});

	# Convert to master zone
	if ($access{'master'} && $st[7]) {
		print &ui_buttons_row("convert_slave.cgi",
			$text{'slave_convert'},
			$text{'slave_convertdesc'},
			&ui_hidden("index", $in{'index'}).
			&ui_hidden("view", $in{'view'}));
		}

	# Delete zone
	if ($access{'delete'}) {
		print &ui_buttons_row("delete_zone.cgi",
			$text{'master_del'}, $text{'slave_delmsg'},
			&ui_hidden("index", $in{'index'}).
			&ui_hidden("view", $in{'view'}));
		}

	print &ui_buttons_end();
	}

&ui_print_footer("", $text{'index_return'});

sub types_table
{
my $rv;
if ($_[0]) {
	$rv .= &ui_columns_start([
		$text{'master_type'},
		$text{'master_records'},
		], 100);
	for(my $i=0; $_[$i]; $i++) {
		local @cols = ( "<a href=\"edit_recs.cgi?".
		      "index=$in{'index'}&view=$in{'view'}&type=$_[$i]\">".
		      ($text{"recs_$_[$i]"} || $_[$i])."</a>",
		      $rnum{$_[$i]} );
		$rv .= &ui_columns_row(\@cols);
		}
	$rv .= &ui_columns_end();
	}
return $rv;
}

