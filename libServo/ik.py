#!/usr/bin/python3

# Bears the IK for the leg in its plane, and later for the whole leg.
# Inverse Kinematics, not Kinematic Inversion...


from math import atan, acos, sqrt, pi, cos, sin, floor, ceil


# Angles are in radians inside the IK,
#  but are in degrees everywhere else, to ease readability of the servo control
DEG = lambda ang:180*ang/pi
PIPI = lambda ang:(ang<-pi and PIPI(ang+2*pi)) or (ang>pi and PIPI(ang-2*pi)) or ang


class ServoConfig:
    '''This should move elsewhere, but I don't know where exactly yet'''
    def __init__(self, tPin, tCalib, iDirection, fShift):
        '''
        Holds the configuration of a pin.
        tPin: P8_29 -> (8,29)
        tCalib: times for 0° and 180° in µs -> (600, 2400)
        iDirection: +1 for 0° is 600 and 180° is 2400, -1 for the opposite direction
        fShift: shifts the domain of the servo e.g. -90 -> servo is now in [-90;90] angles
        '''
        #assert tPin in PORT_TO_MASK, 'Servo should be controllable through a known pin'
        assert tCalib[0] < tCalib[1], 'Use iDirection to reverse the domain of the servo'
        assert iDirection in (-1,1), 'Direction should be +1 or -1'
        self.tPin = tPin
        self.tCalib = tCalib
        self.iDir = iDirection
        self.fShift = fShift
        
    def getShift(self): return self.fShift
    def getTime(self, angle):
        '''Returns control time in µs to obtain angle in ° in the shifted domain'''
        shAng = angle-self.fShift
        # May be made "fault" tolerant, and shAng = min(180, max(0, shAng)) to avoid 180.0001 problems...
        assert shAng >= 0 and shAng <= 180, 'Given angle should be in servo\'s domain'
        a,b = self.tCalib[::self.iDir]
        return a+(b-a)*shAng/180
    #def isInDomain(self, angle):
    #    return angle >= 0+self.fShift and angle <= 180+self.fShift
    def findAngleInDomain(self, angle):
        '''
        Calculates tje angle%360° to obtain it in the domain, if possible.
        Returns None if angle is not found...
        '''
        k1 = ceil((self.fShift-angle)/(360))
        k2 = floor((self.fShift+180-angle)/(360))
        return (k1==k2 and angle+360*k1) or None
        


def ikLegPlane(x,y, servoFemur,servoTibia, lFemur=76.2,lTibia=114.3):
    '''
    IK for the leg, considering the plane in which the femur and tibia are.
    Returns a list of possible angles of the femur and tibia (0 or 1, maybe 2).
    Dimensions are in mm, angles in degrees.
    See the following for direction of x,y. Origin is at the base of the femur.
             /\
      Femur /  \
    ^      /    \ Tibia
    |y    /      \
    |             \
     -->           \
      x
    '''
    lsqu = x**2+y**2
    # Gamma is given in [-pi/2;3pi/2]
    gamma = DEG(  (x == 0 and (y>0 and pi/2 or -pi/2)) or atan(y/x) + (x<0 and pi)  )
    try:
        epsilon = DEG(  acos( (lsqu+lFemur*lFemur-lTibia*lTibia)/(2*lFemur*sqrt(lsqu)) ) )
        beta    = DEG(  acos( (lsqu-lFemur*lFemur-lTibia*lTibia)/(2*lFemur*lTibia) )  )
    except ValueError:
        return []
    lIK = []
    #print(epsilon, beta, gamma)
    a = servoFemur.findAngleInDomain(epsilon+gamma)
    b = servoTibia.findAngleInDomain(beta)
    if a and b:
        lIK.append( (a, b) )
    a = servoFemur.findAngleInDomain(-epsilon+gamma)
    b = servoTibia.findAngleInDomain(-beta)
    if a and b:
        lIK.append( (a, b) )
    return lIK


if __name__=='__main__':
    servoFemur = ServoConfig((8,30), (550,2500), 1, -90)
    servoTibia = ServoConfig((8,31), (550,2500), 1, 19)








