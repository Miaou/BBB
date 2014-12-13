#!/usr/bin/python3

# Du coup, on peut se mettre en Python3...
# Phase de test, on organisera en classes plus tard...

#La rom contient 64bits, les 8bits LSB sont egaux a 28h
#les 48 suivants contiennent l'ID unique
#les 8 derniers sont un crc calcule sur les 56 premiers bits

SEARCH_ROM   =   0xF0
READ_ROM     =   0x33
MATCH_ROM    =   0x55
SKIP_ROM     =   0xCC
ALARM_SEARCH =   0xEC
CONVERT_T    =   0x44
WRITE_SCRATCHPAD =  0x4E
READ_SCRATCHPAD  =  0xBE
COPY_SCRATCHPAD  =  0x48
RECALL_E         =  0xB8
READ_POWER_SUPPLY = 0xB4

import ctypes as c
from binascii import hexlify


lib = c.cdll.LoadLibrary('./libDallas/libDallas.so')
lib.dallas_init()

class Sensor :
#La rom contient 64bits, les 8bits LSB sont egaux a 28h
#les 48 suivants contiennent l'ID unique
#les 8 derniers sont un crc calcule sur les 56 premiers bits 
#pour la commande lib.dallas_match_rom, il faut faire correspondre les 64bits
    """Represents a sensor on a OneWire pin"""
    def __init__(self, wire) :
        self.ID = 0
        self.resolution = 0
        self.wire = wire
       
    def GetTemperature(self) :
        lib.pulseInit(self.wire.port, self.wire.pin)
        lib.dallas_match_rom(self.wire.port, self.wire.pin, self.ID)
        return lib.dallas_read_temperature()

    def ConvertTemperature(self) :
        lib.pulseInit(self.wire.port, self.wire.pin)
        lib.
class OneWire :
#Toutes les communications commencent par lib.pulseInit()
#suivie d'une commande rom lib.dallas_rom_cmd()
#suivie d'une fonction du capteur lib.write_byte()
#                           ou    lib.dallas_scratchpad_write/read
#                           ou    lib.dallas_temperature_read
#disponible en haut(les fonctions)
    """Represents a OneWire pin. Can have several sensors on the same
    wire.
    Attributes : -port
                 -pin
                 -lSensors """
    def __init__(self, port, pin) :
        self.port = port
        self.pin = pin
        self.lSensors = []
        lib.dallas_init()
        lib.pulseInit(port, pin)
        def foundROM(ptr):
            sRom = set()
            rom = c.string_at(ptr, 8)
            sRom.add(rom)
            print(hexlify(rom))
        callback = c.CFUNCTYPE(None, c.c_void_p)(foundROM)
        for i in range(10):
            if not lib.dallas_rom_search(port, pin, callback):
                print("Success reading !!")
                break
        
        #quel est le format de callback??

    def __del__(self) :
        lib.dallas_free()



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
    def foundROM(ptr):
        rom = hexlify( c.string_at(ptr, 8) )
        if rom not in sRoms:
            sRoms.add(rom)
            print(rom)
    callback = c.CFUNCTYPE(None, c.c_void_p)(foundROM)
    # On se donne 10 essais, parce que c'est relou ces bugs perpet
    for i in range(10):
        #if not lib.dallas_rom_search(9, 13, c.CFUNCTYPE(None, c.c_void_p)(
        #                                    lambda rom:foundROM(sRoms,rom))):
        retCode = lib.dallas_rom_search(9, 13, callback)
        if retCode == -4:
            print('No one answered, no device plugged ?')
            break
        elif retCode == 0:
            print('Found in {} tr{}'.format(i+1, 'y' if not i else 'ies'))
            break
    


lib.dallas_free()

