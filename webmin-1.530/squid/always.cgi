#!/usr/local/bin/perl
# always.cgi
# A form for editing or creating http_access directives

require './squid-lib.pl';
$access{'othercaches'} || &error($text{'eicp_ecannot'});
&ReadParse();
$conf = &get_config();

if (!defined($in{'index'})) {
	&ui_print_header(undef, $text{'always_create'}, "",
		undef, 0, 0, 0, &restart_button());
	}
else {
	&ui_print_header(undef, $text{'always_edit'}, "",
		undef, 0, 0, 0, &restart_button());
	@always = @{$conf->[$in{'index'}]->{'values'}};
	}

print "<form action=always_save.cgi>\n";
if (@always) {
	print "<input type=hidden name=index value=$in{'index'}>\n";
	}
print "<table border>\n";
print "<tr $tb> <td><b>$text{'always_header'}</b></td> </tr>\n";
print "<tr $cb> <td><table>\n";

print "<tr> <td><b>$text{'ahttp_a'}</b></td> <td colspan=3>\n";
printf "<input type=radio name=action value=allow %s> $text{'ahttp_a1'}\n",
	$always[0] eq "allow" ? "checked" : "";
printf "<input type=radio name=action value=deny %s> $text{'ahttp_d'}</td> </tr>\n",
	$always[0] eq "allow" ? "" : "checked";

for($i=1; $i<@always; $i++) { $match{$always[$i]}++; }
@acls = grep { !$done{$_->{'values'}->[0]}++ } &find_config("acl", $conf);
$r = @acls; $r = 10 if ($r > 10);

print "<tr> <td valign=top><b>$text{'ahttp_ma'}</b></td>\n";
print "<td valign=top><select name=yes multiple size=$r width=100>\n";
foreach $a (@acls) {
	printf "<option %s>%s\n",
		$match{$a->{'values'}->[0]} ? "selected" : "",
		$a->{'values'}->[0];
	}
print "</select></td>\n";

print "<td valign=top><b>$text{'ahttp_dma'}</b></td>\n";
print "<td valign=top><select name=no multiple size=$r width=100>\n";
foreach $a (@acls) {
	printf "<option %s>%s\n",
		$match{"!$a->{'values'}->[0]"} ? "selected" : "",
		$a->{'values'}->[0];
	}
print "</select></td> </tr>\n";

print "</table></td></tr></table><br>\n";
print "<input type=submit value=$text{'buttsave'}>\n";
if (@always) { print "<input type=submit value=$text{'buttdel'} name=delete>\n"; }
print "</form>\n";

&ui_print_footer("edit_acl.cgi", $text{'ahttp_return'});

