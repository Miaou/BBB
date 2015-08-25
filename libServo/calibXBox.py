#!/usr/bin/python3

# Calibration of the legs using the XBox Controller (see xboxdrv in the ../doc) and evdev
# Small tool provided more than anything else "as-is", just for fun...


from config import lServos
from servos import PruInterface, ServoController
import time
from joy import dev, ecodes, getAxesValues
import curses



def wrap_curses(func):
    def wrap(*args, **kwargs):
        return curses.wrapper(func, *args, **kwargs)
    return wrap

@wrap_curses
def xpadMenu(stdscr, dev):
    class Status:
        def __init__(self):
            self.iCurLeg = -1
            self.iCurJoint = 0
            self.iCurPosition = 0
            self.tCurCalib = ()
            self.lCurServos = []
            #self.t0 = time.time()
            self.bSetAngles = False
            self.fCurShift = 0 # Be warn that femur shift should not be changed (haha, "be warn", in a comment, ...)
            self.nextLeg()
        def nextLeg(self, iShift=1):
            self.iCurLeg = (self.iCurLeg+iShift)%6
            self.lCurServos = lServos[self.iCurLeg*3:self.iCurLeg*3+3] # GLOBAL VAR
            self.iCurJoint = -1
            self.iCurPosition = -1
            self.nextPosition()
            self.nextJoint()
        def nextJoint(self):
                #self.lCurServos[self.iCurJoint].tCalib = self.tCurCalib
            self.iCurJoint = (self.iCurJoint+1)%3
            self.tCurCalib = self.lCurServos[self.iCurJoint].tCalib
            self.fCurShift = self.lCurServos[self.iCurJoint].fShift
        def nextPosition(self):
            self.iCurPosition = (self.iCurPosition+1)%5
        def updateAngles(self):
            fShift = self.lCurServos[2].fShift
            if self.iCurPosition in (1,3):
                self.lCurServos[2].fShift = 0
            llAngles = [(None,90,90), (None,0,0), (None, 0, 0),
                        (None,90,180), (None,-90,0)]
            #print(self.lCurServos[2].fShift)
            lAngles = (None,)*3*self.iCurLeg + llAngles[self.iCurPosition] + (None,)*3*(6-self.iCurLeg-1)
            if self.bSetAngles:
                # Femur shift cannot be changed...
                sctl.setAngles(lAngles) # GLOBAL VAR
            else:
                sctl.setAngles([None]*18)
            if self.iCurPosition in (1,3):
                self.lCurServos[2].fShift = fShift
            #if time.time()-self.t0>1:
            #    print('#DBG#, angles: {}'.format(lAngles))
            #    self.t0 += 1
        def changeAngles(self, vitMin,vitMax):
            vMin,vMax = self.tCurCalib
            self.tCurCalib = (vMin+vitMin, vMax+vitMax)
            self.lCurServos[self.iCurJoint].tCalib = self.tCurCalib
            self.updateAngles()
            #if time.time()-self.t0>1:
            #    print('#DBG#, calib: {}'.format(self.tCurCalib))
            #    self.t0 += 1
        def changeShift(self, vitShift):
            self.fCurShift += vitShift
            self.lCurServos[self.iCurJoint].fShift = self.fCurShift
            self.updateAngles()
        def activateAngles(self, bActive):
            self.bSetAngles = bActive
        def setupText(self):
            STANDOUT = curses.A_BOLD|curses.A_UNDERLINE
            stdscr.erase()
            stdscr.move(0,0)
            stdscr.addstr('Legs (current):  rear right left  middle right left  bottom right left')
            stdscr.chgat(0,6, 7, STANDOUT)
            stdscr.addstr(1,0, 'Positions (current):')
            stdscr.chgat(1,11, 7, STANDOUT)
            stdscr.addstr(1,21, 'Femur up, tibia right angle, ADJUST femur min/max')
            stdscr.addstr(2,21, 'Flat horizontal leg, tibia 0° (no shift), ADJUST tibia min/max')
            stdscr.addstr(3,21, 'Flat horizontal leg, tibia 0°, ADJUST tibia shift')
            stdscr.addstr(4,21, 'Folded leg, tibia 180° (no shift), ADJUST tibia max/min value')
            stdscr.addstr(5,21, 'Vertical leg DOWN, ADJUST femur max/min value')
            stdscr.addstr(6,0,'Joints (current):  hip  femur  tibia\n')
            stdscr.chgat(6,8, 7, STANDOUT)
            stdscr.addstr(7,0,'Calibration:')
            stdscr.addstr(10,0, 'Leg control: ')
            stdscr.move(15,0)
            stdscr.addstr('### HELP ###\n')
            stdscr.addstr('  Start: quits\n')
            stdscr.addstr('  Trigger right/left: next/prev leg\n')
            stdscr.addstr('  A: cycles joints\n')
            stdscr.addstr('  B: cycle leg positions\n')
            stdscr.addstr('  Left Stick vertical: adjust min\n')
            stdscr.addstr('  Right Stick vertical: adjust max\n')
            stdscr.addstr('  Right Stick horizontal + right trigger axis pushed: adjust shift\n')
            #stdscr.addstr('  Y: Show current calibration\n')
            stdscr.addstr('  Left trigger axis: release to cancel control of the leg\n\n')
            #stdscr.addstr('  X: this help')
            stdscr.addstr('--- Calib order ---\n')
            stdscr.addstr(' - Adjust femur up to be vertical\n')
            stdscr.addstr(' - Adjust femur down to be vertical\n')
            stdscr.addstr(' - Adjust tibia no shift unfolded (horizontal flat leg)\n')
            stdscr.addstr(' - Adjust tibia no shift folded\n')
            stdscr.addstr(' - Adjust tibia shift')
        def refresh(self, lLatency):
            STANDOUT = curses.A_BOLD|curses.A_UNDERLINE
            for i in range(6):
                stdscr.chgat(0, (22,28,41,47,60,66)[i], (5,4,5,4,5,4)[i],
                             (i==self.iCurLeg and STANDOUT) or curses.A_NORMAL)
            for i in range(5):
                stdscr.chgat(1+i,21, (49,62,49,60,45)[i],
                          self.iCurPosition==i and STANDOUT or curses.A_NORMAL)
            for i in range(3):
                stdscr.chgat(6, (19, 24, 31)[i], (3,5,5)[i],
                             (i==self.iCurJoint and STANDOUT) or curses.A_NORMAL)
            stdscr.addstr(7,13, 'min    {:6.0f}µs'.format(self.tCurCalib[0]))
            stdscr.addstr(8,13, 'max    {:6.0f}µs'.format(self.tCurCalib[1]))
            stdscr.addstr(9,13, 'shift  {:+5.2f}°'.format(self.fCurShift))
            stdscr.move(10,13)
            stdscr.clrtoeol()
            if self.bSetAngles:
                stdscr.addstr('ON', curses.A_REVERSE)
            else:
                stdscr.addstr('OFF', curses.A_REVERSE)
            stdscr.addstr(12,0, '(latencies: {: 2d},{: 2d},{:2d},{:2d}, tot {:2d})'.format(*map(lambda f:int(f*1000), lLatency)))
            stdscr.move(13,0)
            stdscr.refresh()
    status = Status()
    status.setupText()
    deadZone = lambda i,z: ((i<-z or i>z) and ( (i<-z and (i+z)) or (i>z and (i-z)) )) or 0
    t0 = time.time()
    t0p = t0
    tLastRefr = t0-1
    while not ecodes.BTN_START in dev.active_keys():
        # In fact, we must watch events...
        # Searches for falling edge of btns
        t1 = time.time()
        ev = dev.read_one()
        while ev:
            if ev.type == ecodes.EV_KEY and ev.value == 1: # Values: 0 up 1 down 2 hold
                if ev.code == ecodes.BTN_X:
                    printMenu()
                elif ev.code == ecodes.BTN_TR:
                    status.nextLeg()
                elif ev.code == ecodes.BTN_TL:
                    status.nextLeg(-1)
                elif ev.code == ecodes.BTN_A:
                    status.nextJoint()
                elif ev.code == ecodes.BTN_B:
                    status.nextPosition()
                elif ev.code == ecodes.BTN_Y:
                    status.printCalib()
            ev = dev.read_one()
        t2 = time.time()
        # Change the values
        dAbsInput = getAxesValues(dev)
        t3 = time.time()
        status.activateAngles((dAbsInput[ecodes.ABS_BRAKE] > 250 and True) or False)
        if dAbsInput[ecodes.ABS_GAS] < 10:
            status.changeAngles(-deadZone(dAbsInput[ecodes.ABS_Y],5000)/100000,
                                -deadZone(dAbsInput[ecodes.ABS_RY],5000)/100000)
        elif dAbsInput[ecodes.ABS_GAS] > 250:
            status.changeShift(deadZone(dAbsInput[ecodes.ABS_RX],5000)/1000000)
        t4 = time.time()
        if t4-tLastRefr>1/8:
            status.refresh((t1-t0,t2-t1,t3-t2,t4-t3,t0-t0p))
            tLastRefr = t4
        t0p = t0
        t0 = time.time()
        time.sleep(.01)
    sctl.setAngles([None]*18)


if __name__=='__main__':
    dev = InputDevice('/dev/input/event1') # Hard-coded, don't care, calibration, small tool, fun with controller
    pruface = PruInterface('./servos.bin')
    sctl = ServoController(pruface, lServos, 20000)
    sctl.setAngles([None]*18)
    xpadMenu(dev)





