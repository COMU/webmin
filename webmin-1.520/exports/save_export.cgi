#!/usr/local/bin/perl
# save_export.cgi
# Save, create or delete an export

require './exports-lib.pl';
&ReadParse();
&lock_file($config{'exports_file'});
@exps = &list_exports();

if ($in{'delete'}) {
	# Deleting some export
	$exp = $exps[$in{'idx'}];
	&delete_export($exp);
	}
else {
	if (!$in{'new'}) {
		# Get old export
		$oldexp = $exps[$in{'idx'}];
		%opts = %{$oldexp->{'options'}};
		}

	# Validate and parse inputs
	&error_setup($text{'save_err'});
	$exp{'via_pfs'} = ($exp{'pfs'} ne "") ? $in{'via_pfs'} : 0;
	-d $in{'dir'} || &error(&text('save_edir', $in{'dir'}));
	$exp{'dir'} = $in{'dir'};
	$exp{'pfs'} = $in{'pfs'};
	$exp{'active'} = $in{'active'};
	
	if ($in{'mode'} == 0) { $exp{'host'} = "=public"; }
	elsif ($in{'mode'} == 1) {
		$in{'netgroup'} =~ /^\S+$/ ||
			&error($text{'save_enetgroup'});
		$exp{'host'} = '@'.$in{'netgroup'};
		}
	elsif ($in{'mode'} == 2) {
		&check_ipaddress($in{'network'}) ||
			&error(&text('save_enetwork', $in{'network'}));
		&check_ipaddress($in{'netmask'}) ||
			&error(&text('save_enetmask', $in{'netmask'}));
		$exp{'host'} = $in{'network'}."/".$in{'netmask'};
		}
	elsif ($in{'mode'} == 3) { $exp{'host'} = ""; }
	else {
		$in{'host'} =~ /\*/ || gethostbyname($in{'host'}) ||
			&error(&text('save_ehost', $in{'host'}));
		$exp{'host'} = $in{'host'};
		}

	# Authentication is in the host name
	# Only sys and krb5 for the moment
	local $auth = "";
	if ($in{'auth'}) {
	    if ($in{'sec'} == 0) { $auth = "krb5"; }
	    if ($in{'sec'} == 1) { $auth = "krb5i"; }
	    if ($in{'sec'} == 2) { $auth = "krb5p"; }
	}
	if ($auth ne "") { $exp{'host'} = "gss/$auth"; }

	# validate and parse options
	delete($opts{'rw'}); delete($opts{'ro'});
	if ($in{'ro'}) {
	    $opts{'ro'} = "";
	} else {
	    $opts{'rw'} = "";
	}
	
	delete($opts{'secure'}); delete($opts{'insecure'});
	$opts{'insecure'} = "" if ($in{'insecure'});

	delete($opts{'no_subtree_check'}); delete($opts{'subtree_check'});
	$opts{'no_subtree_check'} = "" if ($in{'no_subtree_check'});

	delete($opts{'nohide'}); delete($opts{'hide'});
	$opts{'nohide'} = "" if ($in{'nohide'});
	
	delete($opts{'sync'}); delete($opts{'async'});
	if ($in{'sync'} == 1) {
	    $opts{'sync'} = "";
	} elsif ($in{'sync'} == 2) {
	    $opts{'async'} = "";
	}

	delete($opts{'root_squash'}); delete($opts{'no_root_squash'});
	delete($opts{'all_squash'}); delete($opts{'no_all_squash'});
	$opts{'no_root_squash'} = "" if ($in{'squash'} == 0);
	$opts{'all_squash'} = "" if ($in{'squash'} == 2);

	if ($in{'anonuid_def'}) { delete($opts{'anonuid'}); }
	elsif ($in{'anonuid'} =~ /^-?[0-9]+$/) {
	    $opts{'anonuid'} = $in{'anonuid'}; }
	else { $opts{'anonuid'} = getpwnam($in{'anonuid'}); }

	if ($in{'anongid_def'}) { delete($opts{'anongid'}); }
	elsif ($in{'anongid'} =~ /^-?[0-9]+$/) {
	    $opts{'anongid'} = $in{'anongid'}; }
	else { $opts{'anongid'} = getgrnam($in{'anongid'}); }

	# NFSv2 specific options
	delete($opts{'link_relative'}); delete($opts{'link_absolute'});
	delete($opts{'noaccess'});
	delete($opts{'squash_uids'});
	delete($opts{'squash_gids'});
	delete($opts{'map_daemon'});

	if (nfs_max_version("localhost") == 2) {
	    $opts{'link_relative'} = "" if ($in{'link_relative'});
	    $opts{'noaccess'} = "" if ($in{'noaccess'});

	    if (!$in{'squash_uids_def'}) {
		if ($in{'squash_uids'} !~ /^[\d+\-\,]+$/) {
		    &error($text{'save_euids'});
		} else {
		    $opts{'squash_uids'} = $in{'squash_uids'};
		    $opts{'map_daemon'} = "";
		}
	    }
	    
	    if (!$in{'squash_gids_def'}) {
		if ($in{'squash_gids'} !~ /^[\d+\-\,]+$/) {
		    &error($text{'save_egids'});
		} else {
		    $opts{'squash_gids'} = $in{'squash_gids'};
		    $opts{'map_daemon'} = "";
		}
	    }
	}

	$exp{'options'} = \%opts;
	if ($in{'new'}) {
	    if ($in{'via_pfs'} == 1) {
		&create_export_via_pfs(\%exp);
	    } else {
		&create_export(\%exp);
	    }
	} else {
	    &modify_export(\%exp, $oldexp);
	}
    }
&unlock_file($config{'exports_file'});
if ($in{'delete'}) {
	&webmin_log("delete", "export", $exp->{'dir'}, $exp);
	}
elsif ($in{'new'}) {
	&webmin_log("create", "export", $exp{'dir'}, \%exp);
	}
else {
	&webmin_log("modify", "export", $exp{'dir'}, \%exp);
	}
&redirect("");

