#!/usr/local/bin/perl
# edit_aifc.cgi
# Edit or create an active interface

require './net-lib.pl';

&ReadParse();
if ($in{'new'}) {
	&ui_print_header(undef, $text{'aifc_create'}, "");
	&can_create_iface() || &error($text{'ifcs_ecannot'});
	}
else {
	@act = &active_interfaces();
	$a = $act[$in{'idx'}];
	&can_iface($a) || &error($text{'ifcs_ecannot_this'});
	&ui_print_header(undef, $text{'aifc_edit'}, "");
	}

# Form start
print &ui_form_start("save_aifc.cgi");
print &ui_hidden("new", $in{'new'});
print &ui_hidden("idx", $in{'idx'});
print &ui_table_start(
	$in{'virtual'} || $a && $a->{'virtual'} ne "" ? $text{'aifc_desc2'}
						      : $text{'aifc_desc1'},
	"width=100%", 4);

# Interface name, perhaps editable
if ($in{'new'} && $in{'virtual'}) {
	$namefield = $in{'virtual'}.":".
		     &ui_textbox("virtual", undef, 3).
		     &ui_hidden("name", $in{'virtual'});
	}
elsif ($in{'new'}) {
	$namefield = &ui_textbox("name", undef, 6);
	}
else {
	$namefield = "<tt>$a->{'fullname'}</tt>";
	}
print &ui_table_row($text{'ifcs_name'}, $namefield);

# IP address
print &ui_table_row($text{'ifcs_ip'},
	&ui_textbox("address", $a ? $a->{'address'} : "", 15));

# Netmask field
if ($in{'virtual'} && $in{'new'} && $virtual_netmask) {
	# Fixed for virtual interface
	$netmaskfield = $virtual_netmask;
	}
elsif (!$access{'netmask'}) {
	# Cannot be edited
	$netmaskfield = $a ? $a->{'netmask'} : $config{'def_netmask'};
	}
elsif ($in{'new'}) {
	# Enter or use default
	$netmaskfield = &ui_opt_textbox(
		"netmask", $config{'def_netmask'}, 15, $text{'ifcs_auto'});
	}
else {
	# Allow editing
	$netmaskfield = &ui_textbox("netmask", $a->{'netmask'}, 15);
	}
print &ui_table_row($text{'ifcs_mask'}, $netmaskfield);

# Broadcast address field, except for IPv6
if ($in{'new'} || !&is_ipv6_address($a->{'address'})) {
	if (!$access{'broadcast'}) {
		# Cannot be edited
		$broadfield = $a ? $a->{'broadcast'} : $config{'def_broadcast'};
		}
	elsif ($in{'new'}) {
		# Can enter or use default
		$broadfield = &ui_opt_textbox(
			"broadcast", $config{'def_broadcast'}, 15,
			$text{'ifcs_auto'});
		}
	else {
		# Allow editing
		$broadfield = &ui_textbox("broadcast", $a->{'broadcast'}, 15);
		}
	print &ui_table_row($text{'ifcs_broad'}, $broadfield);
	}

# Show MTU
if (!$access{'mtu'}) {
	# Cannot be edited
	$mtufield = $a ? $a->{'mtu'} :
		    $config{'def_mtu'} ? $config{'def_mtu'} : $text{'default'};
	}
elsif ($in{'new'}) {
	# Can enter or use default
	$mtufield = &ui_opt_textbox("mtu", $config{'def_mtu'}, 6,
				    $text{'ifcs_auto'});
	}
else {
	# Allow editing
	$mtufield = &ui_textbox("mtu", $a->{'mtu'}, 6);
	}
print &ui_table_row($text{'ifcs_mtu'}, $mtufield);

# Current status
if (!$access{'up'}) {
	# Cannot edit
	$upfield = !$a ? $text{'ifcs_up'} :
		   $a->{'up'} ? $text{'ifcs_up'} : $text{'ifcs_down'};
	}
else {
	$upfield = &ui_radio("up", $in{'new'} || $a->{'up'} ? 1 : 0,
			[ [ 1, $text{'ifcs_up'} ], [ 0, $text{'ifcs_down'} ] ]);
	}
print &ui_table_row($text{'ifcs_status'}, $upfield);

# Hardware address, if non-virtual
if ((!$a && $in{'virtual'} eq "") ||
    ($a && $a->{'virtual'} eq "" && &iface_hardware($a->{'name'}))) {
	if ($in{'new'}) {
		$hardfield = &ui_opt_textbox("ether", undef, 18,
					     $text{'aifc_default'});
		}
	else {
		$hardfield = &ui_textbox("ether", $a->{'ether'}, 18);
		}
	print &ui_table_row($text{'aifc_hard'}, $hardfield);
	}

# Virtual sub-interfaces
if ($a && $a->{'virtual'} eq "") {
	$vcount = 0;
	foreach $va (@act) {
		if ($va->{'virtual'} ne "" && $va->{'name'} eq $a->{'name'}) {
			$vcount++;
			}
		}
	print &ui_table_row($text{'ifcs_virts'},
		$vcount." ".
	        "(<a href='edit_aifc.cgi?new=1&virtual=$a->{'name'}'>".
		"$text{'ifcs_addvirt'}</a>)");
	}
     
# End of the form
print &ui_table_end();
if ($in{'new'}) {
	@buts = ( [ undef, $text{'create'} ] );
	}
else {
	@buts = ( [ undef, $text{'save'} ] );
	if ($access{'delete'}) {
		push(@buts, [ 'delete', $text{'delete'} ]);
		}
	}
print &ui_form_end(\@buts);

&ui_print_footer("list_ifcs.cgi?mode=active", $text{'ifcs_return'});

