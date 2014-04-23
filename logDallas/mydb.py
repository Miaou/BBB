#!/usr/bin/python3

import os
import sys

#for crontab, we must change directory
#os.chdir('/root/BBB/logDallas')

#more elegant way:
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

sys.path.append('../libDS18B20/libDallas-PRU')
sys.path.append('../thermoLog')
sys.path.append('../i2c')

from dallas import OneWire, Sensor, pruicss

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
        self.dsTemp = []

def workerSHT(iface, stop):
    sht = SHT21(0x40, 1)
    print('Starting SHT measures')
    while not stop.value:
        try:
            iface.shtRH = sht.getRH()
            iface.shtTemp = sht.getT()
        except :
            iface.shtRH = -1.
            iface.shtTemp = -1.
        finally:
            time.sleep(1)

    print('End of SHT measurement')

def workerDS(iface, stop):
    wire = OneWire(9,13,9,14,pruicss)
    wire.SearchMoreRoms()
    i = 1
    for sensor in wire.dSensors.values():
        iface.dsTemp.append(sensor)
        sensor.num = i
        i += 1

    print('Starting DS measures')
    while not stop.value:
        wire.ConvertTemperatures()
        wire.ReadTemperatures()

        #for rom in iface.dsTemp:
        #    iface.dsTemp[rom] = 0
        time.sleep(1)
    
    print('End of DS measurement')

iface = Bulk()
stop = Value('b', False)
db = 'essai.db'
if False:
    #time.sleep(15)
    dao = DAO(db)
    dao.newSensor(b'SHT21', b'RH')
    dao.newSensor(b'SHT21', b'Temperature')
    dao.newWave(sComment='Premier essai avec la nouvelle BBB')
    dao.commentSensor(1, 'Derriere le PC', 'Air(%RH)')
    dao.commentSensor(2, 'Derriere le PC', 'Air(°C)')
    Thread(target=workerSHT, args=(iface, stop)).start()

    try:
        while True:
            dao.newMeasure(1, iface.shtRH)
            dao.newMeasure(2, iface.shtTemp)
            time.sleep(5)
    except KeyboardInterrupt:
        print('End of record')
        stop.value = True

if True:
    dao = DAO(db)
    dao.newSensor(b'DS18B20', b'Temperature')
    dao.newWave(sComment='Remise en route du PRU')
    dao.commentSensor(1, 'Derrière le PC', 'Air(°C)')
    Thread(target=workerDS, args=(iface, stop)).start()
    time.sleep(5)

    try:
        while True:
            for sensor in iface.dsTemp:
                dao.newMeasure(sensor.num, sensor.GetTemperature())
                time.sleep(5)
    except KeyboardInterrupt:
        print('End of record')
        stop.value = True


