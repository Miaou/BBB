#!/usr/bin/python3

# Trying to control 1 femur 76.2mm long and 1 tibia 114.3mm long
# Hexapod Phoenix
# (Trying a KI)

# Old demos, may not run anymore.


print('Old demos\n---> Run board.py instead <---')
commentMeIfYouDare

import sys
sys.path.append(sys.path[0]+'/../libServo')
from servos import PruInterface, ServoController, PORT_TO_MASK
from math import atan, acos, sqrt, pi, cos, sin
import time


pruface = PruInterface(sys.path[-1]+'/servos.bin')
sctl = ServoController(pruface, [PORT_TO_MASK[8,29], PORT_TO_MASK[8,30]], 20000)
sctl.setCalibration([((-90,2600),(90,550)),
                     ((-180,2550),(0,600))])


def quickKI(x,y):
    '''x,y in mm'''
    lsqu = x**2+y**2
    l1 = 76.2
    l2 = 114.3
    beta = acos( (lsqu-l1*l1-l2*l2)/(2*l1*l2) ) - pi
    gamma = (x == 0 and (y>0 and pi/2 or -pi/2)) or atan(y/x)
    alpha = acos( (l2*l2-l1*l1-lsqu)/(2*l1*sqrt(lsqu)) ) + gamma
    #if alpha > pi/2: alpha -= pi
    alpha *= -1
    if alpha < pi/2: alpha += pi
    if alpha > pi/2: raise ValueError('Out of boundsi, singularity')
    # Beta must be shifted as the contact point is not aligned with the axe of the servo... (...)
    beta += .3316 # 19°
    if beta > 0: beta -= pi
    return alpha*180/pi,beta*180/pi


def demoLines():
    # Center is (85,0)
    WAIT = .02
    sctl.setAngles(quickKI(145,0))
    time.sleep(1)
    for i in range(45):
        sctl.setAngles(quickKI(146+i,0))
        time.sleep(WAIT)
    for i in range(90):
        sctl.setAngles(quickKI(190-i,0))
        time.sleep(WAIT)
    for i in range(45):
        sctl.setAngles(quickKI(100+i,0))
        time.sleep(WAIT)
    for i in range(45):
        sctl.setAngles(quickKI(145,i))
        time.sleep(WAIT)
    for i in range(90):
        sctl.setAngles(quickKI(145,45-i))
        time.sleep(WAIT)
    for i in range(45):
        sctl.setAngles(quickKI(145,-45+i))
        time.sleep(WAIT)


def demoCircle(nSteps=100):
    WAIT = .015 # Smoother than the motor ^^" 
    for i in range(nSteps):
        sctl.setAngles(quickKI(145+45*cos(2*pi/nSteps*i),0+45*sin(2*pi/nSteps*i)))
        time.sleep(WAIT)



def demoGreg():
    time.sleep(20)
    demoLines()
    demoLines()
    demoLines()
    demoCircle(1000)
    demoCircle(800)
    demoCircle(600)
    demoCircle(200)

