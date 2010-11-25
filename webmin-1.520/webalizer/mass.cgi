#!/usr/local/bin/perl
# Mass schedule or de-schedule a bunch of logs

require './webalizer-lib.pl';
&foreign_require("cron", "cron-lib.pl");
&ReadParse();
&error_setup($text{'mass_err'});
$access{'view'} && &error($text{'edit_ecannot'});

# Validate inputs
@d = split(/\0/, $in{'d'});
@d || &error($text{'mass_enone'});
@jobs = &cron::list_cron_jobs();
foreach $file (@d) {
	&can_edit_log($file) || &error($text{'edit_efilecannot'});
	($job{$file}) = grep { $_->{'command'} eq "$cron_cmd $file" } @jobs;
	}

$count = 0;
if ($in{'enable'}) {
	# Add cron jobs for selected
	foreach $file (@d) {
		$cfile = &config_file_name($file);
		$lconf = &get_log_config($file);
		if (!$lconf->{'sched'}) {
			&lock_file($cfile);
			$lconf->{'sched'} = 1;
			$job = $job{$file};
			if (!$job) {
				$job = { 'user' => 'root',
					 'active' => 1,
					 'command' => "$cron_cmd $file" };
				&lconf_to_cron($lconf, $job);
				&lock_file(&cron::cron_file($job));
				&cron::create_cron_job($job);
				&unlock_file(&cron::cron_file($job));
				}
			&save_log_config($file, $lconf);
			&unlock_file($cfile);
			$count++;
			}
		}
	&webmin_log("enable", "logs", $count);
	}
else {
	# Cancel cron jobs for selected
	foreach $file (@d) {
		$cfile = &config_file_name($file);
		$lconf = &get_log_config($file);
		if ($lconf->{'sched'}) {
			&lock_file($cfile);
			$lconf->{'sched'} = 0;
			$job = $job{$file};
			if ($job) {
				&lock_file(&cron::cron_file($job));
				&cron::delete_cron_job($job);
				&unlock_file(&cron::cron_file($job));
				}
			&save_log_config($file, $lconf);
			&unlock_file($cfile);
			$count++;
			}
		}
	&webmin_log("disable", "logs", $count);
	}

&redirect("");

