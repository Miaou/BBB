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



dev = InputDevice('/dev/input/event1') # Hard-coded, don't care, calibration, small tool, fun with controller


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
        print(' Start: quits\n Trigger right/left: next/prev leg\n A: cycles joints')
        print(' B: cycle leg positions (femur 90°, tibia 0°, tibia 180°, femur -90°)')
        print(' Left Stick vertical: adjust min time\n Right Stick vertical: adjust max time')
        print(' Y: Show current calibration')
        print(' X: this help')
    printMenu()
    class Status:
        def __init__(self):
            self.iCurLeg = -1
            self.iCurJoint = 0
            self.iCurPosition = 0
            self.tCurCalib = ()
            self.lCurServos = []
            self.t0 = time.time()
            self.nextLeg()
        def nextLeg(self, iShift=1):
            self.iCurLeg = (self.iCurLeg+iShift)%6
            print('Current leg: {}'.format(self.iCurLeg))
            self.lCurServos = lServos[self.iCurLeg*3:self.iCurLeg*3+3] # GLOBAL VAR
            self.iCurJoint = -1
            self.iCurPosition = -1
            self.nextPosition()
            self.nextJoint()
        def nextJoint(self):
            if self.iCurJoint > -1:
                print('Result: joint {} calib {}'.format(['hip','femur','tibia'][self.iCurJoint], self.tCurCalib))
                #self.lCurServos[self.iCurJoint].tCalib = self.tCurCalib
            self.iCurJoint = (self.iCurJoint+1)%3
            self.tCurCalib = self.lCurServos[self.iCurJoint].tCalib
            print('Current joint: {} calib {}'.format(['hip','femur','tibia'][self.iCurJoint], self.tCurCalib))
        def nextPosition(self):
            self.iCurPosition = (self.iCurPosition+1)%4
            if self.iCurPosition == 0:
                print('Femur up 90°, adjust min value')
            elif self.iCurPosition == 1:
                print('Tibia 0° vertical, no shift, min value')
            elif self.iCurPosition == 2:
                print('Tibia 180°, max value')
            elif self.iCurPosition == 3:
                print('Femur down -90, max value')
        def updateAngles(self):
            llAngles = [(None,90,90), (None,0,-self.lCurServos[2].fShift),
                        (None,90,180-self.lCurServos[2].fShift), (None,-90,180)]
            lAngles = [(None,)*3*self.iCurLeg + llAngles[self.iCurPosition] + (None,)*3*(6-self.iCurLeg-1)]
            #sctl.setAngles(lAngles) # GLOBAL VAR
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
        def printCalib(self):
            print('Current calib: {}'.format(self.tCurCalib))
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
        status.changeAngles(-deadZone(dAbsInput[ecodes.ABS_Y],5000)/100000,
                            -deadZone(dAbsInput[ecodes.ABS_RY],5000)/100000)
        time.sleep(.01)
    sctl.setAngles([None]*18)


xpadMenu(dev)
if __name__=='__main__' and False:
    pruface = PruInterface('./servos.bin')
    sctl = ServoController(pruface, lServos, 20000)
    sctl.setAngles([None]*18)





