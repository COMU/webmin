#!/usr/local/bin/perl
# edit_db.cgi
# Edit or create a db table record

require './mysql-lib.pl';
&ReadParse();
$access{'perms'} || &error($text{'perms_ecannot'});

if ($in{'new'}) {
	&ui_print_header(undef, $text{'db_title1'}, "", "create_db");
	}
else {
	$d = &execute_sql_safe($master_db, "select * from db order by db");
	$u = $d->{'data'}->[$in{'idx'}];
	$access{'perms'} == 1 || &can_edit_db($u->[1]) ||
		&error($text{'perms_edb'});
	&ui_print_header(undef, $text{'db_title2'}, "", "edit_db");
	}

print &ui_form_start("save_db.cgi");
if ($in{'new'}) {
	print &ui_hidden("new", 1);
	}
else {
	print &ui_hidden("oldhost", $u->[0]);
	print &ui_hidden("olddb", $u->[1]);
	print &ui_hidden("olduser", $u->[2]);
	}
print &ui_table_start($text{'db_header'}, undef, 2);

# Database name
print &ui_table_row($text{'db_db'}, &select_db($u->[1]));

# Apply to user
print &ui_table_row($text{'db_user'},
	&ui_opt_textbox("user", $u->[2], 20, $text{'db_anon'}));

# Apply to hosts
print &ui_table_row($text{'db_host'},
	&ui_radio("host_mode", $u->[0] eq '' ? 0 : $u->[0] eq '%' ? 1 : 2,
	  [ [ 0, $text{'db_hosts'} ],
	    [ 1, $text{'db_any'} ],
	    [ 2, &ui_textbox("host", $u->[0] eq '%' ? '' : $u->[0], 40) ] ]));

# Permissions for DB
for($i=3; $i<=&db_priv_cols()+3-1; $i++) {
	push(@opts, [ $i, $text{"db_priv$i"} ]);
	push(@sel, $i) if ($u->[$i] eq 'Y');
	}
print &ui_table_row($text{'db_perms'},
	&ui_select("perms", \@sel, \@opts, 10, 1, 1));

print &ui_table_end();
print &ui_form_end([ $in{'new'} ? ( [ undef, $text{'create'} ] )
				: ( [ undef, $text{'save'} ],
				    [ 'delete', $text{'delete'} ] ) ]);

&ui_print_footer('list_dbs.cgi', $text{'dbs_return'},
	"", $text{'index_return'});

