#!/usr/local/bin/perl
# save_euser.cgi
# Save an existing samba user

require './samba-lib.pl';
&ReadParse();
# check acls

&error_setup("<blink><font color=red>$text{'eacl_aviol'}</font></blink>");
&error("$text{'eacl_np'} $text{'eacl_pmusers'}")
        unless $access{'maint_users'} && $access{'view_users'};
# save		
$whatfailed = $text{'saveuser_fail'};
&lock_file($config{'smb_passwd'});
@list = &list_users();
$u = $list[$in{'idx'}];

# check inputs
$in{'uid'} =~ /^\d+$/ || &error(&text('saveuser_uid', $in{'uid'}));
$u->{'uid'} = $in{'uid'};
if ($in{'new'}) {
	$u->{'opts'} = [ split(/\0/, $in{'opts'}) ];
	}
else {
	$in{'realname'} !~ /:/ ||
		&error($text{'saveuser_colon'});
	(-d $in{'homedir'}) ||
		&error(&text('saveuser_home', $in{'homedir'}));
	(-x $in{'shell'}) || &error(&text('saveuser_shell', $in{'shell'}));
	$u->{'home'} = $in{'homedir'};
	$u->{'shell'} = $in{'shell'};
	$u->{'real'} = $in{'realname'};
	}

# apply changes
if ($in{ptype} == 0) {
	$u->{'pass1'} = $u->{'$pass2'} = ("X" x 32);
	}
elsif ($in{ptype} == 1) {
	$u->{'pass1'} = "NO PASSWORDXXXXXXXXXXXXXXXXXXXXX";
	$u->{'pass2'} = $u->{'pass1'};
	}
elsif ($in{ptype} == 3) {
	# changing password.. need to set later with smbpasswd
	$u->{'pass1'} = $u->{'$pass2'} = ("X" x 32);
	$set_passwd = 1;
	}
&modify_user($u);

# Call password change program if necessary
if ($set_passwd) {
	&set_password($u->{'name'}, $in{'pass'}, \$err) ||
		&error(&text('saveuser_pass', $err));
	}
&unlock_file($config{'smb_passwd'});
&webmin_log("save", "euser", $u->{'name'}, $u);

&redirect("edit_epass.cgi");

