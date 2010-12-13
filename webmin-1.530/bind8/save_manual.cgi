#!/usr/local/bin/perl
# Update a manually edited config file

require './bind8-lib.pl';
&error_setup($text{'manual_err'});
$access{'defaults'} || &error($text{'manual_ecannot'});
&ReadParseMime();

# Work out the file
$conf = &get_config();
@files = &get_all_config_files($conf);
&indexof($in{'file'}, @files) >= 0 || &error($text{'manual_efile'});
$in{'data'} =~ s/\r//g;
if ($in{'file'} eq $files[0]) {
	$in{'data'} =~ /\S/ || &error($text{'manual_edata'});
	}

# Write to it
&open_lock_tempfile(DATA, ">".&make_chroot($in{'file'}));
&print_tempfile(DATA, $in{'data'});
&close_tempfile(DATA);

&webmin_log("manual", undef, $in{'file'});
&redirect("");

