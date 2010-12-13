#!/usr/local/bin/perl
# edit_view.cgi
# Display options for an existing view

require './bind8-lib.pl';
&ReadParse();
$conf = &get_config();
$view = $conf->[$in{'index'}];
$vconf = $view->{'members'};
$access{'views'} || &error($text{'view_ecannot'});
&can_edit_view($view) || &error($text{'view_ecannot'});

&ui_print_header(undef, $text{'view_title'}, "",
		 undef, undef, undef, undef, &restart_links());

# Form header
print &ui_form_start("save_view.cgi", "post");
print &ui_hidden("index", $in{'index'});
print &ui_table_start($text{'view_opts'}, "width=100%", 4,
		      [ "width=30%", undef, "width=30%", undef ]);

# View name
@v = @{$view->{'values'}};
print &ui_table_row($text{'view_name'}, "<tt>$v[0]</tt>");

# Class (not editable)
print &ui_table_row($text{'view_class'},
	$v[1] ? "<tt>$v[1]</tt>" : "$text{'default'} (<tt>IN</tt>)");

print &addr_match_input($text{'view_match'}, "match-clients", $vconf);
print &choice_input($text{'view_recursion'}, 'recursion', $vconf,
		    $text{'yes'}, 'yes', $text{'no'}, 'no',
		    $text{'default'}, undef);

print &ui_table_end();

# Options for zones in view
print &ui_table_start($text{'view_opts2'}, "width=100%", 4,
		      [ "width=30%", undef, "width=30%", undef ]);

print &address_input($text{'master_transfer'}, "allow-transfer", $vconf);
print &address_input($text{'master_query'}, "allow-query", $vconf);

print &address_input($text{'master_notify2'}, "also-notify", $vconf);
print &address_input($text{'master_notify3'}, "allow-notify", $vconf);

print &ui_table_end();

if ($access{'ro'}) {
	print &ui_form_end();
	}
else {
	print &ui_form_end([ [ undef, $text{'save'} ] ]);

	# Delete button
	print &ui_hr();
	print &ui_buttons_start();
	print &ui_buttons_row("delete_view.cgi",
		$text{'view_delete'}, $text{'view_deletemsg'},
		&ui_hidden("index", $in{'index'}));
	print &ui_buttons_end();
	}
&ui_print_footer("", $text{'index_return'});

