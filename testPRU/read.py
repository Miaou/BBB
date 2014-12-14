#
# Parce que je debug...

import mmap
from binascii import hexlify


# Retrouve l'adresse du PRU-ICSS
addr = int(open('/sys/class/uio/uio0/maps/map0/addr', 'rb').read(), 16)

mem_fd = open('/dev/mem', 'r+b')
pruicss = mmap.mmap(mem_fd.fileno(), 0x080000, offset=addr)

SHARED  = 0x010000
CONTROL = 0x022000
print "Control: "+'-'.join(hexlify(a) for a in pruicss[CONTROL:CONTROL+8])
print "Shared:  "+'-'.join(hexlify(a) for a in pruicss[SHARED:SHARED+16])

print "Don't forget to\npruicss.close()\nmem_fd.close()"
