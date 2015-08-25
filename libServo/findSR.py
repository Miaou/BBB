#
# Dedicated to find the sweet spot and the radius and possible height, from the wished height of the bot.



from ik import ikLegPlane


lZSRH = ((-69., 85.55, 85., 76.),  # Nominal
         (-150, 53.52, 53., 132.), # Fun
         (-41, 105.27, 73.5, 66.), # Low profile
         (-30, 111.72, 69.5, 59.)) # Ultra-low profile. Does the hexa touch the ground?


# Note: findSRH does not take into account the hip joint
def findSRH(z):
    '''
    S will be the distance to the sweet spot, in mm,
    r is the radius of the sweet zone, in mm,
    h is the maximal height of the leg when it prepares for the next step, assuming the trajectory follows a simple triangle, in mm.
    All this only takes place in the plane of the leg, as there is an almost symetry around the vertical axis of the hip...
    '''
##    x1=None
##    x2=None
##    for x in pylab.r_[0:250:2501j]:
##        if (x1 == None) and len(ikLegPlane(x,z, lServos[1],lServos[2]))>0:
##            x1 = x
##        elif (x1 != None):
##            if len(ikLegPlane(x,z, lServos[1],lServos[2])) > 0:
##                x2 = x
##            else:
##                break
    x1 = None
    x = 100
    for i in range(9): # 8 -> resolution is 100/256 < 1mm (last round does not count)
        if len(ikLegPlane(x,z, lServos[1],lServos[2]))>0:
            x1 = x
            x -= 100*2**(-i-1)
        else:
            x += 100*2**(-i-1)
    if not x1:
        raise ValueError
    x2 = None
    x = 100
    for i in range(9):
        if len(ikLegPlane(x,z, lServos[1],lServos[2]))>0 or x<x1:
            x2 = x
            x += 100*2**(-i-1)
        else:
            x -= 100*2**(-i-1)
    if not x2:
        raise ValueError
    S,r = (x1+x2)/2,(x2-x1)/2
    h = 100
    for i in range(9):
        bOk = True
        for j in range(101):
            if (len(ikLegPlane(x1+j/100*r,z+j/100*h, lServos[1],lServos[2])) < 1 or
                len(ikLegPlane(x2-j/100*r,z+j/100*h, lServos[1],lServos[2])) < 1):
                bOk = False
                break
        if bOk:
            hOk = h
            h += 100*2**(-i-1)
        else:
            h -= 100*2**(-i-1)
    return S,r,hOk


def plotSRH(z,S,r,h):
    xA,xB = S-r,S+r
    pygame.draw.aaline(screen, (0,0,0), zoom(xA,z), zoom(xB,z))
    pygame.draw.aaline(screen, (0,0,0), zoom(xA,z), zoom(S,z+h))
    pygame.draw.aaline(screen, (0,0,0), zoom(xB,z), zoom(S,z+h))
    pygame.draw.aaline(screen, (0,250,0), zoom(S,z), zoom(S,z+h))


def findAndPlot(lZ, bNoFill=False):
    if not bNoFill:
        screen.fill( (200, 200, 200) )
    pygame.display.flip()
    t0 = time.time()
    for z in lZ:
        try: S,r,h = findSRH(z)
        except ValueError: continue
        plotSRH(z,S,r,h)
        if time.time()-t0 > .02:
            t0 += .02
            if time.time()-t0 > .02: t0 = time.time()
            pygame.display.flip()


def plotRH(lZ):
    lZSRH = []
    for z in lZ:
        try:
            S,r,h = findSRH(z)
            lZSRH.append( (z,S,r,h) )
        except ValueError: pass
    lZ,lS,lR,lH = tuple(zip(*lZSRH))
    pylab.plot(lZ,lR,'x-', label='r')
    pylab.plot(lZ,lH,'x-', label='h')
    pylab.legend()
    pylab.savefig('findSR-z.png')
    pylab.figure()
    pylab.plot(lR,lH,'x')
    pylab.xlabel('r')
    pylab.ylabel('h')
    pylab.savefig('findSR-pareto.png')
    pylab.show()


if __name__=='__main__':
    from testIK import lServos, pygame, screen, zoom, plotRandom, time
    print('Importing pylab...', end='')
    import pylab
    print(' Ok')
    lZ = pylab.r_[200:-200:401j]
    if False:
        try:
            findAndPlot(lZ)
            plotRandom(3000)
        except BaseException as e:
            pygame.quit()
            raise e
    else:
        pygame.quit()
    plotRH(lZ)



























