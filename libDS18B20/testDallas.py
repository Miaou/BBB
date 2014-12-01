#!/usr/bin/python3

# Du coup, on peut se mettre en Python3...
# Phase de test, on organisera en classes plus tard...

import ctypes as c
from binascii import hexlify


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

# Test new read rom (stress test)
if False:
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

# Test search rom
if True:
    sRoms = set()
    # Fonction qui va être appelée par le module quand on trouve une ROM (oui, le C peut appeler une fonciton Python sans le savoir, c'est assez puissant...)
    def foundROM(sRoms,ptr):
        rom = hexlify( c.string_at(ptr, 8) )
        if rom not in sRoms:
            sRoms.add(rom)
            print(rom)
    # On se donne 10 essais, parce que c'est relou ces bugs perpet
    for i in range(10):
        if not lib.dallas_rom_search(9, 13, c.CFUNCTYPE(None, c.c_void_p)(
                                            lambda rom:foundROM(sRoms,rom))):
            break
    


lib.dallas_free()

