#!/usr/local/bin/perl
# save_bifc.cgi
# Create, save or delete a boot-time interface

require './net-lib.pl';
&ReadParse();
@boot = &boot_interfaces();

if ($in{'delete'} || $in{'unapply'}) {
	# Delete interface
	&error_setup($text{'bifc_err1'});
	$b = $boot[$in{'idx'}];
	&can_iface($b) || &error($text{'ifcs_ecannot_this'});

	if ($in{'unapply'}) {
		# Shut down this interface active (if active)
		&error_setup($text{'bifc_err4'});
		@active = &active_interfaces();
		($act) = grep { $_->{'fullname'} eq $b->{'fullname'} } @active;
		if ($act) {
			if (defined(&unapply_interface)) {
				$err = &unapply_interface($act);
				$err && &error("<pre>$err</pre>");
				}
			else {
				&deactivate_interface($act);
				}
			}

		}
	&delete_interface($b);
	&webmin_log("delete", "bifc", $b->{'fullname'}, $b);
	}
else {
	# Save or create interface
	&error_setup($text{'bifc_err2'});
	if (!$in{'new'}) {
		# Modifying an interface
		$oldb = $boot[$in{'idx'}];
		&can_iface($oldb) || &error($text{'ifcs_ecannot_this'});
		$b->{'name'} = $oldb->{'name'};
		$b->{'file'} = $oldb->{'file'};
		$b->{'gateway'} = $oldb->{'gateway'};
		$b->{'virtual'} = $oldb->{'virtual'}
			if (defined($oldb->{'virtual'}));
		$b->{'code'} = $oldb->{'code'};
		}
	elsif (defined($in{'virtual'})) {
		# creating a virtual interface
		$in{'virtual'} =~ /^\d+$/ ||
			&error($text{'bifc_evirt'});
		$in{'virtual'} >= $min_virtual_number ||
			&error(&text('aifc_evirtmin', $min_virtual_number));
		foreach $eb (@boot) {
			if ($eb->{'name'} eq $in{'name'} &&
			    $eb->{'virtual'} eq $in{'virtual'}) {
				&error(&text('bifc_evirtdup',
				       "$in{'name'}:$in{'virtual'}"));
				}
			}
		$b->{'name'} = $in{'name'};
		$b->{'virtual'} = $in{'virtual'};
		&can_create_iface() || &error($text{'ifcs_ecannot'});
		&can_iface($b) || &error($text{'ifcs_ecannot'});
		}
	elsif ($in{'name'} =~ /^([a-z]+\d*(\.\d+)?):(\d+)$/) {
		# also creating a virtual interface
		foreach $eb (@boot) {
			if ($eb->{'name'} eq $1 &&
			    $eb->{'virtual'} eq $3) {
				&error(&text('bifc_evirtdup', $in{'name'}));
				}
			}
		$3 >= $min_virtual_number ||
			&error(&text('aifc_evirtmin', $min_virtual_number));
		$b->{'name'} = $1;
		$b->{'virtual'} = $3;
		&can_create_iface() || &error($text{'ifcs_ecannot'});
		&can_iface($b) || &error($text{'ifcs_ecannot'});
		}
	elsif ($in{'name'} =~/^[a-z]+\d*(\.\d+)?$/) {
		# creating a real interface
		foreach $eb (@boot) {
			if ($eb->{'fullname'} eq $in{'name'} && (!&is_ipv6_address($in{'address'}))) {
				&error(&text('bifc_edup', $in{'name'}));
				}
			}
		$b->{'name'} = $in{'name'};
		&can_create_iface() || &error($text{'ifcs_ecannot'});
		&can_iface($b) || &error($text{'ifcs_ecannot'});
		}
	elsif ($in{'name'} eq 'auto') {
		# creating a vlan interface
		foreach $eb (@boot) {
			if ($eb->{'fullname'} eq $in{'name'}) {
				&error(&text('bifc_edup', $in{'name'}));
				}
			}
		$b->{'name'} = $in{'name'};
		&can_create_iface() || &error($text{'ifcs_ecannot'});
		&can_iface($b) || &error($text{'ifcs_ecannot'});
		}
	else {
		&error($text{'bifc_ename'});
		}

	# Check for address clash
	$allow_clash = defined(&allow_interface_clash) ?
			&allow_interface_clash($b, 1) : 1;
	if (!$allow_clash && $in{'mode'} eq 'address' &&
	    ($in{'new'} || $oldb->{'address'} ne $in{'address'})) {
		($clash) = grep { $_->{'address'} eq $in{'address'} &&
				  $_->{'up'} } @boot;
		$clash && &error(&text('aifc_eclash', $clash->{'fullname'}));
		}

	# Validate and store inputs
	if ($in{'mode'} eq 'dhcp' || $in{'mode'} eq 'bootp') {
		$in{'activate'} && !defined(&apply_interface) &&
			&error($text{'bifc_eapply'});
		$b->{$in{'mode'}}++;
		$auto++;
		}
	else {
		&valid_boot_address($in{'address'}) ||
			&error(&text('bifc_eip', $in{'address'}));
		$b->{'address'} = $in{'address'};
		}

	# Set description if possible
	if (defined($in{'desc'})) {
		$b->{'desc'} = $in{'desc'};
		}

	if ($virtual_netmask && $b->{'virtual'} ne "") {
		# Always use this netmask for virtuals
		$b->{'netmask'} = $virtual_netmask;
		}
	elsif (!$access{'netmask'}) {
		# Use default netmask
		$b->{'netmask'} = $in{'new'} ?
			$config{'def_netmask'} || "255.255.255.0" :
			$oldb->{'netmask'};
		}
	elsif (&can_edit("netmask", $b) && $access{'netmask'}) {
		$auto && !$in{'netmask'} || &check_netmask($in{'netmask'},$in{'address'}) ||
			&error(&text('bifc_emask', $in{'netmask'}));
		$b->{'netmask'} = $in{'netmask'};
		}

	if (!$access{'broadcast'} || $in{'broadcast_def'}) {
		# Work out broadcast
		$b->{'broadcast'} = $in{'new'} ? 
			&compute_broadcast($b->{'address'}, $b->{'netmask'}) :
			$oldb->{'broadcast'};
		}
	elsif (&can_edit("broadcast", $b)) {
		# Manually entered broadcast
		&is_ipv6_address($in{'address'}) || 
		    ($auto && !$in{'broadcast'}) ||
			&check_ipaddress($in{'broadcast'}) ||
			&error(&text('bifc_ebroad', $in{'broadcast'}));
		$b->{'broadcast'} = $in{'broadcast'};
		}

	if (!$access{'mtu'}) {
		# Use default MTU
		$b->{'mtu'} = $in{'new'} ? $config{'def_mtu'}
					 : $oldb->{'mtu'};
		}
	elsif (&can_edit("mtu", $b) && $access{'mtu'}) {
		$auto && !$in{'mtu'} ||
			$in{'mtu_def'} ||
			$in{'mtu'} =~ /^\d+$/ ||
			&error(&text('bifc_emtu', $in{'mtu'}));
		$b->{'mtu'} = $in{'mtu_def'} ? undef : $in{'mtu'};
		}

	# MAC address
	if (defined($in{'ether'}) && !$in{'ether_def'}) {
		$in{'ether'} =~ /^[A-Fa-f0-9:]+$/ ||
			&error(&text('aifc_ehard', $in{'ether'}));
		$b->{'ether'} = $in{'ether'};
		}

	if ($in{'new'} && !$access{'up'} ||
	    &can_edit("up", $b) && $in{'up'} && $access{'up'}) {
		$b->{'up'}++;
		}
	elsif (!$access{'up'}) {
		$b->{'up'} = $oldb->{'up'};
		}

	if ($in{'bond'}) {
		$b->{'bond'} = 1;
		if ($in{'partner'}) {
			$b->{'partner'} = $in{'partner'};
		}
		if ($in{'bondmode'} ne ''){
			$mode = $in{'bondmode'};
			$b->{'mode'} = $mode;
		}
		if ($in{'miimon'} ne ''){
			$b->{'miimon'} = $in{'miimon'};
		}
		if ($in{'updelay'} ne ''){
			$b->{'updelay'} = $in{'updelay'};
		}
		if ($in{'downdelay'} ne ''){
			$b->{'downdelay'} = $in{'downdelay'};
		}
	}
	
	if($in{'vlan'} == 1) {
		$b->{'vlan'} = 1;
		
		if($in{'physical'}) {
			$b->{'physical'} = $in{'physical'};
		}
		if($in{'vlanid'}) {
			$b->{'vlanid'} = $in{'vlanid'};
		}
  }
  if(&is_ipv6_address){
     $b->{'fullname'} = $in{'name'};
  }   
  else{
    $b->{'fullname'} = $b->{'name'}.( $b->{'virtual'} eq '' ? '' : ':'.$b->{'virtual'});
  } 
	&save_interface($b);

	if ($in{'activate'}) {
		# Make this interface active (if possible)
		&error_setup($text{'bifc_err3'});
		$b->{'up'}++;
		$b->{'address'} = &to_ipaddress($b->{'address'});
		if (defined(&apply_interface)) {
			$err = &apply_interface($b);
			$err && &error("<pre>$err</pre>");
			}
		else {
			if ($in{'bond'}) {
				if (($gconfig{'os_type'} eq 'debian-linux') && ($gconfig{'os_version'} >= 5)) {}
				else {&load_module($b);}
			}
			&activate_interface($b);
			}
		}
	&webmin_log($in{'new'} ? 'create' : 'modify',
		    "bifc", $b->{'fullname'}, $b);
	}
&redirect("list_ifcs.cgi?mode=boot");

