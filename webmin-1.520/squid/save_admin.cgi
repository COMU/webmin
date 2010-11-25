#!/usr/local/bin/perl
# save_admin.cgi
# Save admin options

require './squid-lib.pl';
$access{'admopts'} || &error($text{'eadm_ecannot'});
&ReadParse();
&lock_file($config{'squid_conf'});
$conf = &get_config();
$whatfailed = $text{'sadmin_ftsao'};

($olduser, $oldgroup) = &get_squid_user($conf);
if ($squid_version < 2) {
	if ($in{'effective_def'}) {
		&save_directive($conf, "cache_effective_user", [ ]);
		}
	else {
		%dir = ( 'name', 'cache_effective_user',
			 'values', [ $in{'effective_u'}, $in{'effective_g'} ] );
		&save_directive($conf, "cache_effective_user", [ \%dir ]);
		}
	}
else {
	&save_opt("cache_effective_user", undef, $conf);
	&save_opt("cache_effective_group", undef, $conf);
        }
&save_opt("cache_mgr", \&check_email, $conf);
&save_opt("visible_hostname", \&check_hostname, $conf);
if ($squid_version < 2) {
	&save_opt("announce_to", undef, $conf);
	&save_opt("cache_announce", \&check_announce, $conf);
	}
else {
	&save_opt("unique_hostname", \&check_hostname, $conf);
	if ($squid_version >= 2.4) {
		&save_opt("hostname_aliases", undef, $conf);
		}
	&save_opt("announce_host", \&check_hostname, $conf);
	&save_opt("announce_port", \&check_port, $conf);
	&save_opt("announce_file", undef, $conf);
	&save_opt_time("announce_period", $conf);
	}
&flush_file_lines();
&unlock_file($config{'squid_conf'});
&webmin_log("admin", undef, undef, \%in);

($user, $group) = &get_squid_user($conf);
if (($olduser ne $user || $oldgroup ne $group) && $user && $group) {
	# User/group has changed! Ask user if he wants to chown log/cache/pid
	&ui_print_header(undef, $text{'sadmin_header'}, "");
	print $text{'sadmin_msg1'},"\n"; 
	print "<center><form action=chown.cgi>\n";
	print "<input type=submit value=\"$text{'sadmin_buttco'}\">\n";
	print "</form></center>\n";
	&ui_print_footer("", $text{'sadmin_return'});
	}
else { &redirect(""); }

sub check_email
{
return $_[0] =~ /^\S+$/ ? undef : &text('sadmin_inavea',$_[0]);
}

sub check_hostname
{
return $_[0] =~ /^\S+$/ ? undef : &text('sadmin_inavh',$_[0]);
}

sub check_announce
{
return $_[0] =~ /^\d+$/ ? undef : &text('sadmin_inavap',$_[0]);
}

sub check_port
{
return $_[0] =~ /^\d+$/ ? undef : &text('sadmin_inavp',$_[0]);
}

