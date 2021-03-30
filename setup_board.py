import flower
import pll_config
import time

##registers on FPGA-->
CONFIG_REG_0 = 0x3B
CONFIG_REG_1 = 0x3C
PD_REG       = 0x3A #note this is same as DATVALID reg, but no conflict

##registers on HMCAD-->
HMCAD_ADR_RESET = 0x00
HMCAD_ADR_NUM_CHAN = 0x31
HMCAD_ADR_FULL_SCALE_RANGE = 0x55
HMCAD_ADR_INPUTSEL_0 = 0x3A
HMCAD_ADR_INPUTSEL_1 = 0x3B
HMCAD_ADR_ADC_CURRENT = 0x50
HMCAD_ADR_LVDS_DRIVE = 0x11
HMCAD_ADR_INVERT_INP = 0x24
HMCAD_ADR_TP_MODE = 0x25
HMCAD_ADR_TP_WORD1 = 0x26
HMCAD_ADR_TP_WORD2 = 0x27
HMCAD_ADR_TP_SYNC = 0x45
HMCAD_ADR_PHASE_DDR = 0x42
HMCAD_ADR_BYTE_FORMAT = 0x46
HMCAD_ADR_VCM_DRIVE = 0x50
HMCAD_ADR_STARTUP = 0x56

def spiWriteBothADCS(dev, reg, cmd_hi, cmd_lo):
    dev.write(dev.DEV_FLOWER, [CONFIG_REG_0, 0,0,0]) #select ADC0
    dev.write(dev.DEV_FLOWER, [CONFIG_REG_1, reg, cmd_hi, cmd_lo]) #config ADC0
    dev.write(dev.DEV_FLOWER, [CONFIG_REG_0, 0,0,1]) #select ADC1
    dev.write(dev.DEV_FLOWER, [CONFIG_REG_1, reg, cmd_hi, cmd_lo]) #config ADC1
    
def adcPowerDown(dev, pd):
    if pd:
        dev.write(dev.DEV_FLOWER, [PD_REG, 0, 0, 1]) #assert adc power down
    else:
        dev.write(dev.DEV_FLOWER, [PD_REG, 0, 0, 0]) #de-assert adc power down

def datValid(dev, en):
    if en:
        dev.write(dev.DEV_FLOWER, [dev.map['DATVALID'], 0, 1, 0])
    else:
        dev.write(dev.DEV_FLOWER, [dev.map['DATVALID'], 0, 0, 0])

def configADC(dev):
    ###hard-coded setup for 2-ch operation
    ###-----------------------------------
    #initial sw reset of internal HMCAD registers
    spiWriteBothADCS(dev, HMCAD_ADR_RESET, 0x00, 0x01)
    time.sleep(4)
    ##now, config:
    adcPowerDown(dev, True) #power down
    spiWriteBothADCS(dev, HMCAD_ADR_PHASE_DDR, 0x00, 0x60) #set DDR phase to 0
    #spiWriteBothADCS(dev, HMCAD_ADR_PHASE_DDR, 0x00, 0x40) #set DDR phase to 90
    #spiWriteBothADCS(dev, HMCAD_ADR_PHASE_DDR, 0x00, 0x20) #set DDR phase to 180
    #spiWriteBothADCS(dev, HMCAD_ADR_PHASE_DDR, 0x00, 0x00) #set DDR phase to 270
    spiWriteBothADCS(dev, HMCAD_ADR_BYTE_FORMAT, 0x00, 0x08) #set MSB first
    spiWriteBothADCS(dev, HMCAD_ADR_VCM_DRIVE, 0x00, 0x30) #turn up VCM drive..
    spiWriteBothADCS(dev, HMCAD_ADR_LVDS_DRIVE, 0x05, 0x55) #set LVDS drive to RSDS standards
    spiWriteBothADCS(dev, HMCAD_ADR_NUM_CHAN, 0x00, 0x02) #config to 2-chan operation, clkdivide=1
    spiWriteBothADCS(dev, HMCAD_ADR_STARTUP, 0x00, 0x04) #configure start-up time according to datasheet
    #spiWriteBothADCS(dev, HMCAD_ADR_INVERT_INP, 0x00, 0x30) #invert inputs, 2ch mode
    adcPowerDown(dev, False) #startup!
    print 'starting up...'
    time.sleep(15)
    #configure input cross-switch selection
    spiWriteBothADCS(dev, HMCAD_ADR_INPUTSEL_0, 0x02, 0x02) #set IN1 to ADC1 and ADC2
    #spiWriteBothADCS(dev, HMCAD_ADR_INPUTSEL_0, 0x08, 0x08) #set IN1 to ADC1 and ADC2    
    spiWriteBothADCS(dev, HMCAD_ADR_INPUTSEL_1, 0x08, 0x08) #set IN3 to ADC3 and ADC4

    adcPowerDown(dev, True)
    adcPowerDown(dev, False)
    time.sleep(15)
    
if __name__=='__main__':

    ## configure PLL
    pll = pll_config.ClockConfig()
    pll.configure('config/Si5338-RevB-Registers-472MHz.h')
    time.sleep(1)
    
    ## setup ADC chips
    dev = flower.Flower()
    datValid(dev, 0)

    configADC(dev)
    
    # Test Pattern 
    spiWriteBothADCS(dev, HMCAD_ADR_TP_WORD1, 0x71, 0x00)
    spiWriteBothADCS(dev, HMCAD_ADR_TP_WORD2, 0xAF, 0x00)

    #spiWriteBothADCS(dev, HMCAD_ADR_TP_MODE, 0x00, 0x40) #set ramp test pattern
    spiWriteBothADCS(dev, HMCAD_ADR_TP_MODE, 0x00, 0x20) #set dual-custom word pattern
    #spiWriteBothADCS(dev, HMCAD_ADR_TP_MODE, 0x00, 0x10) #set single-custom word pattern
    #spiWriteBothADCS(dev, HMCAD_ADR_TP_MODE, 0x00, 0x00) #turn off test pattern
    #spiWriteBothADCS(dev, HMCAD_ADR_TP_SYNC, 0x00, 0x02) #enable sync pattern
    spiWriteBothADCS(dev, HMCAD_ADR_TP_SYNC, 0x00, 0x00) #turn off sync pattern

    #set bitshift to 0
    dev.write(dev.DEV_FLOWER, [0x42, 0x00, 0x00, 0x00])
    
    ##enable data-valid --> data from ADCs should start flowing into FPGA
    datValid(dev, 1)
    
