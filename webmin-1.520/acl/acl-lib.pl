=head1 acl-lib.pl

Library for editing webmin users, passwords and access rights.

 foreign_require("acl", "acl-lib.pl");
 @users = acl::list_users();
 $newguy = { 'name' => 'newguy',
             'pass' => acl::encrypt_password('smeg'),
             'modules' => [ 'useradmin' ] };
 acl::create_user($newguy);

=cut

BEGIN { push(@INC, ".."); };
use WebminCore;
&init_config();
do 'md5-lib.pl';
%access = &get_module_acl();
$access{'switch'} = 0 if (&is_readonly_mode());

=head2 list_users

Returns a list of hashes containing Webmin user details. Useful keys include :

=item name - Login name

=item pass - Encrypted password

=item modules - Array references of modules

=item theme - Custom theme, if any

=cut
sub list_users
{
local(%miniserv, $_, @rv, %acl, %logout);
&read_acl(undef, \%acl);
&get_miniserv_config(\%miniserv);
foreach my $a (split(/\s+/, $miniserv{'logouttimes'})) {
	if ($a =~ /^([^=]+)=(\S+)$/) {
		$logout{$1} = $2;
		}
	}
open(PWFILE, $miniserv{'userfile'});
while(<PWFILE>) {
	s/\r|\n//g;
	local @user = split(/:/, $_);
	if (@user) {
		local(%user);
		$user{'name'} = $user[0];
		$user{'pass'} = $user[1];
		$user{'sync'} = $user[2];
		$user{'cert'} = $user[3];
		if ($user[4] =~ /^(allow|deny)\s+(.*)/) {
			$user{$1} = $2;
			}
		if ($user[5] =~ /days\s+(\S+)/) {
			$user{'days'} = $1;
			}
		if ($user[5] =~ /hours\s+(\d+\.\d+)-(\d+\.\d+)/) {
			$user{'hoursfrom'} = $1;
			$user{'hoursto'} = $2;
			}
		$user{'lastchange'} = $user[6];
		$user{'olds'} = [ split(/\s+/, $user[7]) ];
		$user{'minsize'} = $user[8];
		$user{'nochange'} = int($user[9]);
		$user{'temppass'} = int($user[10]);
		$user{'modules'} = $acl{$user[0]};
		$user{'lang'} = $gconfig{"lang_$user[0]"};
		$user{'notabs'} = $gconfig{"notabs_$user[0]"};
		$user{'skill'} = $gconfig{"skill_$user[0]"};
		$user{'risk'} = $gconfig{"risk_$user[0]"};
		$user{'rbacdeny'} = $gconfig{"rbacdeny_$user[0]"};
		if ($gconfig{"theme_$user[0]"}) {
			($user{'theme'}, $user{'overlay'}) =
				split(/\s+/, $gconfig{"theme_$user[0]"});
			}
		elsif (defined($gconfig{"theme_$user[0]"})) {
			$user{'theme'} = "";
			}
		$user{'readonly'} = $gconfig{"readonly_$user[0]"};
		$user{'ownmods'} = [ split(/\s+/,
					   $gconfig{"ownmods_$user[0]"}) ];
		$user{'logouttime'} = $logout{$user[0]};
		$user{'real'} = $gconfig{"realname_$user[0]"};
		push(@rv, \%user);
		}
	}
close(PWFILE);
return @rv;
}

=head2 list_groups

Returns a list of hashes, one per Webmin group. Group membership is stored in
/etc/webmin/webmin.groups, and other attributes in the config file. Useful
keys include :

=item name - Group name

=item members - Array reference of member users

=item modules - Modules to grant to members

=cut
sub list_groups
{
local @rv;
open(GROUPS, "$config_directory/webmin.groups");
while(<GROUPS>) {
	s/\r|\n//g;
	local @g = split(/:/, $_);
	local $group = { 'name' => $g[0],
			 'members' => [ split(/\s+/, $g[1]) ],
			 'modules' => [ split(/\s+/, $g[2]) ],
			 'desc' => $g[3],
			 'ownmods' => [ split(/\s+/, $g[4]) ] };
	push(@rv, $group);
	}
close(GROUPS);
return @rv;
}

=head2 list_modules

Returns a list of the dirs of all modules available on this system.

=cut
sub list_modules
{
return map { $_->{'dir'} } &list_module_infos();
}

=head2 list_module_infos

Returns a list of the details of all modules that can be used on this system,
each of which is a hash reference in the same format as their module.info files.

=cut
sub list_module_infos
{
local @mods = grep { &check_os_support($_) } &get_all_module_infos();
return sort { $a->{'desc'} cmp $b->{'desc'} } @mods;
}

=head2 create_user(&details, [clone])

Creates a new Webmin user, based on the hash reference in the details parameter.
This must be in the same format as those returned by list_users. If the clone
parameter is given, it must be a username to copy detailed access control
settings from for this new user.

=cut
sub create_user
{
local(%user, %miniserv, @mods);
%user = %{$_[0]};

&lock_file($ENV{'MINISERV_CONFIG'});
&get_miniserv_config(\%miniserv);
if ($user{'theme'}) {
	$miniserv{"preroot_".$user{'name'}} =
		$user{'theme'}.($user{'overlay'} ? " ".$user{'overlay'} : "");
	}
elsif (defined($user{'theme'})) {
	$miniserv{"preroot_".$user{'name'}} = "";
	}
if (defined($user{'logouttime'})) {
	local @logout = split(/\s+/, $miniserv{'logouttimes'});
	push(@logout, "$user{'name'}=$user{'logouttime'}");
	$miniserv{'logouttimes'} = join(" ", @logout);
	}
&put_miniserv_config(\%miniserv);
&unlock_file($ENV{'MINISERV_CONFIG'});

local @times;
push(@times, "days", $user{'days'}) if ($user{'days'} ne '');
push(@times, "hours", $user{'hoursfrom'}."-".$user{'hoursto'})
	if ($user{'hoursfrom'});
&lock_file($miniserv{'userfile'});
&open_tempfile(PWFILE, ">>$miniserv{'userfile'}");
&print_tempfile(PWFILE,
	"$user{'name'}:$user{'pass'}:$user{'sync'}:$user{'cert'}:",
	($user{'allow'} ? "allow $user{'allow'}" :
	 $user{'deny'} ? "deny $user{'deny'}" : ""),":",
	join(" ", @times),":",
	$user{'lastchange'},":",
	join(" ", @{$user{'olds'}}),":",
	$user{'minsize'},":",
	$user{'nochange'},":",
	$user{'temppass'},
	"\n");
&close_tempfile(PWFILE);
&unlock_file($miniserv{'userfile'});

&lock_file(&acl_filename());
@mods = &list_modules();
&open_tempfile(ACL, ">>".&acl_filename());
&print_tempfile(ACL, &acl_line(\%user, \@mods));
&close_tempfile(ACL);
&unlock_file(&acl_filename());

delete($gconfig{"lang_".$user{'name'}});
$gconfig{"lang_".$user{'name'}} = $user{'lang'} if ($user{'lang'});
delete($gconfig{"notabs_".$user{'name'}});
$gconfig{"notabs_".$user{'name'}} = $user{'notabs'} if ($user{'notabs'});
delete($gconfig{"skill_".$user{'name'}});
$gconfig{"skill_".$user{'name'}} = $user{'skill'} if ($user{'skill'});
delete($gconfig{"risk_".$user{'name'}});
$gconfig{"risk_".$user{'name'}} = $user{'risk'} if ($user{'risk'});
delete($gconfig{"rbacdeny_".$user{'name'}});
$gconfig{"rbacdeny_".$user{'name'}} = $user{'rbacdeny'} if ($user{'rbacdeny'});
delete($gconfig{"ownmods_".$user{'name'}});
$gconfig{"ownmods_".$user{'name'}} = join(" ", @{$user{'ownmods'}})
	if (@{$user{'ownmods'}});
delete($gconfig{"theme_".$user{'name'}});
if ($user{'theme'}) {
	$gconfig{"theme_".$user{'name'}} =
		$user{'theme'}.($user{'overlay'} ? " ".$user{'overlay'} : "");
	}
elsif (defined($user{'theme'})) {
	$gconfig{"theme_".$user{'name'}} = '';
	}
$gconfig{"readonly_".$user{'name'}} = $user{'readonly'}
	if (defined($user{'readonly'}));
$gconfig{"realname_".$user{'name'}} = $user{'real'}
	if (defined($user{'real'}));
&write_file("$config_directory/config", \%gconfig);

if ($_[1]) {
	foreach $m ("", @mods) {
		local $file = "$config_directory/$m/$_[1].acl";
		local $dest = "$config_directory/$m/$user{'name'}.acl";
		if (-r $file) {
			local %macl;
			&read_file($file, \%macl);
			&write_file($dest, \%macl);
			}
		}
	}
}

=head2 modify_user(old-name, &details)

Updates an existing Webmin user, identified by the old-name paramter. The
details hash must be in the same format as returned by list_users or passed
to create_user.

=cut
sub modify_user
{
local(%user, %miniserv, @pwfile, @acl, @mods, $_, $m);
%user = %{$_[1]};

&lock_file($ENV{'MINISERV_CONFIG'});
&get_miniserv_config(\%miniserv);
delete($miniserv{"preroot_".$_[0]});
if ($user{'theme'}) {
	$miniserv{"preroot_".$user{'name'}} =
		$user{'theme'}.($user{'overlay'} ? " ".$user{'overlay'} : "");
	}
elsif (defined($user{'theme'})) {
	$miniserv{"preroot_".$user{'name'}} = "";
	}
local @logout = split(/\s+/, $miniserv{'logouttimes'});
@logout = grep { $_ !~ /^$_[0]=/ } @logout;
if (defined($user{'logouttime'})) {
	push(@logout, "$user{'name'}=$user{'logouttime'}");
	}
$miniserv{'logouttimes'} = join(" ", @logout);
&put_miniserv_config(\%miniserv);
&unlock_file($ENV{'MINISERV_CONFIG'});

local @times;
push(@times, "days", $user{'days'}) if ($user{'days'} ne '');
push(@times, "hours", $user{'hoursfrom'}."-".$user{'hoursto'})
	if ($user{'hoursfrom'});
&lock_file($miniserv{'userfile'});
open(PWFILE, $miniserv{'userfile'});
@pwfile = <PWFILE>;
close(PWFILE);
&open_tempfile(PWFILE, ">$miniserv{'userfile'}");
foreach (@pwfile) {
	if (/^([^:]+):([^:]*)/ && $1 eq $_[0]) {
		if ($2 ne $user{'pass'} &&
		    "!".$2 ne $user{'pass'} &&
		    $2 ne "!".$user{'pass'} &&
		    $user{'pass'} ne 'x' &&
		    $user{'pass'} ne 'e' &&
		    $user{'pass'} ne '*LK*') {
			# Password change detected .. update change time, and
			# save the old one
			local $nolock = $2;
			$nolock =~ s/^\!//;
			unshift(@{$user{'olds'}}, $nolock);
			if ($miniserv{'pass_oldblock'}) {
				while(scalar(@{$user{'olds'}}) >
				      $miniserv{'pass_oldblock'}) {
					pop(@{$user{'olds'}});
					}
				}
			$user{'lastchange'} = time();
			}
		&print_tempfile(PWFILE,
			"$user{'name'}:$user{'pass'}:",
			"$user{'sync'}:$user{'cert'}:",
			($user{'allow'} ? "allow $user{'allow'}" :
			 $user{'deny'} ? "deny $user{'deny'}" : ""),":",
			join(" ", @times),":",
			$user{'lastchange'},":",
			join(" ", @{$user{'olds'}}),":",
			$user{'minsize'},":",
			$user{'nochange'},":",
			$user{'temppass'},
			"\n");
		}
	else {
		&print_tempfile(PWFILE, $_);
		}
	}
&close_tempfile(PWFILE);
&unlock_file($miniserv{'userfile'});

&lock_file(&acl_filename());
@mods = &list_modules();
open(ACL, &acl_filename());
@acl = <ACL>;
close(ACL);
&open_tempfile(ACL, ">".&acl_filename());
foreach (@acl) {
	if (/^(\S+):/ && $1 eq $_[0]) {
		&print_tempfile(ACL, &acl_line($_[1], \@mods));
		}
	else {
		&print_tempfile(ACL, $_);
		}
	}
&close_tempfile(ACL);
&unlock_file(&acl_filename());

delete($gconfig{"lang_".$_[0]});
$gconfig{"lang_".$user{'name'}} = $user{'lang'} if ($user{'lang'});
delete($gconfig{"notabs_".$_[0]});
$gconfig{"notabs_".$user{'name'}} = $user{'notabs'} if ($user{'notabs'});
delete($gconfig{"skill_".$_[0]});
$gconfig{"skill_".$user{'name'}} = $user{'skill'} if ($user{'skill'});
delete($gconfig{"risk_".$_[0]});
$gconfig{"risk_".$user{'name'}} = $user{'risk'} if ($user{'risk'});
delete($gconfig{"rbacdeny_".$_[0]});
$gconfig{"rbacdeny_".$user{'name'}} = $user{'rbacdeny'} if ($user{'rbacdeny'});
delete($gconfig{"ownmods_".$_[0]});
$gconfig{"ownmods_".$user{'name'}} = join(" ", @{$user{'ownmods'}})
	if (@{$user{'ownmods'}});
delete($gconfig{"theme_".$_[0]});
if ($user{'theme'}) {
        $gconfig{"theme_".$user{'name'}} =
                $user{'theme'}.($user{'overlay'} ? " ".$user{'overlay'} : "");
        }
elsif (defined($user{'theme'})) {
        $gconfig{"theme_".$user{'name'}} = '';
        }
delete($gconfig{"readonly_".$_[0]});
$gconfig{"readonly_".$user{'name'}} = $user{'readonly'}
	if (defined($user{'readonly'}));
delete($gconfig{"realname_".$_[0]});
$gconfig{"realname_".$user{'name'}} = $user{'real'}
	if (defined($user{'real'}));
&write_file("$config_directory/config", \%gconfig);

if ($_[0] ne $user{'name'}) {
	# Rename all .acl files if user renamed
	foreach $m (@mods, "") {
		local $file = "$config_directory/$m/$_[0].acl";
		if (-r $file) {
			&rename_file($file, "$config_directory/$m/$user{'name'}.acl");
			}
		}
	local $file = "$config_directory/$_[0].acl";
	if (-r $file) {
		&rename_file($file, "$config_directory/$user{'name'}.acl");
		}
	}

if ($miniserv{'session'} && $_[0] ne $user{'name'}) {
	# Modify all sessions for the renamed user
	&rename_session_user(\&miniserv, $_[0], $user{'name'});
	}
}

=head2 delete_user(name)

Deletes the named user, including all .acl files for detailed module access
control settings.

=cut
sub delete_user
{
local($_, @pwfile, @acl, %miniserv);

&lock_file($ENV{'MINISERV_CONFIG'});
&get_miniserv_config(\%miniserv);
delete($miniserv{"preroot_".$_[0]});
local @logout = split(/\s+/, $miniserv{'logouttimes'});
@logout = grep { $_ !~ /^$_[0]=/ } @logout;
$miniserv{'logouttimes'} = join(" ", @logout);
&put_miniserv_config(\%miniserv);
&unlock_file($ENV{'MINISERV_CONFIG'});

&lock_file($miniserv{'userfile'});
open(PWFILE, $miniserv{'userfile'});
@pwfile = <PWFILE>;
close(PWFILE);
&open_tempfile(PWFILE, ">$miniserv{'userfile'}");
foreach (@pwfile) {
	if (!/^([^:]+):/ || $1 ne $_[0]) {
		&print_tempfile(PWFILE, $_);
		}
	}
&close_tempfile(PWFILE);
&unlock_file($miniserv{'userfile'});

&lock_file(&acl_filename());
open(ACL, &acl_filename());
@acl = <ACL>;
close(ACL);
&open_tempfile(ACL, ">".&acl_filename());
foreach (@acl) {
	if (!/^([^:]+):/ || $1 ne $_[0]) {
		&print_tempfile(ACL, $_);
		}
	}
&close_tempfile(ACL);
&unlock_file(&acl_filename());

delete($gconfig{"lang_".$_[0]});
delete($gconfig{"notabs_".$_[0]});
delete($gconfig{"skill_".$_[0]});
delete($gconfig{"risk_".$_[0]});
delete($gconfig{"ownmods_".$_[0]});
delete($gconfig{"theme_".$_[0]});
delete($gconfig{"readonly_".$_[0]});
&write_file("$config_directory/config", \%gconfig);

# Delete all module .acl files
&unlink_file(map { "$config_directory/$_/$_[0].acl" } &list_modules());
&unlink_file("$config_directory/$_[0].acl");

if ($miniserv{'session'}) {
	# Delete all sessions for the deleted user
	&delete_session_user(\%miniserv, $_[0]);
	}
}

=head2 create_group(&group, [clone])

Add a new webmin group, based on the details in the group hash. The required
keys are :

=item name - Unique name of the group

=item modules - An array reference of module names

=item members - An array reference of group member names. Sub-groups must have their names prefixed with an @.

=cut
sub create_group
{
&lock_file("$config_directory/webmin.groups");
open(GROUP, ">>$config_directory/webmin.groups");
print GROUP &group_line($_[0]),"\n";
close(GROUP);
&unlock_file("$config_directory/webmin.groups");

if ($_[1]) {
	foreach $m ("", &list_modules()) {
		local $file = "$config_directory/$m/$_[1].gacl";
		local $dest = "$config_directory/$m/$_[0]->{'name'}.gacl";
		if (-r $file) {
			local %macl;
			&read_file($file, \%macl);
			&write_file($dest, \%macl);
			}
		}
	}
}

=head2 modify_group(name, &group)

Update a webmin group, identified by the name parameter. The group's new
details are in the group hash ref, which must be in the same format as
returned by list_groups.

=cut
sub modify_group
{
&lock_file("$config_directory/webmin.groups");
local $lref = &read_file_lines("$config_directory/webmin.groups");
foreach $l (@$lref) {
	if ($l =~ /^([^:]+):/ && $1 eq $_[0]) {
		$l = &group_line($_[1]);
		}
	}
&flush_file_lines();
&unlock_file("$config_directory/webmin.groups");

if ($_[0] ne $_[1]->{'name'}) {
	# Rename all .gacl files if group renamed
	foreach $m (@{$_[1]->{'modules'}}, "") {
		local $file = "$config_directory/$m/$_[0].gacl";
		if (-r $file) {
			&rename_file($file,
				     "$config_directory/$m/$_[1]->{'name'}.gacl");
			}
		}
	}
}

=head2 delete_group(name)

Delete a webmin group, identified by the name parameter.

=cut
sub delete_group
{
&lock_file("$config_directory/webmin.groups");
local $lref = &read_file_lines("$config_directory/webmin.groups");
@$lref = grep { !/^([^:]+):/ || $1 ne $_[0] } @$lref;
&flush_file_lines();
&unlock_file("$config_directory/webmin.groups");
&unlink_file(map { "$config_directory/$_/$_[0].gacl" } &list_modules());
}

=head2 group_line(&group)

Internal function to generate a group file line

=cut
sub group_line
{
return join(":", $_[0]->{'name'},
		 join(" ", @{$_[0]->{'members'}}),
		 join(" ", @{$_[0]->{'modules'}}),
		 $_[0]->{'desc'},
		 join(" ", @{$_[0]->{'ownmods'}}) );
}

=head2 acl_line(&user, &allmodules)

Internal function to generate an ACL file line.

=cut
sub acl_line
{
local(%user);
%user = %{$_[0]};
return "$user{'name'}: ".join(' ', @{$user{'modules'}})."\n";
}

=head2 can_edit_user(user, [&groups])

Returns 1 if the current Webmin user can edit some other user.

=cut
sub can_edit_user
{
return 1 if ($access{'users'} eq '*');
if ($access{'users'} eq '~') {
	return $base_remote_user eq $_[0];
	}
local $u;
local $glist = $_[1] ? $_[1] : [ &list_groups() ];
foreach $u (split(/\s+/, $access{'users'})) {
	if ($u =~ /^_(\S+)$/) {
		foreach $g (@$glist) {
			return 1 if ($g->{'name'} eq $1 &&
				     &indexof($_[0], @{$g->{'members'}}) >= 0);
			}
		}
	else {
		return 1 if ($u eq $_[0]);
		}
	}
return 0;
}

=head2 open_session_db(\%miniserv)

Opens the session database, and ties it to the sessiondb hash. Parameters are :

=item miniserv - The Webmin miniserv.conf file as a hash ref, as supplied by get_miniserv_config

=cut
sub open_session_db
{
local $sfile = $_[0]->{'sessiondb'} ? $_[0]->{'sessiondb'} :
	       $_[0]->{'pidfile'} =~ /^(.*)\/[^\/]+$/ ? "$1/sessiondb"
						      : return;
eval "use SDBM_File";
dbmopen(%sessiondb, $sfile, 0700);
eval { $sessiondb{'1111111111'} = 'foo bar' };
if ($@) {
	dbmclose(%sessiondb);
	eval "use NDBM_File";
	dbmopen(%sessiondb, $sfile, 0700);
	}
else {
	delete($sessiondb{'1111111111'});
	}
}

=head2 delete_session_id(\%miniserv, id)

Deletes one session from the database. Parameters are :

=item miniserv - The Webmin miniserv.conf file as a hash ref, as supplied by get_miniserv_config.

=item user - ID of the session to remove.

=cut
sub delete_session_id
{
return 1 if (&is_readonly_mode());
&open_session_db($_[0]);
local $ex = exists($sessiondb{$_[1]});
delete($sessiondb{$_[1]});
dbmclose(%sessiondb);
return $ex;
}

=head2 delete_session_user(\%miniserv, user)

Deletes all sessions for some user. Parameters are :

=item miniserv - The Webmin miniserv.conf file as a hash ref, as supplied by get_miniserv_config.

=item user - Name of the user whose sessions get removed.

=cut
sub delete_session_user
{
return 1 if (&is_readonly_mode());
&open_session_db($_[0]);
foreach my $s (keys %sessiondb) {
	local ($u,$t) = split(/\s+/, $sessiondb{$s});
	if ($u eq $_[1]) {
		delete($sessiondb{$s});
		}
	}
dbmclose(%sessiondb);
}

=head2 rename_session_user(\%miniserv, olduser, newuser)

Changes the username in all sessions for some user. Parameters are :

=item miniserv - The Webmin miniserv.conf file as a hash ref, as supplied by get_miniserv_config.

=item olduser - The original username.

=item newuser - The new username.

=cut
sub rename_session_user
{
return 1 if (&is_readonly_mode());
&open_session_db(\%miniserv);
foreach my $s (keys %sessiondb) {
	local ($u,$t) = split(/\s+/, $sessiondb{$s});
	if ($u eq $_[1]) {
		$sessiondb{$s} = "$_[2] $t";
		}
	}
dbmclose(%sessiondb);
}

=head2 update_members(&allusers, &allgroups, &modules, &members)

Update the modules for members users and groups of some group. The parameters
are :

=item allusers - An array ref of all Webmin users, as returned by list_users.

=item allgroups - An array ref of all Webmin groups.

=item modules - Modules to assign to members.

=item members - An array ref of member user and group names.

=cut
sub update_members
{
local $m;
foreach $m (@{$_[3]}) {
	if ($m !~ /^\@(.*)$/) {
		# Member is a user
		local ($u) = grep { $_->{'name'} eq $m } @{$_[0]};
		if ($u) {
			$u->{'modules'} = [ @{$_[2]}, @{$u->{'ownmods'}} ];
			&modify_user($u->{'name'}, $u);
			}
		}
	else {
		# Member is a group
		local $gname = substr($m, 1);
		local ($g) = grep { $_->{'name'} eq $gname } @{$_[1]};
		if ($g) {
			$g->{'modules'} = [ @{$_[2]}, @{$g->{'ownmods'}} ];
			&modify_group($g->{'name'}, $g);
			&update_members($_[0], $_[1], $g->{'modules'},
					$g->{'members'});
			}
		}
	}
}

=head2 copy_acl_files(from, to, &modules)

Copy all .acl files from some user to another user in a list of modules.
The parameters are :

=item from - Source user name.

=item to - Destination user name.

=item modules - Array ref of module names.

=cut
sub copy_acl_files
{
local $m;
foreach $m (@{$_[2]}) {
	&unlink_file("$config_directory/$m/$_[1].acl");
	local %acl;
	if (&read_file("$config_directory/$m/$_[0].acl", \%acl)) {
		&write_file("$config_directory/$m/$_[1].acl", \%acl);
		}
	}
}

=head2 copy_group_acl_files(from, to, &modules)

Copy all .acl files from some group to another in a list of modules. Parameters
are :

=item from - Source group name.

=item to - Destination group name.

=item modules - Array ref of module names.

=cut
sub copy_group_acl_files
{
local $m;
foreach $m (@{$_[2]}) {
	&unlink_file("$config_directory/$m/$_[1].gacl");
	local %acl;
	if (&read_file("$config_directory/$m/$_[0].gacl", \%acl)) {
		&write_file("$config_directory/$m/$_[1].gacl", \%acl);
		}
	}
}
=head2 copy_group_user_acl_files(from, to, &modules)

Copy all .acl files from some group to a user in a list of modules. Parameters
are :

=item from - Source group name.

=item to - Destination user name.

=item modules - Array ref of module names.

=cut
sub copy_group_user_acl_files
{
local $m;
foreach $m (@{$_[2]}) {
	&unlink_file("$config_directory/$m/$_[1].acl");
	local %acl;
	if (&read_file("$config_directory/$m/$_[0].gacl", \%acl)) {
		&write_file("$config_directory/$m/$_[1].acl", \%acl);
		}
	}
}

=head2 set_acl_files(&allusers, &allgroups, module, &members, &access)

Recursively update the ACL for all sub-users and groups of a group, by copying
detailed access control settings from the group down to users. Parameters are :

=item allusers - An array ref of Webmin users, as returned by list_users.

=item allgroups - An array ref of Webmin groups.

=item module - Name of the module to update ACL for.

=item members - Names of group members.

=item access - The module ACL hash ref to copy to users.

=cut
sub set_acl_files
{
local $m;
foreach $m (@{$_[3]}) {
	if ($m !~ /^\@(.*)$/) {
		# Member is a user
		local ($u) = grep { $_->{'name'} eq $m } @{$_[0]};
		if ($u) {
			local $aclfile =
				"$config_directory/$_[2]/$u->{'name'}.acl";
			&lock_file($aclfile);
			&write_file($aclfile, $_[4]);
			chmod(0640, $aclfile);
			&unlock_file($aclfile);
			}
		}
	else {
		# Member is a group
		local $gname = substr($m, 1);
		local ($g) = grep { $_->{'name'} eq $gname } @{$_[1]};
		if ($g) {
			local $aclfile =
				"$config_directory/$_[2]/$g->{'name'}.gacl";
			&lock_file($aclfile);
			&write_file($aclfile, $_[4]);
			chmod(0640, $aclfile);
			&unlock_file($aclfile);
			&set_acl_files($_[0], $_[1], $_[2], $g->{'members'}, $_[4]);
			}
		}
	}
}

=head2 get_ssleay

Returns the path to the openssl command (or equivalent) on this system.

=cut
sub get_ssleay
{
if (&has_command($config{'ssleay'})) {
	return &has_command($config{'ssleay'});
	}
elsif (&has_command("openssl")) {
	return &has_command("openssl");
	}
elsif (&has_command("ssleay")) {
	return &has_command("ssleay");
	}
else {
	return undef;
	}
}

=head2 encrypt_password(password, [salt])

Encrypts and returns a Webmin user password. If the optional salt parameter
is not given, a salt will be selected randomly.

=cut
sub encrypt_password
{
local ($pass, $salt) = @_;
if ($gconfig{'md5pass'}) {
	# Use MD5 encryption
	$salt ||= '$1$'.substr(time(), -8).'$xxxxxxxxxxxxxxxxxxxxxx';
	return &encrypt_md5($pass, $salt);
	}
else {
	# Use Unix DES
	&seed_random();
	$salt ||= chr(int(rand(26))+65).chr(int(rand(26))+65);
	return &unix_crypt($pass, $salt);
	}
}

=head2 get_unixauth(\%miniserv)

Returns a list of Unix users/groups/all and the Webmin user that they
authenticate as, as array references.

=cut
sub get_unixauth
{
local @rv;
local @ua = split(/\s+/, $_[0]->{'unixauth'});
foreach my $ua (@ua) {
	if ($ua =~ /^(\S+)=(\S+)$/) {
		push(@rv, [ $1, $2 ]);
		}
	else {
		push(@rv, [ "*", $ua ]);
		}
	}
return @rv;
}

=head2 save_unixauth(\%miniserv, &authlist)

Updates %miniserv with the given Unix auth list, which must be in the format
returned by get_unixauth.

=cut
sub save_unixauth
{
local @ua;
foreach my $ua (@{$_[1]}) {
	if ($ua->[0] ne "*") {
		push(@ua, "$ua->[0]=$ua->[1]");
		}
	else {
		push(@ua, $ua->[1]);
		}
	}
$_[0]->{'unixauth'} = join(" ", @ua);
}

=head2 delete_from_groups(user|@group)

Removes the specified user from all groups.

=cut
sub delete_from_groups
{
local ($user) = @_;
foreach my $g (&list_groups()) {
	local @mems = @{$g->{'members'}};
	local $i = &indexof($user, @mems);
	if ($i >= 0) {
		splice(@mems, $i, 1);
		$g->{'members'} = \@mems;
		&modify_group($g->{'name'}, $g);
		}
	}
}

=head2 check_password_restrictions(username, password)

Checks if some new password is valid for a user, and if not returns
an error message.

=cut
sub check_password_restrictions
{
local ($name, $pass) = @_;
local %miniserv;
&get_miniserv_config(\%miniserv);
local ($user) = grep { $_->{'name'} eq $name } &list_users();
local $minsize = $user ? $user->{'minsize'} : undef;
$minsize ||= $miniserv{'pass_minsize'};
if (length($pass) < $minsize) {
	return &text('cpass_minsize', $minsize);
	}
foreach my $re (split(/\t+/, $miniserv{'pass_regexps'})) {
	if ($re =~ /^\!(.*)$/) {
		$re = $1;
		$pass !~ /$re/ || return ($miniserv{'pass_regdesc'} ||
					  $text{'cpass_notre'});
		}
	else {
		$pass =~ /$re/ || return ($miniserv{'pass_regdesc'} ||
					  $text{'cpass_re'});
		}
	}
if ($miniserv{'pass_nouser'}) {
	$pass =~ /\Q$name\E/i && return $text{'cpass_name'};
	}
if ($miniserv{'pass_nodict'}) {
	local $temp = &transname();
	&open_tempfile(TEMP, ">$temp", 0, 1);
	&print_tempfile(TEMP, $pass,"\n");
	&close_tempfile(TEMP);
	local $unknown;
	if (&has_command("ispell")) {
		open(SPELL, "ispell -a <$temp |");
		while(<SPELL>) {
			if (/^(#|\&|\?)/) {
				$unknown++;
				}
			}
		close(SPELL);
		}
	elsif (&has_command("spell")) {
		open(SPELL, "spell <$temp |");
		local $line = <SPELL>;
		$unknown++ if ($line);
		close(SPELL);
		}
	else {
		return &text('cpass_spellcmd', "<tt>ispell</tt>",
					       "<tt>spell</tt>");
		}
	$unknown || return $text{'cpass_dict'};
	}
if ($miniserv{'pass_oldblock'} && $user) {
	local $c = 0;
	foreach my $o (@{$user->{'olds'}}) {
		local $enc = &encrypt_password($pass, $o);
		$enc eq $o && return $text{'cpass_old'};
		last if ($c++ > $miniserv{'pass_oldblock'});
		}
	}
return undef;
}

=head2 hash_session_id(sid)

Returns an MD5 or Unix-crypted session ID.

=cut
sub hash_session_id
{
local ($sid) = @_;
local $use_md5 = &md5_perl_module();
if (!$hash_session_id_cache{$sid}) {
        if ($use_md5) {
                # Take MD5 hash
                $hash_session_id_cache{$sid} = &hash_md5_session($sid);
                }
        else {
                # Unix crypt
                $hash_session_id_cache{$sid} = &unix_crypt($sid, "XX");
                }
        }
return $hash_session_id_cache{$sid};
}

=head2 hash_md5_session(string)

Returns a string encrypted in MD5 format.

=cut
sub hash_md5_session
{
local $passwd = $_[0];
local $use_md5 = &md5_perl_module();

# Add the password
local $ctx = eval "new $use_md5";
$ctx->add($passwd);

# Add some more stuff from the hash of the password and salt
local $ctx1 = eval "new $use_md5";
$ctx1->add($passwd);
$ctx1->add($passwd);
local $final = $ctx1->digest();
for($pl=length($passwd); $pl>0; $pl-=16) {
	$ctx->add($pl > 16 ? $final : substr($final, 0, $pl));
	}

# This piece of code seems rather pointless, but it's in the C code that
# does MD5 in PAM so it has to go in!
local $j = 0;
local ($i, $l);
for($i=length($passwd); $i; $i >>= 1) {
	if ($i & 1) {
		$ctx->add("\0");
		}
	else {
		$ctx->add(substr($passwd, $j, 1));
		}
	}
$final = $ctx->digest();

# Convert the 16-byte final string into a readable form
local $rv;
local @final = map { ord($_) } split(//, $final);
$l = ($final[ 0]<<16) + ($final[ 6]<<8) + $final[12];
$rv .= &to64($l, 4);
$l = ($final[ 1]<<16) + ($final[ 7]<<8) + $final[13];
$rv .= &to64($l, 4);
$l = ($final[ 2]<<16) + ($final[ 8]<<8) + $final[14];
$rv .= &to64($l, 4);
$l = ($final[ 3]<<16) + ($final[ 9]<<8) + $final[15];
$rv .= &to64($l, 4);
$l = ($final[ 4]<<16) + ($final[10]<<8) + $final[ 5];
$rv .= &to64($l, 4);
$l = $final[11];
$rv .= &to64($l, 2);

return $rv;
}

=head2 md5_perl_module

Returns a Perl module for MD5 hashing, or undef if none.

=cut
sub md5_perl_module
{
eval "use MD5";
if (!$@) {
        $use_md5 = "MD5";
        }
else {
        eval "use Digest::MD5";
        if (!$@) {
                $use_md5 = "Digest::MD5";
                }
        }
}

=head2 session_db_key(sid)

Returns the session DB key for some session ID. Assumes that open_session_db
has already been called.

=cut
sub session_db_key
{
local ($sid) = @_;
local $hash = &hash_session_id($sid);
return $sessiondb{$hash} ? $hash : $sid;
}

=head2 setup_anonymous_access(path, module)

Grants anonymous access to some path. By default, the user for other anonymous
access will be used, or if there is none, a user named 'anonymous' will be
created and granted access to the module.

=cut
sub setup_anonymous_access
{
local ($path, $mod) = @_;

# Find out what users and paths we grant access to currently
local %miniserv;
&get_miniserv_config(\%miniserv);
local @anon = split(/\s+/, $miniserv{'anonymous'});
local $found = 0;
local $user;
foreach my $a (@anon) {
        local ($p, $u) = split(/=/, $a);
	$found++ if ($p eq $path);
	$user = $u;
	}
return 1 if ($found);		# Already setup

if (!$user) {
	# Create a user if need be
	$user = "anonymous";
	local $uinfo = { 'name' => $user,
			 'pass' => '*LK*',
			 'modules' => [ $mod ],
		       };
	&create_user($uinfo);
	}
else {
	# Make sure the user has the module
	local ($uinfo) = grep { $_->{'name'} eq $user } &list_users();
	if ($uinfo && &indexof($mod, @{$uinfo->{'modules'}}) < 0) {
		push(@{$uinfo->{'modules'}}, $mod);
		&modify_user($uinfo->{'name'}, $uinfo);
		}
	else {
		print STDERR "Anonymous access is granted to user $user, but he doesn't exist!\n";
		}
	}

# Grant access to the user and path
push(@anon, "$path=$user");
$miniserv{'anonymous'} = join(" ", @anon);
&put_miniserv_config(\%miniserv);
&reload_miniserv();
}

1;

