#!/usr/local/bin/perl
# Show all scheduled backups, and a form for doing an immediate one

require './backup-config-lib.pl';
&ReadParse();
&ui_print_header(undef, $text{'index_title'}, "", undef, 1, 1);
@mods = &list_backup_modules();
if (!@mods) {
	&ui_print_endpage($text{'index_emods'});
	}
%mods = map { $_->{'dir'}, $_ } @mods;

# Show tabs
@tabs = ( [ "backup", $text{'index_tabbackup'}, "index.cgi?mode=backup" ],
	  [ "sched", $text{'index_tabsched'}, "index.cgi?mode=sched" ],
	  [ "restore", $text{'index_tabrestore'}, "index.cgi?mode=restore" ],
	);
print &ui_tabs_start(\@tabs, "tab", $in{'mode'} || "backup", 1);

print &ui_tabs_start_tab("tab", "sched");
@backups = &list_backups();
if (@backups) {
	# Show all scheduled backups
	print "<a href='edit.cgi?new=1'>$text{'index_add'}</a><br>\n";
	print &ui_columns_start([ $text{'index_dest'},
			    	  $text{'index_mods'},
			    	  $text{'index_sched'} ], 100);
	foreach $b (@backups) {
		local @m = map { $mods{$_}->{'desc'} }
			       split(/\s+/, $b->{'mods'});
		print &ui_columns_row(
			[ "<a href='edit.cgi?id=$b->{'id'}'>".
			  &nice_dest($b->{'dest'})."</a>",
			  @m > 5 ? &text('index_count', scalar(@m))
				 : join(", ", @m),
			  $b->{'sched'} ? &text('index_when',
				&cron::when_text($b)) : $text{'no'} ]);
		$using_strftime++ if ($b->{'dest'} =~ /%/);
		}
	print &ui_columns_end();
	}
else {
	print "<b>$text{'index_none'}</b><p>\n";
	}
print "<a href='edit.cgi?new=1'>$text{'index_add'}</a><p>\n";
if ($using_strftime && !$config{'date_subs'}) {
	print "<font color=#ff0000><b>$text{'index_nostrftime'}",
	      "</b></font><p>\n";
	}
print &ui_tabs_end_tab();

# Show immediate form
print &ui_tabs_start_tab("tab", "backup");
print &ui_form_start("backup.cgi/backup.tgz", "post");
print &ui_table_start($text{'index_header'}, undef, 2);

@dmods = split(/\s+/, $config{'mods'});
print &ui_table_row($text{'edit_mods'},
		    &ui_select("mods", \@dmods,
		       [ map { [ $_->{'dir'}, $_->{'desc'} ] } @mods ],
		       5, 1));

print &ui_table_row($text{'edit_dest'},
		    &show_backup_destination("dest", $config{'dest'}, 2));

print &ui_table_row($text{'edit_what'},
		    &show_backup_what("what", $config{'configfile'},
					      $config{'nofiles'}));

print &ui_table_end();
print &ui_form_end([ [ 'backup', $text{'index_now'} ] ]);

print &ui_tabs_end_tab();

# Show restore form
print &ui_tabs_start_tab("tab", "restore");
print &ui_form_start("restore.cgi", "form-data");
print &ui_table_start($text{'index_header2'}, undef, 2);

@dmods = split(/\s+/, $config{'mods'});
print &ui_table_row($text{'edit_mods2'},
		    &ui_select("mods", \@dmods,
		       [ map { [ $_->{'dir'}, $_->{'desc'} ] } @mods ],
		       5, 1));

print &ui_table_row($text{'edit_dest2'},
		    &show_backup_destination("src", $config{'dest'}, 1));

print &ui_table_row($text{'index_apply'},
		    &ui_yesno_radio("apply", $config{'apply'} ? 1 : 0));

print &ui_table_row($text{'index_test'},
		    &ui_yesno_radio("test", 0));

print &ui_table_end();
print &ui_form_end([ [ 'restore', $text{'index_now2'} ] ]);

print &ui_tabs_end_tab();
print &ui_tabs_end(1);

&ui_print_footer("/", $text{'index'});

