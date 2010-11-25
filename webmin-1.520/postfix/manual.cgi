#!/usr/local/bin/perl
# Show a page for manually editing the Postfix config file

require './postfix-lib.pl';
$access{'manual'} || &error($text{'cmanual_ecannot'});
&ReadParse();
&ui_print_header(undef, $text{'cmanual_title'}, "");

# Work out and show the files
@files = ( $config{'postfix_config_file'}, $config{'postfix_master'} );
$in{'file'} ||= $files[0];
&indexof($in{'file'}, @files) >= 0 || &error($text{'cmanual_efile'});
print &ui_form_start("manual.cgi");
print "<b>$text{'cmanual_file'}</b>\n";
print &ui_select("file", $in{'file'},
		 [ map { [ $_ ] } @files ]),"\n";
print &ui_submit($text{'cmanual_ok'});
print &ui_form_end();

# Show the file contents
print &ui_form_start("manual_update.cgi", "form-data");
print &ui_hidden("file", $in{'file'}),"\n";
$data = &read_file_contents($in{'file'});
print &ui_textarea("data", $data, 20, 80),"\n";
print &ui_form_end([ [ "save", $text{'save'} ] ]);

&ui_print_footer("", $text{'index_return'});

