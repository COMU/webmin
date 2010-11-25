#!/usr/local/bin/perl
# save_fshare.cgi
# Save a new or edited file share

require './samba-lib.pl';
&ReadParse();
&lock_file($config{'smb_conf'});
&get_share($in{old_name}) if $in{old_name};

# check acls

&error_setup("<blink><font color=red>$text{'eacl_aviol'}</font></blink>");
if ($in{old_name}) {
    &error("$text{'eacl_np'} $text{'eacl_pus'}") 
		unless &can('rw', \%access, $in{old_name});
	}
else {
    &error("$text{'eacl_np'} $text{'eacl_pcrs'}") unless $access{'c_fs'};
	}

$whatfailed = $text{'savefshare_fail'};
# store share options
if ($in{old_name} eq "global") {
	$name = "global";
	}
else {
	$name = $in{"homes"} ? "homes" : $in{"share"};
	if ($in{"path"} !~ /\S/ && !$in{"homes"}) {
		&error($text{'savefshare_nopath'});
		}
	}
&setval("path", $in{"path"});
&setval("available", $in{"available"});
&setval("browseable", $in{"browseable"});
&setval("comment", $in{"comment"});

# Check for clash
if ($name ne "global") {
	foreach (&list_shares()) {
		$exists{$_}++;
		}
	if (!$in{old_name} && $exists{$name}) {
		&error(&text('savefshare_exist', $name));
		}
	elsif ($in{old_name} ne $name && $exists{$name}) {
		&error(&text('savefshare_exist', $name));
		}
	elsif ($name !~ /^[A-Za-z0-9_\$\- ]+$/) {
		&error(&text('savefshare_mode', $name));
		}
	elsif ($name eq "global") {   # unreachable code ? EB
		&error($text{'savefshare_global'});
		}
	}

# Check creator
if ($in{'create'} eq "yes") {
	defined(getpwnam($in{'createowner'})) ||
		&error($text{'savefshare_owner'});
	defined(getgrnam($in{'creategroup'})) ||
		&error($text{'savefshare_group'});
	$in{'createperms'} =~ /^[0-7]{3,4}$/ ||
		&error($text{'savefshare_perms'});
	}

# Update config file
if ($in{old_name}) {
	# Changing an existing share
	&modify_share($in{old_name}, $name);
	if ($name ne $in{old_name}) {
		local $oldacl=$access{'ACLfs_' . $in{old_name}};
		&drop_samba_acl(\%access, $in{old_name});
		&save_samba_acl($oldacl, \%access, $name);
		}
	}
else {
	# Creating a new share
	&create_share($name);
	if ($in{'create'} eq "yes" && !-d $in{'path'}) {
		&make_dir($in{'path'}, oct($in{'createperms'}));
		&set_ownership_permissions($in{'createowner'},
					   $in{'creategroup'},
					   oct($in{'createperms'}),
					   $in{'path'});
		}
	&save_samba_acl('rwvVsSpPnNoO', \%access, $name);
	}
&unlock_file($config{'smb_conf'});
&webmin_log($in{old_name} ? "save" : "create", "fshare", $name, \%in);
&redirect("");
