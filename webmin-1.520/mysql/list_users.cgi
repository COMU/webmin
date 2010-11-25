#!/usr/local/bin/perl
# list_users.cgi
# Display a list of all database users

require './mysql-lib.pl';
$access{'perms'} == 1 || &error($text{'perms_ecannot'});
&ui_print_header(undef, $text{'users_title'}, "", "users");

print &ui_form_start("delete_users.cgi");
@rowlinks = ( &select_all_link("d", 0),
	      &select_invert_link("d", 0),
	      "<a href='edit_user.cgi?new=1'>$text{'users_add'}</a>" );
print &ui_links_row(\@rowlinks);
@tds = ( "width=5" );
print &ui_columns_start([ "",
			  $text{'users_user'},
			  $text{'users_host'},
			  $text{'users_pass'},
			  $mysql_version >= 5 ? ( $text{'users_ssl'} ) : ( ),
			  $text{'users_perms'} ], 100, 0, \@tds);
$d = &execute_sql_safe($master_db, "select * from user order by user");
%fieldmap = map { $_->{'field'}, $_->{'index'} }
		&table_structure($master_db, "user");
$i = 0;
foreach $u (@{$d->{'data'}}) {
	local @cols;
	push(@cols, "<a href='edit_user.cgi?idx=$i'>".
		    ($u->[1] ? &html_escape($u->[1]) : $text{'users_anon'}).
		    "</a>");
	push(@cols, $u->[0] eq '' || $u->[0] eq '%' ?
		      $text{'user_any'} : &html_escape($u->[0]));
	push(@cols, &html_escape($u->[2]));
	if ($mysql_version >= 5) {
		$ssl = $u->[$fieldmap{'ssl_type'}];
		push(@cols, $text{'user_ssl_'.lc($ssl)} || $ssl);
		}
	local @priv;
	for($j=3; $j<=&user_priv_cols()+3-1; $j++) {
		push(@priv, $text{"users_priv$j"}) if ($u->[$j] eq 'Y');
		}
	push(@cols,
		scalar(@priv) == &user_priv_cols() ? $text{'users_all'} :
		!@priv ? $text{'users_none'} : join("&nbsp;| ", @priv));
	print &ui_checked_columns_row(\@cols, \@tds, "d", $u->[0]." ".$u->[1]);
	$i++;
	}
print &ui_columns_end();
print &ui_links_row(\@rowlinks);
print &ui_form_end([ [ "delete", $text{'users_delete'} ] ]);

# Unix / MySQL user syncing
print &ui_hr();
print &ui_form_start("save_sync.cgi");
print "$text{'users_sync'}<p>\n";
print &ui_table_start(undef, undef, 2);

# When to sync
print &ui_table_row($text{'users_syncwhen'},
	&ui_checkbox("sync_create", 1, $text{'users_sync_create'},
		     $config{'sync_create'})."<br>\n".
	&ui_checkbox("sync_modify", 1, $text{'users_sync_modify'},
		     $config{'sync_modify'})."<br>\n".
	&ui_checkbox("sync_delete", 1, $text{'users_sync_delete'},
		     $config{'sync_delete'}));

# Privs for new users
print &ui_table_row($text{'users_sync_privs'},
	&ui_select("sync_privs",
		   [ split(/\s+/, $config{'sync_privs'}) ],
		   [ map { [ $_, $text{"user_priv$_"} ] }
			 ( 3 .. &user_priv_cols()+3-1 ) ],
		   5, 1));

# Hosts for new users
print &ui_table_row($text{'users_sync_host'},
	&ui_opt_textbox("host", $config{'sync_host'}, 30,
			$text{'users_sync_def'}, $text{'users_sync_sel'}));

print &ui_table_end();
print &ui_form_end([ [ undef, $text{'save'} ] ]);

&ui_print_footer("", $text{'index_return'});

