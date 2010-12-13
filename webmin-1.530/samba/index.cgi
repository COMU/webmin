#!/usr/local/bin/perl
# index.cgi
# Display a list of available samba shares. Special shares (like [homes] and
# [printers]) are included as well.

require './samba-lib.pl';

# Check for Samba executable
if (!-x $config{'samba_server'}) {
	&ui_print_header(undef, $text{'index_title'}, "", undef, 1, 1, 0,
		&help_search_link("samba", "man", "doc", "google"));
	print &text('error_nosamba', $config{'samba_server'}, "$gconfig{'webprefix'}/config.cgi?$module_name"),"<p>\n";

	&foreign_require("software", "software-lib.pl");
	$lnk = &software::missing_install_link("samba", $text{'index_samba'},
			"../$module_name/", $text{'index_title'});
	print $lnk,"<p>\n" if ($lnk);

	&ui_print_footer("/", $text{'index'});
	exit;
	}

# Check the samba version
if ($samba_version = &get_samba_version(\$out, 0)) {
	# Save version number
	&open_tempfile(VERSION, ">$module_config_directory/version");
	&print_tempfile(VERSION, $samba_version,"\n");
	&close_tempfile(VERSION);
	}
else {
	&ui_print_header(undef, $text{'index_title'}, "", undef, 1, 1, 0,
		&help_search_link("samba", "man", "doc", "google"));
	print &text('error_version', $config{'samba_server'},
		    "$gconfig{'webprefix'}/config.cgi?$module_name"),"<p>\n";
	print "<pre>$out</pre>\n";
	&ui_print_footer("/", $text{'index'});
	exit;
	}
&ui_print_header(undef, $text{'index_title'}, "", undef, 1, 1, 0,
	&help_search_link("samba", "man", "doc", "google"), undef, undef,
	&text('index_version', &get_samba_version(\$out, 1)));

@empty = &list_shares();
if (!@empty && (-r $config{alt_smb_conf})) {
	# Copy the sample smb.conf file to the real location
	# This is a hack for slackware
	system("cp $config{alt_smb_conf} $config{smb_conf} >/dev/null 2>&1");
	}
if (!(-r $config{smb_conf})) {
	print &text('error_config', $config{'smb_conf'}, "$gconfig{'webprefix'}/config.cgi?$module_name");
	print "<p>\n";
	&ui_print_footer("/", $text{'index'});
	exit;
	}

# Check for 'config' or 'include' directives
&get_share("global");
if (&getval("config") || &getval("include")) {
	print &text('index_einclude',
		    "<tt>$config{'smb_conf'}</tt>",
		    "<tt>config</tt>", "<tt>include</tt>"),"<p>\n";
	}

# Work out links for adding things
@links = ( );
push(@links, "<a href=edit_fshare.cgi>$text{'index_createfileshare'}</a>")
	if ($access{'c_fs'});
push(@links, "<a href=edit_pshare.cgi>$text{'index_createprnshare'}</a>")
	if ($access{'c_ps'});
push(@links, "<a href=create_copy.cgi>$text{'index_createcopy'}</a>")
	if ($access{'copy'});
push(@links, "<a href=view_users.cgi>$text{'index_view'}</a>")
	if ($access{'view_all_con'});

foreach $s (&list_shares()) {
	next unless &can('r', \%access, $s) || !$access{'hide'};
	$us = "share=".&urlize($s);
	if ($s eq "global") { next; }
	if (!$donefirst) {
		# Show headers
		@tds = ( "width=5" );
		print &ui_form_start("delete_shares.cgi", "post");
		unshift(@links, &select_all_link("d"),
				&select_invert_link("d"));
		print &ui_links_row(\@links);
		print &ui_columns_start([
			"",
			$text{'index_sharename'},
			$text{'index_path'},
			$text{'index_security'} ], 100, 0, \@tds);
		$donefirst = 1;
		}

	# Show share details
	&get_share($s);
	local @cols;
	if ($cp = &getval("copy")) { $cp = "(copy of <i>$cp</i>)"; }
	if (&istrue("printable")) {
		push(@cols, "<a href=\"edit_pshare.cgi?$us\">".
			    &html_escape($s)."</a> $cp");
		}
	else {
		push(@cols, "<a href=\"edit_fshare.cgi?$us\">".
			    &html_escape($s)."</a> $cp");
		}

	# Output location / path info
	if ($s eq "homes") {
		$p = "<i>$text{'index_homedir'}</i>";
		}
	elsif ($s eq "printers") {
		$p = "<i>$text{'index_allprinter'}</i>";
		}
	elsif (&istrue("printable")) {
		$p = &getval("printer") ? $text{'index_printer'}." ".&html_escape(&getval("printer")) : $text{'index_defaultprn'};
		}
	else {
		$p = &html_escape(&getval("path"));
		}
	push(@cols, $p);

	# Output security information
	if (&istrue("printable")) {
		if (&getval("valid users")) {
			# Only accessible to some users..
			$sc = $text{'index_printableto'}." ".
				&user_list(&getval("valid users"));
			}
		elsif (&istrue("public")) {
			# Accessible to everyone
			$sc = $text{'index_prneveryone'};
			}
		else {
			$sc = $text{'index_prnalluser'};
			}
		}
	elsif (&istrue("writable")) {
		# Default is read/write access
		if (&istrue("public")) {
			# No password needed..
			$sc = $text{'index_rwpublic'};
			}
		else {
			# Password needed..
			if (&getval("read list")) {
				$sc = &text('index_readonly', &user_list(&getval("read list")));
				}
			else {
				$sc = $text{'index_rwalluser'};
				}
			}
		}
	else {
		# Default is read-only access
		if (&istrue("public")) {
			# No password needed..
			$sc = $text{'index_roeveryone'};
			}
		else {
			# Password needed..
			if (&getval("write list")) {
				$sc = &text('index_readwrite', &user_list(&getval("write list")));
				}
			else {
				$sc = $text{'index_roalluser'};
				}
			}
		}
	push(@cols, $sc);
	print &ui_checked_columns_row(\@cols, \@tds, "d", $s);
	}
if ($donefirst) {
	print &ui_columns_end();
	}
else {
	print "<b>$text{'index_noshares'}</b>. <p>\n";
	}
print &ui_links_row(\@links);
if ($donefirst) {
	print &ui_form_end([ [ "delete", $text{'index_delete'} ] ]);
	}

@gc_acl = qw(conf_net conf_smb conf_pass conf_print conf_misc conf_bind
			  ACLfs_global ACLps_global manual swat winbind);
@gc_progs = ("conf_net.cgi", "conf_smb.cgi", "conf_pass.cgi",
	     "conf_print.cgi", "conf_misc.cgi", "conf_bind.cgi",
	     "edit_fshare.cgi?share=global", "edit_pshare.cgi?share=global",
	     "edit_manual.cgi");
@gc_names = ($text{'global_unixnetwork'}, $text{'global_winnetwork'},
	     $text{'global_auth'}, $text{'global_printing'},
	     $text{'global_misc'}, $text{'global_bind'},
	     $text{'global_filedefault'},
	     $text{'global_prndefault'},
	     $text{'manual_title'});
@gc_icons = ("images/icon_0.gif", "images/icon_1.gif", "images/icon_2.gif",
	     "images/icon_3.gif", "images/icon_4.gif",
	     "images/icon_10.gif", "images/icon_5.gif", "images/icon_6.gif",
	     "images/manual.gif");
if (&has_command($config{'swat_path'})) {
	push(@gc_progs, "swat.cgi");
	push(@gc_names, "SWAT");
	push(@gc_icons, "images/icon_9.gif");
	}

foreach $i (0..$#gc_acl) {
	next unless ($access{$gc_acl[$i]} && $gc_progs[$i]);
	next if ($gc_acl[$i] eq "conf_winbind" && $samba_version < 3);
	push(@gc_progs1, $gc_progs[$i]);
	push(@gc_names1, $gc_names[$i]);
	push(@gc_icons1, $gc_icons[$i]);
	$disp++;
	}

if ($disp) {
	print &ui_hr();
	print &ui_subheading($text{'global_title'});
	&icons_table(\@gc_progs1, \@gc_names1, \@gc_icons1, 4);
	}

# Generate table of accessible user and group editing icons
if ($access{'view_users'}) {
	push(@utitles, $text{'global_edit'});
	push(@ulinks, "edit_epass.cgi");
	push(@uicons, "images/editepass.gif");
	}
if ($access{'maint_makepass'}) {
	push(@utitles, $text{'global_convert'});
	push(@ulinks, "ask_epass.cgi");
	push(@uicons, "images/askepass.gif");
	}
if ($access{'maint_sync'}) {
	push(@utitles, $text{'global_sync'});
	push(@ulinks, "edit_sync.cgi");
	push(@uicons, "images/editsync.gif");
	}
if ($samba_version >= 3) {
	if ($access{'maint_groups'}) {
		push(@utitles, $text{'global_gedit'});
		push(@ulinks, "list_groups.cgi");
		push(@uicons, "images/listgroups.gif");
		}
	if ($access{'maint_gsync'}) {
		push(@utitles, $text{'global_gsync'});
		push(@ulinks, "edit_gsync.cgi");
		push(@uicons, "images/editgsync.gif");
		}
	if ($access{'winbind'} && $has_net) {
		push(@utitles, $text{'global_winbind'});
		push(@ulinks, "edit_winbind.cgi");
		push(@uicons, "images/winbind.gif");
		}
	}

if (@utitles) {
	# We have some icons to show
	print &ui_hr();
	print &ui_subheading($text{'global_users'});
	&icons_table(\@ulinks, \@utitles, \@uicons, 3);
	}

if ($access{'apply'}) {
	$isrun = &is_samba_running();
	print &ui_hr();
	print &ui_buttons_start();
	if ($isrun == 0) {
		# Start button
		print &ui_buttons_row("start.cgi", $text{'index_start'},
				      $text{'index_startmsg'});
		}
	elsif ($isrun == 1) {
		# Restart / stop buttons
		print &ui_buttons_row("restart.cgi", $text{'index_restart'},
				      $text{'index_restartmsg'}."\n".
				      $text{'index_restartmsg2'});
		print &ui_buttons_row("stop.cgi", $text{'index_stop'},
				      $text{'index_stopmsg'});
		}
	print &ui_buttons_end();
	}

&ui_print_footer("/", $text{'index'});

