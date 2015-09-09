#!/usr/bin/python3
# Debugging the PRU by hand: accessing its memory through the mapped memory interface.

import mmap
from binascii import hexlify
import struct


# Retrouve l'adresse du PRU-ICSS
addr = int(open('/sys/class/uio/uio0/maps/map0/addr', 'rb').read(), 16)

mem_fd = open('/dev/mem', 'r+b')
pruicss = mmap.mmap(mem_fd.fileno(), 0x080000, offset=addr)

SHARED  = 0x010000
CONTROL = 0x022000
P_HEADER = 0x010100
P_SERVOS = 0x01010C
MASK_FETCH = 0x1000
CFG = 0x026000

print("Control: "+'-'.join('{:02x}'.format(a) for a in pruicss[CONTROL:CONTROL+8]))
print("Shared:  "+'-'.join('{:02x}'.format(a) for a in pruicss[SHARED:SHARED+16]))

print("Don't forget to\npruicss.close()\nmem_fd.close()")

def read(off,size):
    print(hexlify(pruicss[off:off+size]))
def set(off,data):
    pruicss[off:off+len(data)] = data

print('read(CONTROL,16)\nset(SHARED,bytes([0,0,0,0])')
