#!/usr/bin/python3

import sys
sys.path.append('../libDS18B20/libDallas-PRU')
sys.path.append('../thermoLog')
sys.path.append('../i2c')

#from dallas import OneWire, Sensor, pruicss

from dao import DAO
from threading import Thread
from multiprocessing import Value
from SHT21 import SHT21
import time

import subprocess

class Bulk:
    def __init__(self):
        self.shtTemp = 0
        self.shtRH = 0

def workerSHT(iface, stop):
    sht = SHT21(0x40, 1)
    print('Starting measures')
    while not stop.value:
        try:
            iface.shtRH = sht.getRH()
            iface.shtTemp = sht.getT()
        except :
            iface.shtRH = -1.
            iface.shtTemp = -1.
        finally:
            time.sleep(1)

    print('End of measurement')

if True:
    db = 'essai.db'
    dao = DAO(db)
    dao.newSensor(b'SHT21', b'RH')
    dao.newSensor(b'SHT21', b'Temperature')
    dao.newWave(sComment='Premier essai avec la nouvelle BBB')
    dao.commentSensor(1, 'Derriere le PC', 'Air(%RH)')
    dao.commentSensor(2, 'Derriere le PC', 'Air(°C)')
    iface = Bulk()
    stop = Value('b', False)
    Thread(target=workerSHT, args=(iface, stop)).start()

    try:
        while True:
            dao.newMeasure(1, iface.shtRH)
            dao.newMeasure(2, iface.shtTemp)
            time.sleep(5)
    except KeyboardInterrupt:
        print('End of record')
        stop.value = True

