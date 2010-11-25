#!/usr/local/bin/perl
# Create, update or delete a job

require './bacula-backup-lib.pl';
&ReadParse();

if ($in{'run'}) {
	# Just run this job
	&redirect("backup.cgi?job=".&urlize($in{'old'}).
		  "&wait=$config{'wait'}");
	exit;
	}

$conf = &get_director_config();
$parent = &get_director_config_parent();
@jobs = ( &find("JobDefs", $conf), &find("Job", $conf) );

if (!$in{'new'}) {
	$job = &find_by("Name", $in{'old'}, \@jobs);
        $job || &error($text{'job_egone'});
	}
else {
	$job = { 'type' => 1,
		 'name' => 'Job',
		 'members' => [ ] };
	}

&lock_file($parent->{'file'});
if ($in{'delete'}) {
	# Just delete this one
	if ($job->{'name'} eq 'JobDefs') {
		# Cannot delete if anything inherits from it
		$name = &find_value("Name", $job->{'members'});
		$child = &find_dependency("JobDefs", $name, [ "Job" ], $conf);
		$child && &error(&text('job_echild', $child));
		}
	&save_directive($conf, $parent, $job, undef, 0);
	}
else {
	# Validate and store inputs
	&error_setup($text{'job_err'});
	$in{'name'} =~ /\S/ || &error($text{'job_ename'});
	if ($in{'new'} || $in{'name'} ne $in{'old'}) {
		$clash = &find_by("Name", $in{'name'}, \@jobs);
		$clash && &error($text{'job_eclash'});
		}
	&save_directive($conf, $job, "Name", $in{'name'}, 1);

	if ($in{'dmode'} == 0) {
		$job->{'name'} = "JobDefs";
		}
	else {
		$job->{'name'} = "Job";
		&save_directive($conf, $job, "JobDefs",
			$in{'dmode'} == 1 ? undef : $in{'defs'}, 1);
		}

	&save_directive($conf, $job, "Type", $in{'type'} || undef, 1);
	&save_directive($conf, $job, "Level", $in{'level'} || undef, 1);
	&save_directive($conf, $job, "Client", $in{'client'} || undef, 1);
	&save_directive($conf, $job, "FileSet", $in{'fileset'} || undef, 1);
	&save_directive($conf, $job, "Schedule", $in{'schedule'} || undef, 1);
	&save_directive($conf, $job, "Storage", $in{'storage'} || undef, 1);
	&save_directive($conf, $job, "Pool", $in{'pool'} || undef, 1);
	&save_directive($conf, $job, "Messages", $in{'messages'} || undef, 1);
	$in{'priority_def'} || $in{'priority'} =~ /^\d+$/ ||
		&error($text{'job_epriority'});
	&save_directive($conf, $job, "Priority",
		$in{'priority_def'} ? undef : $in{'priority'}, 1);

	&save_directive($conf, $job, "Run Before Job",
			$in{'before_def'} ? undef : $in{'before'}, 1);
	&save_directive($conf, $job, "Run After Job",
			$in{'after_def'} ? undef : $in{'after'}, 1);
	&save_directive($conf, $job, "Client Run Before Job",
			$in{'cbefore_def'} ? undef : $in{'cbefore'}, 1);
	&save_directive($conf, $job, "Client Run After Job",
			$in{'cafter_def'} ? undef : $in{'cafter'}, 1);

	# Create or update
	if ($in{'new'}) {
		&save_directive($conf, $parent, undef, $job, 0);
		}
	}

&flush_file_lines();
&unlock_file($parent->{'file'});
&auto_apply_configuration();
&webmin_log($in{'new'} ? "create" : $in{'delete'} ? "delete" : "modify",
	    "job", $in{'old'} || $in{'name'});
&redirect("list_jobs.cgi");

