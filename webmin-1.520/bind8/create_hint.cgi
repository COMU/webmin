#!/usr/local/bin/perl
# create_hint.cgi
# Create a new root zone

require './bind8-lib.pl';
&ReadParse();
&error_setup($text{'hcreate_err'});
$access{'master'} || &error($text{'hcreate_ecannot'});
$access{'ro'} && &error($text{'master_ero'});

# Validate inputs
&allowed_zone_file(\%access, $in{'file'}) ||
	&error(&text('hcreate_efile', $in{'file'}));
&lock_file(&make_chroot($in{'file'}));
open(FILE, ">>".&make_chroot($in{'file'})) ||
	&error($text{'hcreate_efile2'});
close(FILE);

# Get the root server information
if ($in{'real'} == 1) {
	# Download from internic
	$err = &download_root_zone($in{'file'});
	&error($err) if ($err);
	}
elsif ($in{'real'} == 2) {
	# Use webmin's copy
	&copy_source_dest("$module_root_directory/db.cache",
		          &make_chroot($in{'file'}));
	}
else {
	# Just check the existing file
	@recs = &read_zone_file(&make_chroot($in{'file'}), ".");
	&error($text{'mcreate_erecs'}) if (@recs < 2);
	}
&unlock_file(&make_chroot($in{'file'}));

# Create zone structure
$dir = { 'name' => 'zone',
	 'values' => [ '.' ],
	 'type' => 1,
	 'members' => [ { 'name' => 'type',
			  'values' => [ 'hint' ] },
			{ 'name' => 'file',
			  'values' => [ $in{'file'} ] }
		      ]
	};

# Add a new hint zone
$conf = &get_config();
&create_zone($dir, $conf, $in{'view'});
&webmin_log("create", "hint", ".", \%in);
&redirect("");

