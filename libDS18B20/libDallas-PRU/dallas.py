#!/bin/usr/python3

# This is the libDallas, PRU edition...
# This was built because the C-version is not executed realtime.
#  It is based on:
#  - pypruss which is based on
#  - am335x_pru_package (prussdrv) which contains PASM
#  PyPRUSS was modified to compile with last prussdrv.

# The goal was initially to build a identical C-interface to the non-PRU edition,
#  but because there is pypruss, why would I build another interface layer ???

# So maybe we will build an identical Python-interface to compare...


# FIXME: this paradigm (returning an error-code instead
#  of a value or using a callback) is very C-like.
#  We should raise exceptions, even if I am not confortable with putting try: except: everywhere...
# See: http://www.jeffknupp.com/blog/2013/02/06/write-cleaner-python-use-exceptions/
# And: http://stackoverflow.com/questions/1630706/best-practice-in-python-for-return-value-on-error-vs-success


import struct
import pypruss
import mmap



# Get PRU's address (shouldn't it be hardware dependent? Is there an equivalent for GPIOs?)
#  and mmap it
addr = int(open('/sys/class/uio/uio0/maps/map0/addr', 'rb').read(), 16)
mem_fd = open('/dev/mem', 'r+b')
pruicss = mmap.mmap(mem_fd.fileno(), 0x080000, offset=addr)

# Useful offsets
SHARED  = 0x010000
CONTROL = 0x022000
ACTION  = 0x010100 # SHARED + 0x100



# ----------
# Dallas API
# ----------

class OneWire:
    nInstances = 0
    def __init__(self, port, pin, bMappedPRU):
        if not OneWire.nInstances:
            # Init PRU
            print('Loading program into PRU')
            pypruss.init();
            pypruss.open(pypruss.PRU_EVTOUT_0)
            pypruss.pruintc_init();
            pypruss.exec_program(0, './dallas.bin')
        OneWire.nInstances += 1
        self.bIsBusy = False # May help in the future
        self.bMappedPRU = bMappedPRU
    def __del__(self):
        OneWire.nInstances -= 1
        if not OneWire.nInstances:
            print('Exiting PRU program')
            pypruss.pru_disable(0)
            pypruss.exit()
    def GetPins(self):
        return self.port, self.pin, self.pullup_port, pullup_pin
    def GetPRU(self):
        return self.bMappedPRU



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
def ActWait(nNano):
    "Waits nNano, and nNano must be >= 100. Resolution is 10 ns"
    n10Nano = nNano//10
    assert n10Nano > 9, 'You can\'t wait less than 10*10ns'
    return Actionify(6, n10Nano, 0)
def WriteActions(prussmem, lActions):
    '''prussmem is a void* mapped to the whole PRU memory
       (starting from 0x00, to more than 0x2000)'''
    assert len(lActions) <= 512
    data = struct.pack('<I', len(lActions)) + b''.join(lActions)
    prussmem[ACTION:ACTION+len(data)] = data
def ReadActions(prussmem, lActions):
    '''Reads prussmem for actions, as ActGet has a return value set in Actionify()[4:8]'''
    lRes = []
    for i,act in enumerate(lActions):
        iAct, iRet = struct.unpack('<II', prussmem[ACTION+4+i*12:ACTION+4+i*12+8])
        if iAct == 5:
            lRes.append(iRet)
    return lRes
def ExecuteActions(prussmem, lActions):
    # Write actions (PRU is in standby)
    WriteActions(prussmem, lActions)
    # Makes the PRU treat actions
    prussmem[SHARED] = 1 # COMMAND_START
    # Waits for completion
    pypruss.wait_for_event(pypruss.PRU_EVTOUT_0)
    pypruss.clear_event(pypruss.PRU_EVTOUT_0, pypruss.PRU0_ARM_INTERRUPT)
    return ReadActions(prussmem, lActions)


# ----------------
# Dallas low-level
# ----------------


# Constants
ROM_SEARCH          = 0xF0
ROM_READ            = 0x33
ROM_MATCH           = 0x55
ROM_SKIP            = 0xCC
ROM_ALARM_SEARCH    = 0xEC
FUNC_CONVERT_T          = 0x44
FUNC_SCRATCHPAD_WRITE   = 0x4E
FUNC_SCRATCHPAD_READ    = 0xBE
FUNC_SCRATCHPAD_copy    = 0x48
FUNC_RECALL_E           = 0xB8
FUNC_READ_POWER_SUPPLY  = 0xB4

# Error codes returned by low-level functions
ERR_OK              = 0
ERR_FAILED          = 0xFFFFFFFF
#ERR_NO_CLOCK        = 0xFFFFFFFE
#ERR_MISSED_TSLOT    = 0xFFFFFFFD
ERR_NO_PRESENCE     = 0xFFFFFFFC
ERR_INVALID_ARGS    = 0xFFFFFFFB
ERR_SEARCH_PARTIAL  = 0xFFFFFFFA



# Now the signal timing sequences, on which libdallas is built.
# There is the pulse_init, the read/write bit, the strong pullup ctrl
#  (and read/write byte, as a gift)
# cf. libDallas/dallas.c (no PRU edition) for more details on the timings and so on...

# Remember : pull up pin must be high when pullup is disabled and low when it is enabled
#  (GPIO sampling is disabled on the onewire pin through another transistor)

# Pulse, to reset sensors, returns presence
def PulseInit(wire):
    port, pin, pport, ppin = wire.GetPins()
    lActs = [ActSetHigh(pport, ppin), ActSetDirOut(pport, ppin), # Pullup pin is reset to high
             ActSetLow(port, pin), ActSetDirOut(port, pin),
             ActWait(480000),
             ActSetDirIn(port, pin),
             ActWait(67000),
             ActGet(port, pin),
             ActWait(480000-67000)]
    maskPres, = ExecuteActions(wire.GetPRU(), lActs)
    # maskPres should be 1<<mask_of_pin if not null
    return maskPres != 0



def WriteBit(wire, bBit):
    port, pin, pport, ppin = wire.GetPins()
    lActs = [ActSetLow(port, pin), ActSetDirOut(port, pin),
             ActWait(2000)]
    if bBit:
        lActs.append(ActSetDirIn(port, pin))
    lActs += [ActWait(75000-2000),
              ActSetDirIn(port, pin),
              ActWait(10000)] # 10µ, just to be sure (needs > 1µ)
    ExecuteActions(wire.GetPRU(), lActs)


# Waits might be tweaked with an oscillo:
#  First wait must be > 1µs
#  Second wait must be < 15µs-first_wait
#  Total slot must be > 60µs+1µs before next slot
def ReadBit(wire):
    port, pin, pport, ppin = wire.GetPins()
    lActs = [ActSetLow(port, pin), ActSetDirOut(port, pin),
             ActWait(1500),
             ActSetDirIn(port, pin),
             ActWait(13000),
             ActGet(port, pin),
             ActWait(50000)]
    maskPres, = ExecuteActions(wire.GetPRU(), lActs)
    return maskPres != 0
    

# ---
# Low-level Wrappers

def WriteByte(wire, bByte):
    'bByte can be an int() or a bytes()'
    assert isinstance(bByte, (bytes,int))
    by = bByte if isinstance(int) else bByte[0]
    for i in range(8):
        WriteBit(wire, (by>>i))

def ReadByte(wire):
    'Returns an int'
    by = 0
    for i in range(8):
        by += (ReadByte(wire)<<i)
    return by


# ---
# Dallas ROM commands
# (ROM commands do their own PulseInit and might return ERR_NO_PRESENCE)

def DallasRomRead(wire):
    if not pulseInit(wire):
        return ERR_NO_PRESENCE
    WriteByte(wire, ROM_READ)
    
    lB = bytearray()
    for i in range(8):
        lB.append(ReadByte(wire))

    return bytes(lB)


def DallasRomSearch(wire, FoundRom):
    'Callback is a f(rom) where rom is a bytes() of length 8'
    # Stores traces which ends are to be explored again in the binary tree
    #  So the algorithm begins knowing nothing, and this is the trace of lenght 0
    lToRedo = [ [] ]
    while lToRedo:
        if not PulseInit(wire):
            return ERR_NO_PRESENCE
        WriteByte(wire, ROM_SEARCH)
        
        currTrace = lToRedo.pop()
        for bi in currTrace:
            # We don't check errors, as we are re-doing an already known path. Be confident.
            ReadBit(wire)
            ReadBit(wire)
            WriteBit(wire)
        for i in range(len(currTrace), 64):
            bit0 = ReadBit(wire)
            bit1 = ReadBit(wire)
            if (not bit0) and bit1:
                currTrace.append(0)
                WriteBit(wire, 0)
            elif bit0 and (not bit1):
                currTrace.eppend(1)
                WriteBit(wire, 1)
            elif (not bit0) and (not bit1):
                # Creates an alternative trace.
                # Continues current trace with a 0
                # Appends alternative trace with a 1 and put it in lToRedo so it is done next time.
                altTrace = currTrace[:]
                currTrace.append(0)
                WriteBit(wire, 0)
                altTrace.append(1)
                lToRedo.append( altTrace )
            else:
                return ERR_SEARCH_PARTIAL # FIXME: unify error-code with libDallas-C
        
        # Convert trace to bytes()
        lBy = []
        for i in range(8):
            by = 0
            for j in range(8): # FIXME: there should be a more elegant way to do this...
                by += (currTrace[i*8+j]<<j)
            lBy.append(by)
        FoundRom(bytes(lBy))
    return ERR_OK


def DallasRomSkip(wire):
    if not pulseInit(wire):
        return ERR_NO_PRESENCE
    WriteByte(wire, ROM_SKIP)


def DallasRomMatch(wire, rom):
    '''rom must be a list(integer) or a bytes() or compatible
    LSB must be first (same order as read)'''
    if not pulseInit(wire):
        return ERR_NO_PRESENCE
    WriteByte(wire, ROM_MATCH)
    for by in rom:
        WriteByte(wire, by)


def DallasRomAlarmSearch(wire):
    raise NotImplementedError('Not yet')


# ---
# Dallas functions

FUNC_CONVERT_T          = 0x44
FUNC_SCRATCHPAD_WRITE   = 0x4E
FUNC_SCRATCHPAD_copy    = 0x48
FUNC_SCRATCHPAD_READ    = 0xBE
FUNC_RECALL_E           = 0xB8
FUNC_READ_POWER_SUPPLY  = 0xB4 # Not in the "parasite-only" reference. Should be tester with them.

def DallasFuncConvertT(wire):
    # Prepare pullup actions
    port, pin, pport, ppin = wire.GetPins()
    lActs = [ActSetLow(pport, ppin), ActSetDirOut(pport, ppin),
             ActWait(750000000),
             ActSetDirOut(pport, ppin), ActSetHigh(pport, ppin)]
    
    WriteByte(wire, FUNC_CONVERT_T)
    # Here, there is a temporal gap, the sensor might begin the conversion before
    #  we have time to raise the pullup. That ain't good...
    # Fixing it cleanly requires big changes in the lib, so...
    ExecuteActions(wire.GetPRU(), lActs)


def DallasFuncScratchpadRead(wire):
    WriteByte(wire, FUNC_SCRATCHPAD_READ)
    return bytes(ReadByte(wire)[0] for i in range(9))

def DallasFuncScratchpadWrite(wire, buf):
    '''Writes Alarm temps high and low and configuration
    ALL 3 BYTES MUST BE WRITTEN'''
    assert len(buf) == 3, 'Tech ref says there must be 3 bytes, or data may get corrupted'
    WriteByte(wire, FUNC_SCRATCHPAD_WRITE)
    for by in buf:
        WriteByte(wire, by)
    
def DallasFuncScratchpadCopy(wire):
    # Same comments as DallasFuncConvertT
    port, pin, pport, ppin = wire.GetPins()
    lActs = [ActSetLow(pport, ppin), ActSetDirOut(pport, ppin),
             ActWait(10000000),
             ActSetDirOut(pport, ppin), ActSetHigh(pport, ppin)]
    WriteByte(wire, FUNC_SCRATCHPAD_COPY)
    ExecuteActions(wire.GetPRU(), lActs)
    
def DallasFuncRecallE(wire):
    WriteByte(wire, FUNC_RECALL_E)

def DallasFuncReadPowerSupply(wire):
    WriteByte(wire, FUNC_RECALL_E)
    return ReadBit(wire)







