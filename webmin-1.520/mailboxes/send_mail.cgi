#!/usr/local/bin/perl
# send_mail.cgi
# Send off an email message

require './mailboxes-lib.pl';
&ReadParse(\%getin, "GET");
&ReadParseMime(undef, \&read_parse_mime_callback, [ $getin{'id'} ]);
&can_user($in{'user'}) || &error($text{'mail_ecannot'});
@uinfo = &get_mail_user($in{'user'});
@uinfo || &error($text{'view_eugone'});

# Check inputs
@folders = &list_user_folders($in{'user'});
$folder = $folders[$in{'folder'}];
&error_setup($text{'send_err'});
$in{'to'} || &error($text{'send_eto'});
if ($access{'fmode'} == 0) {
	# Any from address allowed
	$in{'from'} || &error($text{'send_efrom'});
	}
elsif ($access{'fmode'} == 1) {
	# From address must be in an allowed domain, and match username
	$validfrom = &get_user_from_address(\@uinfo);
	foreach $f (split(/\s+/, $access{'from'})) {
		$found++ if ("$in{'user'}\@$f" eq $in{'from'} ||
			     "$in{'ouser'}\@$f" eq $in{'from'} ||
			     $validfrom eq $in{'from'});
		}
	&error($text{'send_efrom'}) if (!$found);
	}
elsif ($access{'fmode'} == 2) {
	# From address must be in allowed list
	foreach $f (split(/\s+/, $access{'from'})) {
		$found++ if ($f eq $in{'from'});
		}
	&error($text{'send_efrom'}) if (!$found);
	}
elsif ($access{'fmode'} == 3) {
	$in{'from'} .= "\@$access{'from'}";
	}
if ($in{'from'} =~ /^(\S+)\@(\S+)$/ && $access{'fromname'}) {
	$in{'from'} = "$access{'fromname'} <$in{'from'}>";
	}
@sub = split(/\0/, $in{'sub'});
$subs = join("", map { "&sub=$_" } @sub);

# Construct the email
$in{'from'} || &error($text{'send_efrom'});
$newmid = &generate_message_id($in{'from'});
$mail->{'headers'} = [ [ 'From', $in{'from'} ],
		       [ 'Subject', &encode_mimewords($in{'subject'}) ],
		       [ 'To', &encode_mimewords($in{'to'}) ],
		       [ 'Cc', &encode_mimewords($in{'cc'}) ],
		       [ 'Bcc', &encode_mimewords($in{'bcc'}) ],
		       [ 'Message-Id', $newmid ] ];
&add_mailer_ip_headers($mail->{'headers'});
push(@{$mail->{'headers'}}, [ 'X-Priority', $in{'pri'} ]) if ($in{'pri'});
$in{'body'} =~ s/\r//g;
if ($in{'body'} =~ /\S/) {
	# Perform spell check on body if requested
	local $plainbody = $in{'html_edit'} ? &html_to_text($in{'body'})
                                            : $in{'body'};
	if ($in{'spell'}) {
		@errs = &spell_check_text($plainbody);
		if (@errs) {
			# Spelling errors found!
			&mail_page_header($text{'compose_title'}, undef, undef,
					  &folder_link($in{'user'}, $folder));
			print "<b>$text{'send_espell'}</b><p>\n";
			print map { $_."<p>\n" } @errs;
			&mail_page_footer(
			    "javascript:back()", $text{'reply_return'},
			    "index.cgi?user=$in{'user'}&folder=$in{'folder'}",
			    $text{'mail_return'});
			exit;
			}
		}
	local $mt = $in{'html_edit'} ? "text/html" : "text/plain";
	if ($in{'charset'}) {
		$mt .= "; charset=$in{'charset'}";
		}
	if ($in{'body'} =~ /[\177-\377]/) {
		# Contains 8-bit characters .. need to make quoted-printable
		$quoted_printable++;
		@attach = ( { 'headers' => [ [ 'Content-Type', $mt ],
					     [ 'Content-Transfer-Encoding',
					       'quoted-printable' ] ],
			      'data' => quoted_encode($in{'body'}) } );
		}
	else {
		# Plain 7-bit ascii text
		@attach = ( { 'headers' => [ [ 'Content-Type', $mt ],
					     [ 'Content-Transfer-Encoding',
					       '7bit' ] ],
			      'data' => $in{'body'} } );
		}
	$bodyattach = $attach[0];

	if ($in{'html_edit'}) {
		# Create an attachment which contains both the HTML and plain
		# bodies as alternatives
		local @alts = ( $attach[0] );
		local $mt = "text/plain; charset=$charset";
		if ($plainbody =~ /[\177-\377]/) {
			unshift(@alts,
			  { 'headers' => [ [ 'Content-Type', $mt ],
					   [ 'Content-Transfer-Encoding',
					     'quoted-printable' ] ],
			    'data' => quoted_encode($plainbody) });
			}
		else {
			unshift(@alts,
			  { 'headers' => [ [ 'Content-Type', $mt ],
					   [ 'Content-Transfer-Encoding',
					     '7bit' ] ],
			    'data' => $plainbody });
			}

		# Set content type to multipart/alternative, to tell mail
		# clients about the optional body
		local $bound = "altsbound".time();
		$attach[0] = {
			'headers' => [ [ 'Content-Type',
					 'multipart/alternative; '.
					 'boundary="'.$bound.'"' ],
				       [ 'Content-Transfer-Encoding',
					 '7bit' ] ],
			'data' => join("", &unparse_mail(\@alts, "\n", $bound))
			};
		}
	}
$attachsize = 0;
for($i=0; defined($in{"attach$i"}); $i++) {
	# Add uploaded attachment
	next if (!$in{"attach$i"});
	&test_max_attach($attachsize);
	local $filename = $in{"attach${i}_filename"};
	$filename =~ s/^.*(\\|\/)//;
	local $type = $in{"attach${i}_content_type"}."; name=\"".
		      $filename."\"";
	local $disp = "inline; filename=\"".$filename."\"";
	push(@attach, { 'data' => $in{"attach${i}"},
			'headers' => [ [ 'Content-type', $type ],
				       [ 'Content-Disposition', $disp ],
				       [ 'Content-Transfer-Encoding',
					 'base64' ] ] });
	$atotal += length($in{"attach${i}"});
	}
for($i=0; defined($in{"file$i"}); $i++) {
	# Add uploaded attachment
	# Add server-side attachment
	next if (!$in{"file$i"} || !$access{'canattach'});
	@uinfo = &get_mail_user($in{'user'});
	@uinfo || &error($text{'view_eugone'});
	if ($in{"file$i"} !~ /^\//) {
		$in{"file$i"} = $uinfo[7]."/".$in{"file$i"};
		}

	local @st = stat($in{"file$i"});
	&test_max_attach($st[7]);
	local $data;
	&switch_to_user($in{'user'});
	$data = &read_file_contents($in{"file$i"});
	$data || &error(&text('send_efile', $in{"file$i"}, $!));
	&switch_user_back();
	$in{"file$i"} =~ s/^.*\///;
	local $type = &guess_mime_type($in{"file$i"}).
		      "; name=\"".$in{"file$i"}."\"";
	local $disp = "inline; filename=\"".$in{"file$i"}."\"";
	push(@attach, { 'data' => $data,
			'headers' => [ [ 'Content-type', $type ],
				       [ 'Content-Disposition', $disp ],
				       [ 'Content-Transfer-Encoding',
					 'base64' ] ] });
	$atotal += length($data);
	}
@fwd = split(/\0/, $in{'forward'});
if (@fwd) {
	# Add forwarded attachments
	@mail = &mailbox_list_mails($in{'idx'}, $in{'idx'}, $folder);
	$fwdmail = $mail[$in{'idx'}];
	&parse_mail($fwdmail);

	foreach $s (@sub) {
		# We are looking at a mail within a mail ..
		local $amail = &extract_mail($fwdmail->{'attach'}->[$s]->{'data'});
		&parse_mail($amail);
		$fwdmail = $amail;
		}

	foreach $f (@fwd) {
		&test_max_attach(length($fwdmail->{'attach'}->[$f]->{'data'}));
		push(@attach, $fwdmail->{'attach'}->[$f]);
		$atotal += length($fwdmail->{'attach'}->[$f]->{'data'});
		}
	}
@mailfwd = split(/\0/, $in{'mailforward'});
if (@mailfwd) {
	# Add forwarded emails
	@mail = &mailbox_list_mails($mailfwd[0], $mailfwd[@mailfwd-1], $folder);
	foreach $f (@mailfwd) {
		$fwdmail = $mail[$f];
		local $headertext;
		foreach $h (@{$fwdmail->{'headers'}}) {
			$headertext .= $h->[0].": ".$h->[1]."\n";
			}
		push(@attach, { 'data' => $headertext."\n".$fwdmail->{'body'},
				'headers' => [ [ 'Content-type', 'message/rfc822' ],
					       [ 'Content-Description',
						  $fwdmail->{'header'}->{'subject'} ] ]
			      });
		}
	}
$mail->{'attach'} = \@attach;
if ($access{'attach'} >= 0 && $atotal > $access{'attach'}*1024) {
	&error(&text('send_eattach', $access{'attach'}));
	}

# Check for text-only email
$textonly = $config{'no_mime'} && !$quoted_printable &&
	    @{$mail->{'attach'}} == 1 &&
	    $mail->{'attach'}->[0] eq $bodyattach &&
	    !$in{'html_edit'};

# Send it off
&send_mail($mail, undef, $textonly, $config{'no_crlf'});
&webmin_log("send", undef, undef, { 'from' => $in{'from'}, 'to' => $in{'to'} });

# Tell the user that email as sent
&mail_page_header($text{'send_title'}, undef, undef,
		  &folder_link($in{'user'}, $folder));

@tos = ( split(/,/, $in{'to'}), split(/,/, $in{'cc'}), split(/,/, $in{'bcc'}) );
$tos = join(" , ", map { "<tt>".&html_escape($_)."</tt>" } @tos);
print "<p>",&text($in{'draft'} ? 'send_draft' : 'send_ok', $tos),"<p>\n";

if ($in{'idx'} ne '') {
	&mail_page_footer("view_mail.cgi?idx=$in{'idx'}&folder=$in{'folder'}&user=$in{'user'}$subs",
	        $text{'view_return'},
		"list_mail.cgi?folder=$in{'folder'}&user=$in{'user'}",
		$text{'mail_return'},
		"", $text{'index_return'});
	}
else {
	&mail_page_footer("list_mail.cgi?folder=$in{'folder'}&user=$in{'user'}",
		$text{'mail_return'},
		"", $text{'index_return'});
	}

# write_attachment(&attach)
sub write_attachment
{
local ($a) = @_;
local ($enc, $rv);
foreach $h (@{$a->{'headers'}}) {
	$rv .= $h->[0].": ".$h->[1]."\r\n";
	$enc = $h->[1]
	    if (lc($h->[0]) eq 'content-transfer-encoding');
	}
$rv .= "\r\n";
if (lc($enc) eq 'base64') {
	local $encoded = &encode_base64($a->{'data'});
	$encoded =~ s/\r//g;
	$encoded =~ s/\n/\r\n/g;
	$rv .= $encoded;
	}
else {
	$a->{'data'} =~ s/\r//g;
	$a->{'data'} =~ s/\n/\r\n/g;
	$rv .= $a->{'data'};
	if ($a->{'data'} !~ /\n$/) {
		$rv .= "\r\n";
		}
	}
return $rv;
}

sub test_max_attach
{
$attachsize += $_[0];
if ($access{'attach'} >= 0 && $attachsize > $access{'attach'}) {
	&error(&text('send_eattachsize', $access{'attach'}));
	}
}

