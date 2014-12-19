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
import time


lib = c.cdll.LoadLibrary('./libDallas/libDallas.so')
lib.dallas_init()

class Sensor :
#La rom contient 64bits, les 8bits LSB sont egaux a 28h
#les 48 suivants contiennent l'ID unique
#les 8 derniers sont un crc calcule sur les 56 premiers bits 
#pour la commande lib.dallas_match_rom, il faut faire correspondre les 64bits
    """Represents a sensor on a OneWire pin"""
    def __init__(self, ID, wire) :
        self.ID = ID
        self.resolution = 0
        self.wire = wire
    
    def checkID(ID) :
        #implementation du CRC
        poly = 0x8C
        s = 0
        for by in list(ID):
            for i in range(8):
                r =  (s&0x01)
                f = (by&0x01)
                by >>= 1
                xor = poly if (r^f) else 0
                s = ((s>>1) ^ xor)&0xFF
        return s==0
        

    def GetTemperature(self) :
        lib.pulseInit(c.byref(self.wire))
        cBuf = c.create_string_buffer(self.ID, size=8)
        #a = lib.dallas_rom_match(c.byref(self.wire), c.byref(cBuf))
        #return a, lib.dallas_temperature_read(c.byref(self.wire))
        a = lib.dallas_rom_match(c.byref(self.wire), c.byref(cBuf))
        scratchBuf = c.create_string_buffer(9)
        b = lib.dallas_scratchpad_read(c.byref(self.wire), c.byref(scratchBuf), 9)
        print(a,b,hexlify(scratchBuf.raw))
        return a, b, scratchBuf.raw

    def ConvertTemperature(self) :
        lib.pulseInit(c.byref(self.wire))
        lib.dallas_rom_match(c.byref(self.wire), self.ID)
        lib.write_byte(c.byref(self.wire), CONVERT_T)
        #must enable strong pullup

class OneWire(c.Structure) :
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
    _fields_ = [("port", c.c_char),
                ("pin", c.c_char),
                ("pullup_port", c.c_char),
                ("pullup_pin", c.c_char)]
    def __init__(self, port, pin, pullup_port, pullup_pin) :
        self.port = port
        self.pin = pin
        self.pullup_port = pullup_port
        self.pullup_pin = pullup_pin
        self.lSensors = []
        lib.dallas_init()
        #lib.pulseInit(port, pin)
        sRoms = set()
        def foundROM(ptr):
            rom = c.string_at(ptr, 8)
            sRoms.add(rom)
            print(hexlify(rom))
        callback = c.CFUNCTYPE(None, c.c_void_p)(foundROM)
        for i in range(10):
            if not lib.dallas_rom_search(c.byref(self), callback):
                print("Success, {} reading{}!!".format(i, 's' if i!=1 else ''))
                break
        
        #quel est le format de callback??
        #mauvaise question, comment identifier les bons IDs 64bits des faux?
        for rom in sRoms:
            if Sensor.checkID(rom):
                self.lSensors.append(Sensor(rom, self))

    #def __del__(self) :
    #    lib.dallas_free()

    def AllConvertTemperature(self) :
        lib.pulseInit(c.byref(self))
        return lib.dallas_rom_skip(c.byref(self), CONVERT_T)
        #must enable strong pullup
        #this is now done in C library





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
if False:
    sRoms = set()
    # Fonction qui va être appelée par le module quand on trouve une ROM (oui, le C peut appeler une fonciton Python sans le savoir, c'est assez puissant...)
    def foundROM(ptr):
        rom = c.string_at(ptr, 8)
        if rom not in sRoms:
            sRoms.add(rom)
            print(hexlify(rom))
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


if True:
    wire = OneWire(9,13,9,14)
    wire.AllConvertTemperature()
    buf = (c.c_byte*9)()
    #lib.dallas_rom_match(c.byref(wire), c.byref(buf), 9)
    #time.sleep(1)
    lTemp = []
    for sensor in wire.lSensors :
        lTemp.append(sensor.GetTemperature())

    print(lTemp)
 

#lire scratchpad :
#lib.dallas_scratchpad_read(c.byref(wire), buf*9, 9
#lib.dallas_free()
