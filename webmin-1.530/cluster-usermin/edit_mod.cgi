#!/usr/local/bin/perl
# edit_mod.cgi
# Display details of a module or theme

require './cluster-usermin-lib.pl';
&ReadParse();
$type = $in{'tedit'} || !$in{'mod'} ? 'theme' : 'mod';
$name = $in{$type};
&ui_print_header(undef, $text{"edit_title_$type"}, "");

# Find all hosts with the module or theme
@hosts = &list_usermin_hosts();
@servers = &list_servers();
foreach $h (@hosts) {
	local ($s) = grep { $_->{'id'} == $h->{'id'} } @servers;
	foreach $m ($type eq 'theme' ? @{$h->{'themes'}}
				     : @{$h->{'modules'}}) {
		if ($m->{'dir'} eq $name) {
			$s->{'module'} = $m;
			push(@got, $s);
			push(@goth, $h);
			$mod = $m if (!$mod);
			if (!$checkon && ($s->{'id'} == $in{'host'} ||
				  !$s->{'id'} && !defined($in{'host'}))) {
				$checkon = $s;
				$checkonh = $h;
				}
			}
		}
	}

# Get the details from this host, or the first in the list
if (!$checkon) {
	$checkonh = $goth[0];
	$checkon = $got[0];
	}
#&remote_foreign_require($checkon->{'host'}, "software", "software-lib.pl");
#@pinfo = &remote_foreign_call($checkon->{'host'}, "software", "package_info",
#			      $in{'package'});

# Show module/theme details
print "<table border width=100%>\n";
print "<tr $tb> <td><b>",&text("edit_header_$type", &server_name($checkon)),
      "</b></td> </tr>\n";
print "<tr $cb> <td><table width=100%>\n";

print "<tr> <td><b>$text{'edit_desc'}</b></td>\n";
print "<td>",$mod->{'desc'},"</td>\n";

print "<td><b>$text{'edit_ver'}</b></td>\n";
print "<td>",$mod->{'version'} ? $mod->{'version'}
			       : $text{'edit_nover'},"</td> </tr>\n";

if ($type eq 'mod') {
	# Show details of module
	foreach $m (@{$checkonh->{'modules'}}) {
		$modmap{$m->{'dir'}} = $m;
		foreach $d (split(/\s+/, $m->{'depends'})) {
			push(@{$ondeps{$d}}, $m);
			}
		}

	&read_file("$usermin::config{'usermin_dir'}/webmin.catnames",
		   \%catnames);
	%utext = &get_usermin_text();
	print "<tr> <td><b>$text{'edit_cat'}</b></td>\n";
	$c = $mod->{'category'};
	print "<td>",$catname{$c} ? $catname{$c} :
		     $utext{"category_$c"} ? $utext{"category_$c"} :
					     $utext{"category_"},"</td>\n";

	print "<td><b>$text{'edit_dir'}</b></td>\n";
	print "<td><tt>$mod->{'dir'}</tt></td> </tr>\n";

	# Show operating systems
	print "<tr> <td valign=top><b>$text{'edit_os'}</b></td>\n";
	print "<td colspan=3>\n";
	$oss = $mod->{'os_support'};
	if (!$oss) {
		print $text{'edit_osall'};
		}
	else {
		open(OSLIST, "$root_directory/os_list.txt");
		while(<OSLIST>) {
			chop;
			if (/^([^\t]+)\t+([^\t]+)\t+(\S+)\t+(\S+)\t*(.*)$/) {
				$osname{$3} = $1 if (!$osname{$3});
				}
			}
		close(OSLIST);
		$osname{"*-linux"} = "Linux";
		while(1) {
			local ($os, $ver, $codes);
			if ($oss =~ /^([^\/\s]+)\/([^\{\s]+)\{([^\}]*)\}\s*(.*)$/) {
				$os = $1; $ver = $2; $codes = $3; $oss = $4;
				}
			elsif ($oss =~ /^([^\/\s]+)\/([^\/\s]+)\s*(.*)$/) {
				$os = $1; $ver = $2; $oss = $3;
				}
			elsif ($oss =~ /^([^\{\s]+)\{([^\}]*)\}\s*(.*)$/) {
				$os = $1; $codes = $2; $oss = $3;
				}
			elsif ($oss =~ /^\{([^\}]*)\}\s*(.*)$/) {
				$codes = $1; $oss = $2;
				}
			elsif ($oss =~ /^(\S+)\s*(.*)$/) {
				$os = $1; $oss = $2;
				}
			else { last; }
			print "&nbsp;,&nbsp;\n" if ($doneone++);
			$osn = $osname{$os} ? $osname{$os} : $os;
			$osn =~ s/\s/&nbsp;/g;
			if ($ver) {
				print "$osn&nbsp;$ver";
				}
			elsif ($os) {
				print "$osn";
				}
			if ($codes) {
				$codes =~ s/\s/&nbsp;/g;
				if ($os) {
					print " (",&text('edit_codes',
							"<tt>$codes</tt>"),")";
					}
				else {
					print &text('edit_codes',
						    "<tt>$codes</tt>");
					}
				}
			}
		}
	print "</td> </tr>\n";

	# Show which modules this module depends upon
	local @deps = grep { !/^[0-9\.]+$/ } split(/\s+/, $mod->{'depends'});
	local @pdeps = split(/\s+/, $mod->{'perldepends'});
	print "<tr> <td valign=top><b>$text{'edit_deps'}</b></td>\n";
	print "<td valign=top>\n";
	if (@deps || @pdeps) {
		foreach $d (@deps) {
			local $mm = $modmap{$d};
			print $mm->{'desc'}," (<tt>$mm->{'dir'}</tt>)<br>\n";
			}
		foreach $d (@pdeps) {
			print &text('edit_pdep', "<tt>$d</tt>"),"<br>\n";
			}
		}
	else {
		print "$text{'edit_nodeps'}\n";
		}
	print "</td>\n";

	# Show which other modules depend on this one
	print "<td valign=top><b>$text{'edit_ondeps'}</b></td>\n";
	print "<td valign=top>\n";
	if ($ondeps{$mod->{'dir'}}) {
		foreach $d (@{$ondeps{$mod->{'dir'}}}) {
			print $d->{'desc'}," (<tt>$d->{'dir'}</tt>)<br>\n";
			}
		}
	else {
		print "$text{'edit_nodeps'}\n";
		}
	print "</td> </tr>\n";
	}
else {
	# Show details of theme
	}

print "</table></td></tr></table><p>\n";

print "<table width=100%><tr>\n";
print "<form action=delete_mod.cgi>\n";
print "<input type=hidden name=type value=\"$type\">\n";
print "<input type=hidden name=mod value=\"$name\">\n";
print "<td><input type=submit value='",$text{"edit_uninst_$type"},"'>\n";
print "<select name=server>\n";
print "<option value=-1>$text{'edit_all'}\n";
foreach $s (@got) {
	print "<option value='$s->{'id'}'>",&server_name($s),"\n";
	}
print "</select></td></form>\n";

print "</tr></table>\n";

# Show hosts with the module or theme
print &ui_hr();
print &ui_subheading($text{'edit_hosts'});
@icons = map { "/servers/images/$_->{'type'}.gif" } @got;
@links = map { "edit_host.cgi?id=$_->{'id'}" } @got;
@titles = map { &server_name($_).
	        ($_->{'module'}->{'version'} ? " ($text{'host_version2'} $_->{'module'}->{'version'})" : "") } @got;
&icons_table(\@links, \@titles, \@icons);

&remote_finished();
&ui_print_footer("", $text{'index_return'});


