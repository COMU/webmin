#!/usr/local/bin/perl

require "./time-lib.pl";

local ($rawdate, $rawhwdate, %system_date, $rawtime, %hw_date, $txt);
$txt = "";
&ReadParse();

&error( $text{ 'acl_error' } ) if( $access{ 'sysdate' } && $access{ 'hwdate' } );

if (!$access{'sysdate'} && !$access{'hwdate'} && &support_hwtime()) {
	$arr = "0,1";
	}
else {
	$arr = "0";
	}
&ui_print_header(undef,  $text{ 'index_title' }, "", "index", 1, 1, undef,
	&help_search_link("date hwclock ntpdate", "man"),
	qq(<script src="time.js"></script>\n),
	qq(onLoad="F=[$arr];timeInit(F); setTimeout('timeUpdate(F)', 5000);"));

if (!$access{'sysdate'} && !&has_command("date")) {
	print &text( 'error_cnf', "<tt>date</tt>"),"<p>\n";
	&ui_print_footer("/", $text{'index'});
	exit;
	}
if (!$access{'hwdate'} && $config{'hwtime'} == 1 && !&has_command("hwclock")) {
	print &text( 'error_cnf', "<tt>hwclock</tt>"),"<p>\n";
	&ui_print_footer("/", $text{'index'});
	exit;
	}

# Show tabs for times, timezones and syncing
@tabs = ( );
push(@tabs, [ "time", $text{'index_tabtime'}, "index.cgi?mode=time" ]);
if ($access{'timezone'} && &has_timezone()) {
	push(@tabs, [ "zone", $text{'index_tabzone'}, "index.cgi?mode=zone" ]);
	}
if ($access{'ntp'}) {
	push(@tabs, [ "sync", $text{'index_tabsync'}, "index.cgi?mode=sync" ]);
	}
print &ui_tabs_start(\@tabs, "mode", $in{'mode'} || $tabs[0]->[0], 1);

# Get the system time
@tm = &get_system_time();
$system_date{ 'second' } = $tm[0];
$system_date{ 'minute' } = $tm[1];
$system_date{ 'hour' } = $tm[2];
$system_date{ 'date' } = $tm[3];
$system_date{ 'month' } = &number_to_month($tm[4]);
$system_date{ 'year' } = $tm[5]+1900;
$system_date{ 'day' } = &number_to_weekday($tm[6]);

print &ui_tabs_start_tab("mode", "time");
print $text{'index_desctime'},"<p>\n";

if( !$access{'sysdate'} )
{
  # Show system time for editing
  print &ui_form_start("apply.cgi");
  print &tabletime(&hlink($text{'sys_title'}, "system_time"), 0, %system_date);
  print &ui_submit($text{'action_apply'}, "action");
  if (&support_hwtime()) {
	print &ui_submit($text{'action_sync'}, "action");
  }
  print &ui_form_end();
}
else
{
   # Just show current time
   print &tabletime( &hlink( $text{ 'sys_title' }, "system_time" ), 1, %system_date ),"<p>\n";
}

# Get the hardware time
if (&support_hwtime()) {
	local @tm = &get_hardware_time();
	@tm || &error($get_hardware_time_error || $text{'index_eformat'});
	$hw_date{ 'second' } = $tm[0];
	$hw_date{ 'minute' } = $tm[1];
	$hw_date{ 'hour' } = $tm[2];
	$hw_date{ 'date' } = $tm[3];
	$hw_date{ 'month' } = &number_to_month($tm[4]);
	$hw_date{ 'year'} = $tm[5]+1900;
	$hw_date{ 'day' } = &number_to_weekday($tm[6]);

	if(!$access{'hwdate'}) {
		# Allow editing of hardware time
		if( !$access{ 'sysdate' } ) {
		    $hw_date{ 'second' } = $system_date{ 'second' } if( $hw_date{ 'second' } - $system_date{ 'second' } <= $config{ 'lease' } );
			}
	    
		print &ui_form_start("apply.cgi");
		print &tabletime(&hlink($text{'hw_title'}, "hardware_time"),
				 0, %hw_date);
		print &ui_submit($text{'action_save'}, "action");
		if (support_hwtime()) {
			print &ui_submit($text{'action_sync_s'}, "action");
			}
		print &ui_form_end();
		}
	else {
		# Show show the hardware time
		print &tabletime(&hlink($text{'hw_title'}, "hardware_time"),
				 1, %hw_date ),"<p>\n";
		}
	}
print &ui_tabs_end_tab();

if ($access{'timezone'} && &has_timezone()) {
	print &ui_tabs_start_tab("mode", "zone");
	print $text{'index_desczone'},"<p>\n";

	print &ui_form_start("save_timezone.cgi");
	print &ui_table_start($text{'index_tzheader'}, "width=100%", 2);

	@zones = &list_timezones();
	$cz = &get_current_timezone();
	$found = 0;
	@opts = ( );
	foreach $z (@zones) {
		if ($z->[0] =~ /^(.*)\/(.*)$/) {
			$pfx = $1;
			}
		else {
			$pfx = undef;
			}
		if ($pfx ne $lastpfx && $z ne $zones[0]) {
			push(@opts, [ '', '----------' ]);
			}
		$lastpfx = $pfx;
		push(@opts, [ $z->[0], $z->[1] ? "$z->[0] ($z->[1])"
					       : $z->[0] ]);
		}
	print "</select></td> </tr>\n";
	print &ui_table_row($text{'index_tz'},
		&ui_select("zone", $cz, \@opts, 1, 0, $cz ? 1 : 0));

	print &ui_table_end();
	print &ui_form_end([ [ undef, $text{'save'} ] ]);
	print &ui_tabs_end_tab();
	}

if ( ( !$access{ 'sysdate' } && &has_command( "date" ) || !$access{ 'hwdate' } && &has_command( "hwclock" ) ) && $access{'ntp'} )
{
	# Show time server input
	print &ui_tabs_start_tab("mode", "sync");
	print $text{'index_descsync'},"<p>\n";

	print &ui_form_start("apply.cgi");
	print &ui_table_start(&hlink($text{'index_timeserver'}, "timeserver"),
			      "width=100%", 2, [ "width=30%" ]);

	print &ui_table_row($text{'index_addresses'},
		&ui_textbox("timeserver", $config{'timeserver'}, 60));

	# Show hardware time checkbox
	if (&support_hwtime()) {
		print &ui_table_row(" ",
			&ui_checkbox("hardware", 1, $text{'index_hardware2'},
				     $config{'timeserver_hardware'}));
		}

	# Show schedule input
	$job = &find_webmin_cron_job();
	print &ui_table_row($text{'index_sched'},
		&ui_radio("sched", $job ? 1 : 0,
		  [ [ 0, $text{'no'} ], [ 1, $text{'index_schedyes'} ] ]));
	&seed_random();
	$job ||= { 'mins' => int(rand()*60),
		   'hours' => int(rand()*24),
		   'days' => '*',
		   'months' => '*',
		   'weekdays' => '*' };
	print &ui_table_row(undef,
		&webmincron::show_times_input($job), 2);

	print &ui_table_end();
	print &ui_form_end([ [ "action", $text{'index_sync'} ] ]);
	print &ui_tabs_end_tab();
}
print &ui_tabs_end(1);


&ui_print_footer( "/", $text{ 'index' } );

# tabletime(label, read-only, &time)
# Output a table for setting the date and time
sub tabletime
{
  my ( $label, $ro, %src ) = @_,
  %assoc_day = ( "Mon", $text{ 'day_1' }, "Tue", $text{ 'day_2' }, "Wed", $text{ 'day_3' }, "Thu", $text{ 'day_4' }, "Fri", $text{ 'day_5' }, "Sat", $text{ 'day_6' }, "Sun", $text{ 'day_0' } ),
  %assoc_month = ( "Jan", $text{ 'month_1' }, "Feb", $text{ 'month_2' }, "Mar", $text{ 'month_3' }, "Apr", $text{ 'month_4' }, "May", $text{ 'month_5' }, "Jun", $text{ 'month_6' }, "Jul", $text{ 'month_7' }, "Aug", $text{ 'month_8' }, "Sep", $text{ 'month_9' }, "Oct", $text{ 'month_10' }, "Nov", $text{ 'month_11' }, "Dec", $text{ 'month_12' } );

$rv = &ui_table_start($label, "width=100%", 6);
if (!$ro) {
	$rv .= &ui_table_row($text{'date'},
	    &ui_select("date", $src{'date'}, [ 1 .. 31 ]));
	$rv .= &ui_table_row($text{'month'},
	    &ui_select("month",
		       &zeropad(&month_to_number($src{'month'})+1, 2),
                       [ map { [ &zeropad($_, 2), $text{'month_'.$_} ] }
                             ( 1 .. 12 ) ]));
	$rv .= &ui_table_row($text{'year'},
	    &ui_select("year", $src{'year'}, [ 1969 .. 2037 ]));
	$rv .= &ui_table_row($text{'hour'},
	    &ui_select("hour", &zeropad($src{'hour'}, 2),
		       [ map { &zeropad($_, 2) } (00 .. 23) ]));
	$rv .= &ui_table_row($text{'minute'},
		&ui_select("minute", &zeropad($src{'minute'}, 2),
                       [ map { &zeropad($_, 2) } (00 .. 59) ]));
	$rv .= &ui_table_row($text{'second'},
		&ui_select("second", &zeropad($src{'second'}, 2),
                       [ map { &zeropad($_, 2) } (00 .. 59) ]));
	}
else {
	$rv .= &ui_table_row($text{'date'}, $src{'date'});
	$rv .= &ui_table_row($text{'month'}, $src{'month'});
	$rv .= &ui_table_row($text{'year'}, $src{'year'});
	$rv .= &ui_table_row($text{'hour'}, $src{'hour'});
	$rv .= &ui_table_row($text{'minute'}, $src{'minute'});
	$rv .= &ui_table_row($text{'second'}, $src{'second'});
	}
$rv .= &ui_table_end();
return $rv;
}
