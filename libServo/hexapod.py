#!/usr/bin/python3

# Hexapod structure and alike. Gather all the things...
#  Uses ServoController to set the timings
#  Uses IKs to calculate the angles of the joints

# Traectories?



from servos import PruInterface, ServoController
from config import lServos
from ik import ikLegPlane
from math import sqrt



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
    sctl = ServoController(pruface, lServos, 10000) # Supposed to be 20ms, but can be less
    legRL = Leg(lServos[:], (0,1,2))
    beast = Hexapod([legRL])
    def demoCircle(N=400):
        import time
        from math import cos, sin, pi
        for i in range(N):
            sctl.setAngles(beast.buildAngles([(0,145+45*cos(i*2*pi/N),45*sin(i*2*pi/N))]))
            time.sleep(.02)




