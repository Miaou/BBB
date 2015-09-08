#!/usr/bin/python3

# Python "package" to control the servos through the PRU.
# This package uses pypruss (which uses libprussdrv) to load the PRU program into PRU mem
#  and to configure it.

# This is the high-level end of the servos.
# There are, of course, no requirement on which servos are connected where, and so on.

# Time resolution  may be measured with modifications on the PRU part of the program.
# Currently not implemented...
# However, it should very better than 8µs/servo while controlling 18 servos.

# For now, the lib does not store the commands, all the servos has to be set in oneshot



import struct
import pypruss
import mmap
from binascii import hexlify # Printing content of memory (debug)
from config import lServos # Calibrated servos



class PruInterface:
    def __init__(self, sPathBin):
        try:
            addr = int(open('/sys/class/uio/uio0/maps/map0/addr', 'rb').read(), 16)
        except IOError as e:
            print('---> ERROR while opening the pruss memory <---')
            print('Probably there is something wrong with capes (did you "echo BB-BONE-PRU-ACT > /sys/devices/bone_capemgr.9/slots" ?)')
            raise e
        self.sPathBin = sPathBin
        self.mem_fd = open('/dev/mem', 'r+b')
        self.pruicss = mmap.mmap(self.mem_fd.fileno(), 0x080000, offset=addr)
        pypruss.init()
        # Reset is VERY important... otherwise the PRU might start at random
        #pypruss.pru_reset(0) # FAILS! x_x
        self.pruicss[0x022000] = 0 # Manual set 0 to the byte of CONTROL reg in the control regs...
        pypruss.open(pypruss.PRU_EVTOUT_0) # Is this required?
        pypruss.pruintc_init()
        pypruss.exec_program(0, self.sPathBin)
        # Here, PRU is up and running the controls code

    def __del__(self):
        # Hope we get there
        print('Closing the PRU interface')
        pypruss.pru_disable(0) # Does not wait for program to complete, I don't care here
        pypruss.exit()
        self.pruicss.close()
        self.mem_fd.close()

    def getMappedMem(self):
        return self.pruicss
    
    # Usefull offsets
    SHARED   = 0x010000
    CONTROL  = 0x022000
    P_HEADER = 0x010100
    P_SERVOS = 0x01010C
    MASK_FETCH = 0x1000


# GPIO registers base addresses
BASE_ADDR_GPIO = [0x44E07000, 0x4804C000, 0x481AC000, 0x481AE000]
# SOME mapping (port, pin) to (gpiobase, bitmask) when they are in mode 7
# (see a table like http://www.element14.com/community/servlet/JiveServlet/download/76417-112705/pinmux.pdf to find the others)
PORT_TO_MASK = {(8, 7): (BASE_ADDR_GPIO[2], 1<<2),
                (8, 8): (BASE_ADDR_GPIO[2], 1<<3),
                (8, 9): (BASE_ADDR_GPIO[2], 1<<5), # So P8_9 is gpio2_5
                (8, 10): (BASE_ADDR_GPIO[2], 1<<4),
                (8, 11): (BASE_ADDR_GPIO[1], 1<<13),
                (8, 12): (BASE_ADDR_GPIO[1], 1<<12),
                (8, 13): (BASE_ADDR_GPIO[0], 1<<23),
                (8, 14): (BASE_ADDR_GPIO[0], 1<<26),
                (8, 15): (BASE_ADDR_GPIO[1], 1<<15),
                (8, 16): (BASE_ADDR_GPIO[1], 1<<14),
                (8, 17): (BASE_ADDR_GPIO[0], 1<<27),
                (8, 18): (BASE_ADDR_GPIO[2], 1<<1),
                (8, 29): (BASE_ADDR_GPIO[2], 1<<23),
                (8, 30): (BASE_ADDR_GPIO[2], 1<<25),
                (8, 31): (BASE_ADDR_GPIO[0], 1<<10),
                (8, 32): (BASE_ADDR_GPIO[0], 1<<11),
                (8, 33): (BASE_ADDR_GPIO[0], 1<<9),
                (8, 34): (BASE_ADDR_GPIO[2], 1<<17),
                (8, 35): (BASE_ADDR_GPIO[0], 1<<8),
                (8, 36): (BASE_ADDR_GPIO[2], 1<<16),
                (8, 37): (BASE_ADDR_GPIO[2], 1<<14),
                (8, 38): (BASE_ADDR_GPIO[2], 1<<15),
                (8, 39): (BASE_ADDR_GPIO[2], 1<<12),
                (8, 40): (BASE_ADDR_GPIO[2], 1<<13),
                (8, 41): (BASE_ADDR_GPIO[2], 1<<10),
                (8, 42): (BASE_ADDR_GPIO[2], 1<<11),
                (8, 43): (BASE_ADDR_GPIO[2], 1<<8),
                (8, 44): (BASE_ADDR_GPIO[2], 1<<9),
                (8, 45): (BASE_ADDR_GPIO[2], 1<<6),
                (8, 46): (BASE_ADDR_GPIO[2], 1<<7),
                (9, 11): (BASE_ADDR_GPIO[0], 1<<30),
                (9, 12): (BASE_ADDR_GPIO[1], 1<<28),
                (9, 13): (BASE_ADDR_GPIO[0], 1<<31),
                (9, 14): (BASE_ADDR_GPIO[1], 1<<18),
                (9, 15): (BASE_ADDR_GPIO[1], 1<<16),
                (9, 16): (BASE_ADDR_GPIO[1], 1<<19)}


# Now the class that controls our servos...
class ServoController:
    FETCH_NO_CHANGE = 0
    FETCH_CHANGE = 1
    FETCH_QUIT = 2

    def __init__(self, pruface, lCfgServos, tPeriod=20000):
        '''
        pruface is a PruInterface instance
        lCfgServos is a list of ServoConfig which gives pin info of servo[i], as well as its calibration (see config.py)
        tPeriod is the PWM-like period of the signals (in µs)
        '''
        for servo in lCfgServos:
            assert servo.getPort() in PORT_TO_MASK
        self.lCfgServos = lCfgServos[:] # Copy the list content (servos cfg are not copied)
        assert isinstance(pruface, PruInterface)
        self.pruface = pruface
        self.iPeriod = int(tPeriod*200)
        self.struct = struct # Keeps a link to struct because I need it in __del__
        

    def __del__(self):
        # Tells the PRU program to end (optional)
        # Using __del__ to clean out is not a very brilliant idea, as many objects are already deleted
        global ServoController # Pb with order of del
        print('Waiting for the PRU program to self-stop')
        pMem = PruInterface.MASK_FETCH|PruInterface.P_HEADER
        self.pruface.getMappedMem()[pMem:pMem+4] = self.struct.pack('<I', 2)
        # Waits for completion.
        pypruss.wait_for_event(pypruss.PRU_EVTOUT_0)
        pypruss.clear_event(pypruss.PRU_EVTOUT_0, pypruss.PRU0_ARM_INTERRUPT)
        # I don't know why we have to wait and clear 2 times...
        # I thought that there was a delay between the PRU signaled the interrupt and
        #  and the Linux updating the shared mem, but no, you have to wait for event twice...
        pypruss.wait_for_event(pypruss.PRU_EVTOUT_0)
        pypruss.clear_event(pypruss.PRU_EVTOUT_0, pypruss.PRU0_ARM_INTERRUPT)



    def setTimes(self, lTimes, bWait=False):
        '''
        Speaks to the PRU, and writes the times (given in µs, float or int, 0 for no command)
        lTimes must match in size the lCfgServos given to this instance of ServoController
        Optionnally bWait for the PRU to be able to process the setTimes command.
        '''
        assert len(lTimes)==len(self.lCfgServos), "More (or less) commands than known pins, aborting"
        
        # If a write setTimes occurs before PRU had time to fetch the last one, skip or wait!
        prussmem = self.pruface.getMappedMem()
        pMem = PruInterface.MASK_FETCH|PruInterface.P_HEADER
        while True: # I will stop using hideous while-trues when they do a do...while
            iCurStatus, = struct.unpack('<I', prussmem[pMem:pMem+4]) # This value acts as a semaphore...
            if not bWait:
                if iCurStatus != ServoController.FETCH_NO_CHANGE:
                    return # Skip
                break
            elif iCurStatus == ServoController.FETCH_NO_CHANGE:
                break # Has waited until condition's met

        # I create a buffer, then I write it to the PRU.
        # Begins with the header, and then n*servo
        buf = bytearray(struct.pack('<III', ServoController.FETCH_NO_CHANGE, # Writes no change as we must write the whole buffer before telling to take it into account
                                            len(lTimes), self.iPeriod))
        for i,t in enumerate(lTimes):
            assert t>=0 and t*200 < self.iPeriod, 'Invalid specified time: negative or longer than period...'
            base,mask = PORT_TO_MASK[self.lCfgServos[i].getPort()]
            buf += struct.pack('<III', base, mask, int(t*200))
        
        # And writes to the PRU memory
        pMem = PruInterface.MASK_FETCH|PruInterface.P_HEADER
        prussmem[pMem:pMem+len(buf)] = bytes(buf)

        # Now we can tell the PRU that we want it updates the command for the servos
        prussmem[pMem:pMem+4] = struct.pack('<I', ServoController.FETCH_CHANGE)
    

    # TODO: add a way to disable the control of a given servo...
    def setAngles(self, lAngles, bWait=False):
        '''
        Calculates times command corresponding to the given angles for each servo
        lAngles must match in size the lCfgServos given to this instance of ServoController
        Angles are in what-you-unit-you-want, but be consistent
        Optionnally bWait for the PRU to be able to process the setAngles command.
        '''
        assert len(lAngles)==len(self.lCfgServos), "More (or less) commands than known pins, aborting"
        
        #(t1-t0)/(a1-a0)*(a-a0)+t0
        lTimes = [0]*len(lAngles)
        for i,ang in enumerate(lAngles):
            if ang != None:
                lTimes[i] = self.lCfgServos[i].getTime(ang)
        self.setTimes(lTimes, bWait)




# Basic testing, and acts as a usecase
if __name__=='__main__':
    pruface = PruInterface('./servos.bin')
    sctl = ServoController(pruface, lServos, 20000) # 20ms
    sctl.setAngles([None]*18)
    def testLegI(i):
        sctl.setAngles([None]*3*i+[0,5,0]+[None]*3*(6-i-1))


