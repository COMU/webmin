#!/usr/local/bin/perl
# Show a page of icons for various PHP config sections

require './phpini-lib.pl';
&ReadParse();
&can_php_config($in{'file'}) || &error($text{'list_ecannot'});

# Work out if we can just see one file
@files = &list_php_configs();
if (@files == 1 && !$access{'anyfile'} && $access{'noconfig'}) {
	$onefile = 1;
	}

&ui_print_header("<tt>$in{'file'}</tt>", $text{'list_title'}, "", undef, 0,
		 $onefile);

@pages = ( "vars", "dirs", "db", "session", "safe", "limits",
	   "errors", "misc" );
@links = map { "edit_${_}.cgi?file=".&urlize($in{'file'}) } @pages;
@titles = map { $text{$_."_title"} } @pages;
@icons = map { "images/$_.gif" } @pages;
&icons_table(\@links, \@titles, \@icons, 4);

if ($onefile) {
	&ui_print_footer("/", $text{'index'});
	}
else {
	&ui_print_footer("", $text{'index_return'});
	}

