#!/usr/local/bin/perl

BEGIN { push(@INC, ".."); };
use WebminCore;
@available = ("webmin", "system", "servers", "cluster", "hardware", "", "net");
&init_config();
$hostname = &get_display_hostname();
$ver = &get_webmin_version();
&get_miniserv_config(\%miniserv);
if ($gconfig{'real_os_type'}) {
	if ($gconfig{'os_version'} eq "*") {
		$ostr = $gconfig{'real_os_type'};
		}
	else {
		$ostr = "$gconfig{'real_os_type'} $gconfig{'real_os_version'}";
		}
	}
else {
	$ostr = "$gconfig{'os_type'} $gconfig{'os_version'}";
	}
&ReadParse();

# Redirect if the user has only one module
@msc_modules = &get_visible_module_infos()
	if (!defined(@msc_modules));

if (!defined($in{'cat'})) {
	# Maybe redirect to some module after login
	local $goto = &get_goto_module(\@msc_modules);
	if ($goto) {
		&redirect($goto->{'dir'}.'/');
		exit;
		}
	}

# Show standard header
$gconfig{'sysinfo'} = 0 if ($gconfig{'sysinfo'} == 1);
$main::theme_index_page = 1;
$title = $gconfig{'nohostname'} ? $text{'main_title2'} :
        &text('main_title', $ver, $hostname, $ostr);
&header($title, "",
	undef, undef, 1, 1);
print $text{'main_header'};

if (!@msc_modules) {
	# use has no modules!
	print "<p><b>$text{'main_none'}</b><p>\n";
	}
elsif ($gconfig{"notabs_${base_remote_user}"} == 2 ||
    $gconfig{"notabs_${base_remote_user}"} == 0 && $gconfig{'notabs'}) {
	# Generate main menu with all modules on one page
	print "<center><table cellpadding=0>\n";
	$pos = 0;
	$cols = $gconfig{'nocols'} ? $gconfig{'nocols'} : 4;
	$per = 100.0 / $cols;
	foreach $m (@msc_modules) {
		if ($pos % $cols == 0) { print "<tr>\n"; }
		print "<td valign=top align=center>\n";
		local $idx = $m->{'index_link'};
		$desc = $m->{'longdesc'} || $m->{'desc'};
		print "<table border><tr><td><a href=$m->{'dir'}/$idx>",
		      "<img src=$m->{'dir'}/images/icon.gif border=0 ",
		      "width=48 height=48 title=\"$desc\"></a></td></tr></table>\n";
		print "<a href=$m->{'dir'}/$idx>$m->{'desc'}</a></td>\n";
		if ($pos % $cols == $cols - 1) { print "</tr>\n"; }
		$pos++;
		}
	print "</table></center><p><table width='100%' bgcolor='#FFFFFF'><tr><td></td></tr></table><br>\n";
	}
else {
	# Generate categorized module list
	print "<table border=0 cellpadding=0 cellspacing=0 width=95% align=center><tr><td><table border=0 cellpadding=0 cellspacing=0 height=20><tr>\n";
	$usercol = defined($gconfig{'cs_header'}) ||
		   defined($gconfig{'cs_table'}) ||
		   defined($gconfig{'cs_page'});
	foreach $c (@cats) {
		$t = $cats{$c};
		if ($in{'cat'} eq $c) {
			print "<td bgcolor=#bae3ff>",
			  "<img src=images/tabs/blue_left.jpg alt=\"\">","</td>\n";
			print "<td bgcolor=#bae3ff>&nbsp;<b>$t</b>&nbsp;</td>\n";
			print "<td bgcolor=#bae3ff>",
			  "<img src=images/tabs/blue_right.jpg alt=\"\">","</td>\n";
			}
#		print "<td width=10></td>\n";
		}
	print "</tr></table> <table border=0 cellpadding=0 cellspacing=0 ",
              "width=100% bgcolor=#FFFFFF background=images/msctile2.jpg>\n";
	print "<tr><td><table width=100% cellpadding=5>\n";

	# Display the modules in this category
	$pos = 0;
	$cols = $gconfig{'nocols'} ? $gconfig{'nocols'} : 4;
	$per = 100.0 / $cols;
	foreach $m (@msc_modules) {
		next if ($m->{'category'} ne $in{'cat'});

		if ($pos % $cols == 0) { print "<tr>\n"; }
		$desc = $m->{'longdesc'} || $m->{'desc'};
		print "<td valign=top align=center width=$per\%>\n";
		print "<table border bgcolor=#ffffff><tr><td><a href=$m->{'dir'}/>",
		      "<img src=$m->{'dir'}/images/icon.gif title=\"$desc\" border=0></a>",
		      "</td></tr></table>\n";
		print "<a href=$m->{'dir'}/><font color=#000000>$m->{'desc'}</font></a></td>\n";
		if ($pos++ % $cols == $cols - 1) { print "</tr>\n"; }
		}
	while($pos++ % $cols) {
		print "<td width=$per\%></td>\n";
		}
	print "</table></td></tr></table></td></tr></table>";

    print qq~<table width="95%" border="0" cellspacing="0" cellpadding="0" align="center">
  <tr>
    <td background="images/white_bar.jpg" nowrap><img src="images/white_bar.jpg"></td>
  </tr>
</table>~;

    print qq~<p><table width="98%" border="0" cellspacing="0" cellpadding="0" height="4" align="center">
  <tr>
    <td background="images/white_bar2.jpg" nowrap><img src="images/white_bar2.jpg"></td>
  </tr>
</table><p>~;

	}

if ($miniserv{'logout'} && !$gconfig{'alt_startpage'} &&
    !$ENV{'SSL_USER'} && !$ENV{'LOCAL_USER'} &&
    $ENV{'HTTP_USER_AGENT'} !~ /webmin/i) {
    print "<table width=95% align=center><tr><td width=100%><b><font color='#FFFFFF'>&nbsp;&nbsp;";
    print &text('main_version', $ver, $hostname, $ostr)."\n"
	if (!$gconfig{'nohostname'});
    print $text{'main_readonly'}."\n" if (&is_readonly_mode());
    print "</font></b>\n";
    print "</td>\n";

    print "<td align=right><img src='images/theme_by.jpg' border='0'>&nbsp;&nbsp;</td>\n";
    print "</tr></table>\n";

	}

# Check for incorrect OS
if (&foreign_check("webmin")) {
	&foreign_require("webmin", "webmin-lib.pl");
	&webmin::show_webmin_notifications();
	}

print $text{'main_footer'};
&footer();


sub chop_font {

        foreach $l (split(//, $t)) {
            $ll = ord($l);
            if ($ll > 127 && $lang->{'charset'}) {
                print "<img src=images/letters2/$ll.$lang->{'charset'}.gif alt=\"$l\" align=bottom border=0>";
                }
            elsif ($l eq " ") {
                print "<img src=images/letters2/$ll.gif alt=\"\&nbsp;\" align=bottom border=0>";
                }
            else {
                print "<img src=images/letters2/$ll.gif alt=\"$l\" align=bottom border=0>";
                }
            }

}
