#!/usr/local/bin/perl
# Save advanced options

require './usermin-lib.pl';
&ReadParse();
&error_setup($text{'advanced_err'});
&get_usermin_miniserv_config(\%miniserv);
&get_usermin_config(\%uconfig);

# Save global temp dir setting
if ($in{'tempdir_def'}) {
	delete($uconfig{'tempdir'});
	}
else {
	-d $in{'tempdir'} || &error($text{'advanced_etemp'});
	$uconfig{'tempdir'} = $in{'tempdir'};
	}

# Save per-module temp dirs
for($i=0; defined($tmod = $in{'tmod_'.$i}); $i++) {
	next if (!$tmod);
	$tdir = $in{'tdir_'.$i};
	%minfo = &get_usermin_module_info($tmod);
	-d $tdir || &error(&text('advanced_etdir', $minfo{'desc'}));
	push(@tdirs, [ $tmod, $tdir ]);
	}
&webmin::save_tempdirs(\%uconfig, \@tdirs);

# Save stack trace option
$uconfig{'error_stack'} = $in{'stack'};

# Save umask
if ($in{'umask_def'}) {
	delete($uconfig{'umask'});
	}
else {
	$in{'umask'} =~ /^[0-7]{3}$/ ||
		&error($text{'advanced_eumask'});
	$uconfig{'umask'} = $in{'umask'};
	}

&lock_file($usermin_config);
&write_file($usermin_config, \%uconfig);
&unlock_file($usermin_config);

# Save password pass option
$miniserv{'pass_password'} = $in{'pass'};

&lock_file($usermin_miniserv_config);
&put_usermin_miniserv_config(\%miniserv);
&unlock_file($usermin_miniserv_config);
&restart_usermin_miniserv();

&webmin_log("advanced");
&redirect("");

