#!/usr/bin/python3

# Calibration of the legs using the XBox Controller (see xboxdrv in the ../doc) and evdev
# Small tool provided more than anything else "as-is", just for fun...


from evdev import InputDevice, ecodes
from config import lServos
from servos import PruInterface, ServoController
import time


# InputDevice has a nice active_keys() which avoids the parsing of the events, but not abs_values()...
# This should not be THAT hard to add. However, I don't want to compile/test/install, and not very comfortable with the Python C-API.
# To do so, see https://github.com/gvalkov/python-evdev/blob/master/evdev/device.py,
#  -> active_keys() uses _input.ioctl_EVIOCGKEY(self.fd) (see https://github.com/gvalkov/python-evdev/blob/master/evdev/input.c)
#   and implementing a ioctl_EVIOCGABS should not be that hard
#  -> but abs values are also stored in the capabilities() (see device.py)
#   and this is generated when ._rawcapabilities is created,
#   and this is done by _input.ioctl_capabilities() (see input.c)
#   which has the code ready for EVIOCGABS
#  -> so we just have to call _input.ioctl_capabilities() and find the interesting value.
#   (our task is not real-time sensitive)

from evdev._input import ioctl_capabilities # Sole parameter: InputDevice.fd





def getAxesValues(dev):
    # Yes, this is "kind of" brutal, but who cares...
    # 1) Get _rawcapabilities (via ioctl_[...])
    # 2) Take EV_ABS part out of it, which is a list [(iAxis, tAbsInfo), ...]
    # 3) Reform the list as a more usable dict
    return {iAxis:tAbsInfo[0] for iAxis,tAbsInfo in ioctl_capabilities(dev.fd)[ecodes.EV_ABS]} # In fact, we don't need InputDevice


def testRawCapa():
    POLL_PERIOD = .5
    t0 = time.time()
    while True:
        if time.time()-t0 > POLL_PERIOD:
            dAbsInputs = getAxesValues(dev)
            print('  '.join('{}: {:<6}'.format(ecodes.ABS[k][4:],v) for k,v in dAbsInputs.items()))
            t0 += POLL_PERIOD
        time.sleep(.01)



def xpadMenu(dev):
    def printMenu():
        print('### Menu ###')
        print('  Start: quits')
        print('  Trigger right/left: next/prev leg')
        print('  A: cycles joints')
        print('  B: cycle leg positions (femur 90°, tibia 0°, tibia 180°, femur -90°)')
        print('  Left Stick vertical: adjust min time')
        print('  Right Stick vertical: adjust max time')
        print('  Right Stick horizontal + right trigger axis pushed: adjust shift')
        print('  Y: Show current calibration')
        print('  Left trigger axis: release to cancel control of the leg')
        print('  X: this help')
        print('### Calib order ###')
        print(' - Adjust femur up to be vertical')
        print(' - Adjust femur down to be vertical')
        print(' - Adjust tibia no shift unfolded (horizontal flat leg)')
        print(' - Adjust tibia no shift folded')
        print(' - Adjust tibia shift')
    printMenu()
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
            print('Leg: current {} ({})'.format(self.iCurLeg, ['rear right', 'rear left', 'middle right', 'middle left', 'front right', 'front left'][self.iCurLeg]))
            self.lCurServos = lServos[self.iCurLeg*3:self.iCurLeg*3+3] # GLOBAL VAR
            self.iCurJoint = -1
            self.iCurPosition = -1
            self.nextPosition()
            self.nextJoint()
        def nextJoint(self):
            if self.iCurJoint > -1:
                print('Joint: LAST {} calib {}'.format(['hip','femur','tibia'][self.iCurJoint], self.tCurCalib))
                #self.lCurServos[self.iCurJoint].tCalib = self.tCurCalib
            self.iCurJoint = (self.iCurJoint+1)%3
            self.tCurCalib = self.lCurServos[self.iCurJoint].tCalib
            self.fCurShift = self.lCurServos[self.iCurJoint].fShift
            print('Joint: CURR {} calib ({:.2f},{:.2f}) shift {:.2f}'.format(['hip','femur','tibia'][self.iCurJoint], self.tCurCalib[0], self.tCurCalib[1], self.fCurShift))
        def nextPosition(self):
            self.iCurPosition = (self.iCurPosition+1)%5
            if self.iCurPosition == 0:
                print('Pos: Femur up tibia right angle, ADJUST femur min/max')
            elif self.iCurPosition == 1:
                print('Pos: Flat horizontal leg, tibia 0° (no shift), ADJUST tibia min/max')
            elif self.iCurPosition == 2:
                print('Pos: Flat horizontal leg, tibia 0°, ADJUST tibia shift')
            elif self.iCurPosition == 3:
                print('Pos: Folded leg, tibia 180° (no shift), ADJUST tibia max/min value')
            elif self.iCurPosition == 4:
                print('Pos: Vertical leg DOWN, ADJUST femur max/min value')
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
        def printCalib(self):
            print('Status: calib ({:.2f},{:.2f}) shift {:.2f}'.format(self.tCurCalib[0],
                                                                      self.tCurCalib[1],
                                                                      self.fCurShift))
        def activateAngles(self, bActive):
            self.bSetAngles = bActive
    status = Status()
    deadZone = lambda i,z: ((i<-z or i>z) and ( (i<-z and (i+z)) or (i>z and (i-z)) )) or 0
    while not ecodes.BTN_START in dev.active_keys():
        # In fact, we must watch events...
        # Searches for falling edge of btns
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
        # Change the values
        dAbsInput = getAxesValues(dev)
        status.activateAngles((dAbsInput[ecodes.ABS_BRAKE] > 250 and True) or False)
        if dAbsInput[ecodes.ABS_GAS] < 10:
            status.changeAngles(-deadZone(dAbsInput[ecodes.ABS_Y],5000)/100000,
                                -deadZone(dAbsInput[ecodes.ABS_RY],5000)/100000)
        elif dAbsInput[ecodes.ABS_GAS] > 250:
            status.changeShift(deadZone(dAbsInput[ecodes.ABS_RX],5000)/1000000)
        time.sleep(.01)
    sctl.setAngles([None]*18)


if __name__=='__main__':
    dev = InputDevice('/dev/input/event1') # Hard-coded, don't care, calibration, small tool, fun with controller
    pruface = PruInterface('./servos.bin')
    sctl = ServoController(pruface, lServos, 20000)
    sctl.setAngles([None]*18)
    xpadMenu(dev)





