#!/usr/local/bin/perl
# restart_zone.cgi
# Apply changes to one zone only using the ndc command

require './bind8-lib.pl';
&ReadParse();
$access{'ro'} && &error($text{'restart_ecannot'});
$access{'apply'} || &error($text{'restart_ecannot'});
$zone = &get_zone_name($in{'index'}, $in{'view'});
if ($zone->{'view'}) {
	# Reload a zone in a view
	$dom = $zone->{'name'};
	&can_edit_zone($zone) || &error($text{'restart_ecannot'});
	$out = &try_cmd("reload '$dom' IN '$zone->{'view'}'");
	}
else {
	# Just reload one top-level zone
	$dom = $zone->{'name'};
	&can_edit_zone($zone) || &error($text{'restart_ecannot'});
	$out = &try_cmd("reload '$dom' 2>&1 </dev/null");
	}
if ($out =~ /not found/i) {
	# Zone is not known to BIND yet - do a total reload
	$err = &restart_bind();
	&error($err) if ($err);
	if ($access{'remote'}) {
		# Restart all slaves too
		&error_setup();
		@slaveerrs = &restart_on_slaves();
		if (@slaveerrs) {
			&error(&text('restart_errslave',
			     "<p>".join("<br>",
					map { "$_->[0]->{'host'} : $_->[1]" }
					    @slaveerrs)));
			}
		}
	}
elsif ($? || $out =~ /failed|not found|error/i) {
	&error(&text('restart_endc', "<tt>$out</tt>"));
	}
&refresh_nscd();
&webmin_log("apply", $dom);

$tv = $zone->{'type'};
if ($in{'return'}) {
	&redirect($ENV{'HTTP_REFERER'});
	}
else {
	&redirect(($tv eq "master" ? "edit_master.cgi" :
		  $tv eq "forward" ? "edit_forward.cgi" : "edit_slave.cgi").
		  "?index=$in{'index'}&view=$in{'view'}");
	}

