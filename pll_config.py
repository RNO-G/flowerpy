import i2c_bridge
import binascii
import gc
import time

class ClockConfig:
    def __init__(self):
        
        self.i2c = i2c_bridge()
        self.i2c.write(0xFF, 0x00) #set to page 0
        self.page = 0

    def configure(self):
        #
        # config procedure for Si5338. A pain in the neck!
        #
        #disable clock outputs
        self.readModifyWrite(230, 0x10, 0x10)
        #pause LOL
        self.write(241, 0x80)
        #load register config
        self.load(TODO)
        #'Validate clock input status'
        val = 4
        while val & 0x4:
            val = self.read(218)
        #'Configure PLL for locking'
        self.read_modify_write(49, 0x00, 0x80)
        #'Wait 25 ms'
        time.sleep(0.025)
        #'Restart LOL'
        self.write(241, 0x65)
        #'Confirm PLL Lock Status'
        val = 0x11
        while val & 0x11:
            val = self.read(218)
        #'Copy FCAL registers'
        # 237[1:0] to 47[1:0]
        val = self.read(237)
        val &= 0x3
        self.readModifyWrite(47, cal, 0x3)
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
        # Enable outputs
        self.readModifyWrite(230, 0x00, 0x10)
        
        
    def load(self, filename=None):
        None

    def read(self, addr):
        val = self.i2c.read(adr)[0]
        return val

    def write(self, addr, val):
        self.i2c.write(addr, val)


    def readModifyWrite(self, addr, val, mask):
        #
        # MASK = bits to be updated
        #
        oldval = self.read(addr)
        oldval &= mask ^ 0xFF
        #make sure we write sensible values
        val = val & mask
        val |= oldval
        self.write(addr, val)
        

def loadRegisterFile(filename='config/Si5338-Registers.h'):
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
    loadRegisterFile()
    
