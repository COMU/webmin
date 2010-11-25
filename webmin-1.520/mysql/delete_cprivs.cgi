#!/usr/local/bin/perl
# Delete several selected column permissions

require './mysql-lib.pl';
&ReadParse();
$access{'perms'} || &error($text{'perms_edb'});
&error_setup($text{'cprivs_derr'});
@d = split(/\0/, $in{'d'});
@d || &error($text{'cprivs_enone'});

# Delete the table privs
foreach $hdutc (@d) {
	($host, $db, $user, $table, $column) = split(/ /, $hdutc);
	$access{'perms'} == 1 || &can_edit_db($db) ||
		&error($text{'perms_edb'});
	&execute_sql_logged($master_db,
		     "delete from columns_priv where host = '$host' ".
		     "and db = '$db' ".
		     "and user = '$user' ".
		     "and table_name = '$table' ".
		     "and column_name = '$column'");
	}
&execute_sql_logged($master_db, 'flush privileges');

# Log it
&webmin_log("delete", "cprivs", scalar(@d));
&redirect("list_cprivs.cgi");

