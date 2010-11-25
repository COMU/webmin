#!/usr/local/bin/perl
# index.cgi
# Display available apache or squid logfiles

require './webalizer-lib.pl';
&foreign_require("cron", "cron-lib.pl");

# Check if webalizer is actually installed
if (!&has_command($config{'webalizer'})) {
	&ui_print_header(undef, $text{'index_title'}, "", undef, 1, 1, 0,
		&help_search_link("webalizer", "man", "doc", "google"));
	print &text('index_ewebalizer', "<tt>$config{'webalizer'}</tt>",
		  "$gconfig{'webprefix'}/config.cgi?$module_name"),"<p>\n";

	&foreign_require("software", "software-lib.pl");
	$lnk = &software::missing_install_link(
			"webalizer", $text{'index_webalizer'},
			"../$module_name/", $text{'index_title'});
	print $lnk,"<p>\n" if ($lnk);

	&ui_print_footer("/", $text{'index'});
	exit;
	}

# Get the version number
$webalizer_version = &get_webalizer_version(\$out);
if (!$webalizer_version) {
	&ui_print_header(undef, $text{'index_title'}, "", undef, 1, 1, 0,
		&help_search_link("webalizer", "man", "doc", "google"));
	print &text('index_egetversion',
			  "<tt>$config{'webalizer'} -v</tt>",
			  "<pre>$out</pre>"),"<p>\n";
	&ui_print_footer("/", $text{'index'});
	exit;
	}

if ($webalizer_version < 2) {
	&main_header();
	print &text('index_eversion', "<tt>$config{'webalizer'}</tt>",
			  "$webalizer_version", "2.0"),"<p>\n";
	&ui_print_footer("/", $text{'index'});
	exit;
	}

# Check if the config file exists
if (!-r $config{'webalizer_conf'}) {
	&main_header();
	print &text('index_econf', "<tt>$config{'webalizer_conf'}</tt>",
		  "$gconfig{'webprefix'}/config.cgi?$module_name"),"<p>\n";
	&ui_print_footer("/", $text{'index'});
	exit;
	}

# Query apache and squid for their logfiles
@logs = &get_all_logs();

# Remove in-accessible logs, and redirect if only one
@logs = grep { &can_edit_log($_->{'file'}) } @logs;
if (@logs == 1 && -r $logs[0]->{'file'} &&
    $access{'noconfig'} && !$access{'add'} && !$access{'global'}) {
	# User can only edit/view one log file ..
	local $l = $logs[0];
	if ($access{'view'}) {
		&redirect("view_log.cgi/".&urlize(&urlize($l->{'file'})).
			  "/index.html");
		}
	else {
		&redirect("edit_log.cgi?file=".&urlize($l->{'file'}).
                	  "&type=$l->{'type'}&custom=$l->{'custom'}");
		}
	exit;
	}

&main_header();
@links = ( );
if (@logs) {
	if (!$access{'view'}) {
		print &ui_form_start("mass.cgi", "post");
		push(@links, &select_all_link("d"),
			     &select_invert_link("d"));
		}
	push(@links, "<a href='edit_log.cgi?new=1'>$text{'index_add'}</a>")
		if (!$access{'view'} && $access{'add'});
	print &ui_links_row(\@links);
	local @tds = ( "width=5" );
	print &ui_columns_start([ $access{'view'} ? ( ) : ( "" ),
				  $text{'index_path'},
				  $text{'index_type'},
			 	  $text{'index_size'},
				  $text{'index_sched'},
				  $text{'index_rep'} ], 100, 0, \@tds);
	foreach $l (@logs) {
		next if ($done{$l->{'file'}}++);
		local @files = &all_log_files($l->{'file'});
		next if (!@files);
		local $lconf = &get_log_config($l->{'file'});
		local @cols;
		local $short = $l->{'file'};
		if (length($short) > 40) {
			$short = "...".substr($short, -40);
			}
		if ($access{'view'}) {
			push(@cols, $short);
			}
		else {
			push(@cols, "<a href='edit_log.cgi?file=".
				   &urlize($l->{'file'}).
				   "&type=$l->{'type'}&custom=$l->{'custom'}'>".
				   "$short</a>");
			}
		push(@cols, &text('index_type'.$l->{'type'}));
		local ($size, $latest);
		foreach $f (@files) {
			local @st = stat($f);
			$size += $st[7];
			$latest = $st[9] if ($st[9] > $latest);
			}
		$latest = $latest ? localtime($latest) : "<br>";
		push(@cols, $size ? &nice_size($size) : $text{'index_empty'});
		push(@cols, $lconf->{'sched'} ?
			&text('index_when', &cron::when_text($lconf)) :
			$text{'no'});
		if ($lconf->{'dir'} && -r "$lconf->{'dir'}/index.html") {
			push(@cols, "<a href='view_log.cgi/".
				    &urlize(&urlize($l->{'file'})).
				    "/index.html'>$text{'index_view'}</a>");
			}
		else {
			push(@cols, "");
			}
		if ($access{'view'}) {
			print &ui_columns_row(\@cols);
			}
		elsif (!%$lconf) {
			print &ui_columns_row([ "<img src=images/empty.gif>",
						@cols ]);
			}
		else {
			print &ui_checked_columns_row(\@cols, \@tds, "d",
						      $l->{'file'});
			}
		}
	print &ui_columns_end();
	}
else {
	print "<p><b>$text{'index_nologs'}</b><p>\n";
	push(@links, "<a href='edit_log.cgi?new=1'>$text{'index_add'}</a>")
		if (!$access{'view'} && $access{'add'});
	}
print &ui_links_row(\@links);
if (@logs && !$access{'view'}) {
	print &ui_form_end([ [ "enable", $text{'index_enable'} ],
			     [ "disable", $text{'index_disable'} ] ]);
	}

if (!$access{'view'} && $access{'global'}) {
	print &ui_hr();
	print "<form action=edit_global.cgi>\n";
	print "<table width=100%><tr>\n";
	print "<td><input type=submit value='$text{'index_global'}'></td>\n";
	print "<td>$text{'index_globaldesc'}</td>\n";
	print "</tr></table></form>\n";
	}

&ui_print_footer("/", $text{'index'});

sub main_header
{
local $prog = &get_webalizer_prog();
&ui_print_header(undef, $text{'index_title'}, "", undef, 1, 1, 0,
	&help_search_link($prog, "man", "doc", "google"),
	undef, undef, &text('index_version_'.$prog, $webalizer_version));
}

