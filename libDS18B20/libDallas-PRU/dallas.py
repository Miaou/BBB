#!/usr/bin/python3

# This is the libDallas, PRU edition...
# This was built because the C-version is not executed realtime.
#  It is based on:
#  - pypruss which is based on
#  - am335x_pru_package (prussdrv) which contains PASM
#  PyPRUSS was modified to compile with last prussdrv.

# The goal was initially to build a identical C-interface to the non-PRU edition,
#  but because there is pypruss, why would I build another interface layer ???

# So maybe we will build an identical Python-interface to compare...


# Almost-fixed: Returning an error-code instead of a value, or using callbacks, is very C-like.
#  We should raise exceptions, even if I am not confortable with putting try: except: everywhere...
#  And maybe return a list instead of calling callbacks...
# See: http://www.jeffknupp.com/blog/2013/02/06/write-cleaner-python-use-exceptions/
# And: http://stackoverflow.com/questions/1630706/best-practice-in-python-for-return-value-on-error-vs-success


# FIXME: the Dallas API is for now very C-like: a bunch of functions in the
#  global namespace, using a struct as the first argument...
# So current "OneWire" is instead "OneWireHardwareInterface", and a true OneWire should be created.

# Then think about fault tolerance to create more Exceptions, and set behavior of
#  functions such as OneWire.ReadTemperature(): should it print the CRC error, leave it?
#  Be able to continue and raise it again when reads are all done?

# Then Sensor should go out: it uses Dallas, it is not the only thing that might use Dallas' protocol.



import struct
import pypruss
import mmap



# This is low-level stuff, it maybe should be in OneWireHWIface... Maybe.

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
    def __init__(self, port, pin, pullup_port, pullup_pin, bMappedPRU):
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
        self.port, self.pin, self.pullup_port, self.pullup_pin = port, pin, pullup_port, pullup_pin
        self._keepalive = OneWire # Avoids that the OneWire class is deleted before its instances...
        self.dSensors = {}
    def __del__(self):
        global OneWire # Hack: sometimes OneWire is deleted before self
        if not OneWire:
            OneWire = self._keepalive
        OneWire.nInstances -= 1
        if not OneWire.nInstances:
            print('Exiting PRU program')
            pypruss.pru_disable(0)
            pypruss.exit()
    def GetPins(self):
        return self.port, self.pin, self.pullup_port, self.pullup_pin
    def GetPRU(self):
        return self.bMappedPRU

    # --------------------------
    # Here is the "true" OneWire
    def CreateSensor(self, rom):
        if rom in self.dSensors:
            return
        self.dSensors[rom] = Sensor(rom, self)
    #def ReadSoleRom(self)
    def SearchMoreRoms(self):
        DallasRomSearch(self, lambda rom:self.CreateSensor(rom))
    def PrintSensors(self):
        "Display sensor list and last temperatures"
        print('Sensor list')
        for rom in self.dSensors:
            print(' - {}: {}°C'.format(hexlify(rom), self.dSensors[rom].GetTemperature()))
    def ConvertTemperatures(self):
        "Starts the temperature conversion for all sensors (skip rom)"
        DallasRomSkip(self)
        DallasFuncConvertT(self)
    def ReadTemperatures(self):
        "Reads the temperature for all known sensors (wrapper for Sensor.ReadTemperature)"
        for sens in self.dSensors.values():
            sens.ReadTemperature()


class Sensor:
    def CheckCRC(buf):
        poly = 0x8C
        s = 0
        for by in buf:
            for i in range(8):
                r =  (s&0x01)
                f = (by&0x01)
                by >>= 1
                xor = poly if (r^f) else 0
                s = ((s>>1) ^ xor)&0xFF
        return s==0
    def __init__(self, rom, wire):
        "rom should be a bytes (or any iterable iterating on 8-ints)"
        assert Sensor.CheckCRC(rom), "CRC on serial number failed"
        self.rom = rom
        self.wire = wire
        self.iLastTemp = None

    def ConvertTemperature(self):
        "Can be skiped if a ConvertTemperature() is done on the OneWire instead"
        DallasRomMatch(self.wire, self.rom)
        DallasFuncConvertT(self.wire)
    def ReadTemperatureRaw(self):
        "Reads the scratchpad and returns temperature"
        DallasRomMatch(self.wire, self.rom)
        buf = DallasFuncScratchpadRead(self.wire)
        assert Sensor.CheckCRC(buf), "CRC on read scratchpad failed (was {})".format(hexlify(buf))
        iTemp, = struct.unpack('<h', buf[:2])
        # It is tempting to say that if iTemp == 0x0550 (85°C), then it is the reset value
        #  and measure should be discarded. However, DS18B20 can measure up to 100°C, so...
        #  and it is specific to DS18B20, not included in Dallas
        self.iLastTemp = iTemp
        return iTemp
    def ReadTemperature(self):
        return GetTemperature()
    def GetTemperature(self):
        "Returns the last result of ReadTemperature()"
        return self.iLastTemp/16.
    def GetTemperatureRaw(self):
        "Returns the last result of ReadTemperatureRaw()"
        return self.iLastTemp


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
    # Waits for completion.
    pypruss.wait_for_event(pypruss.PRU_EVTOUT_0)
    pypruss.clear_event(pypruss.PRU_EVTOUT_0, pypruss.PRU0_ARM_INTERRUPT)
    # I don't know why we have to wait and clear 2 times...
    # I thought that there was a delay between the PRU signaled the interrupt and
    #  and the Linux updating the shared mem, but no, you have to wait for event twice...
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

## Error codes returned by low-level functions
# Let's try the Easier to Ask for Forgiveness than Permission...
# Errors raised by low-level IO
class NoResponseError(Exception): pass
class SearchPartialError(Exception): pass


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
    if maskPres:
        raise NoResponseError('No DS18B20x answered the reset pulse.')



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
    by = bByte if isinstance(bByte, int) else bByte[0]
    for i in range(8):
        WriteBit(wire, ((by>>i)&1))

def ReadByte(wire):
    'Returns an int'
    by = 0
    for i in range(8):
        by += (ReadBit(wire)<<i)
    return by


# ---
# Dallas ROM commands
# (ROM commands do their own PulseInit and might return ERR_NO_PRESENCE)

def DallasRomRead(wire):
    PulseInit(wire)
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
        PulseInit(wire)
        WriteByte(wire, ROM_SEARCH)
        
        currTrace = lToRedo.pop()
        for bi in currTrace:
            ReadBit(wire)
            ReadBit(wire)
            WriteBit(wire, bi)
        for i in range(len(currTrace), 64):
            bit0 = ReadBit(wire)
            bit1 = ReadBit(wire)
            if (not bit0) and bit1:
                currTrace.append(0)
                WriteBit(wire, 0)
            elif bit0 and (not bit1):
                currTrace.append(1)
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
                raise SearchPartialError('Both bits were set: no one is responding anymore')
        
        # Convert trace to bytes()
        lBy = []
        for i in range(8):
            by = 0
            for j in range(8): # FIXME: there should be a more elegant way to do this...
                by += (currTrace[i*8+j]<<j)
            lBy.append(by)
        FoundRom(bytes(lBy))


def DallasRomSkip(wire):
    PulseInit(wire)
    WriteByte(wire, ROM_SKIP)


def DallasRomMatch(wire, rom):
    '''rom must be a list(integer) or a bytes() or compatible
    LSB must be first (same order as read)'''
    PulseInit(wire)
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
    return bytes(ReadByte(wire) for i in range(9))

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




if __name__=='__main__':
    from binascii import hexlify
    owire = OneWire(9,13, 9,14, pruicss)
    owire.SearchMoreRoms()
    print('Found {} sensors'.format(len(owire.dSensors)))
    owire.ConvertTemperatures()
    owire.ReadTemperatures()
    owire.PrintSensors()
    # TODO: test le read Power supply pour les DS18B20-P et pour les autres...






