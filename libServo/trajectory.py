#
#


from math import cos, sin, acos, atan, pi



def computeDeltaTheta(Vx, Vy, Omega, lSxy, r, deltaU):
    '''
    Vx and Vy are planar velocities of the object, in mm/s
    Omega is the angular velocity of the object, in rad/s
    lSxy is the list of all leg's sweet spot (Sx,Sy), "center" of the trajectory
    r is the radius of reachable positions from S, in mm
    deltaU is half the shortest time to take a leg from -r to +r (fastest movement),
     and deltaTheta is computed so that a leg step foot exactly 2*deltaU
     (speed is reduced if it is not possible)
    Returns deltaTheta in rad. OmegaMax is deltaTheta/deltaU. Max velocity is r/deltaU.
    '''
    if Omega != 0:
        lDT = []
        for Sx,Sy in lSxy:
            x = +Vy+Omega*Sx
            y = -Vx+Omega*Sy
            R = (x**2 + y**2)**.5/abs(Omega)
            try:
                lDT.append( acos((2*R**2-r**2)/(2*R**2)) )
            except ValueError:
                lDT.append( pi )
        return min(min(( Omega*deltaU, deltaTheta )) for deltaTheta in lDT)
    else:
        # This is not exactly deltaTheta, but at least it is comparable to rad
        return min( ((Vx**2+Vy**2)**.5*deltaU/r, 1) )

    
def quickTraj(Vx, Vy, Omega, u, Sx, Sy, r, deltaTheta):
    '''
    Vx and Vy are planar velocities of the object, in mm/s
    Omega is the angular velocity of the object, in rad/s
    u is in [-1..1]
    The trajectory goes through (Sx, Sy) at u=0, in mm
    r is the radius of reachable positions from S, in mm
    deltaTheta is the max angular amplitude along the trajectory, in rad
    r and deltaTheta must be the same for all legs
    Returns (x(u), y(u), z(u)=0)
    '''
    x = +Vy+Omega*Sx
    y = -Vx+Omega*Sy
    Theta0 =  (atan( y/x ) if x!= 0 else (y>0 and pi/2 or -pi/2)) + (pi if x*(Omega or 1.)<0 else 0)
    if Omega != 0:
        R = (x**2 + y**2)**.5/abs(Omega)
        return (R*(cos(Theta0-u*deltaTheta) - cos(Theta0)), # x(u)
                R*(sin(Theta0-u*deltaTheta) - sin(Theta0)), # y(u)
                0) # z(u)
    else:
        return (+r*u*deltaTheta*sin(Theta0), # Yes, using Taylor expansion of the above
                -r*u*deltaTheta*cos(Theta0),
                0)


def plotTraj(Vx,Vy,Omega,sCol='b'):
    lSxy = ((-42.75, -82.5), (+42.75, -82.5),
            (-63,0),         (+63,0),
            (-42.75, +82.5), (+42.75, +82.5))
    deltaTheta = computeDeltaTheta(Vx, Vy, Omega, lSxy, 30, 1)
    for Sx,Sy in lSxy:
        lX,lY,lZ = list(zip(*(quickTraj(Vx, Vy, Omega, u, Sx, Sy, 30, deltaTheta) for u in pylab.r_[-1:1:11j])))
        pylab.plot((Sx+lX[0],),(Sy+lY[0],),sCol+'x')
        pylab.plot([Sx+x for x in lX],[Sy+y for y in lY],sCol+'-')
        pylab.plot((Sx,),(Sy,),'kx')
    pylab.plot((0,),(0,),'kx')
    pylab.axis('equal')
    #pylab.show()


if __name__=='__main__':
    print('Importing pylab...', end='')
    import pylab
    print(' Ok')









