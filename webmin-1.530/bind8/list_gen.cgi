#!/usr/local/bin/perl
# list_gen.cgi
# Display $generate entries

require './bind8-lib.pl';
&ReadParse();
$access{'gen'} || &error($text{'gen_ecannot'});
$zone = &get_zone_name($in{'index'}, $in{'view'});
$dom = $zone->{'name'};
&can_edit_zone($zone) ||
	&error($text{'recs_ecannot'});
$desc = &text('recs_header', &ip6int_to_net(&arpa_to_ip($dom)));
&ui_print_header($desc, $text{'gen_title'}, "",
		 undef, undef, undef, undef, &restart_links($zone));

@gens = grep { $_->{'generate'} } &read_zone_file($zone->{'file'}, $dom);
print "$text{'gen_desc'}<p>\n";
print &ui_form_start("save_gen.cgi", "post");
print &ui_hidden("index", $in{'index'});
print &ui_hidden("view", $in{'view'});

print &ui_columns_start([ $text{'gen_type'}, $text{'gen_range'},
			  $text{'gen_name'}, $text{'gen_value'},
			  $text{'gen_cmt'} ], 100);
$i = 0;
if ($bind_version >= 9) {
	@types = ( 'PTR', 'CNAME', 'NS', 'A', 'AAAA', 'DNAME' );
	}
else {
	@types = ( 'PTR', 'CNAME', 'NS' );
	}
foreach $g (@gens, { }) {
	@gv = @{$g->{'generate'}};
	@cols = ( );
	local @r = $gv[0] =~ /^(\d+)-(\d+)(\/(\d+))?$/ ? ( $1, $2, $4 ) : ( );
	push(@cols, &ui_select("type_$i", uc($gv[2]),
		[ [ '', '&nbsp;' ],
		  map { uc($_) } @types ]));
	push(@cols, &ui_textbox("start_$i", $r[0], 3)." - ".
		    &ui_textbox("stop_$i", $r[1], 3)." $text{'gen_skip'} ".
		    &ui_textbox("skip_$i", $r[2], 3));
	push(@cols, &ui_textbox("name_$i", $gv[1], 20));
	push(@cols, &ui_textbox("value_$i", $gv[3], 20));
	push(@cols, &ui_textbox("cmt_$i", join(" ", @gv[4..$#gv]), 25));
	print &ui_columns_row(\@cols);
	$i++;
	}
print &ui_columns_end();
@buts = ( [ undef, $text{'save'} ] );
if (@gens) {
	push(@buts, [ "show", $text{'gen_show'} ]);
	}
print &ui_form_end(\@buts);

&ui_print_footer("edit_master.cgi?index=$in{'index'}&view=$in{'view'}",
	$text{'master_return'});

