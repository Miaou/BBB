// Interface for the Dallas' exclusive 1-Wire bus protocol
// PAB, 2014 and other people should put their name here.

// Maybe I will do a one-file lib...

// Later in this document, Master refers to the BBB
//  and Slaves to the one or multiple DS18B20 (or compatible)
// Documentation was taken from DS18B20-PAR's datasheet

// This file is divided in 2 parts:
//  - low-level signal handling
//  - higher-level communication handling
// Remember, communications must follow the following pattern
//  1. Initialization
//  2. ROM Command (followed by any required data exchange)
//  3. DS18B20-PAR Function Command (followed by any required data exchange)




// Controlling which functions are exported in the lib:
//  (https://www.gnu.org/software/gnulib/manual/html_node/Exported-Symbols-of-Shared-Libraries.html)
#define LIBDALLAS_API __attribute__((__visibility__("default")))



#include "BBBiolib.h"
#include <time.h>



// Macro to wait some nanoseconds
#define WAIT_NANO(t0,t1,nNano) while(!clock_gettime(CLOCK_REALTIME, &t1) && \
                                     nanodiff(&t0, &t1) < nNano)



//-----------------------------------------------------------------------------
// libDallas init/cleaning
//-----------------------------------------------------------------------------

// "Inits" the lib
LIBDALLAS_API int dallas_init(void)
{
    struct timespec tTest;
    if(clock_gettime(CLOCK_REALTIME, &tTest))
        return -1;
    return iolib_init();
}

// Clean
LIBDALLAS_API int dallas_free(void)
{
    return iolib_free();
}

// Substract two timespec (comparing clock_gettime)
int nanodiff(struct timespec *t0, struct timespec *t1)
{
    if(-1 > t1->tv_sec-t0->tv_sec && t1->tv_sec-t0->tv_sec > 1)
        return 0xDEADBEEF;

    int nd = t1->tv_nsec-t0->tv_nsec;
    int sd = t1->tv_sec-t0->tv_sec;
    if(sd == 1)
        return nd+1000000000;
    else if(sd == -1)
        return nd-1000000000;
    return nd;
}


//-----------------------------------------------------------------------------
// Signals and wrapper.
// There are 6 signal types
//  - reset pulse (Master)
//  - presence pulse (Slaves)
//  - write time slot, bit 0 or 1 (Master then Slave)
//  - read time slot, bit 0 or 1 (Master then Slave)
// Wrappers: write byte, read byte.
//-----------------------------------------------------------------------------

// This one is not a single signal.
// Set master to low for at least 480µs,
//  goes into receive mode,
//  waits 15 to 60µs (signals is pulled back up),
//  a slave should then put the pin to low for 60 to 240µs,
//  master should stay in receive mode until 480µs has been spent since entering receive mode
LIBDALLAS_API int pulseInit(char port, char pin)
{
    struct timespec tBegins, tSwitch, tEnd;
    char bPresence;//, bPresenceTested; // (remember, bool does not exist in C ^^)

    iolib_setdir(port, pin, BBBIO_DIR_OUT);
    pin_low(port, pin); // This takes ~0.25µs
    clock_gettime(CLOCK_REALTIME, &tBegins); // This takes ~2µs (the first calls are always longer)
    WAIT_NANO(tBegins, tSwitch, 480000);

    iolib_setdir(port, pin, BBBIO_DIR_IN); // This takes ~0.5µs
    WAIT_NANO(tSwitch, tEnd, 67000);
    pin_low(port, pin);
    bPresence = is_low(port, pin); // This takes ~0µs
    WAIT_NANO(tSwitch, tEnd, 480000);

    return bPresence;
}


// Write time slot, one bit
// Set master to low for at least 1µs, less than 15µs,
//  if bit&0x1 is 0, then stay low,
//  if bit&0x1 is 1, then let it be pulled up,
//  for a total time of at least 60 and less than 120.
// The time  before next written bit (> 1µs) is waited here (master must be released)
// (for debug purposes, it is in the API, but it should not)
LIBDALLAS_API
int write_bit(char port, char pin, char bit)
{
    struct timespec tBegins, tEnd;
    
    iolib_setdir(port, pin, BBBIO_DIR_OUT);
    pin_low(port, pin);
    clock_gettime(CLOCK_REALTIME, &tBegins);
    WAIT_NANO(tBegins, tEnd, 8000);

    if(bit&1)
        iolib_setdir(port, pin, BBBIO_DIR_IN);
    WAIT_NANO(tBegins, tEnd, 75000);

    iolib_setdir(port, pin, BBBIO_DIR_IN);
    WAIT_NANO(tEnd, tBegins, 1000); 
    
    return 0;
}


// Read time slot (be careful, reads are only valid after some commands...)
// Set master to low for at least 1µs (staying low as little as possible),
//  release the master,
//  read before 15µs, as close to 15µs as possible,
//  wait until the end of the time slot (which should be >60µs),
//  wait at least 1µs before next read slot
// Function may return -1 if read is not done within 15µs
LIBDALLAS_API
int read_bit(char port, char pin)
{
    struct timespec tBegins, tEnd;
    char bBit;
    int nNanosec;
    
    // Taking the reference time is difficult: all these function take time ~µs
    //  and the waited time IS critical... Little margins.
    pin_low(port, pin); // I hope this is effective when pin is in BBBIO_DIR_IN mode
    clock_gettime(CLOCK_REALTIME, &tBegins);
    iolib_setdir(port, pin, BBBIO_DIR_OUT); // Considered <1µs
    WAIT_NANO(tBegins, tEnd, 1000); // Will be more than 1µs
    iolib_setdir(port, pin, BBBIO_DIR_IN);
    WAIT_NANO(tBegins, tEnd, 10000);
    bBit = is_high(port, pin);

    // Now we check that the 15µs window was not exceeded
    //  Because clock_gettime takes some time, we could conclude to a false negative...
    clock_gettime(CLOCK_REALTIME, &tEnd);
    nNanosec = nanodiff(&tBegins, &tEnd);
    WAIT_NANO(tBegins, tEnd, 60000);
    if(nNanosec == 0xDEADBEEF || nNanosec > 15000)
        return -1;
    return bBit;
}



//- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// Wrappers/helpers
// Bytes are written/read with least significant bit first.
//- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

LIBDALLAS_API int write_byte(char port, char pin, unsigned char by)
{
    char i;
    int status = 0;
    
    for(i=0; i<8 && !status; ++i)
        status = write_bit(port, pin, (by>>i));

    return status;
}

LIBDALLAS_API int read_byte(char port, char pin)
{
    char i;
    int status = 0;
    unsigned char byte = 0;

    for(i=0; i<8; ++i)
    {
        status = read_bit(port, pin);
        if(status<0)
            return -1;
        byte |= (status<<i);
    }

    return byte;
}


//-----------------------------------------------------------------------------
// Handling communications
//-----------------------------------------------------------------------------

//- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// ROM commands
// Search ROM is a little sepcial, refer to page 51 of the Book of iButton Standards
//  (now at http://pdfserv.maximintegrated.com/en/an/AN937.pdf)
//  After reading that, you might understand figure 10 of the DS18B20's datasheet...
//- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

//- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// Function Commands
//- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
