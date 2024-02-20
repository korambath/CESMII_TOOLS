#!/usr/bin/perl

use POSIX;
$ENV{'TZ'} = "GMT";

# Set the Time Zone to GMT (Greenwich Mean Time) for date
# calculations.

for ($clock = 2147483646; $clock < 2147483651; $clock++) {
       print ctime($clock); }


# If you are running on a 32 bit OS your output will be something like this
#Tue Jan 19 03:14:06 2038
#Tue Jan 19 03:14:07 2038
#Tue Jan 19 03:14:07 2038
#Tue Jan 19 03:14:07 2038
#Tue Jan 19 03:14:07 2038

# Notice that the time didn't change after 03:14:07 2038
# Some system may print Dec 13 20:45:52 1901 on a 32 bit OS.  Not issues on 64 bit OS.

my $last_second_32bit = 2**31 -1;
print "Last time in seconds that can be stored on a 32 bit machine $last_second_32bit \n";
print "Last day on 32/64 bit ", scalar gmtime($last_second_32bit), "\n";
print "Current time on 32 bit/64 bit ", ctime($last_second_32bit++), "\n";
print "Next time after a second increment on 32 bit/64 bit ", ctime($last_second_32bit++), "\n";

