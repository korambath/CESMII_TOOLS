#include <stdio.h>
#include <limits.h>
#include <stdlib.h>
#include <time.h>

int main()
{
    printf("This program tests time related issues regarding Year 2038 (Y2k38) !\n");
    time_t seconds;
     
    seconds = time(NULL);
    printf("Current seconds since January 1, 1970 = %ld\n", seconds);

    printf("\nTest whether you are running a 32 bit or 64 bit OS \n");

    printf("Your system is running %d bit OS \n",  sizeof(void*) * CHAR_BIT);
    printf("sizeof(int): %ld\n",sizeof(int));
    printf("sizeof(long long int): %ld\n",sizeof(long long int));
    printf("sizeof(time_t): %ld\n",sizeof(time_t));

    /* 
       Background Binary Information

       Each bit of information can be set to either "0" or "1". In order to represent more than two states 
       we have to put multiple bits together to form a data type. Put eight togther to make a "byte". 
       For example, 00000000 to 11111111 gives 2^8 = 256 different values. 

       00000000 00000000 00000000 00000000
       11111111 11111111 11111111 11111111

       Unix time is number of seconds elapsed since the Unix epoch (00:00:00 UTC on Jan 1, 1970
       On a 32 bit hardware and OS it is stored in signed 32 bit integer capable of representing
       integer between -(2^31) and 2^31 -1.  Latest time that can be properly stored is 2^31 − 1 
       seconds after epoch, which is 03:14:07 UTC on 19 January 2038.  The overflow error will occur at 
       03:14:08 UTC on 19 January 2038. Attempting to increment to the following second (03:14:08) 
       will cause the integer to overflow, setting its value to −(2^31) which systems will interpret 
       as 2^31 seconds before epoch (20:45:52 UTC on 13 December 1901. 

       If a signed 32-bit integer is used to store Unix time, the latest time that can be stored is 
       2^31 − 1 (2,147,483,647) seconds after epoch, which is 03:14:07 on Tuesday, 19 January 2038.

       This is not an issue on 64 bit architecture where signed integer is stored between -(2^63) and 2^63 -1.

    */

    time_t t = time(NULL);
    printf("Local time and date: %s\n", asctime(localtime(&t)));
    printf("UTC time and date: %s\n", asctime(gmtime(&t)));

    struct tm  tm;
    t = 2147483644;
  
    // set seconds close to 03:14:07 on Tuesday, 19 January 2038

    t = (time_t) 2147483647;

    for (int i = 0; i< 4; i++ ) {

       printf ("%ld, %s", (long) t, asctime (gmtime (&t)));
       t++;

    }

    // set time in hexadecimal 
    //t = (time_t) (0x7FFFFFFF);
    //t++;
    //printf ("%ld, %s", (long) t, asctime (gmtime (&t)));


    return 0;
}
