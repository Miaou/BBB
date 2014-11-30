// Juste pour tester la vitesse de on/off
// Compile with: gcc -o testBBBIO -I[path to BBBiolib.h] testBBBIO.c -lrt -L[path to libBBBio.a] -lBBBio

#include <time.h>
#include "BBBiolib.h"
#include <stdlib.h>


#define N_TESTS 10
#define PIN 9,13
#define N_LOOP 104857600


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
    
    // On veut temps mini, on fait fonctionner le proco pour qu'il sorte de som mode d'économie
    // On en profite pour voir le temps qu'il met à compter, et le temps qu'il met à regarder le temps
    printf("\nTemps en secondes.\n\nBoucle à %u: ", N_LOOP);
    clock_gettime(CLOCK_REALTIME, &t[0]);
    for(i=0; i<N_LOOP; ++i);
    clock_gettime(CLOCK_REALTIME, &t[1]);
    clock_gettime(CLOCK_REALTIME, &t[2]);
    printf("%g\n2 appels conséc: %g\n\n", diff(&t[0],&t[1]), diff(&t[1],&t[2]));

    iolib_setdir(PIN, BBBIO_DIR_OUT);
    pin_low(PIN);
    
    printf("Montées/descentes\n");
    for(i=0; i<N_TESTS; ++i)
    {
        clock_gettime(CLOCK_REALTIME, &t[2*i]);
        pin_high(PIN);
        pin_low(PIN);
        clock_gettime(CLOCK_REALTIME, &t[2*i+1]);
    }

    pin_low(PIN);
    
    for(i=0; i<N_TESTS; ++i)
        printf("-> %g\n",diff(&t[2*i],&t[2*i+1]));
    
    printf("\nChangements de directions\n");
    for(i=0; i<N_TESTS; ++i)
    {
        clock_gettime(CLOCK_REALTIME, &t[2*i]);
        iolib_setdir(PIN, BBBIO_DIR_OUT);
        iolib_setdir(PIN, BBBIO_DIR_IN);
        clock_gettime(CLOCK_REALTIME, &t[2*i+1]);
    }
    
    for(i=0; i<N_TESTS; ++i)
        printf("-> %g\n",diff(&t[2*i],&t[2*i+1]));
    
    printf("\nLecture de la valeur du signal (haut)\n");
    for(i=0; i<N_TESTS; ++i)
    {
        clock_gettime(CLOCK_REALTIME, &t[2*i]);
        is_high(PIN);
        clock_gettime(CLOCK_REALTIME, &t[2*i+1]);
    }
    
    for(i=0; i<N_TESTS; ++i)
        printf("-> %g\n",diff(&t[2*i],&t[2*i+1]));
    
    printf("\nLecture de la valeur du signal (low)\n");
    for(i=0; i<N_TESTS; ++i)
    {
        clock_gettime(CLOCK_REALTIME, &t[2*i]);
        is_low(PIN);
        clock_gettime(CLOCK_REALTIME, &t[2*i+1]);
    }
    
    for(i=0; i<N_TESTS; ++i)
        printf("-> %g\n",diff(&t[2*i],&t[2*i+1]));
    
    
    iolib_free();
    return 0;
}
