# trigger control for FLOWER board.

import flower

class FlowerTrig():
    
    map = {
        'SCALER_READ_REG'        : 0x03,
        'SCALER_SEL_REG'         : 0x29,
        'SCALER_UPDATE_REG'      : 0x28,
        'COINC_TRIG_CH0_THRESH'  : 0x57,
        'COINC_TRIG_CH1_THRESH'  : 0x58,
        'COINC_TRIG_CH2_THRESH'  : 0x59,
        'COINC_TRIG_CH3_THRESH'  : 0x5A,
        'COINC_TRIG_PARAM'       : 0x5B,
        'TRIG_ENABLES'           : 0x3D,
        'PHASED_THRESHOLDS':0x80,
        'PHASED_MASK': 0x50
    }
    
    def __init__(self):
        self.dev = flower.Flower()

    def initPhasedTrig(self, power=0xfff, servo=0xfff, num_beams=12, mask=0xffff, offset=0000, do_readback=False):
        for i in range(num_beams):
            self.dev.write(self.dev.DEV_FLOWER, [self.map['PHASED_THRESHOLDS']+i, (servo&0xff0)>>4, ((servo&0x00f)<<4)+((power&0xf00)>>8), power&0xff])
        self.dev.write(self.dev.DEV_FLOWER, [self.map['PHASED_MASK'], 0, (mask&0xff00)>>8, mask&0xff])
        self.dev.write(self.dev.DEV_FLOWER, [self.map['PHASED_MASK']+1, 0, (offset&0xff00)>>8, (offset&0xff)])
        if do_readback:self.read_phased_trig()

    def readPhasedTrig(self, num_beams=12):
        for i in range(num_beams):
            thresh=self.dev.readRegister(self.dev.DEV_FLOWER, self.map['PHASED_THRESHOLDS']+i)
            print(thresh)

    def initCoincTrig(self, num_coinc=2, thresh=[127,127,127,127], servo_thresh=[127,127,127,127], vppmode=True, coinc_window=2,mask=0xf):
        for i in range(4):
            self.dev.write(self.dev.DEV_FLOWER, [self.map['COINC_TRIG_CH0_THRESH']+i,0,servo_thresh[i], thresh[i]])
        self.dev.write(self.dev.DEV_FLOWER, [self.map['COINC_TRIG_PARAM'],
                                             vppmode,coinc_window, num_coinc])
        self.dev.write(self.dev.DEV_FLOWER,[self.map['COINC_TRIG_PARAM']+4,0,0,mask])

    def setScalerOut(self, scaler_adr=0):
        if scaler_adr < 0 or scaler_adr > 6*(16+1)+32:
            print('out of bounds')
            return None
        self.dev.write(self.dev.DEV_FLOWER, [self.map['SCALER_SEL_REG'],0,0,scaler_adr])
        #print self.dev.readRegister(self.dev.DEV_FLOWER, 41)
        
    def readSingleScaler(self):
        self.dev.write(self.dev.DEV_FLOWER, [self.map['SCALER_UPDATE_REG'],0,0,1])
        read_scaler_reg = self.dev.readRegister(self.dev.DEV_FLOWER,self.map['SCALER_READ_REG'])
        scaler_low = (read_scaler_reg[2] & 0x0F) << 8 | read_scaler_reg[3]
        scaler_hi  = (read_scaler_reg[1] & 0xFF) << 4 | (read_scaler_reg[2] & 0xF0) >> 4
        return scaler_low, scaler_hi
    
    def readScalerPPS(self):
        if self.dev.firmware_version_int < 12:
            self.setScalerOut(31)
            scaler_pps = self.readSingleScaler()
        else:
            self.setScalerOut(0)
            scaler_pps = self.readSingleScaler()

        return scaler_pps

    def readCoincTrigScaler(self):
        if self.dev.firmware_version_int < 12:
            self.setScalerOut(0)
            coinc_trigger_scaler = self.readSingleScaler()[0]
        else:
            self.setScalerOut(3)
            coinc_trigger_scaler = self.readSingleScaler()[0]

        return coinc_trigger_scaler
    

    def readCoincTrigChannelScaler(self, channel=0):
        if self.dev.firmware_version_int < 12:
            if channel == 0:
                scaler_addr = 0
                reg_addr = 1
            elif (channel == 1) or (channel == 2):
                scaler_addr = 1
                reg_addr = channel - 1
            elif channel == 3:
                scaler_addr = 2
                reg_addr = 0

        else:
            if channel == 0:
                scaler_addr = 3
                reg_addr = 1
            elif (channel == 1) or (channel == 2):
                scaler_addr = 4
                reg_addr = channel - 1
            elif channel == 3:
                scaler_addr = 5
                reg_addr = 0

        self.setScalerOut(scaler_addr)
        return self.readSingleScaler[reg_addr]
        
    def readPhasedTrigScaler(self):
        if self.dev.firmware_version_int < 12:
            print("Image not running phased trigger")
            return 0
        else:
            self.setScalerOut(18)
            phased_trigger_scaler = self.readSingleScaler()[0]

        return phased_trigger_scaler

    def readPhasedTrigBeamScaler(self, beam=0):
        if self.dev.firmware_version_int < 12:
            print("Image not running phased trigger")
            return 0

        else:
            scaler_addr = int((beam + 1) / 2) + 18
            if (beam % 2) == 0:
                reg_addr = 1
            else:
                reg_addr = 0

        self.setScalerOut(scaler_addr)
        return self.readSingleScaler[reg_addr]

    def trigEnable(self, coinc_trig=0, phased_trig=0, pps_trig=0, ext_trig=0):
        '''specify '0' or '1' for trigger types
        '''
        self.dev.write(self.dev.DEV_FLOWER, [self.map['TRIG_ENABLES'],ext_trig, (phased_trig<<1)+coinc_trig, pps_trig])
        
    
    
