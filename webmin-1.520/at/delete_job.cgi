#!/usr/local/bin/perl
# Delete or run an at job

require './at-lib.pl';
&ReadParse();
&foreign_require("proc", "proc-lib.pl");

@jobs = &list_atjobs();
($job) = grep { $_->{'id'} eq $in{'id'} } @jobs;
$job || &error($text{'delete_egone'});

if ($in{'run'}) {
	# Run the command and show output
	&ui_print_header(undef, $text{'run_title'}, "");

	# Create temp script for job
	$temp = &transname();
	&open_tempfile(TEMP, ">$temp");
	&print_tempfile(TEMP, $job->{'cmd'});
	&close_tempfile(TEMP);
	chmod(0755, $temp);

	print "<p>\n";
	print &text('run_output'),"<p>\n";
	@uinfo = getpwnam($job->{'user'});
	print "<pre>";
	&additional_log('exec', undef, $job->{'cmd'});
	$got = &proc::safe_process_exec($temp, $uinfo[2], $uinfo[3],
					STDOUT, undef, 1);
	if (!$got) { print "<i>$text{'run_none'}</i>\n"; }
	unlink($temp);
	print "</pre>\n";
	&webmin_log("exec", "job", $job->{'user'}, $job);

	&ui_print_footer("", $text{'index_return'});
	}
else {
	# Just delete the at job
	&error_setup($text{'delete_err'});
	%access = &get_module_acl();
	&can_edit_user(\%access, $job->{'user'}) || &error($text{'edit_ecannot'});
	&delete_atjob($in{'id'});
	&webmin_log("delete", "job", $job->{'user'}, $job);
	&redirect("");
	}

