#
# Test the Inverse Kinematics, there's sthg wrong with offsets, and angle diretion...


WIDTH, HEIGHT = 600, 600



import pygame
import time
from math import pi, cos, sin
import random
from ik import ikLegPlane
from config import lServos




def zoom(x,y):
    '''Cooridnates to screen coordinates'''
    kx = 1/400. # Plots at least xx units height or width
    ky = (kx*WIDTH)/HEIGHT # Ratio is presesrved
    return int(WIDTH*(.5+x*kx)),int(HEIGHT*(.5-ky*y)) # Direct orthonormal Cartesian system, centered half way on the left border


from math import atan, acos, sqrt
def quickKI(x,y): # IK, not KI
    '''x,y in mm'''
    lsqu = x**2+y**2
    l1 = 76.2
    l2 = 114.3
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
pygame.init()
screen = pygame.display.set_mode( (WIDTH,HEIGHT) )

def plotLegs(a,b, colMark=(240,0,0), bLeg=True):
    u,v = 76.2*cos(a*pi/180),76.2*sin(a*pi/180)
    x,y = u+114.3*cos((a-b)*pi/180),v+114.3*sin((a-b)*pi/180)
    if bLeg:
        pygame.draw.aaline(screen, (0,0,0), zoom(0,0), zoom(u,v))
        pygame.draw.aaline(screen, (0,0,0), zoom(u,v), zoom(x,y))
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
        plotLegs(-90+a*180/N, 19+b*180/N, bLeg=False)
        pygame.display.flip()
        time.sleep(fSleep)

def plotRandom(N=10000, bNoFill=True):
    if not bNoFill:
        screen.fill( (200, 200, 200) )
        pygame.display.flip()
    t0 = time.time()
    while N>0:
        plotLegs(-90+random.random()*180, 19+random.random()*180, (240,120,0), False)
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
        # Domain should be in a circle centered in 0 and of radius 114.3+76.2=190.5
        x,y = -190.5+381*random.random(), -190.5+381*random.random()
        plotMark(x,y, lCols[len(ikLegPlane(x,y, servoFemur,servoTibia))])
        if time.time()-t0 > .02: # 50Hz
            t0 += .02
            pygame.display.flip()
        N -= 1

servoFemur = lServos[1]
servoTibia = lServos[2]
#plotAccessibleRange(N=200, fSleep=.001)
plotRandomIK(100000)
plotRandom(3000)
plotAccessibleRange(200, .0, True)

