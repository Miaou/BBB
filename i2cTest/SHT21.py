from Adafruit_I2C import Adafruit_I2C
import time

class SHT21:
    Tmeasure_Hold    = 0xE3
    RHmeasure_Hold   = 0xE5
    Tmeasure_noHold  = 0xF3
    RHmeasure_noHold = 0xF5
    write_reg = 0xE6
    read_reg  = 0xE7
    def __init__(self, name):
        self.name = name
        self.i2c = Adafruit_I2C(0x40, debug=True)
 
    def getRH(self):
        self.i2c.write8(self.write_reg, self.RHmeasure_noHold)
        time.sleep(1)
        rawRH = self.i2c.readList(self.read_reg, 3)
        print hex(rawRH[0]), hex(rawRH[1])
        print inttobits(rawRH[0]), inttobits(rawRH[1])
        RH = rawRH[0]*256+rawRH[1]-2
        RH1 = rawRH[1]*256+rawRH[0]-2
        RH = -6+125*RH/65536
        RH1 = -6+125*RH1/65536
        return RH, RH1

    def getT(self):
        self.i2c.write8(self.write_reg, self.Tmeasure_noHold)
        time.sleep(1)
        rawT = self.i2c.readList(self.read_reg, 3)
        rawT = self.i2c.readU16(self.write_reg)
        #T = rawT[0]*256+rawT[1]
        #T1 = rawT[1]*256+rawT[0]
        #T = -46.85+175.72*T/65536
        #T1 = -46.85+175.72*T1/65536
        T = -46.85+175.72*rawT/65536
        T1 = -46.85+175.72*self.i2c.reverseByteOrder(rawT)/65536
        return T,T1


sensor = SHT21('test')
print sensor.getRH()
print sensor.getT()
