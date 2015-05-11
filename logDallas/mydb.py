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

from dallas import OneWire, Sensor, pruicss, NoResponseError

from dao import DAO
from threading import Thread
from multiprocessing import Value
from SHT21 import SHT21
import time
from OnOff import OnOff
from binascii import unhexlify

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

def workerDS(iface, stop, mesure_reussie):
## capteur 1 : 28ff753e651401b3
## capteur 2 : 28ffd58c65140116
## capteur 3 : 28ffbef1691404c6
## capteur 4 : 28ff498a65140189
## capteur test : 2864edaa050000b0    
    wire = OneWire(9,13,9,14,pruicss)
    wire.SearchMoreRoms()
    
    iface.dsTemp.append(wire.dSensors[unhexlify(b'2864edaa050000b0')])
    #iface.dsTemp.append(wire.dSensors[unhexlify(b'28ff753e651401b3')])
    #iface.dsTemp.append(wire.dSensors[unhexlify(b'28ffd58c65140116')])
    #iface.dsTemp.append(wire.dSensors[unhexlify(b'28ffbef1691404c6')])
    #iface.dsTemp.append(wire.dSensors[unhexlify(b'28ff498a65140189')])

    log = open('measures.log', 'a', 1)
    log.write("\n\n\nStarting DS measures : " + time.ctime() + '\n')
    print('Starting DS measures')
    while not stop.value:
        try :
            wire.ConvertTemperatures()
            wire.ReadTemperatures()
            mesure_reussie.value = True
        except (NoResponseError, AssertionError) as e:
            log.write(time.ctime()+" : "+str(e) + "\n")
            mesure_reussie.value = False
        finally:
            time.sleep(1)
    
    print('End of DS measurement')
    log.write(time.ctime() + " : End of DS measurement")
    log.close()


iface = Bulk()
stop = Value('b', False)
db = 'essai.db'
dao = DAO(db)
mesure_reussie = Value('b', False)
if False:
    #time.sleep(15)
    dao.newSensor(b'SHT21', b'RH')
    dao.newSensor(b'SHT21', b'Temperature')
    dao.newWave(sComment='Premier essai avec la nouvelle BBB')
    dao.commentSensor(1, 'Derriere le PC', 'Air(%RH)')
    dao.commentSensor(2, 'Derriere le PC', 'Air(.C)')
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
    dao.newSensor(b'DS18B20', b'2864edaa050000b0')
    #dao.newSensor(b'DS18B20', b'28ff753e651401b3')
    #dao.newSensor(b'DS18B20', b'28ffd58c65140116')
    #dao.newSensor(b'DS18B20', b'28ffbef1691404c6')
    #dao.newSensor(b'DS18B20', b'28ff498a65140189')
    dao.newWave(sComment='Essai du week-end 8 mai')
    dao.commentSensor(1, 'test maison longue duree')
    #dao.commentSensor(1, 'Pale du haut, au milieu')
    #dao.commentSensor(2, "Pale du bas, a l'exterieur")
    #dao.commentSensor(3, "dans l'isolation, a l'exterieur")
    #dao.commentSensor(4, 'Pale du bas, au milieu')
    Thread(target=workerDS, args=(iface, stop, mesure_reussie)).start()
    time.sleep(5)
    #onoffventilo = OnOff(pin, value_to_trigger, mode=True)
    #onoffpompe = OnOff(pin, value_to_trigger, mode=False)
    #tempvalue = Value('f', 0)
    #rhvalue = Value('f', autre)
    #Thread(target=onoff.run, args=(tempvalue, stop)).start()
    pin = "P9_31"
    onoffdiode = OnOff(pin, 0.5)
    diode = Value('b', True)
    Thread(target=onoffdiode.run, args=(diode, stop)).start()


    try:
        while True:
            #tempvalue.value = dsTemp[??]
            if mesure_reussie.value:
                for i in range(len(iface.dsTemp)):
                    dao.newMeasure(i+1, iface.dsTemp[i].GetTemperature())
                diode.value = not diode.value
            time.sleep(5)
    except KeyboardInterrupt:
        print('End of record')
        stop.value = True


