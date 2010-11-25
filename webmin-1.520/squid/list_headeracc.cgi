#!/usr/local/bin/perl
# list_headeracc.cgi
# Display all header access control restrictions

require './squid-lib.pl';
$access{'headeracc'} || &error($text{'header_ecannot'});
&ui_print_header(undef, $text{'header_title'}, "", "list_headeracc", 0, 0, 0, &restart_button());
$conf = &get_config();

# Work out what header access directives we support
@types = $squid_version >= 3.0 ?
	("request_header_access", "reply_header_access") : ("header_access");

# Show a table for each
foreach $t (@types) {
	@headeracc = &find_config($t, $conf);
	@links = ( "<a href='edit_headeracc.cgi?new=1&type=$t'>".
		   "$text{'header_add'}</a>" );
	print &ui_subheading($text{'header_'.$t}),"<p>\n"
		if ($t ne "header_access");
	if (@headeracc) {
		print &ui_links_row(\@links);
		print &ui_columns_start([ $text{'header_name'},
					  $text{'header_act'},
					  $text{'header_acls'},
					  $text{'eacl_move'} ]);
		$hc = 0;
		foreach $h (@headeracc) {
			@v = @{$h->{'values'}};
			@cols = ( );
			push(@cols, "<a href='edit_headeracc.cgi?type=$t&".
				    "index=$h->{'index'}'>$v[0]</a>");
			push(@cols, $v[1] eq 'allow' ? $text{'eacl_allow'}
						     : $text{'eacl_deny'});
			push(@cols, join(" ", @v[2..$#v]));
			push(@cols, &ui_up_down_arrows(
				"move_headeracc.cgi?$hc+-1+$t",
				"move_headeracc.cgi?$hc+1+$t",
				$hc != 0, $hc != @headeracc-1));
			print &ui_columns_row(\@cols);
			$hc++;
			}
		print &ui_columns_end();
		}
	else {
		print "$text{'header_none'}<p>\n";
		}
	print &ui_links_row(\@links);
	print "<hr>" if ($t ne $types[$#types]);
	}

&ui_print_footer("", $text{'index_return'});

