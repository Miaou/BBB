#!/usr/bin/python3

# Du coup, on peut se mettre en Python3...

import ctypes as c


lib = c.cdll.LoadLibrary('./libDallas/libDallas.so')
lib.dallas_init()


#for i in range(10):
#    print(lib.pulseInit(9,13))

# Test Read ROM
l = []
if lib.pulseInit(9,13):
    lib.write_byte(9,13,0x33)
    for i in range(8): # Read 8 bytes
        l.append(lib.read_byte(9,13))

lib.dallas_free()

print(l)
