#!/usr/local/bin/perl
# save_acls.cgi
# Update all the acl directives

require './bind8-lib.pl';
$access{'defaults'} || &error($text{'acls_ecannot'});
&error_setup($text{'acls_err'});
&ReadParse();

# Convert inputs into ACL structures
%depmap = ( );
&lock_file(&make_chroot($config{'named_conf'}));
$conf = &get_config();
for($i=0; defined($name = $in{"name_$i"}); $i++) {
	next if (!$name);
	$name =~ /^\S+$/ || &error(&text('acls_ename', $name));
	$in{"values_$i"} =~ s/\r//g;
	@vals = split(/\n+/, $in{"values_$i"});
	foreach $v (@vals) {
		if ($v =~ /^[0-9\.]+\s+\S/) {
			&error(&text('acls_eline', $name));
			}
		}
	push(@acls, { 'name' => 'acl',
		      'values' => [ $name ],
		      'type' => 1,
		      'members' => [ map { my ($n, @w)=split(/\s+/, $_);
				           { 'name' => $n,
					     'values' => \@w } } @vals ] });

	# Record this ACL as a dependency of some ACL it refers to
	foreach (@vals) {
		my ($n, @w)=split(/\s+/, $_);
		if ($n !~ /^[0-9\.]+$/) {
			push(@{$depmap{$n}}, $name);
			}
		}
	}

# Sort the list so that depended-on ACLs come first
@acls = sort { my $an = $a->{'values'}->[0];
	       my $bn = $b->{'values'}->[0];
	       &indexof($an, @{$depmap{$bn}}) >= 0 ? 1 :
	       &indexof($bn, @{$depmap{$an}}) >= 0 ? -1 : 0 } @acls;

&save_directive(&get_config_parent(), 'acl', \@acls, 0, 0, 1);
&flush_file_lines();
&unlock_file(&make_chroot($config{'named_conf'}));
&webmin_log("acls", undef, undef, \%in);
&redirect("");

