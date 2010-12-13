#!/usr/local/bin/perl
# Create, update or delete a scheduled backup

require './backup-config-lib.pl';
&ReadParse();

# Find the backup job
if (!$in{'new'}) {
	$backup = &get_backup($in{'id'});
	$job = &find_cron_job($backup);
	}
else {
	$backup = { };
	}

if ($in{'delete'}) {
	# Delete the backup
	&delete_backup($backup);
	if ($job) {
		&lock_file(&cron::cron_file($job));
		&cron::delete_cron_job($job);
		&unlock_file(&cron::cron_file($job));
		}
	}
else {
	# Validate inputs
	&error_setup($text{'save_err'});
	@mods = split(/\0/, $in{'mods'});
	$backup->{'mods'} = join(" ", @mods);
	$backup->{'dest'} = &parse_backup_destination("dest", \%in);
	&cron::parse_times_input($backup, \%in);
	$backup->{'emode'} = $in{'emode'};
	$backup->{'email'} = $in{'email'};
	$backup->{'pre'} = $in{'pre'};
	$backup->{'post'} = $in{'post'};
	$backup->{'sched'} = $in{'sched'};
	($backup->{'configfile'}, $backup->{'nofiles'}, $backup->{'others'}) =
		&parse_backup_what("what", \%in);
	@mods || ($backup->{'nofiles'} && !$backup->{'configfile'}) ||
		&error($text{'save_emods'});

	# Save or create
	&save_backup($backup);
	if ($job) {
		&lock_file(&cron::cron_file($job));
		&cron::delete_cron_job($job);
		}
	if ($in{'sched'}) {
		&cron::create_wrapper($cron_cmd, $module_name, "backup.pl");
		$job = { 'user' => 'root',
			 'command' => "$cron_cmd $backup->{'id'}",
			 'active' => 1,
			 'mins' => $backup->{'mins'},
			 'hours' => $backup->{'hours'},
			 'days' => $backup->{'days'},
			 'months' => $backup->{'months'},
			 'weekdays' => $backup->{'weekdays'},
			 'special' => $backup->{'special'} };
		&lock_file(&cron::cron_file($job));
		&cron::create_cron_job($job);
		}
	&unlock_file(&cron::cron_file($job)) if ($job);
	}
&webmin_log($in{'new'} ? 'create' : $in{'delete'} ? 'delete' : 'modify',
	    'backup', $backup->{'dest'}, $backup);

if ($in{'run'}) {
	# Execute the backup now
	&ui_print_unbuffered_header(undef, $text{'run_title'}, "");
	@mods = split(/\s+/, $backup->{'mods'});
	$nice = &nice_dest($backup->{'dest'}, 1);
	print &text('run_doing', scalar(@mods), "<tt>$nice</tt>"),"<br>\n";
	$err = &execute_backup(\@mods, $backup->{'dest'}, \$size, undef,
			       $backup->{'configfile'}, $backup->{'nofiles'},
			       [ split(/\t+/, $backup->{'others'}) ]);
	if ($err) {
		print "<pre>$err</pre>";
		print "$text{'run_failed'}<p>\n";
		}
	else {
		print "$text{'run_ok'}<p>\n";
		}
	&webmin_log("run", "backup", $backup->{'dest'}, $backup);
	&ui_print_footer("edit.cgi?id=$in{'id'}", $text{'edit_return'},
			 "index.cgi?mode=sched", $text{'index_return'});
	exit;
	}
else {
	&redirect("index.cgi?mode=sched");
	}


