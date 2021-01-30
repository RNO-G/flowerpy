import i2c_bridge
import binascii
import gc
import time

class ClockConfig:
    def __init__(self):
        
        self.i2c = i2c_bridge.I2CBridge()
        self.i2c.write(0xFF, 0x00) #set to page 0
        self.page = 0

    def configure(self, filename='config/Si5338-Registers.h'):    
        #
        # config procedure for Si5338. A pain in the neck!
        #
        #disable clock outputs
        self.readModifyWrite(230, 0x10, 0x10)
        #pause LOL
        self.write(241, 0x80)
        #load register config
        self.load(filename)
        #'Validate clock input status'
        val = 4
        while val & 0x4:
            val = self.read(218)
        #'Configure PLL for locking'
        self.readModifyWrite(49, 0x00, 0x80)
        #'Initiate locking of PLL'
        self.readModifyWrite(246, 0x2, 0x2)
        #'Wait a bit'
        time.sleep(0.1)
        #'Restart LOL'
        self.write(241, 0x65)
        #'Confirm PLL Lock Status'
        val = 0x11
        print('waiting on lock status....\r')
        while val & 0x11:
            val = self.read(218)
        print('done')
        #'Copy FCAL registers'
        # 237[1:0] to 47[1:0]
        val = self.read(237)
        val &= 0x3
        self.readModifyWrite(47, val, 0x3)
        # 236 to 46
        val = self.read(236)
        self.write(46, val)
        # 235 to 45
        val = self.read(235)
        self.write(45, val)
        # set 47 [7:2] to 00101b
        self.readModifyWrite(47, 0x14, 0xFC)
        # 'Set PLL to use FCAL values'
        self.readModifyWrite(49, 0x80, 0x80)
        # Not using down-spread
        # Enable outputs reg_230[4]
        self.readModifyWrite(230, 0x00, 0x10)

    def disableOutputs(self):
        self.readModifyWrite(230, 0x10, 0x10)
        
    def load(self, filename):        
        config_registers = loadRegisterFile(filename)
        for i in range(len(config_registers)):
            mask = config_registers[i][2]
            addr = config_registers[i][0]
            val  = config_registers[i][1]
            if mask == 0:
                continue
            elif mask != 0xFF:
                self.readModifyWrite(addr, val, mask)
            else:
                self.write(addr, val)     

    def read(self, addr):
        val = self.i2c.read(addr)[3]
        return val

    def write(self, addr, val):
        self.i2c.write(addr, val)

    def readModifyWrite(self, addr, val, mask):
        #
        # MASK = bits to be updated
        #
        oldval = self.read(addr)
        #print 'rmw', oldval
        oldval &= mask ^ 0xFF
        #make sure we write sensible values
        val = val & mask
        val |= oldval
        self.write(addr, val)
        
def loadRegisterFile(filename):
    #
    # parser of the c header file from ClockBuilderPro
    #
    pll_configuration_registers = []
    with open(filename, 'r') as f:
        for line in f:
            if line[0] == '{':
                line = line.replace('{', '')
                line = line.replace('}', '')
                line = line.replace(';', ',')
                ##OK, this should give a usable per-line list now:
                tmp = line.split(',')
                ## tmp[0]=register, tmp[1]=hex value, tmp[2]=hex mask
                pll_configuration_registers.append([int(tmp[0]), int(tmp[1], 16), int(tmp[2], 16)])

    f.close()
    
    return pll_configuration_registers
    
if __name__=='__main__':
    pll = ClockConfig()
    pll.configure()
    #pll.disableOutputs()
