#!/usr/local/bin/perl
# save_progs.cgi
# Save helper program options

require './squid-lib.pl';
$access{'hprogs'} || &error($text{'eprogs_ecannot'});
&ReadParse();
&lock_file($config{'squid_conf'});
$conf = &get_config();
$whatfailed = $text{'sprog_ftshpo'};

if ($squid_version < 2) {
	&save_opt("ftpget_program", \&check_prog, $conf);
	&save_opt("ftpget_options", \&check_opts, $conf);
	}
else {
	&save_opt("ftp_list_width", \&check_width, $conf);
	}
&save_opt("ftp_user", \&check_ftpuser, $conf);
&save_opt("cache_dns_program", \&check_prog, $conf);
&save_opt("dns_children", \&check_children, $conf);
&save_choice("dns_defnames", "off", $conf);
if ($squid_version >= 2) {
	&save_opt("dns_nameservers", \&check_dnsservers, $conf);
	}
&save_opt("unlinkd_program", \&check_prog, $conf);
&save_opt("pinger_program", \&check_prog, $conf);
&save_opt("redirect_program", \&check_prog, $conf);
&save_opt("redirect_children", \&check_children, $conf);

&flush_file_lines();
&unlock_file($config{'squid_conf'});
&webmin_log("progs", undef, undef, \%in);
&redirect("");

sub check_opts
{
return $_[0] =~ /\S/ ? undef : $text{'sprog_emsg1'};
}

sub check_prog
{
$_[0] =~ /^(\/\S+)/ || return &text('sprog_emsg2', $_[0]);
return -x $1 ? undef : &text('sprog_emsg3',$_[0]); 
}

sub check_ftpuser
{
return $_[0] =~ /^\S+@\S*$/ ? undef : &text('sprog_emsg4',$_[0]);
}

sub check_children
{
return $_[0] =~ /^\d+$/ ? undef : &text('sprog_emsg5',$_[0]);
}

sub check_width
{
return $_[0] =~ /^\d+$/ ? undef : &text('sprog_emsg6',$_[0]);
}

sub check_dnsservers
{
local $dns;
local @dns = split(/\s+/, $_[0]);
return $text{'sprog_emsg7'} if (!@dns);
foreach $dns (@dns) {
	&check_ipaddress($dns) || return &text('sprog_emsg8',$dns);
	}
return undef;
}


