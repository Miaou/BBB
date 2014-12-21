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



