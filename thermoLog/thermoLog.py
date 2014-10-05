#
#

from Adafruit_BBIO import UART # Used to create '/dev/ttyOx' with x in range(4)
import serial
import time
from dao import DAO



# RX1 on P9_26
UART.setup('UART1')
ser = serial.Serial('/dev/ttyO1') # 9600, as connection between BT -> Android is 9600


# Data model is "well" defined, but RX-sync is done down in the log function ^^
def log(ser, iSecInterval):
    dao = DAO()
    ser.flushInput()
    t0 = time.time()-iSecInterval
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


