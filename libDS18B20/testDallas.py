#!/usr/bin/python3

# Du coup, on peut se mettre en Python3...

import ctypes as c


lib = c.cdll.LoadLibrary('./libDallas/libDallas.so')
lib.dallas_init()


#for i in range(10):
#    print(lib.pulseInit(9,13))

# Test Read ROM
if False:
    l = []
    if lib.pulseInit(9,13):
        lib.write_byte(9,13,0x33)
        for i in range(8): # Read 8 bytes
            l.append(lib.read_byte(9,13))
    print(l)

# Test new read rom
if True:
    n = 0
    for i in range(1000):
        l = (c.c_ubyte*8)()
        if lib.dallas_rom_read(9, 13, c.byref(l)) == 0:
            #print(list(l))
            n += 1
        else:
            #print('Read failed')
            pass
    print(n)

lib.dallas_free()

