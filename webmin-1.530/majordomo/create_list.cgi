#!/usr/local/bin/perl
# create_list.cgi
# Create a new mailing list

require './majordomo-lib.pl';
require 'ctime.pl';
%access = &get_module_acl();
$access{'create'} || &error($text{'create_ecannot'});
&ReadParse();
$conf = &get_config();
$ldir = &perl_var_replace(&find_value("listdir", $conf), $conf);
$program_dir = $config{'smrsh_program_dir'} || $config{'program_dir'};
$wrapper_path = $config{'wrapper_path'} || "$program_dir/wrapper";
$wrapper_program_path = $config{'wrapper_path'} || "$config{'program_dir'}/wrapper";
&error_setup($text{'create_err'});

# Validate inputs
$in{'name'} =~ /^\S+$/ ||
	&error($text{'create_ename'});
$in{'name'} = lc($in{'name'});
if (&get_list($in{'name'}, $conf)) {
	&error(&text('create_eexists', $in{'name'}));
	}
$aliases_files = &get_aliases_file();
@aliases = &foreign_call($aliases_module, "list_aliases", $aliases_files);
foreach $a (@aliases) {
	if ($a->{'enabled'} && lc($a->{'name'}) eq lc($in{'name'})) {
		&error(&text('create_ealias', $in{'name'}));
		}
	}
$in{'owner'} =~ /^\S+$/ ||
	&error($text{'create_eowner'});
$in{'password'} =~ /^\S+$/ ||
	&error($text{'create_epassword'});
$in{'moderator_def'} || $in{'moderator'} =~ /^\S+$/ ||
	&error($text{'create_emoderator'});
$in{'info'} =~ s/\r//g;
$in{'footer'} =~ s/\r//g;

# Create list members file
&lock_file("$ldir/$in{'name'}");
&open_tempfile(MEMS, ">$ldir/$in{'name'}");
&close_tempfile(MEMS);
&set_permissions("$ldir/$in{'name'}");
&unlock_file("$ldir/$in{'name'}");

# Have majordomo create the new config file, by fooling the wrapper
# into thinking it has received an email with a resend command
$lfile = "$ldir/$in{'name'}.config";
$cmd = "$wrapper_program_path resend -l $in{'name'} nobody";
open(WRAPPER, "|$cmd nobody >/dev/null 2>&1");
print WRAPPER "config $in{'name'} $in{'password'}\n\n";
close(WRAPPER);
&additional_log("exec", $cmd);
sleep(3);

# create the .info file
&lock_file($lfile);
$list = &get_list_config($lfile);
chop($ctime = ctime(time()));
$updated = "[Last updated on: $ctime]\n";
&lock_file("$ldir/$in{'name'}.info");
&open_tempfile(INFO, ">$ldir/$in{'name'}.info");
if (&find_value("date_info", $list) eq "yes") {
	&print_tempfile(INFO, $updated);
	}
&print_tempfile(INFO, $in{'info'});
&close_tempfile(INFO);
&set_permissions("$ldir/$in{'name'}.info");
&unlock_file("$ldir/$in{'name'}.info");

# create the archive directory
$adir = &perl_var_replace(&find_value("filedir", $conf), $conf);
$aext = &perl_var_replace(&find_value("filedir_suffix", $conf), $conf);
if ($adir && $aext) {
	&lock_file("$adir/$in{'name'}$aext");
	mkdir("$adir/$in{'name'}$aext", 0755);
	&set_permissions("$adir/$in{'name'}$aext");
	&unlock_file("$adir/$in{'name'}$aext");
	$arch = "$adir/$in{'name'}$aext/archive";
	}
elsif ($in{'archive'}) {
	&lock_file("$ldir/$in{'name'}.archive");
	mkdir("$ldir/$in{'name'}.archive", 0755);
	&set_permissions("$ldir/$in{'name'}.archive");
	&unlock_file("$ldir/$in{'name'}.archive");
	$arch = "$ldir/$in{'name'}.archive/archive";
	}

# Create aliases for the new list
&foreign_call($aliases_module, "lock_alias_files", $aliases_files);
$lname = $config{'dynamic'} ? time()+$$ : "$in{'name'}-list";
if ($in{'archive'}) {
	&newlist_alias($in{'name'}, "|$wrapper_path resend ".
				    "-l $in{'name'} $lname", 0,
				    $in{'name'}."-archive");
	&newlist_alias($in{'name'}."-archive", "|$wrapper_path archive2.pl -f $arch -$in{'archive'} -a");
	}
else {
	&newlist_alias($in{'name'}, "|$wrapper_path resend ".
				    "-l $in{'name'} $lname");
	}
&newlist_alias($lname, ":include:$ldir/$in{'name'}");
&newlist_alias("owner-".$in{'name'}, $in{'owner'});
&newlist_alias($in{'name'}."-owner", $in{'owner'});
&newlist_alias($in{'name'}."-approval", $in{'owner'});
&newlist_alias($in{'name'}."-request", "|$wrapper_path ".
				       "majordomo -l $in{'name'}", 1);
&foreign_call($aliases_module, "unlock_alias_files", $aliases_files);

# Update the new config file
&save_list_directive($list, $lfile, "description", $in{'desc'});
&save_list_directive($list, $lfile, "admin_passwd", $in{'password'});
&save_list_directive($list, $lfile, "approve_passwd", $in{'password'});
&save_list_directive($list, $lfile, "message_footer", $in{'footer'}, 1)
	if ($in{'footer'});
&save_list_directive($list, $lfile, "moderate", $in{'moderate'});
&save_list_directive($list, $lfile, "moderator",
		     $in{'moderator_def'} ? "" : $in{'moderator'});
&flush_file_lines();
&unlock_file($lfile);
&webmin_log("create", "list", $in{'name'}, \%in);

# add to this user's ACL
if ($access{'lists'} ne '*') {
	$access{'lists'} .= " $in{'name'}";
	&save_module_acl(\%access);
	}
&redirect("edit_list.cgi?name=$in{'name'}");

# newlist_alias(name, value, last, othervalue)
sub newlist_alias
{
local @v = ( $_[1] );
push(@v, $_[3]) if ($_[3]);
local $al = { 'name' => $_[0],
	      'values' => \@v,
	      'enabled' => 1 };
&foreign_call($aliases_module, "create_alias", $al, $aliases_files, !$_[2]);
}

