#
# Test the Inverse Kinematics, there's sthg wrong with offsets, and angle diretion...

# First, "2D" IK with ikLegPlane, the results are shown in the plane of the leg
# Then, "3D" IK with ikLeg, the results are shown as seen from above the pod (functions ending with Z)


WIDTH, HEIGHT = 1000, 1000



import sys
sys.path.append(sys.path[0]+'/../libServo')
import pygame
import time
from math import pi, cos, sin
import random
from ik import ikLegPlane, ikLeg
from config import lServos




def zoom(x,y):
    '''Cooridnates to screen coordinates'''
    kx = 1/450. # Plots at least xx units height or width
    ky = (kx*WIDTH)/HEIGHT # Ratio is presesrved
    return int(WIDTH*(.5+x*kx)),int(HEIGHT*(.5-ky*y)) # Direct orthonormal Cartesian system, centered half way on the left border


from math import atan, acos, sqrt
def quickKI(x,y): # IK, not KI
    '''x,y in mm'''
    lsqu = x**2+y**2
    l1 = 76.2
    l2 = 107.95 #114.3
    beta = acos( (lsqu-l1*l1-l2*l2)/(2*l1*l2) )# - pi
    # Gamma is given in [-pi/2;3pi/2]
    gamma = (x == 0 and (y>0 and pi/2 or -pi/2)) or atan(y/x) + (x<0 and pi)
    alpha = acos( - (l2*l2-l1*l1-lsqu)/(2*l1*sqrt(lsqu)) ) + gamma
    #if alpha > pi/2: alpha -= pi
    #alpha *= -1
    #if alpha < pi/2: alpha += pi
    #if alpha > pi/2: raise ValueError('Out of boundsi, singularity')
    # Beta must be shifted as the contact point is not aligned with the axe of the servo... (...)
    #beta += .3316 # 19°
    #if beta > 0: beta -= pi
    return alpha*180/pi,beta*180/pi


pygame.quit()
from os import environ
environ['SDL_VIDEO_WINDOW_POS'] = '{},{}'.format(10,25)
pygame.init()
screen = pygame.display.set_mode( (WIDTH,HEIGHT) )


def plotLegs(a,b, colMark=(240,0,0), bLeg=True):
    u,v = 76.2*cos(a*pi/180),76.2*sin(a*pi/180)
    x,y = u+107.95*cos((a-b)*pi/180),v+107.95*sin((a-b)*pi/180)
    if bLeg:
        pygame.draw.aaline(screen, (0,0,0), zoom(0,0), zoom(u,v))
        pygame.draw.aaline(screen, (0,0,0), zoom(u,v), zoom(x,y))
    if colMark:
        plotMark(x,y,colMark)
    return x,y

def plotLegsZ(aH,a,b, colMark=(240,0,0), bLeg=True):
    delta = atan(7/34) # sqrt(7**2+34**2) == 37.71[...]
    d,e = 34.7*cos(delta+aH*pi/180),34.7*sin(delta+aH*pi/180)
    u,v = d+76.2*cos(a*pi/180)*cos(aH*pi/180),e+76.2*cos(a*pi/180)*sin(aH*pi/180)
    x,y = u+107.95*cos((a-b)*pi/180)*cos(aH*pi/180),v+107.95*cos((a-b)*pi/180)*sin(aH*pi/180)
    if bLeg:
        pygame.draw.aaline(screen, (0,0,0), zoom(0,0), zoom(d,e))
        pygame.draw.aaline(screen, (0,0,0), zoom(d,e), zoom(u,v))
        pygame.draw.aaline(screen, (230,230,230), zoom(u,v), zoom(x,y))
    if colMark:
        plotMark(x,y,colMark)
    return x,y

def plotMark(x,y,col=(0,0,0)):
    X,Y = zoom(x,y)
    pygame.draw.aaline(screen, col, (X-3,Y-3), (X+3,Y+3))
    pygame.draw.aaline(screen, col, (X-3,Y+3), (X+3,Y-3))


def plotIK(x,y,fill=True):
    if fill:
        screen.fill( (200, 200, 200) )
    #pygame.draw.aaline(screen, (0,0,0), zoom(0,0), zoom(100,50))
    plotMark(x,y) # This mark is the goal point
    #plotLegs(*quickKI(x,y)) # ... whereas the bMark plots a mark at the end of the leg
    for a,b in ikLegPlane(x,y, servoFemur,servoTibia):
        plotLegs(a,b, None)
    pygame.display.flip()

def plotIKZ(x,y,z,fill=True):
    if fill:
        screen.fill( (200, 200, 200) )
    #pygame.draw.aaline(screen, (0,0,0), zoom(0,0), zoom(100,50))
    plotMark(x,y) # This mark is the goal point
    #plotLegs(*quickKI(x,y)) # ... whereas the bMark plots a mark at the end of the leg
    for aH,a,b in ikLeg(x,y,z, servoHip,servoFemur,servoTibia):
        plotLegsZ(aH,a,b, None)
    pygame.display.flip()



def IKCircles():
    for r in [50, 80, 100, 125, 160, 190]:
        for i in range(36):
            plotAll(r*cos(10*i*pi/180), r*sin(10*i*pi/180), fill=(i==0))
            time.sleep(.1)


def plotAccessibleRange(N=20, fSleep=.1, bNoFill=False):
    if not bNoFill:
        screen.fill( (200, 200, 200) )
        pygame.display.flip()
    for a,b in [(i,0) for i in range(N+1)]+[(N,i) for i in range(N+1)]+[(N-i,N) for i in range(N+1)]+[(0,N-i) for i in range(N+1)]:
        plotLegs(servoFemur.fShift+a*180/N, servoTibia.fShift+b*180/N, bLeg=False)
        pygame.display.flip()
        time.sleep(fSleep)

def plotRandom(N=10000, bNoFill=True):
    if not bNoFill:
        screen.fill( (200, 200, 200) )
        pygame.display.flip()
    t0 = time.time()
    while N>0:
        plotLegs(servoFemur.fShift+servoFemur.iDir*random.random()*180,
                 servoTibia.fShift+servoTibia.iDir*random.random()*180,
                 (240,120,0), False)
        if time.time()-t0 > .02: # 50Hz
            t0 += .02
            pygame.display.flip()
        N -= 1

def plotRandomZ(N=10000, bNoFill=True):
    if not bNoFill:
        screen.fill( (200, 200, 200) )
        pygame.display.flip()
    t0 = time.time()
    while N>0:
        plotLegsZ(servoHip.fShift+servoHip.iDir*random.random()*180,
                  servoFemur.fShift+servoFemur.iDir*random.random()*180,
                  servoTibia.fShift+servoTibia.iDir*random.random()*180,
                  (240,120,0), False)
        if time.time()-t0 > .02: # 50Hz
            t0 += .02
            pygame.display.flip()
        N -= 1

def plotRandomIK(N=10000, bNoFill=False):
    if not bNoFill:
        screen.fill( (200, 200, 200) )
        pygame.display.flip()
    t0 = time.time()
    lCols = [(0,0,0), (0,220,0), (0,0,250)]
    while N>0:
        # Domain should be in a disk centered in 0 and of radius 114.3+76.2=190.5 107.95+76.2=184.15
        x,y = -184.15+368.3*random.random(), -184.15+368.3*random.random()
        plotMark(x,y, lCols[len(ikLegPlane(x,y, servoFemur,servoTibia))])
        if time.time()-t0 > .02: # 50Hz
            t0 += .02
            pygame.display.flip()
        N -= 1

def plotRandomIKZ(z=0, N=10000, bNoFill=False):
    if not bNoFill:
        screen.fill( (200, 200, 200) )
        pygame.display.flip()
    t0 = time.time()
    lCols = [(0,0,0), (0,220,0), (0,0,250), (0,200,200), (255,255,255)]
    while N>0:
        # Domain should be in a disk centered in 0 and of radius sqrt( (34+184.15)**2+7**2 ) = 218.26
        x,y = -219+438*random.random(), -219+438*random.random()
        plotMark(x,y, lCols[len(ikLeg(x,y,z, servoHip,servoFemur,servoTibia))])
        if time.time()-t0 > .02: # 50Hz
            t0 += .02
            pygame.display.flip()
        N -= 1

servoHip,servoFemur,servoTibia = lServos[:3]
if __name__=='__main__':
    #plotAccessibleRange(N=200, fSleep=.001)
    DIM3 = True
    if not DIM3:
        plotRandomIK(80000)
        plotRandom(5000)
        pygame.image.save(screen, 'ikPlane.png')
        plotAccessibleRange(200, .0, True)
    else:
        if False:
            for i,z in enumerate(range(-200,201,20)):
                plotRandomIKZ(z, 100000)
                pygame.image.save(screen, 'ikz.{:02d}.{:+04.0f}.png'.format(i,z))
                for ev in pygame.event.get(): pass
        if False:
            screen.fill( (200, 200, 200) )
            for i in range(0,200,10):
                plotMark(i,0)
            plotLegsZ(*ikLeg(100,0,-100, servoHip,servoFemur,servoTibia)[0])
            pygame.display.flip()
        plotRandomZ(10000, False) # Kind of unreadable, cf plotRandomIKZ(z=-40) to understand


