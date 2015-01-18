#!/usr/bin/python3
# Testing everything together.


import sys
sys.path.append('../libDS18B20/libDallas-PRU')
sys.path.append('../thermoLog')

from dao import DAO, DAODrawer

try:
    print('Import pylab+numpy...', end='')
    import pylab
    import numpy as np
    print(' Ok')
except ImportError:
    print(' No pylab')
    pylab = None
    np = None


sDB = 'cristal.db'




if __name__=='__main__':
    if not pylab:
        dao = DAO(sDB)
        dao.displaySensors()
        dao.displayWaves()
        print('for t,v in dao.iterMeasures(sensID, waveID)')
    else:
        dao = DAODrawer(sDB)
        dao.assertPylab()
        dao.displaySensors()
        dao.displayWaves()
        dao.pylabPltWave(3, [], 1300)



