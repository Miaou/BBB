#!/usr/bin/python3
# Parce que je debug...

import mmap
from binascii import hexlify
import struct


# Retrouve l'adresse du PRU-ICSS
addr = int(open('/sys/class/uio/uio0/maps/map0/addr', 'rb').read(), 16)

mem_fd = open('/dev/mem', 'r+b')
pruicss = mmap.mmap(mem_fd.fileno(), 0x080000, offset=addr)

SHARED  = 0x010000
CONTROL = 0x022000
print("Control: "+'-'.join('{:02x}'.format(a) for a in pruicss[CONTROL:CONTROL+8]))
print("Shared:  "+'-'.join('{:02x}'.format(a) for a in pruicss[SHARED:SHARED+16]))

print("Don't forget to\npruicss.close()\nmem_fd.close()")

MENU = SHARED + 0x20
CFG = 0x026000
INTC = 0x020000

def selectMenu(i,arg):
    """0 is oldest: test sync own measure
    1: wait arg steps*2 between set and clear and set and clear, loops until selectMenu(i!=1)
    2: no 2"""
    pruicss[MENU:MENU+4] = struct.pack('<I', i)
    pruicss[MENU+4:MENU+8] = struct.pack('<I',arg)

print('selectMenu(1,1)')

def read(off,size):
    print(hexlify(pruicss[off:off+size]))
def set(off,data):
    pruicss[off:off+len(data)] = data

print('read(CFG,4)\nset(SHARED,bytes([0,0,0,0])')


def LCG(Xn):
    return (1664525*(Xn+1013904223))&0xFFFFFFFF
def init(N=1):
    set(SHARED+0, struct.pack('<I', N))
    set(SHARED+4, struct.pack('<I', LCG(0)))

def run(N=1):
    N -= 1
    Xn = LCG(0)
    for i in range(N):
        Xn = LCG(Xn)
        set(SHARED+4, struct.pack('<I', Xn))
    return struct.unpack('<I',pruicss[SHARED+8:SHARED+12])
