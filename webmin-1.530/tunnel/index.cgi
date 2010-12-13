#!/usr/local/bin/perl
# Either redirects to link.cgi, if a URL has been set, or asks for a URL

require './tunnel-lib.pl';
if ($config{'url'}) {
	&redirect("link.cgi/$config{'url'}");
	}
else {
	# Ask for a URL
	&ui_print_header(undef, $module_info{'desc'}, "", undef, 1, 1);
	print &ui_form_start("seturl.cgi");
	print "<b>$text{'index_url'}</b>\n";
	print &ui_textbox("url", undef, 50),"\n";
	print &ui_submit($text{'index_open'}),"\n";
	print &ui_form_end();
	&ui_print_footer("/", $text{'index'});
	}

