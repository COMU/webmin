
do 'burner-lib.pl';

sub feedback_files
{
local (@rv, $f);
opendir(DIR, $module_config_directory);
foreach $f (readdir(DIR)) {
	push(@rv, "$module_config_directory/$f") if ($f =~ /\.burn$/);
	}
closedir(DIR);
return @rv;
}

1;

