// Juste pour tester la vitesse de on/off
// Compile with: gcc -o testBBBIO -I[path to BBBiolib.h] testBBBIO.c -lrt -L[path to libBBBio.a] -lBBBio

#include <time.h>
#include "BBBiolib.h"
#include <stdlib.h>


#define N_TESTS 10
#define PIN 9,13


float diff(struct timespec *t0, struct timespec *t1)
{
    float t = (float)(t1->tv_nsec-t0->tv_nsec);
    t *= 1e-9;
    t += (float)(t1->tv_sec-t0->tv_sec);
    return t;
}


int main(void)
{
    struct timespec t[N_TESTS*2];
    int i;

    iolib_init();
    iolib_setdir(PIN, BBBIO_DIR_OUT);
    pin_low(PIN);
    
    for(i=0; i<N_TESTS; ++i)
    {
        clock_gettime(CLOCK_REALTIME, &t[2*i]);
        pin_high(PIN);
        pin_low(PIN);
        clock_gettime(CLOCK_REALTIME, &t[2*i+1]);
    }

    pin_low(PIN);
    iolib_free();

    for(i=0; i<N_TESTS; ++i)
    {
        printf("-> %g\n",diff(&t[2*i],&t[2*i+1]));
    }

    return 0;
}
