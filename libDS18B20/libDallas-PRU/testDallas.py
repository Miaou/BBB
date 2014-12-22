# Testing PyPRUSS 3.2 btw...

import pypruss
import mmap
from binascii import hexlify
import struct


# Get PRU's address and mmap it
addr = int(open('/sys/class/uio/uio0/maps/map0/addr', 'rb').read(), 16)
mem_fd = open('/dev/mem', 'r+b')
pruicss = mmap.mmap(mem_fd.fileno(), 0x080000, offset=addr)

# Accessors to the mmap
def read(off,size):
    return pruicss[off:off+size]
def pri(off,size):
    print(hexlify(pruicss[off:off+size]))
def write(off,data):
    pruicss[off:off+len(data)] = data


# Useful offsets
SHARED  = 0x010000
CONTROL = 0x022000
ACTION  = 0x010100 # SHARED + 0x100


# Init PRU
pypruss.init();
pypruss.open(pypruss.PRU_EVTOUT_0)
pypruss.pruintc_init();


def load(path):
    print('Loading program')
    pypruss.exec_program(0, path)
def end():
    pypruss.pru_disable(0)
    pypruss.exit()


print("Control: "+'-'.join('{:02x}'.format(a) for a in pruicss[CONTROL:CONTROL+8]))
print("Shared:  "+'-'.join('{:02x}'.format(a) for a in pruicss[SHARED:SHARED+16]))
print("\nDon't forget to\nend()\npruicss.close()\nmem_fd.close()")



# ----------
# Action API
# ----------

# GPIO registers base addresses
pBaseGPIO = [0x44E07000, 0x4804C000, 0x481AC000, 0x481AE000]
# Some (port, pin) -> (gpio, mask) mapping when they are in pinmux mode 7
# (thanks http://www.element14.com/community/message/76416/l/re-pinmux--enabling-spi#76416)
dPort2Reg = {(9, 13): (pBaseGPIO[0], 1<<31),
             (9, 14): (pBaseGPIO[1], 1<<18)}
# Action API
def Actionify(cmd, gpio, mask):
    return struct.pack('<III', cmd, gpio, mask)
def ActSetDirOut(port, pin):
    return Actionify(1, *dPort2Reg[port,pin])
def ActSetDirIn(port, pin):
    return Actionify(2, *dPort2Reg[port,pin])
def ActSetLow(port, pin):
    return Actionify(3, *dPort2Reg[port,pin])
def ActSetHigh(port, pin):
    return Actionify(4, *dPort2Reg[port,pin])
def ActGet(port, pin):
    return Actionify(5, *dPort2Reg[port,pin])
def ActWait(n10Nano):
    "Waits n10Nano * 10ns, and n10Nano must be >= 10"
    assert n10Nano > 9, 'You can\'t wait less than 10*10ns'
    return Actionify(6, n10Nano, 0)
def WriteActions(pruicss, lActions):
    assert len(lActions) <= 512
    data = struct.pack('<I', len(lActions)) + b''.join(lActions)
    pruicss[ACTION:ACTION+len(data)] = data


#if True:
#    pypruss.wait_for_event(pypruss.PRU_EVTOUT_0)
#    pypruss.clear_event(pypruss.PRU_EVTOUT_0, pypruss.PRU0_ARM_INTERRUPT)
