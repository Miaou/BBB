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
        return ERR_NO_CLOCK;
    return iolib_init();
}

// Clean
LIBDALLAS_API int dallas_free(void)
{
    return iolib_free();
}

// Substract two timespec (comparing clock_gettime)
//  (up two +/- 1 seconde)
int nanodiff(struct timespec *t0, struct timespec *t1)
{
    if(-1 > t1->tv_sec-t0->tv_sec && t1->tv_sec-t0->tv_sec > 1)
        return ERR_DIFF_TOO_BIG;

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
LIBDALLAS_API int pulseInit(OneWire* onewire)
{
//FIXME: check timings and return ERR_MISSED_TSLOT
    struct timespec tBegins, tSwitch, tEnd;
    char bPresence;//, bPresenceTested; // (remember, bool does not exist in C ^^)

    iolib_setdir(onewire->pullup_port, onewire->pullup_pin, BBBIO_DIR_OUT); //Each transaction begins with a pulse
    //so we set the pullup to high here for every transaction
    //pullup is handling a mosfet, not a direct pullup.
    pin_high(onewire->pullup_port, onewire->pullup_pin);

    iolib_setdir(onewire->port, onewire->pin, BBBIO_DIR_OUT);
    pin_low(onewire->port, onewire->pin); // This takes ~0.25µs
    clock_gettime(CLOCK_REALTIME, &tBegins); // This takes ~2µs (the first calls are always longer)
    WAIT_NANO(tBegins, tSwitch, 480000);

    iolib_setdir(onewire->port, onewire->pin, BBBIO_DIR_IN); // This takes ~0.5µs
    WAIT_NANO(tSwitch, tEnd, 67000);
    pin_low(onewire->port, onewire->pin);
    bPresence = is_low(onewire->port, onewire->pin); // This takes ~0µs
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
int write_bit(OneWire* onewire, char bit)
{
    struct timespec tBegins, tEnd;
    int nNanosec;

    iolib_setdir(onewire->port, onewire->pin, BBBIO_DIR_OUT);
    pin_low(onewire->port, onewire->pin);
    clock_gettime(CLOCK_REALTIME, &tBegins);
    WAIT_NANO(tBegins, tEnd, 2000);

    if(bit&1)
    {
        nNanosec = nanodiff(&tBegins, &tEnd);
        if(nNanosec == ERR_DIFF_TOO_BIG || nNanosec > 15000)
            return ERR_MISSED_TSLOT;
        iolib_setdir(onewire->port, onewire->pin, BBBIO_DIR_IN);
    }
    WAIT_NANO(tBegins, tEnd, 75000);

    iolib_setdir(onewire->port, onewire->pin, BBBIO_DIR_IN);
    WAIT_NANO(tEnd, tBegins, 10000); // Leave it 10 instead of just 1, to be sure !
    nNanosec = nanodiff(&tBegins, &tEnd);

    if(nNanosec == ERR_DIFF_TOO_BIG || nNanosec > 120000)
        return ERR_MISSED_TSLOT;

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
int read_bit(OneWire* onewire)
{
    struct timespec tBegins, tEnd;
    char bBit;
    int nNanosec;

    // Taking the reference time is difficult: all these function take time ~µs
    //  and the waited time IS critical... Little margins.
    pin_low(onewire->port, onewire->pin); // I hope this is effective when pin is in BBBIO_DIR_IN mode
    clock_gettime(CLOCK_REALTIME, &tBegins);
    iolib_setdir(onewire->port, onewire->pin, BBBIO_DIR_OUT); // Considered <1µs
    WAIT_NANO(tBegins, tEnd, 2000); // Will be more than 1µs
    iolib_setdir(onewire->port, onewire->pin, BBBIO_DIR_IN);
    // We have 15µs to read the value, the later the better.
    //  Raise the value if CRCs are invalid
    //  Lower the value if read_bit returns -1 too easily
    //   (beware, because of something unknow,
    //   you can't hope for miracles, and sometimes something takes around 1ms...)
    //   Interesting fact, changing overall length of the read slot affects greatly
    //   the false negative. For now, having 60000 -> 75% success, 63000 -> 95% success.
    //   THIS IS F*CK*D UP
    WAIT_NANO(tBegins, tEnd, 8000);
    bBit = is_high(onewire->port, onewire->pin);

    // Now we check that the 15µs window was not exceeded
    //  Because clock_gettime takes some time, we could conclude to a false negative...
    clock_gettime(CLOCK_REALTIME, &tEnd);
    nNanosec = nanodiff(&tBegins, &tEnd);
    WAIT_NANO(tBegins, tEnd, 63000); // 60+safety.
    if(nNanosec == ERR_DIFF_TOO_BIG || nNanosec > 15000)
    {
        //printf("Time frame was missed: %u nanosecs elapsed\n", nNanosec);
        return ERR_MISSED_TSLOT;
    }
    return bBit;
}



//- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// Wrappers/helpers
// Bytes are written/read with least significant bit first.
//- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

LIBDALLAS_API int write_byte(OneWire* onewire, unsigned char by)
{
    char i;
    int status = 0;

    for(i=0; i<8 && !status; ++i)
        status = write_bit(onewire, (by>>i));

    return status;
}

LIBDALLAS_API int read_byte(OneWire* onewire)
{
    char i;
    int status = 0;
    unsigned char byte = 0;

    for(i=0; i<8; ++i)
    {
        status = read_bit(onewire);
        if(status<0)
            return status;
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
LIBDALLAS_API int dallas_rom_read(OneWire* onewire, unsigned char *bRom)
{
    //unsigned char bRom[8];
    int i, status;

    if(! pulseInit(onewire))
        return ERR_NO_PRESENCE;
    if(! bRom)
        return ERR_INVALID_ARGS;

    // Send a 0x33
    write_byte(onewire, READ_ROM);
    // Reads the 8 bytes
    for(i=0; i<8; ++i)
    {
        status = read_byte(onewire);
        if(status < 0)
            return status;
        bRom[i] = status;
    }

    return 0;
}


// Do Search: helper.
// Does the search from bit number iFrom.
//  If bRedo, resends the validated sequence contained in static bRom until bit iFrom,
//  then continues the search.
int do_search(OneWire* onewire, unsigned char iFrom, char bRedo, SEARCH_CALLBACK found_rom)
{
    // Least significant bit firts, least significant byte first (little endian)
    static unsigned char bRom[8];
    int i, status;
    unsigned char bit0, bit1;


    if(iFrom > 63)
        return -5;

    if(bRedo || iFrom==0)
    {
        if(! pulseInit(onewire))
            return ERR_NO_PRESENCE;
        // Sends a 0xF0
        write_byte(onewire, SEARCH_ROM); // FIXME: check return value
    }

    if(bRedo)
    {
        for(i=0; i<iFrom; ++i)
        {
            // This is me following a route. Don't check if read is successful: we don't care.
            // If it was a true fail, we will have no response later, and it will be filtered...
            // Otherwise, it was a false negative, and we are glad to pursue...
            read_bit(onewire);
            read_bit(onewire);
            write_bit(onewire, (bRom[i/8]>>(i%8)));
        }
    }
    for(i=iFrom; i<64; ++i)
    {
        status = read_bit(onewire);
        if(status < 0)
            return ERR_MISSED_TSLOT;
        bit0 = status;
        status = read_bit(onewire);
        if(status < 0)
            return ERR_MISSED_TSLOT;
        bit1 = status;

        if(!bit0 && bit1)
        {
            // All devices have a 0, so we select them all
            bRom[i/8] &= ~(1<<(i%8));
            write_bit(onewire, 0); // FIXME: check return value
        }
        else if(bit0 && !bit1)
        {
            // All devices have a 1, so we select them all
            bRom[i/8] |= (1<<(i%8));
            write_bit(onewire, 1); // FIXME: check return value
        }
        else if(!bit0 && !bit1)
        {
            // Both 0 and 1 are found. Our path must be split.
            // First, we continue the branch were a 0 is at rank i
            bRom[i/8] &= ~(1<<(i%8));
            write_bit(onewire, 0); // A write must follow each couple of reads // FIXME: check return value
            status  = 0;
            status |= do_search(onewire, i+1, 0, found_rom);
            // Then, we redo the first part, use a 1 at rank i, and finish the branch
            bRom[i/8] |= (1<<(i%8));
            status |= do_search(onewire, i+1, 1, found_rom);
            // If status < 0, something went wrong, the results may be partial only.
            return (! status) ? 0 : ERR_SEARCH_PARTIAL;
        }
        else // bit0 && bit1
            // Devices are not responding.
            return ERR_NO_PRESENCE;
    }

    // Only reach here if a branch is finished.
    found_rom(bRom);
    //for(i=0; i<8; ++i)
    //    printf("0x%02X ", bRom[i]);
    //printf("\n");

    return 0;
}


LIBDALLAS_API int dallas_rom_search(OneWire* onewire, SEARCH_CALLBACK found_rom)
{
    return do_search(onewire, 0, 0, found_rom);
}

LIBDALLAS_API int dallas_rom_skip(OneWire* onewire, unsigned char operation)
{
    //send a 0xCC
    write_byte(onewire, SKIP_ROM);
    write_byte(onewire, operation);

    if(operation == CONVERT_T || operation == COPY_SCRATCHPAD) //User be careful about pullup
    {
        struct timespec tBegins, tEnd;
        clock_gettime(CLOCK_REALTIME, &tBegins); // This takes ~2µs (the first calls are always longer)
        pin_low(onewire->pullup_port, onewire->pullup_pin);
        WAIT_NANO(tBegins, tEnd, 750000000); /*Blocking here or risk user destroy the BBB?
        waiting tconv for conversion or 10ms for copying scratchpad
        1.5mA current
        scheme is on page 3 of documentation*/
        pin_high(onewire->pullup_port, onewire->pullup_pin);
    }

    return 0;
}

LIBDALLAS_API int dallas_rom_match(OneWire* onewire, unsigned char* rom_code)
{
    int i;
    int status = write_byte(onewire, MATCH_ROM);
    for(i = 0, status = 0; i < 8 && !status; ++i)
    {
        status = write_byte(onewire, rom_code[i]);
    }

    return status;
}

//- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
// Function Commands
//- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

LIBDALLAS_API int dallas_scratchpad_read(OneWire* onewire, unsigned char *scratch, char num)
{
    int i, status;
    status = write_byte(onewire, READ_SCRATCHPAD);

    for(i = 0; i < num && (status>-1); ++i)
    {
        status = read_byte(onewire);
        scratch[i] = (unsigned char)status;
    }

    return (status>-1) ? 0:status;
}

LIBDALLAS_API int dallas_scratchpad_write(OneWire* onewire, unsigned char *data)
{
    int i;
    int status = write_byte(onewire, WRITE_SCRATCHPAD);

    for(i = 0; i < 3 && !status; ++i)
    {
        status = write_byte(onewire, data[i]);
    }

    return status;
}

LIBDALLAS_API int dallas_temperature_read(OneWire* onewire)
{
    int i, status, temperature = 0;
    status = write_byte(onewire, READ_SCRATCHPAD);
    if(status)
        return 0xDEADBEEF;
        //0xB16B00B5

    for(i = 0; i < 2; ++i)
    {
        status = read_byte(onewire);
        if(status < 0)
            return 0xDEADBEEF;

        /*We keep all the bits whatever the resolution is.
        It is user responsibility to remove all undesired bits by reading scratchpad
        to get resolution(9 to 12 bits), LSB are undefined for 9-10-11 bits resolution
        the 4 MSB contains the sign S, positive(0) or negative(1)*/
        temperature += status<<(8*i);
    }

    pulseInit(onewire);
    return temperature;
}

