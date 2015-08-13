#
# Test the sensibility of the IK to the parameters of the real structure
#  (importance of the calibration)



from testIK import pygame, time, pi, cos, sin, random, ikLegPlane, lServos, zoom, atan, acos, sqrt, plotLegs, plotMark, screen, servoFemur, servoTibia, plotAccessibleRange, WIDTH, HEIGHT
import numpy as np



def unzoom(x,y):
    # Inverse of zoom
    kx = 1/400. # Plots at least xx units height or width
    ky = (kx*WIDTH)/HEIGHT # Ratio is presesrved
    return (x/WIDTH-.5)/kx,(y/HEIGHT-.5)/(-ky)# Direct orthonormal Cartesian system, centered half way on the left border


def posLeg(a,b, l1=76.2,l2=114.3):
    u,v = l1*cos(a*pi/180),l1*sin(a*pi/180)
    return u+l2*cos((a-b)*pi/180),v+l2*sin((a-b)*pi/180)



# Sensib to the length of the legs, for straight lines
def compare(x,y, kx,ky, N=20, bNoFill=True):
    if not bNoFill:
        screen.fill( (200, 200, 200) )
        pygame.display.flip()
    for i in range(N):
        u,v = x+kx*i/N,y+ky*i/N # .../(N-1)
        plotMark(u,v)
        lAB = ikLegPlane(u,v, servoFemur, servoTibia)
        if not lAB:
            continue
        a,b = lAB[0]
        X,Y = posLeg(a,b, 76.2, 106.4)
        plotMark(X,Y, (200,100,0))
        pygame.display.flip()

def compareInteract():
    plotAccessibleRange(200, .0, False)
    bEnd = False
    while not bEnd:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                bEnd = True
                pygame.quit()
            #elif ev.type == pygame.MOUSEMOTION:
            #    x,y = ev.pos
            #    x,y = unzoom(x,y)
            elif ev.type == pygame.MOUSEBUTTONDOWN: # 1,2,3,4,5,6,7 = left,middle,right,up,down,prev,next
                if ev.button == 1: # LEFT is not define
                    x,y = unzoom(*pygame.mouse.get_pos())
                    lAB = ikLegPlane(x,y, servoFemur, servoTibia)
                    if not lAB:
                        plotMark(x,y,(255,255,255))
                    else:
                        a,b = lAB[0]
                        X,Y = posLeg(a,b, 76.2, 106.4)
                        plotMark(x,y)
                        plotMark(X,Y, (200,100,0))
                    pygame.display.flip()
        time.sleep(.1)
compareInteract()

if False:
    compare(80,0,100,0,20,False)
    compare(80,40,50,0)
    compare(80,-40,50,0)
    compare(100,-150,0,200)
    compare(80,-50,100,100)
    compare(80,-50,100,-100)


# Could imagine a field of vectors, where the arrows are the errors

# Could analyze the sensibility with a variation of the controled angles of the servos
#  -> l1*dalpha + l2*dbeta, ... dalpha? dbeta? 1° -> ~2mm

# Could analyze the derivative of the angles in each position, to see almost unreachable points (grad)
def buildGrad(N = 101):
    X,Y = np.meshgrid(np.r_[-200:200:N*1j],np.r_[-200:200:N*1j])
    ZA = np.zeros_like(X, dtype=np.float32)
    ZB = np.zeros_like(X, dtype=np.float32)
    for i in range(N):
        for j in range(N):
            lAB = ikLegPlane(X[i,j],Y[i,j], servoFemur,servoTibia)
            ZA[i,j],ZB[i,j] = (lAB and lAB[0]) or (float('nan'),float('nan'))
    print('+',end='')
    gradA = np.gradient(ZA) # Returns 2 arrays, directions are ... not clear
    gradB = np.gradient(ZB)
    nGradA = np.zeros_like(ZA) # Norm
    nGradB = np.zeros_like(ZB)
    for i in range(N):
        for j in range(N):
            nGradA[i,j] = sqrt(gradA[0][i,j]**2+gradA[1][i,j]**2)
            nGradB[i,j] = sqrt(gradB[0][i,j]**2+gradB[1][i,j]**2)
    print('+')
    return nGradA, nGradB
def plotGrad(grad, bNoFill=False):
    N = len(grad)
    X,Y = np.meshgrid(np.r_[-200:200:N*1j],np.r_[-200:200:N*1j])
    from math import isnan
    if not bNoFill:
        screen.fill( (200, 200, 200) )
        pygame.display.flip()
    for ev in pygame.event.get(): pass
    for i in range(N):
        for j in range(N):
            if not isnan(nga[i,j]):
                plotMark(X[i,j], Y[i,j], (max(0,min(255*grad[i,j]/10,255)), 0, 0))
        pygame.display.flip()

if False:
    nga,ngb = buildGrad()
    plotGrad(ngb)




