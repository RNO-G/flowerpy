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
    }
        
    def __init__(self):
        self.dev = flower.Flower()
    
    def initCoincTrig(self, num_coinc, thresh, vppmode=True, coinc_window=2):
        
        for i in range(4):
            self.dev.write(self.dev.DEV_FLOWER, [self.map['COINC_TRIG_CH0_THRESH']+i,0,0, thresh[i]])
        self.dev.write(self.dev.DEV_FLOWER, [self.map['COINC_TRIG_PARAM'],
                                             vppmode,coinc_window, num_coinc])

    def setScalerOut(self, scaler_adr=0):
        if scaler_adr < 0 or scaler_adr > 63:
            return None
        self.dev.write(self.dev.DEV_FLOWER, [self.map['SCALER_SEL_REG'],0,0,scaler_adr])
        #print self.dev.readRegister(self.dev.DEV_FLOWER, 41)
        
    def readSingleScaler(self):
        self.dev.write(self.dev.DEV_FLOWER, [self.map['SCALER_UPDATE_REG'],0,0,1])
        read_scaler_reg = self.dev.readRegister(self.dev.DEV_FLOWER,self.map['SCALER_READ_REG'])
        scaler_low = (read_scaler_reg[2] & 0x0F) << 8 | read_scaler_reg[3]
        scaler_hi  = (read_scaler_reg[1] & 0xFF) << 4 | (read_scaler_reg[2] & 0xF0) >> 4
        return scaler_low, scaler_hi

        
    
    
