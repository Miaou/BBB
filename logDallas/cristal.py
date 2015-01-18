#!/usr/bin/python3
# Testing everything together.

# But the command needs GPIO in Python3... So it will wait, and will be done in another program...

# This is very impressive how much it is not easy to manipulate the sensors...


import sys
sys.path.append('../libDS18B20/libDallas-PRU')
sys.path.append('../thermoLog')

# FIXME: importing pruicss is UGLY
# FIXME: importing dallas from another directory breaks the path to dallas.bin
from dallas import OneWire, Sensor, pruicss
# FIXME: expr* are maybe not well defined besides the DAO
from dao import DAO, exprRawToCelsiusDS, exprRawToCelsiusMLX
from threading import Thread
from multiprocessing import Value
import smbus # Install: cf ../doc
import time
from binascii import hexlify, unhexlify


sDB = 'cristal.db'


# Small interface, holds temperatures and command values
class Iface:
    def __init__(self):
        self.iTempEau = 0
        self.iTempAirDS = 0
        self.iTempAirML = 0
        self.iTempObj = 0
        self.iCmd = 0


# Dans un thread, on a l'acquisition et la commande
def workerHWIFace(iface, bEnd):
    wire = OneWire(9,13, 9,14, pruicss)
    wire.SearchMoreRoms()
    bus = smbus.SMBus(1)
    print('Starting measures')
    while not bEnd.value:
        # Temperatures from the DS18B20s
        wire.ConvertTemperatures()
        wire.ReadTemperatures()
        iface.iTempEau   = wire.dSensors[unhexlify(b'289abbab05000057')].GetTemperatureRaw()
        iface.iTempAirDS = wire.dSensors[unhexlify(b'28cde9f505000027')].GetTemperatureRaw()
        # Temperatures from the MLX90614
        try:
            iface.iTempAirML = bus.read_word_data(0x5A, 0x06)
            iface.iTempObj   = bus.read_word_data(0x5A, 0x07)
        except IOError:
            print('IO Err on I2C bus, but it\'s okay')
        # Cmd is not elaborated here yet (install Adafruit_BBIO for Py3 first)
        time.sleep(0.01)
    print('Measures stopped')



if __name__=='__main__':
    dao = DAO(sDB)
    # One time inits
    if True:
        # The serials are hexlified versions, to be more readable.
        dao.newSensor(b'DS18B20P', b'28cde9f505000027', exprRawToCelsiusDS)
        dao.newSensor(b'DS18B20P', b'289abbab05000057', exprRawToCelsiusDS) # Waterproof
        dao.newSensor(b'MLX90614', b'Ambient', exprRawToCelsiusMLX)
        dao.newSensor(b'MLX90614', b'Object', exprRawToCelsiusMLX)
        dao.newSensor(b'CommandeBouilleur')

    iface = Iface()
    bEnd = Value('b', False)
    Thread(target=workerHWIFace, args=(iface,bEnd)).start()

    if True:
        dao.newWave(sComment='Cristaux, chauffe un peu pas longtemps')
        # FIXME: change dao API, comment sensor with bPartNumber,bHardID...
        dao.commentSensor(1, 'Sur la breadboard, un peu loin de la casserole', 'Air (°C)')
        dao.commentSensor(2, 'Dans l\'eau, le plus loin de la résistance', 'Eau (°C)')
        dao.commentSensor(3, 'Sur la breadboard, près de la casserole', 'Air (°C)')
        dao.commentSensor(4, 'Vise le cul de la casserole', 'Eau, ext (°C)')
        dao.commentSensor(5, 'N/A')
        t0 = time.time()
        try:
            while not bEnd.value:
                while time.time()-t0 > 1:
                    time.sleep(.001)
                t0 += 1
                assert time.time()-t0 < 1
                # FIXME: think about sensorID too in newMeasure...
                iT = int(time.time())
                # Records measures
                dao.newMeasure(1, iface.iTempAirDS, iT)
                dao.newMeasure(2, iface.iTempEau, iT)
                dao.newMeasure(3, iface.iTempAirML, iT)
                dao.newMeasure(4, iface.iTempObj, iT)
        except KeyboardInterrupt:
            print('Ending record')
            bEnd.value = True





