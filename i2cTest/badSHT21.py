from Adafruit_I2C import Adafruit_I2C
import time

######################################################
#The BBB has 3 i2c, to activate the third one :
#echo BB-I2C1 > /sys/devices/bone_capemgr.9/slots
#to check: 
#ls -l /sys/bus/i2c/devices/i2c-*
# or i2cdetect -r -y 2
#####################################################


class SHT21:
    Tmeasure_Hold    = 0xE3
    RHmeasure_Hold   = 0xE5
    Tmeasure_noHold  = 0xF3
    RHmeasure_noHold = 0xF5
    write_reg = 0xE6
    read_reg  = 0xE7
    soft_reset = 0xFE
    #writing on this registers works
    unknown1 = 0xFA
    unknown2 = 0xFC
    unknown3 = 0x1A
    unknown4 = 0x1C
    unknown5 = 0x06
    #reading those works too, but none are in the documentation
    #none were found, but spamming reading any reg value will get some results... 
    def __init__(self, name):
        self.name = name
        self.i2c = Adafruit_I2C(0x40, debug=True)
 
    def getRH(self, reg):
        self.i2c.write8(0, self.RHmeasure_noHold)
        time.sleep(1)
        #rawRH = self.i2c.readList(self.read_reg, 3)
        rawRH = self.i2c.readU16(0)
        #RH = rawRH[0]*256+rawRH[1]-2
        #RH1 = rawRH[1]*256+rawRH[0]-2
        RH = -6.+125.*rawRH/65536.0
        RH1 = -6.+125.*self.i2c.reverseByteOrder(rawRH)/65536.
        return RH, RH1

    def getT(self,reg):
        self.i2c.write8(reg, self.Tmeasure_noHold)
        time.sleep(1)
        #rawT = self.i2c.readList(self.read_reg, 3)
        rawT = self.i2c.readU16(self.read_reg)
        #T = rawT[0]*256+rawT[1]
        #T1 = rawT[1]*256+rawT[0]
        #T = -46.85+175.72*T/65536
        #T1 = -46.85+175.72*T1/65536
        T = -46.85+175.72*rawT/65536.
        T1 = -46.85+175.72*self.i2c.reverseByteOrder(rawT)/65536.
        return T,T1
    
    def reset(self, reg):
        self.i2c.write8(reg, self.soft_reset)

sensor = SHT21('test')
reg = 0xE6
print sensor.getRH(reg)
time.sleep(1)
print sensor.getT(reg)

if False:
    try:
        liste = []
        while True:
            liste.append(sensor.getT())
            time.sleep(10)

    except KeyboardInterrupt, err:
        print 'End of recording'


