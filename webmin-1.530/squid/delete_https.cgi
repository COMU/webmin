#!/usr/local/bin/perl
# Delete multiple proxy restrictions

require './squid-lib.pl';
&error_setup($text{'dhttp_err'});
$access{'actrl'} || &error($text{'eacl_ecannot'});
&ReadParse();
@d = split(/\0/, $in{'d'});
@d || &error($text{'dhttp_enone'});

# Get the existing restrictions
&lock_file($config{'squid_conf'});
$conf = &get_config();
@https = &find_config("http_access", $conf);

# Delete them
foreach $d (sort { $b <=> $c } @d) {
	$http = $conf->[$d];
	splice(@https, &indexof($http, @https), 1);
	}

# Write out
&save_directive($conf, "http_access", \@https);
&flush_file_lines();
&unlock_file($config{'squid_conf'});
&webmin_log("delete", "https", scalar(@d));
&redirect("edit_acl.cgi");

