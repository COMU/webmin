#!/usr/local/bin/perl
# delete_queues.cgi
# Delete multiple messages from the postfix queue

require './postfix-lib.pl';
$access{'mailq'} || &error($text{'mailq_ecannot'});
&ReadParse();

if ($in{'move'}) {
	# Re-queuing messages
	foreach $f (split(/\0/, $in{'file'})) {
		&system_logged("$config{'postfix_super_command'} -r ".
				quotemeta($f));
		}
	}
elsif ($in{'hold'}) {
	# Holding messages
	foreach $f (split(/\0/, $in{'file'})) {
		&system_logged("$config{'postfix_super_command'} -h ".
				quotemeta($f));
		}
	}
elsif ($in{'unhold'}) {
	# Un-holding messages
	foreach $f (split(/\0/, $in{'file'})) {
		&system_logged("$config{'postfix_super_command'} -H ".
				quotemeta($f));
		}
	}
else {
	@files = split(/\0/, $in{'file'});
	if ($in{'confirm'} || !$config{'delete_confirm'}) {
		# Deleting messages
		if ($postfix_version < 1.1) {
			@qfiles = &recurse_files($config{'mailq_dir'});
			}
		foreach $f (@files) {
			$f =~ /^[A-Za-z0-9]+$/ || next;
			if ($postfix_version >= 1.1) {
				&system_logged("$config{'postfix_super_command'} -d ".quotemeta($f));
				}
			else {
				&unlink_file(grep { $_ =~ /\/$f$/ } @qfiles);
				}
			}
		if ($postfix_version < 1.1) {
			&system_logged("$config{'postfix_super_command'} -p >/dev/null 2>&1");
			}
		&webmin_log("delqs", undef, scalar(@files));
		}
	else {
		# Ask for confirmation
		&ui_print_header(undef, $text{'delq_titles'}, "");
		print &ui_confirmation_form("delete_queues.cgi",
			&text('delq_rusure', scalar(@files)),
			[ map { [ 'file', $_ ] } @files ],
			[ [ 'confirm', $text{'delq_confirm'} ] ],
			);
		&ui_print_footer("mailq.cgi", $text{'mailq_return'});
		exit;
		}
	}
&redirect("mailq.cgi");

