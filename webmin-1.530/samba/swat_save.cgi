#!/usr/local/bin/perl
# swat_save.cgi
# Save the entered SWAT username and password

require './samba-lib.pl';
&ReadParse();

# check acls

&error_setup("<blink><font color=red>$text{'eacl_aviol'}</font></blink>");
&error("$text{'eacl_np'} $text{'eacl_pcswat'}") unless $access{'swat'};
 
$whatfailed = $text{'swats_fail'};
$in{'user'} || &error($text{'swats_user'});
&write_file("$module_config_directory/swat", { 'user' => $in{'user'},
					       'pass' => $in{'pass'} });
chmod(0600, "$module_config_directory/swat");
&redirect("swat.cgi");

