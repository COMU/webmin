#!/usr/local/bin/perl
# Show all secret keys

require './ipsec-lib.pl';
&ui_print_header(undef, $text{'secrets_title'}, "");

@secs = &list_secrets();
if (@secs) {
	print &ui_columns_start([ $text{'secrets_name'},
				  $text{'secrets_type'},
				  $text{'secrets_desc'} ]);
	foreach $s (@secs) {
		local $desc;
		if (lc($s->{'type'}) eq "psk" &&
		    $s->{'value'} =~ /"(.*)"/) {
			$desc = &text('secrets_pass', "<tt>$1</tt>");
			}
		elsif (lc($s->{'type'}) eq "rsa" &&
		       $s->{'value'} =~ /Modulus:\s*(\S+)/i) {
			$desc = &text('secrets_mod', "<tt>".substr($1, 0, 20)."..</tt>");
			}
		print &ui_columns_row([
			"<a href='edit_secret.cgi?idx=$s->{'idx'}'>".
			($s->{'name'} || $text{'secrets_any'})."</a>",
			$text{'secrets_'.lc($s->{'type'})} || uc($s->{'type'}),
			$desc,
			]);
		}
	print &ui_columns_end();
	}
else {
	print "<b>$text{'secrets_none'}</b><p>\n";
	}
print "<a href='edit_secret.cgi?new=1&type=psk'>$text{'secrets_newpsk'}</a>\n";
print "&nbsp;" x 2;
print "<a href='edit_secret.cgi?new=1&type=rsa'>$text{'secrets_newrsa'}</a>\n";
print "<br>\n";

&ui_print_footer("", $text{'index_return'});
