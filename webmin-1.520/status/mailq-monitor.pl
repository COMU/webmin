# Check if a mail queue is too long

sub get_mailq_status
{
local $m = $_[0]->{'mod'};
return { 'up' => -1 } if (!&foreign_installed($m));
local @qfiles;
if ($m eq "sendmail") {
	&foreign_require("sendmail", "sendmail-lib.pl");
	@qfiles = &sendmail::list_mail_queue();
	}
elsif ($m eq "qmailadmin") {
	&foreign_require("qmailadmin", "qmail-lib.pl");
	@qfiles = &qmailadmin::list_queue();
	}
elsif ($m eq "postfix") {
	&foreign_require("postfix", "postfix-lib.pl");
	@qfiles = &postfix::list_queue();
	}
if (@qfiles > $_[0]->{'size'}) {
	return { 'up' => 0,
		 'desc' => "<font color=#ff0000>".&text('mailq_toomany', scalar(@qfiles))."</font>" };
	}
else {
	return { 'up' => 1,
		 'desc' => &text('mailq_ok', scalar(@qfiles)) };
	}
}

sub show_mailq_dialog
{
# Mail system to check
print &ui_table_row($text{'mailq_system'},
	&ui_select("mod", $_[0]->{'mod'},
		[ map { [ $_, $text{'mailq_'.$_} ] }
		  ("sendmail", "qmailadmin", "postfix") ]));

# Max queue size
print &ui_table_row($text{'mailq_size'},
	&ui_textbox("size", $_[0]->{'size'}, 10));
}

sub parse_mailq_dialog
{
$_[0]->{'mod'} = $in{'mod'};
$in{'size'} =~ /^\d+$/ || &error($text{'mailq_esize'});
$_[0]->{'size'} = $in{'size'};
}

