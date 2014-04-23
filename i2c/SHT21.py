from smbus import SMBus
import time

#dont forget to :
#echo BB-I2C1 > /sys/devices/bone_capemgr.9/slots
#to enable i2c1, on bus 2(bus 0 is system reserved)

class SHT21 :
    RHmeasure_noHold = 0xF5
    Tmeasure_noHold  = 0xF3
    RHmeasure_Hold   = 0xE5
    Tmeasure_Hold    = 0xE3
    Soft_Reset       = 0xFE
    Write_Reg        = 0xE6
    Read_Reg         = 0xE7
##############################################################################
##  Experimental register found by looking for each one individually        ##
##  with a 10 seconds wait between each try. CheckCRC says true for all.    ##
    RH_Reg           = 0x05                                                 ##
    T_Reg            = 0x03                                                 ##
##  read_reg?          0x06                                                 ##
##  read_reg           0x07                                                 ##
##  unknown            0x09     result was 6,0,90(constant over time)       ##
##  unknown            0x0F     result was 2,68,32(constant over time)      ##
##  serial number?     0x1A     periodic on 64 bits?                        ##
##  result was      [25, 203, 218, 223, 71, 170, 137, 242, 217, 140, 232    ##
##                  , 120, 231, 86, 128, 122, 7, 151, 248, 59, 252, 255,    ##
##                  232, 120, 54, 99, 129, 75, 30, 92, 80, 126]             ##
##  serial number?     0x1B     same as 0x1A with random shift              ##
##  T_reg?             0xE3     result was 103,88,60(made a new measure?)   ##
##  RH_reg?            0xE5     result was 83,206,146(new measure?)         ##
##  read_reg           0xE6     result was 58,30                            ##
##  read_reg           0xE7     result was 58,30                            ##
##  unknown            0xE9     result was 6,0,90                           ##
##  unknown            0xEF     result was 2,68,32                          ##
##  serial number      0xFA     same as 1A, check sensirion(says 64 bits ID)##
##  serial number?     0xFB     same as 1B                                  ##
##  device ID?         0xFF     check i2c full specs, results seems random  ##
############################1#################################################
    class CRCError(Exception):
        pass

    def __init__(self, addr, busnum = 1) :
        self.address = addr
        self.bus = SMBus(busnum)
        #self.bus.open(busnum)
        self.Reset()
        #reg = self.ReadReg()
        reg = 0
        if (reg & 0x80) and (reg & 0x01):
            self.RH_res = 11
            self.T_res  = 11
        elif (reg & 0x80) and not(reg & 0x01):
            self.RH_res = 10
            self.T_res  = 13
        elif not(reg & 0x80) and not(reg & 0x01):
            self.RH_res = 12
            self.T_res  = 14
        else:
            self.RH_res = 8
            self.T_res  = 12

    def getRH(self):
        self.bus.write_byte(self.address, self.RHmeasure_noHold)
        time.sleep(0.1)
        RH = self.bus.read_i2c_block_data(self.address, self.RH_Reg, 3)
        #print RH
        if self.CheckCRC(RH):
            self.RHum = RH
            RH[1] &= ~0x03      #reset 2 status bits(LSB)
            return -6+125.*(RH[0]*256+RH[1])/65536.
        else:
            #print 'CRC checksum failed, data was corrupted(RH reading)'
            #return -1
            raise self.CRCError


    def getT(self):
        self.bus.write_byte(self.address, self.Tmeasure_noHold)
        time.sleep(0.1)
        T = self.bus.read_i2c_block_data(self.address, self.T_Reg, 3)
        #print T
        if self.CheckCRC(T):
            self.Temp = T
            T[1] &= ~0x03       #reset 2 status bits(LSB)
            return -46.85+175.72*(T[0]*256+T[1])/65536.
        else:
            #print 'CRC checksum failed, data was corrupted(temp reading)'
            #return -1
            raise self.CRCError
    
    def Reset(self):
        self.bus.write_byte(self.address, self.Soft_Reset)
        time.sleep(0.02) #must wait 15ms

    def ReadReg(self):
        reg = self.bus.read_word_data(self.address, self.Read_Reg)
        crc = [ reg & 0xFF, (reg & 0xFF00) >> 8]
        
        if self.CheckCRC(crc):
            return reg & 0xFF
        else:
            #print 'Error : CRC not matching !'
            #return 0
            raise self.CRCError
        
    def WriteReg(self, val):
        reg = self.ReadReg()
        reg &= 0x38
        self.bus.write_byte_data(self.address, self.Write_Reg, val)

    def test(self):
        self.T = []
        self.getRH()
        self.getT()
        for i in range(256):
            try :
                time.sleep(10)
                self.T.append((hex(i), self.bus.read_i2c_block_data(sensor.address, i)))
                print(hex(i), 'success reading')
            except IOError as err:
                print(hex(i), 'failed reading')
        return self.T

    def CheckCRC(self, buf):
        poly = 0x131
        crc = 0
        #print buf[2]
        for by in buf:
            crc ^= by
            for i in range(8):
                if crc & 0x80 :
                    crc = (crc << 1)^poly
                else:
                    crc <<= 1
                #print crc
        return crc==0

if __name__ == '__main__':
    sensor = SHT21(0x40)
    print(sensor.getRH())
    print(sensor.getT())



