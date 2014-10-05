#
#

from Adafruit_BBIO import UART # Used to create '/dev/ttyOx' with x in range(4)
import serial
import time
import sqlite3


# RX1 on P9_26
UART.setup('UART1')
ser = serial.Serial('/dev/ttyO1') # 9600, as connection between BT -> Android is 9600


class DAO:
    #RAW_TO_CELSIUS = lambda i:i*.02-273.15 # Python3-style
    @staticmethod
    def RAW_TO_CELSIUS(i):
        return i*.02-273.15

    def __init__(self, sDB='thermoLog.db', curWave=int(time.time())):
        self.sDB = sDB
        self.db = sqlite3.connect(self.sDB)
        self.curWave = curWave
        with self.db as db:
            db.execute('CREATE TABLE IF NOT EXISTS logThermo(wave INTEGER, time INTEGER,\
                        iTempAmb INTEGER, iTempObj INTEGER, PRIMARY KEY(wave,time));')

    def newEntry(self, fTime, iRawTempA, iRawTempO):
        with self.db as db:
            db.execute('INSERT INTO logThermo VALUES(?,?,?,?)', (self.curWave, int(fTime), iRawTempA, iRawTempO))
    
    def listWaves(self):
        return [wave for wave, in self.db.execute('SELECT DISTINCT wave FROM logThermo')]
    def listEntriesWave(self, wave):
        return [(t,DAO.RAW_TO_CELSIUS(a),DAO.RAW_TO_CELSIUS(b)) for t,a,b in self.db.execute('SELECT time,iTempAmb,iTempObj FROM logThermo WHERE wave=?', (wave,))]
    def listEntries(self):
        return self.listEntriesWave(self.curWave)

    def showWaves(self):
        for i,wave in enumerate(self.listWaves()):
            print '{:>3d} @ {},  {} samples'.format(i, time.ctime(wave), self.db.execute('SELECT count(time) FROM logThermo WHERE wave=?', (wave,)).fetchone()[0])


# Data model is "well" defined, but RX-sync is done down in the log function ^^
def log(ser, iSecInterval):
    dao = DAO()
    ser.flushInput()
    t0 = time.time()
    try:
        while True: # Moche caca !!
            t = time.time()
            if t-t0 > iSecInterval:
                while ser.read() != 'O': pass
                # Should have used struct.unpack? Hmmm...
                a,b,x,c,d = map(ord,ser.read(5)) # maps where lists... so 2009...
                iRawO = a+b*256
                iRawA = c+d*256
                dao.newEntry(t, iRawA, iRawO)
                t0 += iSecInterval
                print time.ctime(t), DAO.RAW_TO_CELSIUS(iRawA), DAO.RAW_TO_CELSIUS(iRawO)
            time.sleep(.001)
            ser.flushInput()
    except KeyboardInterrupt:
        print 'Ending'


print 'log(ser, iSecInterval)'


