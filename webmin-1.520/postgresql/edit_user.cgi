#!/usr/local/bin/perl
# edit_user.cgi
# Display a form for editing or creating a user

require './postgresql-lib.pl';
&ReadParse();
$access{'users'} || &error($text{'user_ecannot'});
if ($in{'new'}) {
	&ui_print_header(undef, $text{'user_create'}, "");
	}
else {
	&ui_print_header(undef, $text{'user_edit'}, "");
	$s = &execute_sql_safe($config{'basedb'}, "select * from pg_shadow ".
					     "where usename = '$in{'user'}'");
	@user = @{$s->{'data'}->[0]};
	}

# Start of the form
print &ui_form_start("save_user.cgi");
print &ui_hidden("new", $in{'new'});
print &ui_hidden("user", $in{'user'});
print &ui_table_start($text{'user_header'}, undef, 2);

# Username, not always editable
print &ui_table_row($text{'user_name'},
	$in{'new'} || &get_postgresql_version() >= 7.4 ?
		&ui_textbox("name", $user[0], 40) :
		$user[0]);

if ($in{'new'}) {
	# For new users, can select empty or specific password
	print &ui_table_row($text{'user_passwd'},
	      &ui_radio("pass_def", 1,
			[ [ 1, $text{'user_none'} ],
			  [ 0, $text{'user_setto'} ] ])." ".
		     &ui_password("pass", undef, 20));
	}
else {
	# For existing users, can select empty, leave unchanged or
	# specific password
	print &ui_table_row($text{'user_passwd'},
	      &ui_radio("pass_def", 2,
			[ [ 2, $text{'user_nochange'} ],
			  [ 0, $text{'user_setto'} ] ])." ".
		     &ui_password("pass", undef, 20));
	}

# Can create databases?
print &ui_table_row($text{'user_db'},
	&ui_yesno_radio("db", $user[2] =~ /t|1/));

# Create create other users?
print &ui_table_row($text{'user_other'},
	&ui_yesno_radio("other", $user[4] =~ /t|1/));

# Valid until
$user[6] = '' if ($user[6] !~ /\S/);
print &ui_table_row($text{'user_until'},
	$user[6] ? &ui_textbox("until", $user[6], 40) :
		&ui_opt_textbox("until", $user[6], 40, $text{'user_forever'}));

# End of form and buttons
print &ui_table_end();
if ($in{'new'}) {
	print &ui_form_end([ [ undef, $text{'create'} ] ]);
	}
else {
	print &ui_form_end([ [ undef, $text{'save'} ],
			     [ 'delete', $text{'delete'} ] ]);
	}

&ui_print_footer("list_users.cgi", $text{'user_return'});

