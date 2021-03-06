#
# Configuration of the servos: pin layout, calibration.
# This is almost part of hexapod instead of libServo...

# Sorry for the globals...



from math import floor, ceil


# TODO: take into account real angle limits of the servos
#  because it is not 0..180 and 0 is shifted, but 180 could be less or more
class ServoConfig:
    '''
    Holds the configuration of a pin.
    tPort: P8_29 -> (8,29)
    tCalib: times for 0° and 180° in µs -> (600, 2400)
    iDirection: +1 for 0° is 600 and 180° is 2400, -1 for the opposite direction
    fShift: shifts the domain of the servo e.g. -90 -> servo is now in [-90;90] angles
    '''
    def __init__(self, tPort, tCalib, iDirection, fShift):
        #assert tPort in PORT_TO_MASK, 'Servo should be controllable through a known pin' # No, ServoController will check that...
        assert tCalib[0] < tCalib[1], 'Use iDirection to reverse the domain of the servo'
        assert iDirection in (-1,1), 'Direction should be +1 or -1'
        self.tPort = tPort
        self.tCalib = tCalib
        self.iDir = iDirection
        self.fShift = fShift
        
    def getShift(self): return self.fShift
    def getPort(self): return self.tPort
    def getTime(self, angle):
        '''Returns control time in µs to obtain angle in ° in the shifted domain'''
        shAng = angle-self.fShift*self.iDir
        # May be made "fault" tolerant, and shAng = min(180, max(0, shAng)) to avoid 180.0001 problems...
        assert shAng >= 0 and shAng <= 180, 'Given angle should be in servo\'s domain (computed {})'.format(shAng)
        a,b = self.tCalib[::self.iDir]
        return a+(b-a)*shAng/180
    #def isInDomain(self, angle):
    #    return angle >= 0+self.fShift and angle <= 180+self.fShift
    def findAngleInDomain(self, angle):
        '''
        Calculates tje angle%360° to obtain it in the domain, if possible.
        Returns None if angle is not found...
        '''
        k1 = ceil((self.fShift*self.iDir-angle)/(360))
        k2 = floor((self.fShift*self.iDir+180-angle)/(360))
        if k1==k2:
            return angle+360*k1
        return None
        


#lServos = [ServoConfig((8,30), (550,2500), +1, -90),
#           ServoConfig((8,32), (520,2450), -1, 90), # Done
#           ServoConfig((8,34), (520,2400), -1, 21)] # Done
lServos = [# Rear Right
           ServoConfig((8, 7), (631,2517), +1, -90),
           ServoConfig((8, 9), (690,2656), +1, -90),
           ServoConfig((8,11), (741,2653), +1, -25.7),
           # Rear Left
           ServoConfig((8, 8), (531,2426), -1, +90),
           ServoConfig((8,10), (512,2416), -1, +90),
           ServoConfig((8,12), (499,2399), -1, +20.2),
           # Middle Right
           ServoConfig((9,11), (484,2374), +1, -90),
           ServoConfig((9,13), (647,2542), +1, -90),
           ServoConfig((9,15), (671,2574), +1, -19.9),
           # Middle Left
           ServoConfig((9,12), (467,2431), -1, +90),
           ServoConfig((9,14), (515,2458), -1, +90),
           ServoConfig((9,16), (558,2494), -1, +22.1),
           # Front Right
           ServoConfig((8,13), (572,2451), +1, -90),
           ServoConfig((8,15), (661,2574), +1, -90),
           ServoConfig((8,17), (677,2555), +1, -22.0),
           # Front Left
           ServoConfig((8,14), (575,2560), -1, +90),
           ServoConfig((8,16), (559,2499), -1, +90),
           ServoConfig((8,18), (650,2541), -1, +22.7),
           ]



