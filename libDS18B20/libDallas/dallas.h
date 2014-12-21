#ifndef LIBDALLAS_H
#define LIBDALLAS_H

#include <time.h>
#include <stdio.h>
#include "BBBiolib.h"

#define LIBDALLAS_API __attribute__((__visibility__("default")))

/*List of all DS18B.. commands*/

#define SEARCH_ROM   0xF0
#define READ_ROM     0x33
#define MATCH_ROM    0x55
#define SKIP_ROM     0xCC
#define ALARM_SEARCH 0xEC
#define CONVERT_T    0x44
#define WRITE_SCRATCHPAD 0x4E
#define READ_SCRATCHPAD  0xBE
#define COPY_SCRATCHPAD  0x48
#define RECALL_E         0xB8
#define READ_POWER_SUPPLY 0xB4


/* List of errors */
#define ERR_OK              0
//#define ERR_DIFF_TOO_BIG    0xDEADBEEF // Must be between 1000000000 (0x3B9ACA00) and -1000000000 (0xC4653600)
#define ERR_DIFF_TOO_BIG    0xAC1DFOOD
#define ERR_FAILED          0xFFFFFFFF
#define ERR_NO_CLOCK        0xFFFFFFFE
#define ERR_MISSED_TSLOT    0xFFFFFFFD
#define ERR_NO_PRESENCE     0xFFFFFFFC
#define ERR_INVALID_ARGS    0xFFFFFFFB
#define ERR_SEARCH_PARTIAL  0xFFFFFFFA


typedef struct OneWire OneWire;
/* Represents a OneWire pin with a strong pullup pin
because 3.3V is not enough, we use another pin as strong pullup*/
struct OneWire
{
    char port;
    char pin;
    char pullup_port;
    char pullup_pin;
};

/*Initialization and termination*/
LIBDALLAS_API int dallas_init(void);
LIBDALLAS_API int dallas_free(void);


/*Communication : Writing and reading data*/
LIBDALLAS_API int pulseInit(OneWire* onewire);
LIBDALLAS_API int write_bit(OneWire* onewire, char bit);
LIBDALLAS_API int read_bit(OneWire* onewire);
LIBDALLAS_API int write_byte(OneWire* onewire, unsigned char by);
LIBDALLAS_API int read_byte(OneWire* onewire);


/*ROM commands */
typedef void (*SEARCH_CALLBACK)(unsigned char *);
LIBDALLAS_API int dallas_rom_read(OneWire* onewire, unsigned char *bRom);
LIBDALLAS_API int dallas_rom_search(OneWire* onewire, SEARCH_CALLBACK found_rom);
LIBDALLAS_API int dallas_rom_skip(OneWire* onewire, unsigned char operation);
LIBDALLAS_API int dallas_rom_match(OneWire* onewire, unsigned char* rom_code);

/*DS18B20 function commands*/
LIBDALLAS_API int dallas_scratchpad_write(OneWire* onewire, unsigned char *data);
LIBDALLAS_API int dallas_scratchpad_read(OneWire* onewire, unsigned char *scratch, char num);
LIBDALLAS_API int dallas_temperature_read(OneWire* onewire);


#endif
