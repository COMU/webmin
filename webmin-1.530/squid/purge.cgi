#!/usr/local/bin/perl
# Call squidclient to remove just one URL

require './squid-lib.pl';
&error_setup($text{'purge_err'});
$access{'rebuild'} || &error($text{'clear_ecannot'});
&ReadParse();
$in{'url'} || &error($text{'purge_eurl'});

&ui_print_header(undef, $text{'purge_title'}, "");

# Get the port number
$conf = &get_config();
if ($squid_version >= 2.3) {
	@ports = &find_config("http_port", $conf);
	foreach $p (@ports) {
		if ($p->{'values'}->[0] =~ /(\d+)$/) {
			$port = $1;
			last;
			}
		}
	}
else {
	$port = &find_value("http_port", $conf);
	$port ||= 3128;
	}

# Run it
print &text('purge_doing', "<tt>$in{'url'}</tt>"),"\n";
$cmd = "$config{'squidclient'} -p $port -m PURGE ".quotemeta($in{'url'});
$out = &backquote_logged("$cmd 2>&1");
print "<pre>$out</pre>\n";
if ($?) {
	print $text{'purge_failed'},"<br>\n";
	}
else {
	print $text{'purge_done'},"<br>\n";
	}
&webmin_log("purge", undef, $in{'url'});

&ui_print_footer("", $text{'index_return'});

