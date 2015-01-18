#!/usr/bin/python3
# Testing everything together.


import sys
sys.path.append('../libDS18B20/libDallas-PRU')
sys.path.append('../thermoLog')

from dao import DAO


sDB = 'cristal.db'


if __name__=='__main__':
    dao = DAO(sDB)
    dao.displaySensors()
    dao.displayWaves()
    print('for t,v in dao.iterMeasures(sensID, waveID)')




