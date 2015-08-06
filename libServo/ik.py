#!/usr/bin/python3

# Bears the IK for the leg in its plane, and later for the whole leg.
# Inverse Kinematics, not Kinematic Inversion...


from math import atan, acos, sqrt, pi, cos, sin



# Angles are in radians inside the IK,
#  but are in degrees everywhere else, to ease readability of the servo control
DEG = lambda ang:180*ang/pi



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
    from config import lServos
    servoFemur,servoTibia = lServos[1:3]








