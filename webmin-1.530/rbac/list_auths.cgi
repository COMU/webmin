#!/usr/local/bin/perl
# Show a table of all authiles

require './rbac-lib.pl';
$access{'auths'} || &error($text{'auths_ecannot'});
&ui_print_header(undef, $text{'auths_title'}, "", "auths");

$auths = &list_auth_attrs();
if (@$auths) {
	print "<a href='edit_auth.cgi?new=1'>$text{'auths_add'}</a><br>\n";
	print &ui_columns_start(
		[ $text{'auths_name'},
		  $text{'auths_desc'} ]);
	foreach $a (sort { $a->{'name'} cmp $b->{'name'} } @$auths) {
		print &ui_columns_row(
			[ "<a href='edit_auth.cgi?idx=$a->{'index'}'>$a->{'name'}</a>",
			  &rbac_help_link($a, $a->{'short'} || $a->{'desc'}),
			]);
		}
	print &ui_columns_end();
	}
else {
	print "<b>$text{'auths_none'}</b><p>\n";
	}
print "<a href='edit_auth.cgi?new=1'>$text{'auths_add'}</a><br>\n";

&ui_print_footer("", $text{"index_return"});

