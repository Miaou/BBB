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

/*What's best? enumeration or definition?
enum Operation {
    SEARCH_ROM = 0xF0,
    READ_ROM    = 0x33,
};*/

/*Initialization and termination*/
LIBDALLAS_API int dallas_init(void);
LIBDALLAS_API int dallas_free(void);


/*Communication : Writing and reading data*/
LIBDALLAS_API int pulseInit(char port, char pin);
LIBDALLAS_API int write_bit(char port, char pin, char bit);
LIBDALLAS_API int read_bit(char port, char pin);
LIBDALLAS_API int write_byte(char port, char pin, unsigned char by);
LIBDALLAS_API int read_byte(char port, char pin);


/*ROM commands */
typedef void (*SEARCH_CALLBACK)(unsigned char *);
LIBDALLAS_API int dallas_rom_read(char port, char pin, unsigned char *bRom);
LIBDALLAS_API int dallas_rom_search(char port, char pin, SEARCH_CALLBACK found_rom);
LIBDALLAS_API int dallas_skip_rom(char port, char pin, unsigned char operation);

/*DS18B20 function commands*/
LIBDALLAS_API int dallas_write_scratchpad(char port, char pin, unsigned char *data);
LIBDALLAS_API int dallas_read_scratchpad(char port, char pin, unsigned char *scratch);
LIBDALLAS_API int dallas_read_temperature(char port, char pin);


#endif
