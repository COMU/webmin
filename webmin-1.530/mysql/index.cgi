#!/usr/local/bin/perl
# index.cgi
# Display all existing databases

require './mysql-lib.pl';
&ReadParse();

# Check for MySQL programs
foreach $p ( [ $config{'mysqladmin'}, 'index_eadmin', 'index_mysqladmin' ],
	     [ $config{'mysql'}, 'index_esql', 'index_mysql' ],
	     [ $config{'mysqlshow'}, 'index_eshow', 'index_mysqlshow' ]) {
	if (!-x $p->[0]) {
		&ui_print_header(undef, $text{'index_title'}, "", "intro", 1, 1, 0,
			&help_search_link("mysql", "man", "doc", "google"));
		print &text($p->[1], "<tt>$p->[0]</tt>",
			  "$gconfig{'webprefix'}/config.cgi?$module_name"),"<p>\n";

		&foreign_require("software", "software-lib.pl");
		$lnk = &software::missing_install_link(
				"mysql", $text{$p->[2]},
				"../$module_name/", $text{'index_title'});
		print $lnk,"<p>\n" if ($lnk);

		&ui_print_footer("/", $text{'index'});
		exit;
		}
	}

# Try to get the MySQL version
$mysql_version = &get_mysql_version(\$out);
if ($mysql_version < 0) {
	&ui_print_header(undef, $text{'index_title'}, "", "intro", 1, 1, 0,
		&help_search_link("mysql", "man", "doc", "google"));
	print &text('index_elibrary', "<tt>$config{'mysql'}</tt>",
		  "../config.cgi?$module_name"),"<p>\n";
	print &text('index_mysqlver', "$config{'mysql'} -V"),"\n";
	print "<pre>$out</pre>\n";
	&ui_print_footer("/", $text{'index'});
	exit;
	}
elsif (!$mysql_version) {
	&ui_print_header(undef, $text{'index_title'}, "", "intro", 1, 1, 0,
		&help_search_link("mysql", "man", "doc", "google"));
	print &text('index_ever', "<tt>$config{'mysql'}</tt>",
		  "../config.cgi?$module_name"),"<p>\n";
	print &text('index_mysqlver', "$config{'mysql'} -V"),"\n";
	print "<pre>$out</pre>\n";
	&ui_print_footer("/", $text{'index'});
	exit;
	}
open(VERSION, ">$module_config_directory/version");
print VERSION $mysql_version,"\n";
close(VERSION);

# Check if MYSQL_PWD works
($r, $rout) = &is_mysql_running();
if ($r > 0 && !&working_env_pass()) {
	&ui_print_header(undef, $text{'index_title'}, "", "intro", 1, 1, 0,
		&help_search_link("mysql", "man", "doc", "google"));
	print &text('index_eenvpass', "<tt>$config{'mysql'}</tt>",
		    "../config.cgi?$module_name"),"<p>\n";
	&ui_print_footer("/", $text{'index'});
	exit;
	}

if ($r == 0) {
	# Not running .. need to start it
	&main_header();
	print "<p> <b>$text{'index_notrun'}</b> <p>\n";

	if ($access{'stop'} && &is_mysql_local()) {
		print &ui_hr();
		print "<form action=start.cgi>\n";
		print "<table width=100%><tr><td>\n";
		print "<input type=submit ",
		      "value=\"$text{'index_start'}\"></td>\n";
		print "<td>",&text('index_startmsg',
		      "<tt>$config{'start_cmd'}</tt>"),"</td> </tr></table>\n";
		print "</form>\n";
		}
	}
elsif ($r == -1) {
	# Running, but webmin doesn't know the root (or user's) password!
	&main_header();
	print "<b>$text{'index_nopass'}</b> <p>\n";

	print &ui_form_start("login.cgi", "post");
	print &ui_table_start($text{'index_ltitle'}, undef, 2);

	print &ui_table_row($text{'index_login'},
		&ui_textbox("login", $access{'user'} || $config{'login'}, 40));

	print &ui_table_row($text{'index_pass'},
		&ui_password("pass", undef, 40));

	print &ui_table_end();
	print &ui_form_end([ [ undef, $text{'save'} ] ]);

	print &text('index_emsg', "<tt>$rout</tt>"),"<p>\n";
	}
else {
	# Check if we can re-direct to a single DB's page
	@alldbs = &list_databases();
	@titles = grep { &can_edit_db($_) } @alldbs;
	$can_all = (@alldbs == @titles);
	if (@titles == 1 && $access{'dbs'} ne '*' && !$access{'perms'} &&
	    !$access{'stop'} && !$access{'create'} && $access{'noconfig'}) {
		# Only one DB, so go direct to it!
		&redirect("edit_dbase.cgi?db=$titles[0]");
		exit;
		}

	&main_header();
	print &ui_subheading($text{'index_dbs'}) if ($access{'perms'});
	if ($in{'search'}) {
		# Limit to those matching search
		@titles = grep { /\Q$in{'search'}\E/i } @titles;
		print "<table width=100%><tr>\n";
		print "<td> <b>",&text('index_showing',
		    "<tt>".&html_escape($in{'search'})."</tt>"),"</b></td>\n";
		print "<td align=right><a href='index.cgi'>",
			"$text{'view_searchreset'}</a></td>\n";
		print "</tr></table>\n";
		}
	elsif ($in{'show'}) {
		# Limit to specific databases
		%show = map { $_, 1 } split(/\0/, $in{'show'});
		@titles = grep { $show{$_} } @titles;
		}

	# DB is running .. list databases
	@icons = map { "images/db.gif" } @titles;
	@links = map { "edit_dbase.cgi?db=$_" } @titles;
	$can_create = $access{'create'} == 1 ||
		      $access{'create'} == 2 && @titles < $access{'max'};

	@rowlinks = ( );
	push(@rowlinks, "<a href=newdb_form.cgi>$text{'index_add'}</a>")
		if ($can_create);
	if (!@icons) {
		# No databases .. tell user
		if (@alldbs) {
			print "<b>$text{'index_nodbs'}</b> <p>\n";
			}
		else {
			print "<b>$text{'index_nodbs2'}</b> <p>\n";
			}
		}
	elsif (@icons > $max_dbs && !$in{'search'} && !$in{'show'}) {
		# Too many databases to show .. display search and jump forms
		print &ui_form_start("index.cgi");
		print $text{'index_toomany'},"\n";
		print &ui_textbox("search", undef, 20),"\n";
		print &ui_submit($text{'index_search'}),"<br>\n";
		print &ui_form_end();

		print &ui_form_start("edit_dbase.cgi");
		print $text{'index_jump'},"\n";
		print &ui_select("db", undef, [ map { [ $_ ] } @titles ],
				 1, 0, 0, 0, "onChange='form.submit()'"),"\n";
		print &ui_submit($text{'index_jumpok'}),"<br>\n";
		print &ui_form_end();
		}
	else {
		# Show table of databases
		if ($access{'delete'}) {
			print &ui_form_start("drop_dbases.cgi");
			unshift(@rowlinks, &select_all_link("d", 0),
				           &select_invert_link("d", 0));
			}
		print &ui_links_row(\@rowlinks);
		@checks = @titles;
		if ($displayconfig{'style'} == 1) {
			# Show as DB names and table counts
			@tables = map { @t = &list_tables($_); scalar(@t) }
				      @titles;
			@titles = map { &html_escape($_) } @titles;
			&split_table([ "", $text{'index_db'},
				       $text{'index_tables'} ],
				     \@checks, \@links, \@titles, \@tables)
				if (@titles);
			}
		elsif ($displayconfig{'style'} == 2) {
			# Show just DB names
			@grid = ( );
			for(my $i=0; $i<@links; $i++) {
				push(@grid, &ui_checkbox("d", $titles[$i]).
				  " <a href='$links[$i]'>".
				  &html_escape($titles[$i])."</a>");
				}
			print &ui_grid_table(\@grid, 4, 100, undef, undef, "");
			}
		else {
			# Show name icons
			@checks = map { &ui_checkbox("d", $_) } @checks;
			@titles = map { &html_escape($_) } @titles;
			&icons_table(\@links, \@titles, \@icons, 5,
				     undef, undef, undef, \@checks);
			}
		}
	print &ui_links_row(\@rowlinks);
	if (@icons && $access{'delete'} &&
	    (@icons <= $max_dbs || $in{'search'})) {
		print &ui_form_end([ [ "delete", $text{'index_drops'} ] ]);
		}

	if ($access{'perms'}) {
		# Show icons for editing user permissions and server settings
		print &ui_hr();
		print &ui_subheading($text{'index_global'});
		$canvars = &supports_variables();
		@links = ( 'list_users.cgi', 'list_dbs.cgi', 'list_hosts.cgi',
			   'list_tprivs.cgi', 'list_cprivs.cgi',
			   'edit_cnf.cgi', 'list_procs.cgi',
			   $canvars ? ( 'list_vars.cgi' ) : ( ),
			   'root_form.cgi',
			 );
		@titles = ( $text{'users_title'}, $text{'dbs_title'},
			    $text{'hosts_title'}, $text{'tprivs_title'},
			    $text{'cprivs_title'},$text{'cnf_title'},
			    $text{'procs_title'},
			    $canvars ? ( $text{'vars_title'} ) : ( ),
			    $text{'root_title'},
			  );
		@images = ( 'images/users.gif', 'images/dbs.gif',
			    'images/hosts.gif', 'images/tprivs.gif',
			    'images/cprivs.gif', 'images/cnf.gif',
			    'images/procs.gif',
			    $canvars ? ( 'images/vars.gif' ) : ( ),
			    'images/root.gif',
			  );
		if ($access{'perms'} == 2) {
			# Remove my.cnf and database connections icons
			@links = @links[0..4];
			@titles = @titles[0..4];
			@images = @images[0..4];
			}
		&icons_table(\@links, \@titles, \@images, 5);
		}

	if ($access{'stop'} && &is_mysql_local() ||
	    $can_all && !$access{'edonly'} && $access{'buser'}) {
		print &ui_hr();
		print &ui_buttons_start();
		$started_buttons_row = 1;
		}

	# Show stop button
	if ($access{'stop'} && &is_mysql_local()) {
		print &ui_buttons_row("stop.cgi", $text{'index_stop'},
				      $text{'index_stopmsg'});
		}

	# Show backup all button
	if ($can_all && !$access{'edonly'} && $access{'buser'}) {
		print &ui_buttons_row("backup_form.cgi", $text{'index_backup'},
				      $text{'index_backupmsg'},
				      &ui_hidden("all", 1));
		}

	print &ui_buttons_end() if ($started_buttons_row);

	# Check if the optional perl modules are installed
	if (foreign_available("cpan")) {
		eval "use DBI";
		push(@needs, "DBI") if ($@);
		$nodbi++ if ($@);
		eval "use DBD::mysql";
		push(@needs, "DBD::mysql") if ($@);
		if (@needs) {
			$needs = &urlize(join(" ", @needs));
			print "<center><b>",&text(@needs == 2 ? 'index_nomods' : 'index_nomod', @needs,
				"/cpan/download.cgi?source=3&cpan=$needs&mode=2&return=/$module_name/&returndesc=".&urlize($text{'index_return'})),
				"</b></center>\n";
			}
		}
	}

&ui_print_footer("/", "index");

sub main_header
{
&ui_print_header(undef, $text{'index_title'}, "", "intro", 1, 1, 0,
	&help_search_link("mysql", "man", "doc", "google"),
	undef, undef, &text('index_version', $mysql_version));
}

