# unixware-lib.pl
# Filesystem functions for UnixWare (works for me on 7.0.1)

# Return information about a filesystem, in the form:
#  directory, device, type, options, fsck_order, mount_at_boot
# If a field is unused or ignored, a - appears instead of the value.
# Swap-filesystems (devices or files mounted for VM) have a type of 'swap',
# and 'swap' in the directory field
sub list_mounts
{
local(@rv, @p, $_, $i); $i = 0;

# List normal filesystem mounts
open(FSTAB, $config{fstab_file});
while(<FSTAB>) {
	chop; s/#.*$//g;
	if (!/\S/) { next; }
	@p = split(/\s+/, $_);
	if ($p[3] eq "swap") { $p[2] = "swap"; }
	$rv[$i++] = [ $p[2], $p[0], $p[3], $p[6], $p[4], $p[5] ];
	}
close(FSTAB);

# List automount points
open(AUTOTAB, $config{autofs_file});
while(<AUTOTAB>) {
	chop; s/#.*$//g;
	if (!/\S/ || /^[+\-]/) { next; }
	@p = split(/\s+/, $_);
	if ($p[2] eq "") { $p[2] = "-"; }
	else { $p[2] =~ s/^-//g; }
	$rv[$i++] = [ $p[0], $p[1], "autofs", $p[2], "-", "yes" ];
	}
close(AUTOTAB);

return @rv;
}


# create_mount(directory, device, type, options, fsck_order, mount_at_boot)
# Add a new entry to the fstab file, and return the index of the new entry
sub create_mount
{
local($len, @mlist, $fcsk, $dir);
if ($_[2] eq "autofs") {
	# An autofs mount.. add to /etc/auto_master
	$len = grep { $_->[2] eq "autofs" } (&list_mounts());
	&open_tempfile(AUTOTAB, ">> $config{autofs_file}");
	&print_tempfile(AUTOTAB, "$_[0] $_[1]",($_[3] eq "-" ? "" : " -$_[3]"),"\n");
	&close_tempfile(AUTOTAB);
	}
else {
	# Add to the fstab file
	$len = grep { $_->[2] ne "autofs" } (&list_mounts());
	&open_tempfile(FSTAB, ">> $config{fstab_file}");
	if ($_[2] eq "ufs" || $_[2] eq "s5fs") {
		($fsck = $_[1]) =~ s/\/dsk\//\/rdsk\//g;
		}
	else { $fsck = "-"; }
	if ($_[2] eq "swap") { $dir = "-"; }
	else { $dir = $_[0]; }
	&print_tempfile(FSTAB, "$_[1]  $fsck  $dir  $_[2]  $_[4]  $_[5]  $_[3]\n");
	&close_tempfile(FSTAB);
	}
return $len;
}


# delete_mount(index)
# Delete some mount from the table
sub delete_mount
{
local(@fstab, $i, $line, $_);
open(FSTAB, $config{fstab_file});
@fstab = <FSTAB>;
close(FSTAB);
$i = 0;

&open_tempfile(FSTAB, "> $config{fstab_file}");
foreach (@fstab) {
	chop; ($line = $_) =~ s/#.*$//g;
	if ($line =~ /\S/ && $i++ == $_[0]) {
		# found the line not to include
		}
	else { &print_tempfile(FSTAB, $_,"\n"); }
	}
&close_tempfile(FSTAB);

open(AUTOTAB, $config{autofs_file});
@autotab = <AUTOTAB>;
close(AUTOTAB);
&open_tempfile(AUTOTAB, "> $config{autofs_file}");
foreach (@autotab) {
	chop; ($line = $_) =~ s/#.*$//g;
	if ($line =~ /\S/ && $line !~ /^[+\-]/ && $i++ == $_[0]) {
		# found line not to include..
		}
	else { &print_tempfile(AUTOTAB, $_,"\n"); }
	}
&close_tempfile(AUTOTAB);
}


# change_mount(num, directory, device, type, options, fsck_order, mount_at_boot)
# Change an existing permanent mount
sub change_mount
{
local(@fstab, @autotab, $i, $line, $fsck, $dir, $_);
$i = 0;

open(FSTAB, $config{fstab_file});
@fstab = <FSTAB>;
close(FSTAB);
&open_tempfile(FSTAB, "> $config{fstab_file}");
foreach (@fstab) {
	chop; ($line = $_) =~ s/#.*$//g;
	if ($line =~ /\S/ && $i++ == $_[0]) {
		# Found the line to replace
		if ($_[3] eq "ufs" || $_[3] eq "s5fs") {
			($fsck = $_[2]) =~ s/\/dsk\//\/rdsk\//g;
			}
		else { $fsck = "-"; }
		if ($_[3] eq "swap") { $dir = "-"; }
		else { $dir = $_[1]; }
		&print_tempfile(FSTAB, "$_[2]  $fsck  $dir  $_[3]  $_[5]  $_[6]  $_[4]\n");
		}
	else { &print_tempfile(FSTAB, $_,"\n"); }
	}
&close_tempfile(FSTAB);

open(AUTOTAB, $config{autofs_file});
@autotab = <AUTOTAB>;
close(AUTOTAB);
&open_tempfile(AUTOTAB, "> $config{autofs_file}");
foreach (@autotab) {
	chop; ($line = $_) =~ s/#.*$//g;
	if ($line =~ /\S/ && $line !~ /^[+\-]/ && $i++ == $_[0]) {
		# Found the line to replace
		&print_tempfile(AUTOTAB, "$_[1]  $_[2]  ",
				($_[4] eq "-" ? "" : "-$_[4]"),"\n");
		}
	else { &print_tempfile(AUTOTAB, $_,"\n"); }
	}
&close_tempfile(AUTOTAB);
}


# list_mounted()
# Return a list of all the currently mounted filesystems and swap files.
# The list is in the form:
#  directory device type options
# For swap files, the directory will be 'swap'
sub list_mounted
{
local(@rv, @p, $_, $i, $r);
&open_execute_command(SWAP, "swap -l 2>/dev/null", 1, 1);
while(<SWAP>) {
	if (/^(\/\S+)\s+/) { push(@rv, [ "swap", $1, "swap", "-" ]); }
	}
close(SWAP);
&open_tempfile(MNTTAB, "/etc/mnttab");
while(<MNTTAB>) {
	s/#.*$//g; if (!/\S/) { next; }
	@p = split(/\s+/, $_);
	if ($p[0] =~ /:vold/) { next; }
	if ($p[0] =~ /^rumba-(\d+)$/) {
		# rumba smb mount
		local($args, $ps); $p[3] = "pid=$1";
		$ps = (-x "/usr/ucb/ps") ? "/usr/ucb/ps auwwwwx $1"
				 	 : "ps -o args -f $1";
		&backquote_command($ps, 1) =~
			/rumba\s+\/\/([^\/]+)\/(.*\S)\s+(\/\S+)(.*)/ || next;
		$serv = $1; $shar = $2; $p[2] = "rumba"; $args = $4;
		if ($args =~ /\s+-s\s+(\S+)/ && $1 ne $serv) {
			$p[0] = "\\\\$1\\$shar";
			$p[3] .= ",machinename=$serv";
			}
		else { $p[0] = "\\\\$serv\\$shar"; }
		if ($args =~ /\s+-c\s+(\S+)/) { $p[3] .= ",clientname=$1"; }
		if ($args =~ /\s+-U\s+(\S+)/) { $p[3] .= ",username=$1"; }
		if ($args =~ /\s+-u\s+(\S+)/) { $p[3] .= ",uid=$1"; }
		if ($args =~ /\s+-g\s+(\S+)/) { $p[3] .= ",gid=$1"; }
		if ($args =~ /\s+-f\s+(\S+)/) { $p[3] .= ",fmode=$1"; }
		if ($args =~ /\s+-d\s+(\S+)/) { $p[3] .= ",dmode=$1"; }
		if ($args =~ /\s+-C/) { $p[3] .= ",noupper"; }
		if ($args =~ /\s+-P\s+(\S+)/) { $p[3] .= ",password=$1"; }
		if ($args =~ /\s+-S/) { $p[3] .= ",readwrite"; }
		if ($args =~ /\s+-w/) { $p[3] .= ",readonly"; }
		if ($args =~ /\s+-e/) { $p[3] .= ",attr"; }
		}
	else { $p[3] = join(',' , (grep {!/^dev=/} split(/,/ , $p[3]))); }
	push(@rv, [ $p[1], $p[0], $p[2], $p[3] ]);
	}
&close_tempfile(MNTTAB);
foreach $r (@rv) {
	if ($r->[2] eq "cachefs" && $r->[1] =~ /\.cfs_mnt_points/) {
		# Oh no.. a caching filesystem mount. Fiddle things so that
		# it looks right.
		for($i=0; $i<@rv; $i++) {
			if ($rv[$i]->[0] eq $r->[1]) {
				# Found the automatically mounted entry. lose it
				$r->[1] = $rv[$i]->[1];
				splice(@rv, $i, 1);
				last;
				}
			}
		}
	}
return @rv;
}


# mount_dir(directory, device, type, options)
# Mount a new directory from some device, with some options. Returns 0 if ok,
# or an error string if failed. If the directory is 'swap', then mount as
# virtual memory.
sub mount_dir
{
local($out, $opts);
if ($_[0] eq "swap") {
	# Adding a swap device
	$out = &backquote_logged("swap -a $_[1] 2>&1");
	if ($?) { return $out; }
	}
else {
	# Mounting a directory
	if ($_[2] eq "cachefs") {
		# Mounting a caching filesystem.. need to create cache first
		local(%options);
		&parse_options("cachefs", $_[3]);
		if (!(-r "$options{cachedir}/.cfs_resource")) {
			# The cache directory does not exist.. set it up
			if (-d $options{cachedir} &&
			    !rmdir($options{"cachedir"})) {
				return "The directory $options{cachedir} ".
				       "already exists. Delete it";
				}
			$out = &backquote_logged("cfsadmin -c $options{cachedir} 2>&1");
			if ($?) { return $out; }
			}
		}
	if ($_[2] eq "rumba") {
		# call 'rumba' to mount
		local(%options, $shortname, $shar, $opts, $rv);
		&parse_options("rumba", $_[3]);
		$shortname = &get_system_hostname();
		if ($shortname =~ /^([^\.]+)\.(.+)$/) { $shortname = $1; }
		$_[1] =~ /^\\\\(.+)\\(.+)$/;
		$shar = "//".($options{machinename} ?$options{machinename} :$1).
			"/$2";
		$opts = ("-s $1 ").
		 (defined($options{'clientname'}) ?
			"-c $options{'clientname'} " : "-c $shortname ").
		 (defined($options{'username'}) ?
			"-U $options{'username'} " : "").
		 (defined($options{'uid'}) ? "-u $options{'uid'} " : "").
		 (defined($options{'gid'}) ? "-g $options{'gid'} " : "").
		 (defined($options{'fmode'}) ? "-f $options{'fmode'} " : "").
		 (defined($options{'dmode'}) ? "-d $options{'dmode'} " : "").
		 (defined($options{'noupper'}) ? "-C " : "").
		 (defined($options{'password'}) ?
			"-P $options{'password'} " : "-n ").
		 (defined($options{'readwrite'}) ? "-S " : "").
		 (defined($options{'readonly'}) ? "-w " : "").
		 (defined($options{'attr'}) ? "-e " : "");
		local $rtemp = &transname();
		$rv = &system_logged("rumba \"$shar\" $_[0] $opts >$rtemp 2>&1 </dev/null");
		$out = `cat $rtemp`; unlink($rtemp);
		if ($rv) { return "<pre>$out</pre> : rumba \"$shar\" $_[0] $opts"; }
		}
	else {
		$opts = $_[3] eq "-" ? "" : "-o \"$_[3]\"";
		$out = &backquote_logged("mount -F $_[2] $opts -- $_[1] $_[0] 2>&1");
		if ($?) { return $out; }
		}
	}
return 0;
}


# unmount_dir(directory, device, type)
# Unmount a directory (or swap device) that is currently mounted. Returns 0 if
# ok, or an error string if failed
sub unmount_dir
{
if ($_[0] eq "swap") {
	$out = &backquote_logged("swap -d $_[1] 2>&1");
	}
elsif ($_[2] eq "rumba") {
	# kill the process (if nobody is in the directory)
	$dir = $_[0];
	if (&backquote_command("fuser -c $_[0] 2>/dev/null") =~ /\d/) {
		return "$_[0] is busy";
		}
	if (&backquote_command("cat /etc/mnttab") =~
	    /rumba-(\d+)\s+$dir\s+nfs/) {
		&kill_logged('TERM', $1) || return "Failed to kill rumba";
		}
	else {
		return "Failed to find rumba pid";
		}
	sleep(1);
	}
else {
	$out = &backquote_logged("umount $_[0] 2>&1");
	}
if ($?) { return $out; }
return 0;
}


# disk_space(type, directory)
# Returns the amount of total and free space for some filesystem, or an
# empty array if not appropriate.
sub disk_space
{
if (&get_mounted($_[1], "*") < 0) { return (); }
if ($_[0] eq "fd" || $_[0] eq "proc" || $_[0] eq "swap" || $_[0] eq "autofs") {
	return ();
	}
if (&backquote_command("df -k ".quotemeta($_[1]), 1) =~
    /Mounted on\n\S+\s+(\S+)\s+\S+\s+(\S+)/) {
	return ($1, $2);
	}
return ( );
}


# list_fstypes()
# Returns an array of all the supported filesystem types. If a filesystem is
# found that is not one of the supported types, generate_location() and
# generate_options() will not be called for it.
sub list_fstypes
{
local(@fs);
@fs = ("vxfs", "ufs", "nfs", "hsfs", "pcfs", "lofs", "cachefs", "swap", "tmpfs", "autofs");
if (&has_command("rumba")) { push(@fs, "rumba"); }
return @fs;
}


# fstype_name(type)
# Given a short filesystem type, return a human-readable name for it
sub fstype_name
{
local(%fsmap);
%fsmap = ("vxfs", "Veritas Filesystem",
	  "ufs","Unix Filesystem",
	  "nfs","Network Filesystem",
	  "hsfs","ISO9660 CD-ROM",
	  "pcfs","MS-DOS Filesystem",
	  "lofs","Loopback Filesystem",
	  "cachefs","Caching Filesystem",
	  "swap","Virtual Memory",
	  "tmpfs","Ram Disk",
	  "autofs","Automounter Filesystem",
	  "proc","Process Image Filesystem",
	  "fd","File Descriptor Filesystem",
	  "rumba","Windows Networking Filesystem");
return $config{long_fstypes} && $fsmap{$_[0]} ? $fsmap{$_[0]} : uc($_[0]);
}


# mount_modes(type)
# Given a filesystem type, returns 4 numbers that determine how the file
# system can be mounted, and whether it can be fsck'd
#  0 - cannot be permanently recorded
#  1 - can be permanently recorded, and is always mounted at boot
#  2 - can be permanently recorded, and may or may not be mounted at boot
# The second is:
#  0 - mount is always permanent => mounted when saved
#  1 - doesn't have to be permanent
# The third is:
#  0 - cannot be fsck'd at boot time
#  1 - can be be fsck'd at boot time
# The fourth is:
#  0 - can be unmounted
#  1 - cannot be unmounted
sub mount_modes
{
if ($_[0] eq "vxfs" || $_[0] eq "ufs" || $_[0] eq "cachefs" || $_[0] eq "s5fs")
   { return (2, 1, 1, 0); }
elsif ($_[0] eq "rumba") { return (0, 1, 0, 0); }
else { return (2, 1, 0, 0); }
}


# multiple_mount(type)
# Returns 1 if filesystems of this type can be mounted multiple times, 0 if not
sub multiple_mount
{
return ($_[0] eq "vxfs" || $_[0] eq "nfs" || $_[0] eq "tmpfs" || $_[0] eq "cachefs" || $_[0] eq "autofs" || $_[0] eq "lofs" || $_[0] eq "rumba");
}


# generate_location(type, location)
# Output HTML for editing the mount location of some filesystem.
sub generate_location
{
if ($_[0] eq "nfs") {
	# NFS mount from some host and directory
	if ($_[1] =~ /^nfs:/) { $nfsmode = 2; }
	elsif (!$_[1] || $_[1] =~ /^([A-z0-9\-\.]+):([^,]+)$/) {
		$nfsmode = 0; $nfshost = $1; $nfspath = $2;
		}
	else { $nfsmode = 1; }
	if ($gconfig{'os_version'} >= 2.6) {
		# UnixWare 7 can list multiple NFS servers in mount
		print "<tr> <td><b>NFS Source</b></td>\n";
		printf "<td><input type=radio name=nfs_serv value=0 %s>\n",
			$nfsmode == 0 ? "checked" : "";
		print "<b>NFS Hostname</b></td>\n";
		print "<td><input name=nfs_host size=20 value=\"$nfshost\">\n";
		&nfs_server_chooser_button("nfs_host");
		print "&nbsp;<b>NFS Directory</b>\n";
		print "<input name=nfs_dir size=20 value=\"$nfspath\">\n";
		&nfs_export_chooser_button("nfs_host", "nfs_dir");
		print "</td> </tr>\n";

		print "<tr> <td></td>\n";
		printf "<td><input type=radio name=nfs_serv value=1 %s>\n",
			$nfsmode == 1 ? "checked" : "";
		print "<b>Multiple NFS Servers</b></td>\n";
		printf "<td><input name=nfs_list size=40 value=\"%s\">\n",
			$nfsmode == 1 ? $_[1] : "";
		print "</td> </tr>\n";

		if ($gconfig{'os_version'} >= 7) {
			print "<tr> <td></td> <td>\n";
			printf "<input type=radio name=nfs_serv value=2 %s>\n",
				$nfsmode == 2 ? "checked" : "";
			print "<b>WebNFS URL</b></td> <td>\n";
			printf "<input name=nfs_url size=40 value=\"%s\">\n",
				$nfsmode == 2 ? $_[1] : "";
			print "</td> </tr>\n";
			}
		}
	else {
		print "<tr> <td><b>NFS Hostname</b></td>\n";
		print "<td><input name=nfs_host size=20 value=\"$nfshost\">\n";
		&nfs_server_chooser_button("nfs_host");
		print "</td>\n";
		print "<td><b>NFS Directory</b></td>\n";
		print "<td><input name=nfs_dir size=20 value=\"$nfspath\">\n";
		&nfs_export_chooser_button("nfs_host", "nfs_dir");
		print "</td> </tr>\n";
		}
	}
elsif ($_[0] eq "tmpfs") {
	# Location is irrelevant for tmpfs filesystems
	}
elsif ($_[0] eq "ufs") {
	# Mounted from a normal disk, raid (MD) device or from
	# somewhere else
	print "<tr> <td valign=top><b>UFS Disk</b></td>\n";
	print "<td colspan=3>\n";
	if ($_[1] =~ /^\/dev\/dsk\/c([0-9]+)t([0-9]+)d([0-9]+)s([0-9]+)$/) {
		$ufs_dev = 0;
		$scsi_c = $1; $scsi_t = $2; $scsi_d = $3; $scsi_s = $4;
		}
	elsif ($_[1] eq "") {
		$ufs_dev = 0; $scsi_c = $scsi_t = $scsi_s = $scsi_d = 0;
		}
	elsif ($_[1] =~ /^\/dev\/md\/dsk\/d([0-9]+)$/) {
		$ufs_dev = 1; $scsi_md = $1;
		}
	else {
		$ufs_dev = 2; $scsi_path = $_[1];
		}
	printf "<input type=radio name=ufs_dev value=0 %s> SCSI Disk:\n",
		$ufs_dev == 0 ? "checked" : "";
	print "Controller <input name=ufs_c size=3 value=\"$scsi_c\">\n";
	print "Target <input name=ufs_t size=3 value=\"$scsi_t\">\n";
	print "Unit <input name=ufs_d size=3 value=\"$scsi_d\">\n";
	print "Partition <input name=ufs_s size=3 value=\"$scsi_s\"><br>\n";

	printf "<input type=radio name=ufs_dev value=1 %s> RAID Device:\n",
		$ufs_dev == 1 ? "checked" : "";
	print "Unit <input name=ufs_md size=3 value=\"$scsi_md\"><br>\n";

	printf "<input type=radio name=ufs_dev value=2 %s> Other Device:\n",
		$ufs_dev == 2 ? "checked" : "";
	print "<input name=ufs_path size=20 value=\"$scsi_path\"><br>\n";
	print "</td> </tr>\n";
	}
elsif ($_[0] eq "vxfs") {
	# Mounted from a normal disk, LVM device or from
	# somewhere else
	print "<tr> <td valign=top><b>VXFS Device</b></td>\n";
	print "<td colspan=3>\n";
	if ($_[1] =~ /^\/dev\/dsk\/c([0-9]+)t([0-9]+)d([0-9]+)s([0-9]+)$/) {
		$jfs_dev = 0;
		$scsi_c = $1; $scsi_t = $2; $scsi_d = $3; $scsi_s = $4;
		}
	elsif ($_[1] eq "") {
		$jfs_dev = 0; $scsi_c = $scsi_t = $scsi_s = $scsi_d = 0;
		}
	elsif ($_[1] =~ /^\/dev\/vg([0-9]+)\/(\S+)/) {
		$jfs_dev = 1; $scsi_vg = $1; $scsi_lv = $2;
		}
	else {
		$jfs_dev = 2; $scsi_path = $_[1];
		}
	$scsi_path = $_[1];

	printf "<input type=radio name=jfs_dev value=0 %s> SCSI Disk:\n",
		$jfs_dev == 0 ? "checked" : "";
	print "Controller <input name=jfs_c size=3 value=\"$scsi_c\">\n";
	print "Target <input name=jfs_t size=3 value=\"$scsi_t\">\n";
	print "Unit <input name=jfs_d size=3 value=\"$scsi_d\">\n";
	print "Partition <input name=jfs_s size=3 value=\"$scsi_s\"><br>\n";

	printf "<input type=radio name=jfs_dev value=1 %s> LVM Device:\n",
		$jfs_dev == 1 ? "checked" : "";
	print "Volume Group <input name=jfs_vg size=2 value=\"$scsi_vg\">\n";
	print "Logical Volume <input name=jfs_lv size=20 value=\"$scsi_lv\"><br>\n";

	printf "<input type=radio name=jfs_dev value=2 %s> Other Device:\n",
		$jfs_dev == 2 ? "checked" : "";
	print "<input name=jfs_path size=20 value=\"$scsi_path\">";
        print &file_chooser_button("jfs_path", 0);
        print "<br>\n";
	print "</td> </tr>\n";
	}
elsif ($_[0] eq "swap") {
	# Swapping to a disk partition or a file
	print "<tr> <td valign=top><b>Swap File</b></td>\n";
	print "<td colspan=3>\n";
	if ($_[1] =~ /^\/dev\/dsk\/c([0-9]+)t([0-9]+)d([0-9]+)s([0-9]+)$/) {
		$swap_dev = 0;
		$scsi_c = $1; $scsi_t = $2; $scsi_d = $3; $scsi_s = $4;
		}
	elsif ($_[1] eq "") {
		$swap_dev = 1; $scsi_path = "";
		}
	else {
		$swap_dev = 1; $scsi_path = $_[1];
		}
	printf "<input type=radio name=swap_dev value=0 %s> SCSI Disk:\n",
		$swap_dev == 0 ? "checked" : "";
	print "Controller <input name=swap_c size=3 value=\"$scsi_c\">\n";
	print "Target <input name=swap_t size=3 value=\"$scsi_t\">\n";
	print "Unit <input name=swap_d size=3 value=\"$scsi_d\">\n";
	print "Partition <input name=swap_s size=3 value=\"$scsi_s\"><br>\n";

	printf "<input type=radio name=swap_dev value=1 %s> File:\n",
		$swap_dev == 1 ? "checked" : "";
	print "<input name=swap_path size=20 value=\"$scsi_path\"><br>\n";
	print "</td> </tr>\n";
	}
elsif ($_[0] eq "hsfs") {
	# Mounting a SCSI cdrom
	print "<tr> <td valign=top><b>CDROM Disk</b></td>\n";
	print "<td colspan=3>\n";
	if ($_[1] =~ /^\/dev\/dsk\/c([0-9]+)t([0-9]+)d([0-9]+)s([0-9]+)$/) {
		$hsfs_dev = 0;
		$scsi_c = $1; $scsi_t = $2; $scsi_d = $3; $scsi_s = $4;
		}
	elsif ($_[1] eq "") {
		$hsfs_dev = 0;
		$scsi_c = 0; $scsi_t = 6; $scsi_d = 0; $scsi_s = 0;
		}
	else {
		$hsfs_dev = 1; $scsi_path = $_[1];
		}
	printf "<input type=radio name=hsfs_dev value=0 %s> SCSI Device:\n",
		$hsfs_dev == 0 ? "checked" : "";
	print "Controller <input name=hsfs_c size=3 value=\"$scsi_c\">\n";
	print "Target <input name=hsfs_t size=3 value=\"$scsi_t\">\n";
	print "Unit <input name=hsfs_d size=3 value=\"$scsi_d\">\n";
	print "Partition <input name=hsfs_s size=3 value=\"$scsi_s\"><br>\n";

	printf "<input type=radio name=hsfs_dev value=1 %s> Other Device:\n",
		$hsfs_dev == 1 ? "checked" : "";
	print "<input name=hsfs_path size=20 value=\"$scsi_path\"><br>\n";
	print "</td> </tr>\n";
	}
elsif ($_[0] eq "pcfs") {
	# Mounting a SCSI msdos filesystem
	print "<tr> <td valign=top><b>MS-DOS Disk</b></td>\n";
	print "<td colspan=3>\n";
	if ($_[1] =~ /^\/dev\/dsk\/c([0-9]+)t([0-9]+)d([0-9]+)s([0-9]+)$/) {
		$pcfs_dev = 0;
		$scsi_c = $1; $scsi_t = $2; $scsi_d = $3; $scsi_s = $4;
		}
	elsif ($_[1] eq "") {
		$pcfs_dev = 1; $scsi_path = "";
		}
	else {
		$pcfs_dev = 1; $scsi_path = $_[1];
		}
	printf "<input type=radio name=pcfs_dev value=0 %s> SCSI Device:\n",
		$pcfs_dev == 0 ? "checked" : "";
	print "Controller <input name=pcfs_c size=3 value=\"$scsi_c\">\n";
	print "Target <input name=pcfs_t size=3 value=\"$scsi_t\">\n";
	print "Unit <input name=pcfs_d size=3 value=\"$scsi_d\">\n";
	print "Partition <input name=pcfs_s size=3 value=\"$scsi_s\"><br>\n";

	printf "<input type=radio name=pcfs_dev value=1 %s> Other Device:\n",
		$pcfs_dev == 1 ? "checked" : "";
	print "<input name=pcfs_path size=20 value=\"$scsi_path\"><br>\n";
	print "</td> </tr>\n";
	}
elsif ($_[0] eq "lofs") {
	# Mounting some directory to another location
	print "<tr> <td><b>Original Directory</b></td>\n";
	print "<td><input name=lofs_src size=30 value=\"$_[1]\">\n";
	print &file_chooser_button("lofs_src", 1);
	print "</td> </tr>\n";
	}
elsif ($_[0] eq "cachefs") {
	# Mounting a cached filesystem of some type.. need a location for
	# the source of the mount
	print "<tr> <td><b>Cache Source</b></td>\n";
	print "<td><input name=cfs_src size=20 value=\"$_[1]\"></td> </tr>\n";
	}
elsif ($_[0] eq "autofs") {
	# An automounter entry.. can be -hosts, -xfn or from some mapping
	print "<tr> <td valign=top><b>Automounter map</b></td>\n";
	printf "<td><input type=radio name=autofs_type value=0 %s>\n",
		$_[1] eq "-hosts" || $_[1] eq "-xfn" ? "" : "checked";
	printf "Use map <input name=autofs_map size=20 value=\"%s\"><br>\n",
		$_[1] eq "-hosts" || $_[1] eq "-xfn" ? "" : $_[1];
	printf "<input type=radio name=autofs_type value=1 %s>\n",
		$_[1] eq "-hosts" ? "checked" : "";
	print "All NFS exports map<br>\n";
	printf "<input type=radio name=autofs_type value=2 %s>\n",
		$_[1] eq "-xfn" ? "checked" : "";
	print "Federated  Naming  Service map</td> </tr>\n";
	}
elsif ($_[0] eq "rumba") {
	# Windows filesystem
	$_[1] =~ /^\\\\(.*)\\(.*)$/;
	print "<tr> <td><b>Server Name</b></td>\n";
	print "<td><input name=rumba_server value=\"$1\" size=20>\n";
	&smb_server_chooser_button("rumba_server");
	print "</td>\n";
	print "<td><b>Share Name</b></td>\n";
	print "<td><input name=rumba_share value=\"$2\" size=20>\n";
	&smb_share_chooser_button("rumba_server", "rumba_share");
	print "</td> </tr>\n";
	}
}


# generate_options(type, newmount)
# Output HTML for editing mount options for a partilcar filesystem 
# under this OS
sub generate_options
{
if ($_[0] eq "nfs") {
	# UnixWare NFS has many options, not all of which are editable here
	print "<tr> <td><b>Read-Only?</b></td>\n";
	printf "<td nowrap><input type=radio name=nfs_ro value=1 %s> Yes\n",
		defined($options{"ro"}) ? "checked" : "";
	printf "<input type=radio name=nfs_ro value=0 %s> No</td>\n",
		defined($options{"ro"}) ? "" : "checked";

	print "<td><b>Disallow setuid programs?</b></td>\n";
	printf "<td nowrap><input type=radio name=nfs_nosuid value=1 %s> Yes\n",
		defined($options{"nosuid"}) ? "checked" : "";
	printf "<input type=radio name=nfs_nosuid value=0 %s> No</td> </tr>\n",
		defined($options{"nosuid"}) ? "" : "checked";

	print "<tr> <td><b>Files inherit parent GID?</b></td>\n";
	printf "<td nowrap><input type=radio name=nfs_grpid value=0 %s> Yes\n",
		defined($options{"grpid"}) ? "" : "checked";
	printf "<input type=radio name=nfs_grpid value=1 %s> No</td>\n",
		defined($options{"grpid"}) ? "checked" : "";

	print "<td><b>Return error on timeouts?</b></td>\n";
	printf "<td nowrap><input type=radio name=nfs_soft value=1 %s> Yes\n",
		defined($options{"soft"}) ? "checked" : "";
	printf "<input type=radio name=nfs_soft value=0 %s> No</td> </tr>\n",
		defined($options{"soft"}) ? "" : "checked";

	print "<tr> <td><b>Retry mounts in background?</b></td>\n";
	printf "<td nowrap><input type=radio name=nfs_bg value=1 %s> Yes\n",
		defined($options{"bg"}) ? "checked" : "";
	printf "<input type=radio name=nfs_bg value=0 %s> No</td>\n",
		defined($options{"bg"}) ? "" : "checked";

	print "<td><b>Display quotas?</b></td>\n";
	printf "<td nowrap><input type=radio name=nfs_quota value=1 %s> Yes\n",
		defined($options{"quota"}) ? "checked" : "";
	printf "<input type=radio name=nfs_quota value=0 %s> No</td> </tr>\n",
		defined($options{"quota"}) ? "" : "checked";

	print "<tr> <td><b>Allow user interrupt?</b></td>\n";
	printf "<td nowrap><input type=radio name=nfs_nointr value=0 %s> Yes\n",
		defined($options{"nointr"}) ? "" : "checked";
	printf "<input type=radio name=nfs_nointr value=1 %s> No</td>\n",
		defined($options{"nointr"}) ? "checked" : "";

	print "<td><b>NFS version</b></td>\n";
	printf "<td nowrap><input type=radio name=nfs_vers_def value=1 %s> Highest\n",
		defined($options{"vers"}) ? "" : "checked";
	printf "<input type=radio name=nfs_vers_def value=0 %s>\n",
		defined($options{"vers"}) ? "checked" : "";
	print "<input size=1 name=nfs_vers value=$options{vers}></td> </tr>\n";

	print "<tr> <td><b>Protocol</b></td>\n";
	print "<td nowrap><select name=proto>\n";
	printf "<option value=\"\" %s> Default\n",
		defined($options{"proto"}) ? "" : "selected";
	&open_tempfile(NETCONFIG, "/etc/netconfig");
	while(<NETCONFIG>) {
		if (!/^([A-z0-9\_\-]+)\s/) { next; }
		printf "<option value=\"$1\" %s> $1\n",
			$options{"proto"} eq $1 ? "selected" : "";
		}
	&close_tempfile(NETCONFIG);
	print "</select></td>\n";

	print "<td><b>NFS Port</b></td>\n";
	printf "<td nowrap><input type=radio name=nfs_port_def value=1 %s> Default\n",
		defined($options{"port"}) ? "" : "checked";
	printf "<input type=radio name=nfs_port_def value=0 %s>\n",
		defined($options{"port"}) ? "checked" : "";
	print "<input size=5 name=nfs_port value=$options{port}></td> </tr>\n";

	print "<tr> <td><b>Timeout</b></td>\n";
	printf "<td nowrap><input type=radio name=nfs_timeo_def value=1 %s> Default\n",
		defined($options{"timeo"}) ? "" : "checked";
	printf "<input type=radio name=nfs_timeo_def value=0 %s>\n",
		defined($options{"timeo"}) ? "checked" : "";
	printf "<input size=5 name=nfs_timeo value=$options{timeo}></td>\n";

	print "<td><b>Number of Retransmissions</b></td>\n";
	printf "<td nowrap><input type=radio name=nfs_retrans_def value=1 %s> Default\n",
		defined($options{"retrans"}) ? "" : "checked";
	printf "<input type=radio name=nfs_retrans_def value=0 %s>\n",
		defined($options{"retrans"}) ? "checked" : "";
	print "<input size=5 name=nfs_retrans value=$options{retrans}></td> </tr>\n";

	print "<tr> <td><b>Authentication</b></td>\n";
	$nfs_auth = $options{'sec'} ? $options{'sec'} :
		    defined($options{"secure"}) ? "dh" :
		    defined($options{"kerberos"}) ? "krb" : "";
	print "<td><select name=nfs_auth>\n";
	printf "<option value=\"\" %s> None\n",
		$nfs_auth eq "" ? "selected" : "";
	printf "<option value=dh %s> DES\n",
		$nfs_auth eq "dh" ? "selected" : "";
	printf "<option value=krb %s> Kerberos\n",
		$nfs_auth eq "krb" ? "selected" : "";
	print "</select></td>\n";

	if ($gconfig{'os_version'} >= 7) {
		print "<td><b>WebNFS mount?</b></td> <td>\n";
		printf "<input type=radio name=nfs_public value=1 %s> Yes\n",
			defined($options{'public'}) ? "checked" : "";
		printf "<input type=radio name=nfs_public value=0 %s> No\n",
			defined($options{'public'}) ? "" : "checked";
		print "</td>\n";
		}
	print "</tr>\n";
	}
if ($_[0] eq "ufs") {
	# UnixWare UFS also has many options, not all of which are here
	print "<tr> <td><b>Read-Only?</b></td>\n";
	printf "<td nowrap><input type=radio name=ufs_ro value=1 %s> Yes\n",
		defined($options{"ro"}) ? "checked" : "";
	printf "<input type=radio name=ufs_ro value=0 %s> No</td>\n",
		defined($options{"ro"}) ? "" : "checked";

	print "<td><b>Disallow setuid programs?</b></td>\n";
	printf "<td nowrap><input type=radio name=ufs_nosuid value=1 %s> Yes\n",
		defined($options{"nosuid"}) ? "checked" : "";
	printf "<input type=radio name=ufs_nosuid value=0 %s> No</td> </tr>\n",
		defined($options{"nosuid"}) ? "" : "checked";

	print "<tr> <td><b>Allow user interrupt?</b></td>\n";
	printf "<td nowrap><input type=radio name=ufs_nointr value=0 %s> Yes\n",
		defined($options{"nointr"}) ? "" : "checked";
	printf "<input type=radio name=ufs_nointr value=1 %s> No</td>\n",
		defined($options{"nointr"}) ? "checked" : "";

	print "<td><b>Enable quotas at boot time?</b></td>\n";
	printf "<td nowrap><input type=radio name=ufs_quota value=1 %s> Yes\n",
		defined($options{"quota"}) || defined($options{"rq"}) ?
			"checked" : "";
	printf "<input type=radio name=ufs_quota value=0 %s> No</td> </tr>\n",
		defined($options{"quota"}) || defined($options{"rq"}) ?
			"" : "checked";

	print "<tr> <td><b>Action on error</b></td>\n";
	print "<td><select name=ufs_onerror>\n";
	foreach ('panic', 'lock', 'umount', 'repair') {
		printf "<option value=\"$_\" %s> $_\n",
		 $options{onerror} eq $_ ||
		 !defined($options{onerror}) && $_ eq "panic" ? "selected" : "";
		}
	print "</select></td>\n";

	print "<td><b>Repair Delay</b></td>\n";
	$options{toosoon} =~ /([0-9]+)([A-z])/;
	print "<td nowrap><input size=5 name=ufs_toosoon_time value=$1>\n";
	print "<select name=ufs_toosoon_units>\n";
	printf "<option value=s %s> Seconds\n", $2 eq "s" ? "selected" : "";
	printf "<option value=m %s> Minutes\n", $2 eq "m" ? "selected" : "";
	printf "<option value=h %s> Hours\n", $2 eq "h" ? "selected" : "";
	printf "<option value=d %s> Days\n", $2 eq "d" ? "selected" : "";
	printf "<option value=w %s> Months\n", $2 eq "w" ? "selected" : "";
	printf "<option value=y %s> Years\n", $2 eq "y" ? "selected" : "";
	print "</select></td> </tr>\n";

	if ($gconfig{'os_version'} >= 7) {
		print "<tr> <td><b>Update access times?</b></td> <td>\n";
		printf "<input type=radio name=ufs_noatime value=0 %s> Yes\n",
			defined($options{'noatime'}) ? "" : "checked";
		printf "<input type=radio name=ufs_noatime value=1 %s> No\n",
			defined($options{'noatime'}) ? "checked" : "";
		print "</td>\n";

		print "<td><b>Force direct IO?</b></td> <td>\n";
		printf "<input type=radio name=ufs_force value=1 %s> Yes\n",
			defined($options{'forcedirectio'}) ? "checked" : "";
		printf "<input type=radio name=ufs_force value=0 %s> No\n",
			defined($options{'forcedirectio'}) ? "" : "checked";
		print "</td> </tr>\n";

		print "<tr> <td><b>Allow large files?</td> <td>\n";
		printf "<input type=radio name=ufs_nolarge value=0 %s> Yes\n",
			defined($options{'nolargefiles'}) ? "" : "checked";
		printf "<input type=radio name=ufs_nolarge value=1 %s> No\n",
			defined($options{'nolargefiles'}) ? "checked" : "";
		print "</td>\n";

		print "<td><b>Enabled logging?</td> <td>\n";
		printf "<input type=radio name=ufs_logging value=1 %s> Yes\n",
			defined($options{'logging'}) ? "checked" : "";
		printf "<input type=radio name=ufs_logging value=0 %s> No\n",
			defined($options{'logging'}) ? "" : "checked";
		print "</td> </tr>\n";
		}
	}
if ($_[0] eq "hsfs") {
	# UnixWare hsfs is used for CDROMs
	print "<tr> <td><b>Ignore Unix attributes?</b></td>\n";
	printf "<td nowrap><input type=radio name=hsfs_nrr value=1 %s> Yes\n",
		defined($options{"nrr"}) ? "checked" : "";
	printf "<input type=radio name=hsfs_nrr value=0 %s> No</td>\n",
		defined($options{"nrr"}) ? "" : "checked";

	print "<td><b>Ignore trailing dot?</b></td>\n";
	printf "<td nowrap><input type=radio name=hsfs_notraildot value=1 %s> Yes\n",
		defined($options{"notraildot"}) ? "checked" : "";
	printf "<input type=radio name=hsfs_notraildot value=0 %s> No</td> </tr>\n",
		defined($options{"notraildot"}) ? "" : "checked";

	print "<tr> <td><b>Use lower case?</b></td>\n";
	printf "<td nowrap><input type=radio name=hsfs_nomaplcase value=0 %s> Yes\n",
		defined($options{"nomaplcase"}) ? "" : "checked";
	printf "<input type=radio name=hsfs_nomaplcase value=1 %s> No</td>\n",
		defined($options{"nomaplcase"}) ? "checked" : "";

	print "<td><b>Disallow setuid programs?</b></td>\n";
	printf"<td nowrap><input type=radio name=hsfs_nosuid value=1 %s> Yes\n",
		defined($options{"nosuid"}) ? "checked" : "";
	printf "<input type=radio name=hsfs_nosuid value=0 %s> No</td> </tr>\n",
		defined($options{"nosuid"}) ? "" : "checked";
	}
if ($_[0] eq "pcfs") {
	# UnixWare pcfs for for FAT filesystems. It doesn't have many options
	print "<tr> <td width=25%><b>Read Only?</b></td> <td width=25%>\n";
	printf "<input type=radio name=pcfs_ro value=1 %s> Yes\n",
		defined($options{"ro"}) ? "checked" : "";
	printf "<input type=radio name=pcfs_ro value=0 %s> No</td>\n",
		defined($options{"ro"}) ? "" : "checked";

	if ($gconfig{'os_version'} >= 7) {
		print "<td><b>Force lower case?</b></td> <td>\n";
		printf "<input type=radio name=pcfs_foldcase value=1 %s> Yes\n",
			defined($options{'foldcase'}) ? "checked" : "";
		printf "<input type=radio name=pcfs_foldcase value=0 %s> No\n",
			defined($options{'foldcase'}) ? "" : "checked";
		print "</td>\n";
		}
	else {
		print "<td colspan=2></td> </tr>\n";
		}
	}
if ($_[0] eq "vxfs") {
	print "<tr> <td><b>Read-Only?</b></td>\n";
	printf "<td nowrap><input type=radio name=jfs_ro value=1 %s> Yes\n",
		defined($options{"ro"}) ? "checked" : "";
	printf "<input type=radio name=jfs_ro value=0 %s> No</td>\n",
		defined($options{"ro"}) ? "" : "checked";

	print "<td><b>Disallow setuid programs?</b></td>\n";
	printf "<td nowrap><input type=radio name=jfs_nosuid value=1 %s> Yes\n",
		defined($options{"nosuid"}) ? "checked" : "";
	printf "<input type=radio name=jfs_nosuid value=0 %s> No</td> </tr>\n",
		defined($options{"nosuid"}) ? "" : "checked";

	print "<tr> <td><b>Full integrity for all Metadata?</b></td>\n";
	printf "<td nowrap><input type=radio name=jfs_log value=1 %s> Yes\n",
		defined($options{"log"}) ? "checked" : "";
	printf "<input type=radio name=jfs_log value=0 %s> No</td>\n",
		defined($options{"log"}) ? "" : "checked";

	print "<td><b>Synchronous-write data logging?</b></td>\n";
	printf "<td nowrap><input type=radio name=jfs_syncw value=1 %s> Yes\n",
		!defined($options{"nodatainlog"}) ? "checked" : "";
	printf "<input type=radio name=jfs_syncw value=0 %s> No</td> </tr>\n",
		!defined($options{"nodatainlog"}) ? "" : "checked";

        print "<tr> <td><b>Enable quotas at boot time?</b></td>\n";
        printf "<td nowrap><input type=radio name=jfs_quota value=1 %s> Yes\n",
		defined($options{"quota"}) ? "checked" : "";
        printf "<input type=radio name=jfs_quota value=0 %s> No</td> </tr>\n",
		defined($options{"quota"}) ? "" : "checked";
	}
if ($_[0] eq "lofs") {
	# No options as far as I know
	print "<tr> <td><i>No Options Available</i></td> </tr>\n";
	}
if ($_[0] eq "tmpfs") {
	# UnixWare tmpfs (virtual memory) filesystem.
	print "<tr> <td><b>Size</b>&nbsp;&nbsp;&nbsp;</td>\n";
	printf"<td><input type=radio name=tmpfs_size_def value=1 %s> Maximum\n",
		defined($options{"size"}) ? "" : "checked";
	printf"&nbsp;&nbsp;<input type=radio name=tmpfs_size_def value=0 %s>\n",
		defined($options{"size"}) ? "checked" : "";
	($tmpsz = $options{size}) =~ s/[A-z]+$//g;
	print "<input name=tmpfs_size size=6 value=\"$tmpsz\">\n";
	print "<select name=tmpfs_unit>\n";
	printf "<option value=m %s> MB\n",
		$options{"size"} =~ /m$/ ? "selected" : "";
	printf "<option value=k %s> kB\n",
		$options{"size"} =~ /k$/ ? "selected" : "";
	printf "<option value=b %s> bytes\n",
		$options{"size"} !~ /(k|m)$/ ? "selected" : "";
	print "</select></td>\n";

	print "<td><b>Disallow setuid programs?</b></td> <td nowrap>\n";
	printf "<input type=radio name=tmpfs_nosuid value=1 %s> Yes\n",
		defined($options{"nosuid"}) ? "checked" : "";
	printf "<input type=radio name=tmpfs_nosuid value=0 %s> No</td>\n",
		defined($options{"nosuid"}) ? "" : "checked";
	print "</tr>\n";
	}
if ($_[0] eq "swap") {
	# UnixWare swap has no options
	print "<tr> <td><i>No Options Available</i></td> </tr>\n";
	}
if ($_[0] eq "cachefs") {
	# The caching filesystem has lots of options.. cachefs mounts can
	# be of an existing 'manually' mounted back filesystem, or of a
	# back-filesystem that has been automatically mounted by the cache.
	# The user should never see the automatic mountings made by cachefs.
	print "<tr> <td><b>Real filesystem type</b></td>\n";
	print "<td nowrap><select name=cfs_backfstype>\n";
	if (!defined($options{backfstype})) { $options{backfstype} = "nfs"; }
	foreach (&list_fstypes()) {
		if ($_ eq "cachefs") { next; }
		printf "<option value=\"$_\" %s>$_\n",
			$_ eq $options{backfstype} ? "selected" : "";
		}
	print "</select></td>\n";

	print "<td><b>Real mount point</b></td>\n";
	printf"<td nowrap><input type=radio name=cfs_noback value=1 %s> Automatic\n",
		defined($options{"backpath"}) ? "" : "checked";
	printf "<input type=radio name=cfs_noback value=0 %s>\n",
		defined($options{"backpath"}) ? "checked" : "";
	print "<input size=10 name=cfs_backpath value=\"$options{backpath}\"></td> </tr>\n";

	print "<tr> <td><b>Cache directory</b></td>\n";
	printf "<td nowrap><input size=10 name=cfs_cachedir value=\"%s\"></td>\n",
		defined($options{"cachedir"}) ? $options{"cachedir"} : "/cache";

	print "<td><b>Write mode</b></td>\n";
	printf"<td nowrap><input type=radio name=cfs_wmode value=0 %s> Write-around\n",
		defined($options{"non-shared"}) ? "" : "checked";
	printf "<input type=radio name=cfs_wmode value=1 %s> Non-shared\n",
		defined($options{"non-shared"}) ? "checked" : "";
	print "</td> </tr>\n";

	print "<tr> <td><b>Consistency check</b></td>\n";
	print "<td><select name=cfs_con>\n";
	print "<option value=1> Periodically\n";
	printf "<option value=0 %s> Never\n",
		defined($options{"noconst"}) ? "selected" : "";
	printf "<option value=2 %s> On demand\n",
		defined($options{"demandconst"}) ? "selected" : "";
	print "</select></td>\n";

	print "<td><b>Check permissions in cache?</b></td>\n";
	printf "<td nowrap><input type=radio name=cfs_local value=1 %s> Yes\n",
		defined($options{"local-access"}) ? "checked" : "";
	printf "<input type=radio name=cfs_local value=0 %s> No</td> </tr>\n",
		defined($options{"local-access"}) ? "" : "checked";

	print "<tr> <td><b>Read-Only?</b></td>\n";
	printf "<td nowrap><input type=radio name=cfs_ro value=1 %s> Yes\n",
		defined($options{"ro"}) ? "checked" : "";
	printf "<input type=radio name=cfs_ro value=0 %s> No</td>\n",
		defined($options{"ro"}) ? "" : "checked";

	print "<td><b>Disallow setuid programs?</b></td>\n";
	printf "<td nowrap><input type=radio name=cfs_nosuid value=1 %s> Yes\n",
		defined($options{"nosuid"}) ? "checked" : "";
	printf "<input type=radio name=cfs_nosuid value=0 %s> No</td> </tr>\n",
		defined($options{"nosuid"}) ? "" : "checked";
	}
if ($_[0] eq "autofs") {
	# Autofs has lots of options, depending on the type of file
	# system being automounted.. the fstype options determines this
	local($fstype);
	$fstype = $options{fstype} eq "" ? "nfs" : $options{fstype};
	if ($gconfig{'os_version'} >= 2.6) {
		print "<tr> <td><b>Browsing enabled?</b></td> <td>\n";
		printf "<input type=radio name=auto_nobrowse value=0 %s> Yes\n",
			defined($options{'nobrowse'}) ? "" : "checked";
		printf "<input type=radio name=auto_nobrowse value=1 %s> No\n",
			defined($options{'nobrowse'}) ? "checked" : "";
		print "</td> <td colspan=2></td> </tr>\n";
		}
	&generate_options($fstype);
	print "<input type=hidden name=autofs_fstype value=\"$fstype\">\n";
	}
if ($_[0] eq "rumba") {
	# SMB filesystems have a few options..
	print "<tr> <td><b>Server Hostname</b></td>\n";
	printf "<td><input type=radio name=rumba_mname_def value=1 %s> Automatic\n",
		defined($options{"machinename"}) ? "" : "checked";
	printf "<input type=radio name=rumba_mname_def value=0 %s>\n",
		defined($options{"machinename"}) ? "checked" : "";
	print "<input size=10 name=rumba_mname value=\"$options{machinename}\"></td>\n";

	print "<td><b>Client Name</b></td>\n";
	printf "<td><input type=radio name=rumba_cname_def value=1 %s> Automatic\n",
		defined($options{"clientname"}) ? "" : "checked";
	printf "<input type=radio name=rumba_cname_def value=0 %s>\n",
		defined($options{"clientname"}) ? "checked" : "";
	print "<input size=10 name=rumba_cname value=\"$options{clientname}\"></td> </tr>\n";

	print "<tr> <td><b>Login Name</b></td>\n";
	print "<td><input name=rumba_username size=15 value=\"$options{username}\"></td>\n";

	print "<td><b>Login Password</b></td>\n";
	print "<td><input type=password name=rumba_password size=15 value=\"$options{password}\"></td> </tr>\n";

	print "<tr> <td><b>User files are owned by</b></td>\n";
	printf "<td><input name=rumba_uid size=8 value=\"%s\">\n",
		defined($options{'uid'}) ? getpwuid($options{'uid'}) : "";
	print &user_chooser_button("rumba_uid", 0),"</td>\n";

	print "<td><b>Group files are owned by</b></td>\n";
	printf "<td><input name=rumba_gid size=8 value=\"%s\">\n",
		defined($options{'gid'}) ? getgrgid($options{'gid'}) : "";
	print &group_chooser_button("rumba_gid", 0),"</td>\n";

	print "<tr> <td><b>File permissions</b></td>\n";
	printf "<td><input name=rumba_fmode size=5 value=\"%s\"></td>\n",
		defined($options{fmode}) ? $options{fmode} : "755";

	print "<td><b>Directory permissions</b></td>\n";
	printf "<td><input name=rumba_dmode size=5 value=\"%s\"></td> </tr>\n",
		defined($options{dmode}) ? $options{dmode} : "755";

	print "<tr> <td><b>Read/write access is safe?</b></td>\n";
	printf"<td nowrap><input type=radio name=rumba_readwrite value=1 %s> Yes\n",
		defined($options{"readwrite"}) ? "checked" : "";
	printf "<input type=radio name=rumba_readwrite value=0 %s> No</td>\n",
		defined($options{"readwrite"}) ? "" : "checked";

	print "<td><b>Files can be read-only?</b></td>\n";
	printf"<td nowrap><input type=radio name=rumba_readonly value=1 %s> Yes\n",
		defined($options{"readonly"}) ? "checked" : "";
	printf "<input type=radio name=rumba_readonly value=0 %s> No</td> </tr>\n",
		defined($options{"readonly"}) ? "" : "checked";

	print "<tr> <td><b>Send password in upper case?</b></td>\n";
	printf"<td nowrap><input type=radio name=rumba_noupper value=0 %s> Yes\n",
		defined($options{"noupper"}) ? "" : "checked";
	printf "<input type=radio name=rumba_noupper value=1 %s> No</td>\n",
		defined($options{"noupper"}) ? "checked" : "";

	print "<td><b>Use attrE commands?</b></td>\n";
	printf"<td nowrap><input type=radio name=rumba_attr value=1 %s> Yes\n",
		defined($options{"attr"}) ? "checked" : "";
	printf "<input type=radio name=rumba_attr value=0 %s> No</td> </tr>\n",
		defined($options{"attr"}) ? "" : "checked";
	}
}


# check_location(type)
# Parse and check inputs from %in, calling &error() if something is wrong.
# Returns the location string for storing in the fstab file
sub check_location
{
if ($_[0] eq "nfs") {
	local($out, $temp, $mout, $dirlist);

	if ($in{'nfs_serv'} == 1) {
		# multiple servers listed.. assume the user has a brain
		return $in{'nfs_list'};
		}
	elsif ($in{'nfs_serv'} == 2) {
		# NFS url.. check syntax
		if ($in{'nfs_url'} !~ /^nfs:\/\/([^\/ ]+)(\/([^\/ ]*))?$/) {
			&error("'$in{'nfs_url'}' is not a valid NFS URL");
			}
		return $in{'nfs_url'};
		}

	# Use dfshares to see if the host exists and is up
	if ($in{nfs_host} !~ /^\S+$/) {
		&error("'$in{nfs_host}' is not a valid hostname");
		}
	$out = &backquote_command("dfshares '$in{nfs_host}' 2>&1");
	if ($out =~ /Unknown host/) {
		&error("The host '$in{nfs_host}' does not exist");
		}
	elsif ($out =~ /Timed out/) {
		&error("The host '$in{nfs_host}' is down or does not ".
		       "support NFS");
		}
	elsif ($out =~ /Program not registered/) {
		&error("The host '$in{nfs_host}' does not support NFS");
		}

	# Try a test mount to see if filesystem is available
	foreach (split(/\n/, $out)) {
		if (/^\s*([^ :]+):(\/\S+)\s+/) { $dirlist .= "$2\n"; }
		}
	if ($in{nfs_dir} !~ /^\S+$/) {
		&error("'$in{nfs_dir}' is not a valid directory name. The ".
		       "available directories on $in{nfs_host} are:".
		       "<pre>$dirlist</pre>");
		}
	$temp = &transname();
	&make_dir($temp, 0755);
	$mout = &backquote_command("mount $in{nfs_host}:$in{nfs_dir} $temp 2>&1");
	if ($mout =~ /No such file or directory/) {
		rmdir($temp);
		&error("The directory '$in{nfs_dir}' does not exist on the ".
		       "host $in{nfs_host}. The available directories are:".
		       "<pre>$dirlist</pre>");
		}
	elsif ($mout =~ /Permission denied/) {
		rmdir($temp);
		&error("This host is not allowed to mount the directory ".
		       "$in{nfs_dir} from $in{nfs_host}");
		}
	elsif ($?) {
		rmdir($temp);
		&error("NFS Error - $mout");
		}
	# It worked! unmount
	&execute_command("umount $temp");
	&unlink_file($temp);
	return "$in{nfs_host}:$in{nfs_dir}";
	}
elsif ($_[0] eq "ufs") {
	# Get the device name
	if ($in{ufs_dev} == 0) {
		$in{ufs_c} =~ /^[0-9]+$/ ||
			&error("'$in{ufs_c}' is not a valid SCSI controller");
		$in{ufs_t} =~ /^[0-9]+$/ ||
			&error("'$in{ufs_t}' is not a valid SCSI target");
		$in{ufs_d} =~ /^[0-9]+$/ ||
			&error("'$in{ufs_d}' is not a valid SCSI unit");
		$in{ufs_s} =~ /^[0-9]+$/ ||
			&error("'$in{ufs_s}' is not a valid SCSI partition");
		$dv = "/dev/dsk/c$in{ufs_c}t$in{ufs_t}d$in{ufs_d}s$in{ufs_s}";
		}
	elsif ($in{ufs_dev} == 1) {
		$in{ufs_md} =~ /^[0-9]+$/ ||
			&error("'$in{ufs_md}' is not a valid RAID unit");
		$dv = "/dev/md/dsk/d$in{ufs_md}";
		}
	else {
		$in{ufs_path} =~ /^\/\S+$/ ||
			&error("'$in{ufs_path}' is not a valid pathname");
		$dv = $in{ufs_path};
		}

	&fstyp_check($dv, "ufs");
	return $dv;
	}
elsif ($_[0] eq "vxfs") {
	# Get the device name
	if ($in{jfs_dev} == 0) {
		$in{jfs_c} =~ /^[0-9]+$/ ||
			&error("'$in{jfs_c}' is not a valid SCSI controller");
		$in{jfs_t} =~ /^[0-9]+$/ ||
			&error("'$in{jfs_t}' is not a valid SCSI target");
		$in{jfs_d} =~ /^[0-9]+$/ ||
			&error("'$in{jfs_d}' is not a valid SCSI unit");
		$in{jfs_s} =~ /^[0-9]+$/ ||
			&error("'$in{jfs_s}' is not a valid SCSI partition");
		$dv = "/dev/dsk/c$in{jfs_c}t$in{jfs_t}d$in{jfs_d}s$in{jfs_s}";
		}
	elsif ($in{jfs_dev} == 1) {
		$in{jfs_vg} =~ /^[0-9]+$/ ||
			&error("'$in{jfs_vg}' is not a valid Volume Group");
		$in{jfs_lv} =~ /^\S+$/ ||
			&error("'$in{jfs_lv}' is not a valid Logical Volume");
		$dv = "/dev/vg$in{jfs_vg}/$in{jfs_lv}";
		}
	else {
		$in{jfs_path} =~ /^\/\S+$/ ||
			&error("'$in{jfs_path}' is not a valid pathname");
		$dv = $in{jfs_path};
		}

	&fstyp_check($dv, "vxfs");
	return $dv;
	}
elsif ($_[0] eq "lofs") {
	# Get and check the original directory
	$dv = $in{'lofs_src'};
	if (!(-r $dv)) { &error("'$in{lofs_src}' does not exist"); }
	if (!(-d $dv)) { &error("'$in{lofs_src}' is not a directory"); }
	return $dv;
	}
elsif ($_[0] eq "swap") {
	if ($in{swap_dev} == 0) {
		$in{swap_c} =~ /^[0-9]+$/ ||
			&error("'$in{swap_c}' is not a valid SCSI controller");
		$in{swap_t} =~ /^[0-9]+$/ ||
			&error("'$in{swap_t}' is not a valid SCSI target");
		$in{swap_d} =~ /^[0-9]+$/ ||
			&error("'$in{swap_d}' is not a valid SCSI unit");
		$in{swap_s} =~ /^[0-9]+$/ ||
			&error("'$in{swap_s}' is not a valid SCSI partition");
		$dv="/dev/dsk/c$in{swap_c}t$in{swap_t}d$in{swap_d}s$in{swap_s}";
		}
	else { $dv = $in{swap_path}; }

	if (!open(SWAPFILE, $dv)) {
		if ($! =~ /No such file/ && $in{swap_dev}) {
			if ($dv !~ /^\/dev/) {
				&swap_form($dv);
				}
			else {
				&error("The swap file '$dv' does not exist");
				}
			}
		elsif ($! =~ /No such file/) {
			&error("The SCSI target '$in{swap_t}' does not exist");
			}
		elsif ($! =~ /No such device or address/) {
			&error("The partition '$in{swap_s}' does not exist");
			}
		else {
			&error("Failed to open '$dv' : $!");
			}
		}
	close(SWAPFILE);
	return $dv;
	}
elsif ($_[0] eq "tmpfs") {
	# Ram-disk filesystems have no location
	return "swap";
	}
elsif ($_[0] eq "cachefs") {
	# In order to check the location for the caching filesystem, we need
	# to check the back filesystem
	if (!$in{cfs_noback}) {
		# The back filesystem is manually mounted.. hopefully
		local($bidx, @mlist, @binfo);
		$bidx = &get_mounted($in{cfs_backpath}, "*");
		if ($bidx < 0) {
			&error("The back filesystem '$in{cfs_backpath}' is ".
			       "not mounted");
			}
		@mlist = &list_mounted();
		@binfo = @{$mlist[$bidx]};
		if ($binfo[2] ne $in{cfs_backfstype}) {
			&error("The back filesystem is '$binfo[2]', not ".
			       "'$in{cfs_backfstype}'");
			}
		}
	else {
		# Need to automatically mount the back filesystem.. check
		# it for sanity first.
		# But HOW?
		$in{cfs_src} =~ /^\S+$/ ||
			&error("'$in{cfs_src}' is not a valid cache source");
		}
	return $in{cfs_src};
	}
elsif ($_[0] eq "autofs") {
	# An autofs filesystem can be either mounted from the special
	# -hosts and -xfn maps, or from a normal map. The map can be a file
	# name (if it starts with /), or an NIS map (if it doesn't)
	if ($in{autofs_type} == 0) {
		# Normal map
		$in{autofs_map} =~ /\S/ ||
			&error("You did not enter an automount map name");
		if ($in{autofs_map} =~ /^\// && !(-r $in{autofs_map})) {
			&error("The map file '$in{autofs_map}' does not exist");
			}
		return $in{autofs_map};
		}
	elsif ($in{autofs_type} == 1) {
		# Special hosts map (automount all shares from some host)
		return "-hosts";
		}
	else {
		# Special FNS map (not sure what this does)
		return "-xfn";
		}
	}
elsif ($_[0] eq "rumba") {
	# Cannot check much here..
	return "\\\\$in{rumba_server}\\$in{rumba_share}";
	}
}


# fstyp_check(device, type)
# Check if some device exists, and contains a filesystem of the given type,
# using the fstyp command.
sub fstyp_check
{
local($out, $part, $found);

# Check if the device/partition actually exists
if ($_[0] =~ /^\/dev\/dsk\/c(.)t(.)d(.)s(.)$/) {
	# mounting a normal scsi device..
	$out = &backquote_command("prtvtoc -h $_[0] 2>&1");
	if ($out =~ /No such file or directory|No such device or address/) {
		&error("The SCSI target for '$_[0]' does not exist");
		}
	$part = $4;
	foreach (split(/\n/, $out)) {
		/^\s+([0-9]+)\s+([0-9]+)/;
		if ($1 == $part) {
			$found = 1; last;
			}
		}
	if (!$found) {
		&error("The SCSI partition for '$_[0]' does not exist");
		}
	}
elsif ($_[0] =~ /^\/dev\/md\/dsk\/d(.)$/) {
	# mounting a multi-disk (raid) device..
	$out = &backquote_command("prtvtoc -h $_[0] 2>&1");
	if ($out =~ /No such file or directory|No such device or address/) {
		&error("The RAID device for '$_[0]' does not exist");
		}
	if ($out !~ /\S/) {
		&error("No partitions on '$_[0]' ??");
		}
	}
else {
	# Some other device
	if (!open(DEV, $_[0])) {
		if ($! =~ /No such file or directory/) {
			&error("The device file '$_[0]' does not exist");
			}
		elsif ($! =~ /No such device or address/) {
			&error("The device for '$_[0]' does not exist");
			}
		}
	close(DEV);
	}

# Check the filesystem type
$out = &backquote_command("fstyp $_[0] 2>&1");
if ($out =~ /^([A-z0-9]+)\n$/) {
	if ($1 eq $_[1]) { return; }
	else {
		# Wrong filesystem type
		&error("The device '$_[0]' is formatted as a ".
		       &fstype_name($1));
		}
	}
else {
	&error("Failed to check filesystem type : $out");
	}
}


# check_options(type)
# Read options for some filesystem from %in, and use them to update the
# %options array. Options handled by the user interface will be set or
# removed, while unknown options will be left untouched.
sub check_options
{
local($k, @rv);
if ($_[0] eq "nfs") {
	# NFS has lots of options to parse
	if ($in{'nfs_ro'}) {
		# Read-only
		$options{"ro"} = ""; delete($options{"rw"});
		}
	else {
		# Read-write
		$options{"rw"} = ""; delete($options{"ro"});
		}

	delete($options{'quota'}); delete($options{'noquota'});
	if ($in{'nfs_quota'}) { $options{'quota'} = ""; }

	delete($options{"nosuid"}); delete($options{"suid"});
	if ($in{nfs_nosuid}) { $options{"nosuid"} = ""; }

	delete($options{"grpid"});
	if ($in{nfs_grpid}) { $options{"grpid"} = ""; }

	delete($options{"soft"}); delete($options{"hard"});
	if ($in{nfs_soft}) { $options{"soft"} = ""; }

	delete($options{"bg"}); delete($options{"fg"});
	if ($in{nfs_bg}) { $options{"bg"} = ""; }

	delete($options{"intr"}); delete($options{"nointr"});
	if ($in{nfs_nointr}) { $options{"nointr"} = ""; }

	delete($options{"vers"});
	if (!$in{nfs_vers_def}) { $options{"vers"} = $in{nfs_vers}; }

	delete($options{"proto"});
	if ($in{nfs_proto} ne "") { $options{"proto"} = $in{nfs_proto}; }

	delete($options{"port"});
	if (!$in{nfs_port_def}) { $options{"port"} = $in{nfs_port}; }

	delete($options{"timeo"});
	if (!$in{nfs_timeo_def}) { $options{"timeo"} = $in{nfs_timeo}; }

	delete($options{"secure"}); delete($options{"kerberos"});
	delete($options{"sec"});
	if ($gconfig{'os_version'} >= 2.6) {
		if ($in{'nfs_auth'}) { $options{'sec'} = $in{'nfs_auth'}; }
		}
	else {
		if ($in{'nfs_auth'} eq "dh") { $options{"secure"} = ""; }
		elsif ($in{'nfs_auth'} eq "krb") { $options{"kerberos"} = ""; }
		}

	if ($gconfig{'os_version'} >= 7) {
		delete($options{'public'});
		$options{'public'} = "" if ($in{'nfs_public'});
		}
	}
elsif ($_[0] eq "ufs") {
	# UFS also has lots of options..
	if ($in{ufs_ro}) {
		# read-only (and thus no quota)
		$options{"ro"} = ""; delete($options{"rw"});
		delete($options{"rq"}); delete($options{"quota"});
		}
	elsif ($in{ufs_quota}) {
		# read-write, with quota
		delete($options{"ro"}); $options{"rw"} = "";
		$options{"quota"} = "";
		}
	else {
		# read-write, without quota
		delete($options{"ro"}); $options{"rw"} = "";
		delete($options{"quota"});
		}

	delete($options{"nosuid"});
	if ($in{ufs_nosuid}) { $options{"nosuid"} = ""; }

	delete($options{"intr"}); delete($options{"nointr"});
	if ($in{ufs_nointr}) { $options{"nointr"} = ""; }

	delete($options{"onerror"});
	if ($in{ufs_onerror} ne "panic") {
		$options{"onerror"} = $in{ufs_onerror};
		}

	delete($options{"toosoon"});
	if ($in{ufs_toosoon_time}) {
		$options{"toosoon"} = $in{ufs_toosoon_time}.
				      $in{ufs_toosoon_units};
		}
	if ($gconfig{'os_version'} >= 7) {
		delete($options{'noatime'});
		$options{'noatime'} = "" if ($in{'ufs_noatime'});

		delete($options{'forcedirectio'});
		delete($options{'noforcedirectio'});
		$options{'forcedirectio'} = "" if ($in{'ufs_force'});

		delete($options{'nolargefiles'});delete($options{'largefiles'});
		$options{'nolargefiles'} = "" if ($in{'ufs_nolarge'});

		delete($options{'logging'}); delete($options{'nologging'});
		$options{'logging'} = "" if ($in{'ufs_logging'});
		}
	}
elsif ($_[0] eq "vxfs") {
	if ($in{jfs_ro}) {
		# read-only
		$options{"ro"} = ""; delete($options{"rw"});
		}
	else {
		# read-write
		$options{"rw"} = ""; delete($options{"ro"});
		}
	if ($in{jfs_nosuid}) {
		# nosuid
		$options{"nosuid"} = ""; delete($options{"suid"});
		}
	else {
		# suid
		$options{"suid"} = ""; delete($options{"nosuid"});
		}
	if ($in{jfs_log}) {
		# log
		$options{"log"} = ""; delete($options{"delaylog"});
		}
	else {
		# delaylog
		$options{"delaylog"} = ""; delete($options{"log"});
		}
	if ($in{jfs_syncw}) {
		# datainlog
		$options{"datainlog"} = ""; delete($options{"nodatainlog"});
		}
	else {
		# nodatainlog
		$options{"nodatainlog"} = ""; delete($options{"datainlog"});
		}
	if ($in{jfs_quota}) {
		# quota
		$options{"quota"} = "";
		}
	else {
		# noquota
		delete($options{"quota"});
		}
	}
elsif ($_[0] eq "lofs") {
	# Loopback has no options to parse
	}
elsif ($_[0] eq "swap") {
	# Swap has no options to parse
	}
elsif ($_[0] eq "pcfs") {
	# PCFS has only 2 options
	delete($options{'ro'}); delete($options{'rw'});
	$options{'ro'} = "" if ($in{'pcfs_rp'});

	delete($options{'foldcase'}); delete($options{'nofoldcase'});
	$options{'foldcase'} = "" if ($in{'pcfs_foldcase'});
	}
elsif ($_[0] eq "tmpfs") {
	# Ram-disk filesystems have only two options
	delete($options{"size"});
	if (!$in{"tmpfs_size_def"}) {
		$options{"size"} = "$in{tmpfs_size}$in{tmpfs_unit}";
		}

	delete($options{"nosuid"});
	if ($in{'tmpfs_nosuid'}) { $options{"nosuid"} = ""; }
	}
elsif ($_[0] eq "cachefs") {
	# The caching filesystem has lots of options
	$options{"backfstype"} = $in{"cfs_backfstype"};

	delete($options{"backpath"});
	if (!$in{"cfs_noback"}) {
		# A back filesystem was given..  (alreadys checked)
		$options{"backpath"} = $in{"cfs_backpath"};
		}

	if ($in{"cfs_cachedir"} !~ /^\/\S+/) {
		&error("'$in{cfs_cachedir}' is not a valid cache directory");
		}
	$options{"cachedir"} = $in{"cfs_cachedir"};

	delete($options{"write-around"}); delete($options{"non-shared"});
	if ($in{"cfs_wmode"}) {
		$options{"non-shared"} = "";
		}

	delete($options{"noconst"}); delete($options{"demandconst"});
	if ($in{"cfs_con"} == 0) { $options{"noconst"} = ""; }
	elsif ($in{"cfs_con"} == 2) { $options{"demandconst"} = ""; }

	delete($options{"ro"}); delete($options{"rw"});
	if ($in{"cfs_ro"}) { $options{"ro"} = ""; }

	delete($options{"suid"}); delete($options{"nosuid"});
	if ($in{"cfs_nosuid"}) { $options{"nosuid"} = ""; }
	}
elsif ($_[0] eq "autofs") {
	# The options for autofs depend on the type of the automounted
	# filesystem.. 
	$options{"fstype"} = $in{"autofs_fstype"};
	if ($gconfig{'os_version'} >= 2.6) {
		delete($options{'nobrowse'}); delete($options{'browse'});
		$options{'nobrowse'} = "" if ($in{'auto_nobrowse'});
		}
	return &check_options($options{"fstype"});
	}
elsif ($_[0] eq "rumba") {
	# Options for smb filesystems..
	delete($options{machinename});
	if (!$in{rumba_mname_def}) { $options{machinename} = $in{rumba_mname}; }

	delete($options{clientname});
	if (!$in{rumba_cname_def}) { $options{clientname} = $in{rumba_cname}; }

	delete($options{username});
	if ($in{rumba_username}) { $options{username} = $in{rumba_username}; }

	delete($options{password});
	if ($in{rumba_password}) { $options{password} = $in{rumba_password}; }

	delete($options{uid});
	if ($in{rumba_uid} ne "") { $options{uid} = getpwnam($in{rumba_uid}); }

	delete($options{gid});
	if ($in{rumba_gid} ne "") { $options{gid} = getgrnam($in{rumba_gid}); }

	delete($options{fmode});
	if ($in{rumba_fmode} !~ /^[0-7]{3}$/) {
		&error("'$in{rumba_fmode}' is not a valid octal file mode");
		}
	elsif ($in{rumba_fmode} ne "755") { $options{fmode} = $in{rumba_fmode}; }

	delete($options{dmode});
	if ($in{rumba_dmode} !~ /^[0-7]{3}$/) {
		&error("'$in{rumba_dmode}' is not a valid octal directory mode");
		}
	elsif ($in{rumba_dmode} ne "755") { $options{dmode} = $in{rumba_dmode}; }

	delete($options{'readwrite'});
	if ($in{'rumba_readwrite'}) { $options{'readwrite'} = ""; }

	delete($options{'readonly'});
	if ($in{'rumba_readonly'}) { $options{'readonly'} = ""; }

	delete($options{'attr'});
	if ($in{'rumba_attr'}) { $options{'attr'} = ""; }

	delete($options{'noupper'});
	if ($in{'rumba_noupper'}) { $options{'noupper'} = ""; }
	}

# Return options string
foreach $k (keys %options) {
	if ($options{$k} eq "") { push(@rv, $k); }
	else { push(@rv, "$k=$options{$k}"); }
	}
return @rv ? join(',' , @rv) : "-";
}


# create_swap(path, size, units)
# Attempt to create a swap file 
sub create_swap
{
local($out);
$out = &backquote_logged("mkfile $_[1]$_[2] $_[0] 2>&1");
if ($?) {
	&unlink_file($_[0]);
	return "mkfile failed : $out";
	}
return 0;
}


# exports_list(host, dirarray, clientarray)
# Fills the directory and client array references with exports from some
# host. Returns an error string if something went wrong
sub exports_list
{
local($dref, $cref, $out, $_);
$dref = $_[1]; $cref = $_[2];
$out = &backquote_command("showmount -e ".quotemeta($_[0])." 2>&1", 1);
if ($?) { return $out; }
foreach (split(/\n/, $out)) {
	if (/^(\/\S*)\s+(.*)$/) {
		push(@$dref, $1); push(@$cref, $2);
		}
	}
return undef;
}

# broadcast_addr()
# Returns a useable broadcast address for finding NFS servers
sub broadcast_addr
{
local($out);
$out = &backquote_command("ifconfig -a 2>&1", 1);
if ($out =~ /broadcast\s+(\S+)/) { return $1; }
return "255.255.255.255";
}

sub device_name
{
return $_[0];
}

sub files_to_lock
{
return ( $config{'fstab_file'}, $config{'autofs_file'} );
}

1;
