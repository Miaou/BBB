#
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
print "Control: "+'-'.join(hexlify(a) for a in pruicss[CONTROL:CONTROL+8])
print "Shared:  "+'-'.join(hexlify(a) for a in pruicss[SHARED:SHARED+16])

print "Don't forget to\npruicss.close()\nmem_fd.close()"

MENU = SHARED + 0x20

def selectMenu(i,arg):
    """0 is oldest: test sync own measure
    1: wait arg steps*2 between set and clear and set and clear, loops until selectMenu(i!=1)
    2: no 2"""
    pruicss[MENU:MENU+4] = struct.pack('<I', i)
    pruicss[MENU+4:MENU+8] = struct.pack('<I',arg)

print 'selectMenu(0)'
