#!/usr/bin/python3

# Hexapod structure and alike. Gather all the things...
#  Uses ServoController to set the timings
#  Uses IKs to calculate the angles of the joints

# Traectories?



from servos import PruInterface, ServoController
from config import lServos
from ik import ikLegPlane
from math import sqrt
import time
from joy import InputDevice, ecodes, getAxesValues
#from evdev._input import ioctl_capabilities
from trajectory import WalkTrajectory


# A leg is not much more than a container...
class Leg:
    def __init__(self, lCfgServos, lMap):
        '''
        lCfgServos is the list of the 3 servos in the leg: hip, femur, tibia
        lMap is the index of the 3 servos of lCfgServos in the array of servos (convenience)
        '''
        assert len(lCfgServos) == len(lMap) == 3, 'There should be 3 joints in a leg'
        self.lServos = lCfgServos[:]
        self.lMap = lMap[:]

    def getIndexedAngles(self, x,y,z):
        '''
        x: horizontal outward the bot
        y: horizontal toward the front
        z: height of the bot
        Yes, my basis is "weird", you're welcome.
        '''
        # 1) Calculate the hip angle
        # 2) Suppose the femur is in the right plane, calculate femur and tibia
        lIK = ikLegPlane(sqrt(x**2+y**2), -z, self.lServos[1], self.lServos[2])
        if not lIK:
            lAngles = (None,)*3
        else:
            lAngles = (None,) + lIK[0]
        return list(zip(self.lMap, lAngles))


# The bot itself, for now a container too.
class Hexapod:
    def __init__(self, lLegs):
        '''
        Yes, a pod can be summed up by his legs... There should be 6 of them.
        Order of the legs: rear right and left, middle right and left, front right and left
        '''
        #assert len(lLegs) == 6, 'How many legs in an Hexapod?'
        self.lLegs = lLegs[:] # Copy the list, not the legs

    def buildAngles(self, lXYZ):
        '''
        Builds the angle list from the x,y,z positions of each leg, to send it to ServoController
        A leg can be disabled if lXYZ[i] == None
        '''
        assert len(lXYZ) == len(self.lLegs), 'Not enough positions received (or too much)' 
        lAngles = [None]*len(self.lLegs)*3
        for i,leg in enumerate(self.lLegs):
            if not lXYZ[i]:
                continue
            for j,ang in leg.getIndexedAngles(*lXYZ[i]):
                lAngles[j] = ang
        return lAngles



if __name__=='__main__':
    pruface = PruInterface('./servos.bin')
    sctl = ServoController(pruface, lServos, 20000) # Supposed to be 20ms, but can be less
    lLegs = [Leg(lServos[3*i:3*i+3], (3*i+0,3*i+1,3*i+2)) for i in range(6)]
    beast = Hexapod(lLegs)
    def demoCircle(N=400):
        from math import cos, sin, pi
        for i in range(N):
            sctl.setAngles(beast.buildAngles([(0,145+45*cos(i*2*pi/N),45*sin(i*2*pi/N))]))
            time.sleep(.02)
    dev = InputDevice('/dev/input/event1') # Hard-coded, don't care, ...
    def demoXPad(dev):
        while not ecodes.BTN_A in dev.active_keys():
            dAbsInput = getAxesValues(dev)
            if dAbsInput[ecodes.ABS_GAS] > 200:
                sctl.setAngles(beast.buildAngles([(0,100,10+140*max( (0,-dAbsInput[ecodes.ABS_Y]/32768) ))]*6))
            else:
                sctl.setAngles([None]*18)
            time.sleep(.01)
        sctl.setAngles([None]*18)
    def demoWalk(dev):
        t0 = time.time()
        u = 0.
        traj = WalkTrajectory(-69,2)
        while not ecodes.BTN_A in dev.active_keys():
            dAbsInput = getAxesValues(dev)
            t1 = time.time()
            u += 4*(t1-t0)*(dAbsInput[ecodes.ABS_GAS]-dAbsInput[ecodes.ABS_BRAKE])/255
            sctl.setAngles(traj.getAngles(lServos,
                                          +dAbsInput[ecodes.ABS_X]/1000,
                                          -dAbsInput[ecodes.ABS_Y]/1000,
                                          -dAbsInput[ecodes.ABS_RX]/100000,
                                          u))
            t0 = t1
            #time.sleep(.01)
        while u%4 != 0:
            t1 = time.time()
            if t1-t0<4-(u%4): u += t1-t0
            else:             u = 0
            t0 = t1
            sctl.setAngles(traj.getAngles(lServos,0,0,0,u))
            time.sleep(.02)
        for i in range(10):
            sctl.setAngles([None]*18) # I must do something when it does not write because it's busy
            time.sleep(.01)
    import cProfile
    cProfile.run('demoWalk(dev)')




