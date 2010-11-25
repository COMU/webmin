#!/usr/local/bin/perl
# Delete, disable or enable all exports for some directories

require './exports-lib.pl';

# Validate inputs
&error_setup($text{'delete_err'});
&ReadParse();
@d = split(/\0/, $in{'d'});
@d || &error($text{'delete_enone'});

# Find the actual clients
&lock_file($config{'exports_file'});
@exps = &list_exports();
foreach $e (@exps) {
	if (&indexof($e->{'dir'}, @d) >= 0) {
		push(@dels, $e);
		}
	}

# Take them out, one by one
foreach $d (reverse(@dels)) {
	if ($in{'delete'}) {
		&delete_export($d);
		}
	elsif ($in{'disable'} && $d->{'active'}) {
		$d->{'active'} = 0;
		&modify_export($d, $d);
		}
	elsif ($in{'enable'} && !$d->{'active'}) {
		$d->{'active'} = 1;
		&modify_export($d, $d);
		}
	}
&unlock_file($config{'exports_file'});
&webmin_log($in{'delete'} ? "delete" : $in{'disable'} ? "disable" : "enable",
	    "exports", scalar(@dels));
&redirect("");

