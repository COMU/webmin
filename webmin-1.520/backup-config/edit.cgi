#!/usr/local/bin/perl
# Show one scheduled backup

require './backup-config-lib.pl';
&ReadParse();
if ($in{'new'}) {
	&ui_print_header(undef, $text{'edit_title1'}, "");
	$backup = { 'emode' => 0,
		    'sched' => 1,
		    'mins' => 0,
		    'hours' => 0,
		    'days' => '*',
		    'months' => '*',
		    'weekdays' => '*' };
	}
else {
	&ui_print_header(undef, $text{'edit_title2'}, "");
	$backup = &get_backup($in{'id'});
	}

print &ui_form_start("save.cgi", "post");
print &ui_hidden("new", $in{'new'});
print &ui_hidden("id", $in{'id'});

@tds = ( "width=30%" );
print &ui_hidden_table_start($text{'edit_header'}, "width=100%", 2,
			     "main", 1, \@tds);

# Show modules to backup
@mods = &list_backup_modules();
@dmods = split(/\s+/, $backup->{'mods'});
print &ui_table_row($text{'edit_mods'},
		    &ui_select("mods", \@dmods,
		       [ map { [ $_->{'dir'}, $_->{'desc'} ] } @mods ],
		       5, 1));

# Show destination
print &ui_table_row($text{'edit_dest'},
		    &show_backup_destination("dest", $backup->{'dest'}, 0));

# Show files to include
print &ui_table_row($text{'edit_what'},
		    &show_backup_what("what", $backup->{'configfile'},
					      $backup->{'nofiles'},
					      $backup->{'others'}));

print &ui_hidden_table_end();

print &ui_hidden_table_start($text{'edit_header2'}, "width=100%", 2,
			     "prepost", 0, \@tds);

# Show pre-backup command
print &ui_table_row($text{'edit_pre'},
		    &ui_textbox("pre", $backup->{'pre'}, 60));

# Show post-backup command
print &ui_table_row($text{'edit_post'},
		    &ui_textbox("post", $backup->{'post'}, 60));

print &ui_hidden_table_end();

print &ui_hidden_table_start($text{'edit_header3'}, "width=100%", 2,
			     "sched", 0, \@tds);

# Show email address
print &ui_table_row($text{'edit_email'},
		    &ui_textbox("email", $backup->{'email'}, 40));

# Show email mode
print &ui_table_row($text{'edit_emode'},
		    &ui_radio("emode", $backup->{'emode'},
			      [ [ 0, $text{'edit_emode0'} ],
				[ 1, $text{'edit_emode1'} ] ]));

# Show schedule
if ($backup) {
	$job = &find_cron_job($backup);
	}
print &ui_table_row($text{'edit_sched'},
		    &ui_radio("sched", $job || $in{'new'} ? 1 : 0,
			      [ [ 0, $text{'no'} ],
				[ 1, $text{'edit_schedyes'} ] ]));
print &ui_table_row(undef,
	"<tr> <td colspan=2><table border width=100%>\n".
	&capture_function_output(\&cron::show_times_input, $backup).
	"</table></td> </tr>\n");

print &ui_hidden_table_end();
if ($in{'new'}) {
	print &ui_form_end([ [ 'create', $text{'create'} ] ], "100%");
	}
else {
	print &ui_form_end([ [ 'save', $text{'save'} ],
			     [ 'run', $text{'edit_run'} ],
			     [ 'delete', $text{'delete'} ] ], "100%");
	}

&ui_print_footer("", $text{'index_return'});


