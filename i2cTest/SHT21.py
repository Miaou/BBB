from smbus import SMBus
import time

class SHT21 :
    RHmeasure_noHold = 0xF5
    Tmeasure_noHold  = 0xF3
    RHmeasure_Hold   = 0xE5
    Tmeasure_Hold    = 0xE3
    Soft_Reset       = 0xFE
    Write_Reg        = 0xE6
    Read_Reg         = 0xE7
    
    def __init__(self, addr, busnum = 1) :
        self.address = addr
        self.bus = SMBus(busnum)
        self.Reset()
        reg = self.ReadReg()
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
        time.sleep(1)
        RH = self.bus.read_byte(self.address)
        RH1 = self.bus.read_byte(self.address)
        crc = [RH, RH1, self.bus.read_byte(self.address)]
        #print bin(RH), bin(RH1)
        print self.CheckCRC(crc), self.CheckCRC2(crc)
        return -6+125.*(RH*256+RH1)/65536.

    def getT(self):
        self.bus.write_byte(self.address, self.Tmeasure_noHold)
        time.sleep(1)
        T = self.bus.read_byte(self.address)
        T1 = self.bus.read_byte(self.address)
        crc = [T, T1, self.bus.read_byte(self.address)]
        #print bin(T), bin(T1)
        print self.CheckCRC(crc), self.CheckCRC2(crc)
        return -46.85+175.72*(T*256+T1)/65536.
    
    def Reset(self):
        self.bus.write_byte(self.address, self.Soft_Reset)
        time.sleep(0.02) #must wait 15ms

    def ReadReg(self):
        reg = self.bus.read_word_data(self.address, self.Read_Reg)
        crc = [ reg & 0xFF, (reg & 0xFF00) >> 8]
        
        if self.CheckCRC(crc):
            return reg & 0xFF
        else:
            print 'Error : CRC not matching !'
            return 0
        
    def WriteReg(self, val):
        reg = self.ReadReg()
        reg &= 0x38
        self.bus.write_byte_data(self.address, self.Write_Reg, val)

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

    def CheckCRC2(self, buf):
        poly = 0x8C
        s = 0
        #print buf[2]
        for by in buf:
            for i in range(8):
                r =  (s&0x01)
                f = (by&0x01)
                by >>= 1
                xor = poly if (r^f) else 0
                s = ((s>>1) ^ xor)&0xFF
                #print s
        return s==0

sensor = SHT21(0x40)
if True:
    print sensor.getRH()
    print sensor.getT()

if False:
    print sensor.ReadReg()
