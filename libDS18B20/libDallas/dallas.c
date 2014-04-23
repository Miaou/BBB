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



#include "dallas.h"


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
    WAIT_NANO(tEnd, tBegins, 10000); // Leave it 10 instead of just 1, to be sure !
    
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
    WAIT_NANO(tBegins, tEnd, 2000); // Will be more than 1µs
    iolib_setdir(port, pin, BBBIO_DIR_IN);
    // We have 15µs to read the value, the later the better.
    //  Raise the value if CRCs are invalid
    //  Lower the value if read_bit returns -1 too easily
    //   (beware, because of something unknow, 
    //   you can't hope for miracles, and sometimes something takes around 1ms...)
    //   Interesting fact, changing overall length of the read slot affects greatly
    //   the false negative. For now, having 60000 -> 75% success, 63000 -> 95% success.
    //   THIS IS F*CK*D UP
    WAIT_NANO(tBegins, tEnd, 8000);
    bBit = is_high(port, pin);

    // Now we check that the 15µs window was not exceeded
    //  Because clock_gettime takes some time, we could conclude to a false negative...
    clock_gettime(CLOCK_REALTIME, &tEnd);
    nNanosec = nanodiff(&tBegins, &tEnd);
    WAIT_NANO(tBegins, tEnd, 63000); // 60+safety.
    if(nNanosec == 0xDEADBEEF || nNanosec > 15000)
    {
        //printf("Time frame was missed: %u nanosecs elapsed\n", nNanosec);
        return -1;
    }
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

// How do you avoid overflows in this case ???
LIBDALLAS_API int dallas_rom_read(char port, char pin, unsigned char *bRom)
{
    //unsigned char bRom[8];
    int i, status;

    if(! pulseInit(port, pin) || ! bRom)
        return -1;
    
    // Send a 0x33
    write_byte(port, pin, READ_ROM);
    // Reads the 8 bytes
    for(i=0; i<8; ++i)
    {
        status = read_byte(port, pin);
        if(status < 0)
            return -1;
        bRom[i] = status;
    }
    
    return 0;
}


// Do Search: helper.
// Does the search from bit number iFrom.
//  If bRedo, resends the validated sequence contained in static bRom until bit iFrom,
//  then continues the search.
int do_search(char port, char pin, unsigned char iFrom, char bRedo, SEARCH_CALLBACK found_rom)
{
    // Least significant bit firts, least significant byte first (little endian)
    static unsigned char bRom[8];
    int i, status;
    unsigned char bit0, bit1;
    
    
    if(iFrom > 63)
        return -5;

    if(bRedo || iFrom==0)
    {
        if(! pulseInit(port, pin))
            return -1;
        // Sends a 0xF0
        write_byte(port, pin, SEARCH_ROM);
    }
    
    if(bRedo)
    {
        for(i=0; i<iFrom; ++i)
        {
            // This is me following a route. Don't check if read is successful: we don't care.
            // If it was a true fail, we will have no response later, and it will be filtered...
            // Otherwise, it was a false negative, and we are glad to pursue...
            read_bit(port, pin);
            read_bit(port, pin);
            write_bit(port, pin, (bRom[i/8]>>(i%8)));
        }
    }
    for(i=iFrom; i<64; ++i)
    {
        status = read_bit(port, pin);
        if(status < 0)
            return -2;
        bit0 = status;
        status = read_bit(port, pin);
        if(status < 0)
            return -3;
        bit1 = status;

        if(!bit0 && bit1)
        {
            // All devices have a 0, so we select them all
            bRom[i/8] &= ~(1<<(i%8));
            write_bit(port, pin, 0);
        }
        else if(bit0 && !bit1)
        {
            // All devices have a 1, so we select them all
            bRom[i/8] |= (1<<(i%8));
            write_bit(port, pin, 1);
        }
        else if(!bit0 && !bit1)
        {
            // Both 0 and 1 are found. Our path must be split.
            // First, we continue the branch were a 0 is at rank i
            bRom[i/8] &= ~(1<<(i%8));
            write_bit(port, pin, 0); // A write must follow each couple of reads
            status  = 0;
            status |= do_search(port, pin, i+1, 0, found_rom);
            // Then, we redo the first part, use a 1 at rank i, and finish the branch
            bRom[i/8] |= (1<<(i%8));
            status |= do_search(port, pin, i+1, 1, found_rom);
            // If status < 0, something went wrong, the results may be partial only.
            return (! status) ? 0 : -6;
        }
        else // bit0 && bit1
            // Devices are not responding.
            return -4;
    }

    // Only reach here if a branch is finished.
    found_rom(bRom);
    //for(i=0; i<8; ++i)
    //    printf("0x%02X ", bRom[i]);
    //printf("\n");

    return 0;
}


LIBDALLAS_API int dallas_rom_search(char port, char pin, SEARCH_CALLBACK found_rom)
{
    return do_search(port, pin, 0, 0, found_rom);
}

LIBDALLAS_API int dallas_skip_rom(char port, char pin, unsigned char operation)
{
    //send a 0xCC
    write_byte(port, pin, SKIP_ROM);
    write_byte(port, pin, operation);
    if(operation == CONVERT_T || operation == COPY_SCRATCHPAD);
    //need a strong pullup over here for these 2 operations, cf doc
    //during at least 10ms 
    return 0;
}

//- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// Function Commands
//- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

LIBDALLAS_API int dallas_read_scratchpad(char port, char pin, unsigned char *scratch)
{
    write_byte(port, pin, READ_SCRATCHPAD);
    int i, status;

    for(i = 0; i < 9; ++i)
    {
        status = read_byte(port, pin);
        if(status < 0)
            return -1;
        scratch[i] = status;
    }

    return 0;
}

LIBDALLAS_API int dallas_read_temperature(char port, char pin)
{
    write_byte(port, pin, READ_SCRATCHPAD);
    int i, status, temperature = 0;

    for(i = 0; i < 2; ++i)
    {
        status = read_byte(port, pin);
        if(status < 0)
            return -1;

        /*We keep all the bits whatever the resolution is.
        It is user responsibility to remove all undesered bits by reading scratchpad
        to get resolution(9 to 12 bits)*/
        temperature += status<<(8*i);
    } 
    
    pulseInit(port, pin);
    return temperature;
}

LIBDALLAS_API int dallas_write_scratchpad(char port, char pin, unsigned char *data)
{
    int i;
    for(i = 0; i < 3; ++i)
    {
        write_byte(port, pin, data[i]);
    }
    
    return 0;
    /*Aucun contrôle possible, ni sur write_byte, ni sur write_bit*/
}
