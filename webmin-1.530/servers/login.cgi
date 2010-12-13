#!/usr/local/bin/perl
# login.cgi
# Store the username and password for a server in a cookie

require './servers-lib.pl';
&ReadParse();
$enc = &encode_base64($in{'user'}.":".$in{'pass'});
$enc =~ s/\r|\n//g;
print "Set-Cookie: $in{'id'}=$enc; path=/";
if (uc($ENV{'HTTPS'}) eq 'ON') {
	print "; secure";
	}
print "\n";
&redirect("link.cgi/$in{'id'}/");

