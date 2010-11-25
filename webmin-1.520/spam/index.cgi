#!/usr/local/bin/perl
# index.cgi
# Display a menu of spamassassin config category icons

require './spam-lib.pl';
&ReadParse();
$hsl = $module_info{'usermin'} ? undef :
		&help_search_link("spamassassin", "perl", "google");
&set_config_file_in(\%in);

if (!&has_command($config{'spamassassin'}) ||
    (!$module_info{'usermin'} && !($vers = &get_spamassassin_version(\$out)))) {
	# Program not found
	&ui_print_header($header_subtext, $text{'index_title'}, "", undef, 1, 1,
			 undef, $hsl);

	if ($module_info{'usermin'}) {
		print &text('index_ecmd2',
			    "<tt>$config{'spamassassin'}</tt>"),"<p>\n";
		}
	else {
		print &text('index_ecmd', "<tt>$config{'spamassassin'}</tt>",
		    "$gconfig{'webprefix'}/config.cgi?$module_name"),"<p>\n";

		# Offer to install package
		&foreign_require("software", "software-lib.pl");
		$lnk = &software::missing_install_link(
				"spamassassin", $text{'index_spamassassin'},
				"../$module_name/", $text{'index_title'});
		if ($lnk) {
			print $lnk,"<p>\n";
			}
		elsif (&foreign_available("cpan")) {
			# Offer to install perl module
			$modname = "Mail::SpamAssassin";
			print &text('index_cpan', "<tt>$modname</tt>",
				    "../cpan/download.cgi?source=3&cpan=$modname&mode=2&return=/$module_name/&returndesc=".&urlize($module_info{'desc'})),"<p>\n";
			}
		}
	}
else {
	$vtext = $module_info{'usermin'} ? undef :
			&text('index_version', $vers);
	&ui_print_header($header_subtext, $text{'index_title'}, "", undef,
			 1, 1, undef, $hsl, undef, undef, $vtext);

	if (!-r $local_cf && !-d $local_cf && !$module_info{'usermin'}) {
		# Config not found
		print &text('index_econfig',
			"<tt>$local_cf</tt>",
			"../config.cgi?$module_name"),"<p>\n";
		}
	elsif ($dberr = &check_spamassassin_db()) {
		# Cannot contact the DB
		print &text('index_edb', $dberr,
			    "../config.cgi?$module_name"),"<p>\n";
		}
	else {
		# Work out of SpamAssassin is enabled in procmail
		if ($warn_procmail && &foreign_check("procmail")) {
			&foreign_require("procmail", "procmail-lib.pl");
			$spam_enabled = 0;	# Found call to spamassassin
			$delivery_enabled = 0;	# Found X-Spam: header rule
			@pmrcs = &get_procmailrc();
			foreach $pmrc (@pmrcs) {
				local @recipes =
					&procmail::parse_procmail_file($pmrc);
				local $isglobal = $pmrc eq
					          $config{'global_procmailrc'};
				if (&find_spam_recipe(\@recipes)) {
					$spam_enabled ||= 1;
					}
				if (&find_file_recipe(\@recipes)) {
					if ($isglobal) {
						# Enabled globally, and so
						# cannot be changed by user
						$delivery_enabled ||= -2;
						}
					else {
						$delivery_enabled ||= 1;
						}
					}
				if (&find_virtualmin_recipe(\@recipes)) {
					# Controlled by Virtualmin
					if ($isglobal &&
					    &find_force_default_receipe(
					      \@recipes)) {
						# User .procmailrc files are
						# prevented
						$spam_enabled ||= -2;
						$delivery_enabled ||= -2;
						}
					else {
						# Users can have a .procmailrc
						$spam_enabled ||= -2;
						$delivery_enabled ||= 1;
						}
					}
				}
			}
		else {
			# don't know, or checking disabled
			$spam_enabled = -1;
			$delivery_enabled = -1;
			}
		if ($spam_enabled == 0) {
			if ($module_info{'usermin'}) {
				print &text('index_warn_usermin',
					    "<tt>$pmrcs[0]</tt>",
					    "<tt>$pmrcs[1]</tt>"),"<p>\n";
				}
			else {
				print &text('index_warn_webmin',
					    "<tt>$pmrcs[0]</tt>"),"<p>\n";
				}
			}

		# Check if razor is set up
		if ($module_info{'usermin'} &&
		    -r "$remote_user_info[7]/.razor/identity") {
			$razor = 1;
			}

		# Show icons
		@pages = ( 'white', 'score', 'report', 'user' );
		push(@pages, 'simple') if (!$module_info{'usermin'} ||
					   &find_default("allow_user_rules",0));
		push(@pages, 'priv') if (!$module_info{'usermin'});
		push(@pages, 'mail') if ($module_info{'usermin'} &&
					 $userconfig{'spam_file'});
		push(@pages, 'razor') if (!$razor && $module_info{'usermin'});
		push(@pages, 'setup') if ($spam_enabled == 0);
		push(@pages, 'procmail') if ($delivery_enabled == 1);
		push(@pages, 'db') if (!$module_info{'usermin'});
		push(@pages, 'awl') if (&supports_auto_whitelist());
		@pages = grep { &can_use_page($_) } @pages;
		$sfolder = $module_info{'usermin'} ? &spam_file_folder()
						   : undef;
		if (!$sfolder) {
			@pages = grep { $_ ne 'mail' } @pages;
			}
		@links = map { $_ eq "mail" ? "../mailbox/index.cgi?folder=$sfolder->{'index'}" : "edit_${_}.cgi" } @pages;
		if ($in{'file'}) {
			foreach my $l (@links) {
				if ($l !~ /\//) {
					$l .= "?file=".&urlize($in{'file'}).
					      "&title=".&urlize($in{'title'});
					}
				}
			}
		@icons = map { "images/${_}.gif" } @pages;
		@titles = map { $text{"${_}_title"} } @pages;
		&icons_table(\@links, \@titles, \@icons);

		# Show buttons for HUPing spamd processes (if any)
		if (!$module_info{'usermin'} &&
		    (@pids = &get_process_pids())) {
			print &ui_hr();
			print "<form action=apply.cgi>\n";
			print "<table>\n";
			print "<tr> <td><input type=submit ",
			      "value='$text{'index_apply'}'></td>\n";
			print "<td>",&text('index_applydesc',
				"<tt>".join(" and ", &unique(
				map { $_->[1] } @pids))."</tt>"),"</td>\n";
			print "</table>\n";
			}
		}
	}

&ui_print_footer("/", $text{'index'});

