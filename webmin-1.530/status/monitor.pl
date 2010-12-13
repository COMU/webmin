#!/usr/local/bin/perl
# monitor.pl
# Check all the monitors and send email if something is down

$no_acl_check++;
delete($ENV{'FOREIGN_MODULE_NAME'});
delete($ENV{'SCRIPT_NAME'});
delete($ENV{'SERVER_ROOT'});
require './status-lib.pl';

# Check if the monitor should be run now
@tm = localtime(time());
if ($ARGV[0] ne "--force") {
	@hours = split(/\s+/, $config{'sched_hours'});
	!@hours || &indexof($tm[2], @hours) >= 0 || exit;
	@days = split(/\s+/, $config{'sched_days'});
	!@days || &indexof($tm[6], @days) >= 0 || exit;
	}
else {
	shift(@ARGV);
	}

# Check for list of monitors to limit refresh to
%onlycheck = map { $_, 1 } @ARGV;

# Open status and number of fails files
&lock_file($oldstatus_file);
&read_file($oldstatus_file, \%oldstatus);
&lock_file($fails_file);
&read_file($fails_file, \%fails);

# Get the list of services, ordered so that those with dependencies are first
@services = &list_services();
@services = sort { &sort_func($a, $b) } @services;
if (keys %onlycheck) {
	@services = grep { $onlycheck{$_->{'id'}} } @services;
	}

# Check for services that are down
$nowunix = time();
$now = &make_date($nowunix);
($nowdate, $nowtime) = split(/\s+/, $now);
$thishost = &get_system_hostname();
$ecount = 0;
foreach $serv (@services) {
	if ($serv->{'nosched'} == 1) {
		# Scheduled checking totally disabled
		delete($oldstatus{$serv->{'id'}});
		next;
		}
	@remotes = &expand_remotes($serv);

	# Check if we depend on something that is down
	if ($serv->{'depend'} && defined($oldstatus{$serv->{'depend'}})) {
		$depend = &get_service($serv->{'depend'});
		$depstats = &expand_oldstatus($oldstatus{$serv->{'depend'}},
					      $depend);
		@depremotes = split(/\s+/, $depend->{'remote'});
		if ($depstats->{$depremotes[0]} != 1) {
			# It is .. mark all as failed dependencies
			$oldstatus{$serv->{'id'}} = 
				join(" ", map { "$_=-4" } @remotes);
			next;
			}
		}

	# Find the current status
	$warn = $serv->{'nosched'} == 0 ? $config{'sched_warn'} :
		$serv->{'nosched'} - 2;
	@stats = &service_status($serv);
	$oldstats = &expand_oldstatus($oldstatus{$serv->{'id'}}, $serv);

	# Find the notification modes
	%notify = map { $_, 1 } split(/\s+/, $serv->{'notify'});

	# If the number of fails before warning is > 1, then the status may
	# still be considered OK even if it is down right now
	local $up = $stat->{'up'};
	if ($up != 1 && $serv->{'fails'} > 1) {
		$fails{$serv->{'id'}}++;
		if ($fails{$serv->{'id'}} < $serv->{'fails'}) {
			# Not really down yet
			$up = 1;
			}
		}
	else {
		$fails{$serv->{'id'}} = 0;
		}

	# Check for a status change or failure on each monitored host,
	# and perform the appropriate action
	$newstats = { };
	foreach $r (@remotes) {
		# Work out the hostname
		local $host = $r eq "*" ? $thishost : $r;
		$o = $oldstats->{$r};

		# Get the up/down status
		local ($stat) = grep { $_->{'remote'} eq $r } @stats;
		if (!$stat) {
			print STDERR "Failed to find status for $r!\n";
			next;
			}

		# If the number of fails before warning is > 1, then the status
		# may still be considered OK even if it is down right now
		local $up = $stat->{'up'};
		local $fid = $serv->{'id'}."-".$r;
		if ($up != 1 && $serv->{'fails'} > 1) {
			# Not up, but more than one failure is needed for it to
			# be considered down for alerting purposes.
			$fails{$fid}++;
			if ($fails{$fid} < $serv->{'fails'}) {
				# Not really down yet
				$up = 1;
				}
			}
		else {
			$fails{$fid} = 0;
			}

		$thisemail = undef;
		$suffix = undef;
		$out = undef;
		if ($warn == 0 && $up == 0 && $o) {
			# Service has just gone down
			$suffix = "down";
			$out = &run_on_command($serv, $serv->{'ondown'});
			}
		elsif ($warn == 1 && $up != $o &&
		       (defined($o) || $up == 0)) {
			# Service has changed status
			if ($up == 0) {
				# A monitor has gone down
				$suffix = "down";
				$out = &run_on_command($serv, $serv->{'ondown'});
				}
			elsif ($up == 1 && $o != -4) {
				# A monitor has come back up after being down
				$suffix = "up";
				$out = &run_on_command($serv, $serv->{'onup'});
				}
			elsif ($up == -1) {
				# Detected that a program the monitor depends on
				# is not installed
				$suffix = "un";
				}
			elsif ($up == -2) {
				# Cannot contact remote Webmin
				$suffix = "webmin";
				}
			elsif ($up == -3) {
				# Monitor function timed out
				$suffix = "timed";
				$out = &run_on_command($serv,
						       $serv->{'ontimeout'});
				}
			}
		elsif ($warn == 2 && $up == 0) {
			# Service is down now
			$suffix = "isdown";
			$out = &run_on_command($serv, $serv->{'ondown'});
			}

		# If something happened, notify people
		if ($suffix) {
			$subj = &text('monitor_sub_'.$suffix,
				      $serv->{'desc'}, $host);
			if ($notify{'pager'}) {
				$pager_msg .= &make_message($suffix, $host,
							    $serv, 'pager');
				}
			if ($notify{'sms'}) {
				$sms_msg .= &make_message($suffix, $host,
                                                          $serv, 'sms');
				}
			if ($notify{'snmp'}) {
				push(@snmp_msg, &make_message($suffix, $host,
                                                              $serv, 'snmp'));
				}
			if ($notify{'email'}) {
				$thisemail .= &make_message($suffix, $host,
                                                              $serv, 'email');
				if ($out) {
					$thisemail .= $out;
					}
				$thisemail .= "\n";
				$ecount++;
				}
			}
		$newstats->{$r} = $up;

		if ($serv->{'email'} && $thisemail) {
			# If this service has an extra email address specified,
			# send to it
			&send_status_email($thisemail,
			  $config{'subject_mode'} ? $subj : &text('monitor_sub', $subj),
			  $serv->{'email'});
			}

		$email .= $thisemail;
		if ($config{'sched_single'} && $email) {
			# Force the sending of one email and page per report
			&send_status_email($email,
			  $config{'subject_mode'} ? $subj : &text('monitor_sub', $subj),
			  $config{'sched_email'});
			undef($email);
			if ($pager_msg) {
				&send_status_pager($pager_msg);
				undef($pager_msg);
				}
			if ($sms_msg) {
				&send_status_sms($sms_msg);
				undef($sms_msg);
				}
			}

		# If any SNMP messages are defined, send them
		if (@snmp_msg) {
			&send_status_trap(@snmp_msg);
			undef(@snmp_msg);
			}
		}

	# Update old status hash
	$oldstatus{$serv->{'id'}} =
		join(" ", map { "$_=$newstats->{$_}" } @remotes);
	}

# Close oldstatus and fails files
&write_file($oldstatus_file, \%oldstatus);
&unlock_file($oldstatus_file);
&write_file($fails_file, \%fails);
&unlock_file($fails_file);

# Send the email and page with all messages, if necessary
if ($ecount && !$config{'sched_single'}) {
	&send_status_email($email,
			   $config{'subject_mode'} ? $text{'monitor_sub2'} :
			   $ecount == 1 ? &text('monitor_sub', $subj) :
			   	          &text('monitor_sub3', $ecount),
			   $config{'sched_email'});
	}
if ($pager_msg && !$config{'sched_single'}) {
	&send_status_pager($pager_msg);
	}
if ($sms_msg && !$config{'sched_single'}) {
	&send_status_sms($sms_msg);
	}

# send_status_email(text, subject, email-to)
sub send_status_email
{
return if (!$_[2]);
&foreign_require("mailboxes", "mailboxes-lib.pl");

# Construct and send the email (using correct encoding for body)
local $from = $config{'sched_from'} ? $config{'sched_from'}
				    : &mailboxes::get_from_address();
&mailboxes::send_text_mail($from, $_[2], undef, $_[1], $_[0],
			   $config{'sched_smtp'});
}

# send_status_pager(text)
# Send some message with the pager command, if configured
sub send_status_pager
{
local ($text) = @_;
return if (!$config{'sched_pager'});
return if (!&has_command($config{'pager_cmd'}));
system("$config{'pager_cmd'} ".quotemeta($config{'sched_pager'})." ".
       quotemeta($text)." >/dev/null 2>&1 </dev/null");
}

# send_status_sms(text)
sub send_status_sms
{
local ($text) = @_;
return if (!$text || !$config{'sched_carrier'} || !$config{'sched_sms'});
&foreign_require("mailboxes", "mailboxes-lib.pl");

local $from = $config{'sched_from'} ? $config{'sched_from'}
				    : &mailboxes::get_from_address();
local ($carrier) = grep { $_->{'id'} eq $config{'sched_carrier'} }
			&list_sms_carriers();
return if (!$carrier);
local $email = $config{'sched_sms'}."\@".$carrier->{'domain'};
&mailboxes::send_text_mail($from, $email, undef, undef, $text,
			   $config{'sched_smtp'});
}

# send_status_trap(msg, ...)
# Send an SNMP trap for some message, if configured
sub send_status_trap
{
return if (!$config{'snmp_server'});

# Connect to SNMP server
eval "use Net::SNMP qw(OCTET_STRING)";
if (!$@) {
	# Using the Net::SNMP module
	local ($session, $error) = Net::SNMP->session(
		"-hostname" => $config{'snmp_server'},
		"-port" => 162,
		"-version" => $config{'snmp_version'},
		"-community" => $config{'snmp_community'},
		);
	if ($error) {
		print STDERR "SNMP connect failed : $error\n";
		return;
		}

	# Build OIDs list
	local (@oids, $m);
	foreach $m (@_) {
		local $oid = $config{'snmp_trap'};
		push(@oids, $oid, 4, $m);
		}

	# Send off a trap
	local $rv;
	if ($config{'snmp_version'} == 1) {
		$rv = $session->trap(
			"-varbindlist" => \@oids);
		}
	elsif ($config{'snmp_version'} >= 2) {
		@oids = ( "1.3.6.1.2.1.1.3.0", 67, 0,
			  "1.3.6.1.6.3.1.1.4.1.0", 6, $oids[0],
			  @oids );
		$rv = $session->snmpv2_trap(
			"-varbindlist" => \@oids);
		}
	if (!$rv) {
		print STDERR "trap failed! : ",$session->error(),"\n";
		}
	return;
	}
eval "use SNMP_Session";
if (!$@) {
	# Using the SNMP::Session module
	eval "use BER";
	local $session = $config{'snmp_version'} == 1 ?
			SNMP_Session->open($config{'snmp_server'},
					   $config{'snmp_community'}, 162) :
			SNMPv2c_Session->open($config{'snmp_server'},
					   $config{'snmp_community'}, 162);
	if (!$session) {
		print STDERR "SNMP connect to $config{'snmp_server'} failed\n";
		return;
		}

	local $rv;
	if ($config{'snmp_version'} == 1) {
		local @myoid= ( 1,3,6,1,4,1 );
		local @oids;
		foreach my $m (@_) {
			push(@oids, [
				encode_oid(split(/\./, $config{'snmp_trap'})),
				encode_string($m) ]);
			}
		$rv = $session->trap_request_send(
			encode_oid(@myoid),
			encode_ip_address(&to_ipaddress(&get_system_hostname())),
			encode_int(2),
			encode_int(0),
			encode_timeticks(0),
			@oids
			);
		}
	elsif ($config{'snmp_version'} == 2) {
		@oids = ( "1.3.6.1.2.1.1.3.0", 67, 0,
			  "1.3.6.1.6.3.1.1.4.1.0", 6, $oids[0],
			  @oids );
		$rv = $session->v2_trap_request_send(\@oids, 0);
		}
	if (!$rv) {
		print STDERR "trap failed!\n";
		}
	
	return;
	}
print STDERR "No SNMP perl module found\n";
}

# run_on_command(&serv, command)
sub run_on_command
{
return undef if (!$_[1]);
local $out;
if ($_[0]->{'runon'} && $_[0]->{'remote'}) {
	# Run on the remote host
	local $cmd = quotemeta($_[1]);
	$remote_error_msg = undef;
	&remote_error_setup(\&remote_error_callback);
	if ($config{'output'}) {
		$out = &remote_eval($_[0]->{'remote'}, "status",
			     "`($cmd) 2>&1 </dev/null`");
		}
	else {
		&remote_eval($_[0]->{'remote'}, "status",
			     "system('($cmd) >/dev/null 2>&1 </dev/null')");
		}
	&remote_error_setup(undef);
	if ($remote_error_msg) {
		return &text('monitor_runerr', $_[1], $_[0]->{'remote'},
			     $remote_error_msg);
		}
	return &text('monitor_run1', $_[1], $_[0]->{'remote'})."\n";
	}
else {
	# Just run locally
	if ($config{'output'}) {
		$out = `($_[1]) 2>&1 </dev/null`;
		return &text('monitor_run2', $_[1])."\n".
		       $out;
		}
	else {
		system("($_[1]) >/dev/null 2>&1 </dev/null");
		return &text('monitor_run2', $_[1])."\n";
		}
	}
}

sub remote_error_callback
{
$remote_error_msg = $_[0];
}

# Returns 1 if b should be first, -1 if a should be first, 0 if same
sub sort_func
{
local ($a, $b) = @_;
if ($a->{'id'} eq $b->{'id'}) {
	return 0;
	}
elsif (!$a->{'depend'} && !$b->{'depend'}) {
	return $a->{'desc'} cmp $b->{'desc'};
	}
elsif ($a->{'depend'} && !$b->{'depend'}) {
	return 1;
	}
elsif (!$a->{'depend'} && $b->{'depend'}) {
	return -1;
	}
else {
	return $a->{'depend'} eq $b->{'id'} ? 1 :
	       $b->{'depend'} eq $a->{'id'} ? -1 :
		$a->{'desc'} cmp $b->{'desc'};
	}
}

# quoted_encode(text)
sub quoted_encode
{
local $t = $_[0];
$t =~ s/([=\177-\377])/sprintf("=%2.2X",ord($1))/ge;
return $t;
}

# make_message(status, host, &server, type)
# Returns the message for some email, SMS or SNMP. May use a template, or
# the built-in default.
sub make_message
{
local ($suffix, $host, $serv, $type) = @_;
local $tmpl = $serv->{'tmpl'} ? &get_template($serv->{'tmpl'}) : undef;
if ($tmpl && $tmpl->{$type}) {
	# Construct from template
	local %hash = ( 'DESC' => $serv->{'desc'},
			'HOST' => $host,
			'DATE' => $nowdate,
			'TIME' => $nowtime,
			'STATUS' => $text{'mon_'.$suffix},
			uc($suffix) => 1,
		      );
	foreach my $s (@monitor_statuses) {
		$hash{uc($s)} ||= 0;
		}
	foreach my $k (keys %$serv) {
		$hash{'SERVICE_'.uc($k)} = $serv->{$k};
		}
	local $rv = &substitute_template($tmpl->{$type}, \%hash);
	$rv =~ s/[\r\n]+$//;
	$rv .= "\n";
	return $rv;
	}
else {
	# Use built-in
	if ($type eq 'sms') {
		return &text('monitor_pager_'.$suffix,
			     $host, $serv->{'desc'}, $now);
		}
	elsif ($type eq 'snmp') {
		return &text('monitor_snmp_'.$suffix,
			     $host, $serv->{'desc'});
		}
	elsif ($type eq 'email') {
		return &text('monitor_email_'.$suffix,
			     $host, $serv->{'desc'}, $now)."\n";
		}
	}
}

