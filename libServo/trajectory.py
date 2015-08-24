#
# Calculation of the trajectories of the legs, for a given mouvement
# + calculation of r (offline)


from math import cos, sin, acos, atan, pi
from findSR import lZSRH



# TODO: expand to take as argument a function which generates lSxy and r from z
class HexaTrajectory:
    def __init__(self, z,deltaU, **kwargs):
        self.updateParams(z,deltaU, **kwargs)
    def updateParams(self, z,deltaU, xA=34,yA=7):
        '''
        Updates the sweet spots, r, and deltaU, for instance when the height of the pod changes
        lSxy is the list of all leg's sweet spot (Sx,Sy), "center" of the trajectory
        r is the radius of reachable positions from S, in mm
        deltaU is half the shortest time to take a leg from -r to +r (fastest movement),
         and deltaTheta is computed so that a leg step foot exactly 2*deltaU
         (speed will be reduced if it is not possible)
        '''
        z,S,r,h = lZSRH[[z1 for z1,S,r,h in lZSRH].index(z)] # For now, only use predefined z
        lSxy = []
        for i, (Sx, Sy) in enumerate(lSxyBase): # GLOBAL
            t,d = lSxyAnglesDir[i]
            lSxy.append( (Sx+d*(xA+S)*cos(t)-yA*sin(t), Sy+yA*cos(t)+d*(xA+S)*sin(t)) )
        self.lSxy = lSxy
        self.r = r
        self.deltaU = deltaU
        self.h = h
    def _computeDeltaTheta(self, Vx, Vy, Omega):
        '''
        Vx and Vy are planar velocities of the object, in mm/s
        Omega is the angular velocity of the object, in rad/s
        Returns deltaTheta in rad. OmegaMax is deltaTheta/deltaU. Max velocity is r/deltaU.
        '''
        if Omega != 0:
            lDT = []
            for Sx,Sy in self.lSxy:
                x = +Vy+Omega*Sx
                y = -Vx+Omega*Sy
                R = (x**2 + y**2)**.5/abs(Omega)
                try:
                    lDT.append( acos((2*R**2-self.r**2)/(2*R**2)) )
                except ValueError:
                    lDT.append( pi )
            return min(min(( Omega*self.deltaU, deltaTheta )) for deltaTheta in lDT)
        else:
            # This is not exactly deltaTheta, but at least it is comparable to rad
            return min( ((Vx**2+Vy**2)**.5*self.deltaU/self.r, 1) )
    def _trajLeg(self, Vx, Vy, Omega, u, Sx, Sy, deltaTheta):
        '''
        The trajectory goes through (Sx, Sy) at u=0, in mm
        r is the radius of reachable positions from S, in mm
        deltaTheta is the max angular amplitude along the trajectory, in rad
        r and deltaTheta must be the same for all legs
        Returns (x(u), y(u))
        '''
        x = +Vy+Omega*Sx
        y = -Vx+Omega*Sy
        Theta0 =  (atan( y/x ) if x!= 0 else (y>0 and pi/2 or -pi/2)) + (pi if x*(Omega or 1.)<0 else 0)
        if Omega != 0:
            R = (x**2 + y**2)**.5/abs(Omega)
            return (R*(cos(Theta0-u*deltaTheta) - cos(Theta0)), # x(u)
                    R*(sin(Theta0-u*deltaTheta) - sin(Theta0))) # y(u)
        else:
            return (+self.r*u*deltaTheta*sin(Theta0), # Yes, using Taylor expansion of the above
                    -self.r*u*deltaTheta*cos(Theta0))
    def getXYOfLegs(self, Vx, Vy, Omega, u):
        '''
        Vx and Vy are planar velocities of the object, in mm/s
        Omega is the angular velocity of the object, in rad/s
        u is in [-1..1]
        '''
        assert -1 <= u and u <= 1, "u should be in [-1..1]"
        deltaTheta = self._computeDeltaTheta(Vx, Vy, Omega)
        return (self._trajLeg(Vx, Vy, Omega, u, Sx, Sy, deltaTheta) for Sx, Sy in self.lSxy)


# For now, these are only the positions of the hip
lSxyBase = ((+42.75, -82.5), (-42.75, -82.5),
            (+63,0),         (-63,0),
            (+42.75, +82.5), (-42.75, +82.5))
# These are the shift angles of the support of the hip,
#  and the x direction.
lSxyAnglesDir = ((-pi/3,1), (pi/3,-1),
                 (0,1), (0,-1),
                 (pi/3,1), (-pi/3,-1)) 

if __name__=='__main__':
    print('Importing pylab...', end='')
    import pylab
    print(' Ok')
    
    def plotTraj(Vx,Vy,Omega,sCol='b'):
        trajector = HexaTrajectory(-69, 1)
        for i,lXY in enumerate( zip(*(trajector.getXYOfLegs(Vx,Vy,Omega,u) for u in pylab.r_[-1:1:11j])) ): # This is unreadable, yes.
            lX,lY = zip(*lXY)
            Hx, Hy = lSxyBase[i]
            Sx, Sy = trajector.lSxy[i]
            pylab.plot((Sx+lX[0],),(Sy+lY[0],),sCol+'x')
            pylab.plot([Sx+x for x in lX],[Sy+y for y in lY],sCol+'-')
            pylab.plot((Sx,),(Sy,),'kx')
            pylab.plot((Hx,),(Hy,),'rx')
        pylab.plot((0,),(0,),'kx')
        pylab.axis('equal')
        #pylab.show()











