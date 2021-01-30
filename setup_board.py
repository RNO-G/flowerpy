import flower
import pll_config
import time

CONFIG_REG_0 = 0x3B
CONFIG_REG_1 = 0x3C
PD_REG       = 0x3A

HMCAD_ADR_RESET = 0x00
HMCAD_ADR_NUM_CHAN = 0x31
HMCAD_ADR_FULL_SCALE_RANGE = 0x55
HMCAD_ADR_INPUTSEL_0 = 0x3A
HMCAD_ADR_INPUTSEL_1 = 0x3B
HMCAD_ADR_ADC_CURRENT = 0x50
HMCAD_ADR_LVDS_DRIVE = 0x11

def spiWriteBothADCS(dev, reg, cmd_hi, cmd_lo):
    dev.write(dev.DEV_FLOWER, [CONFIG_REG_0, 0,0,0]) #select ADC0
    dev.write(dev.DEV_FLOWER, [CONFIG_REG_1, reg, cmd_hi, cmd_lo]) #config ADC0
    dev.write(dev.DEV_FLOWER, [CONFIG_REG_0, 0,0,1]) #select ADC1
    dev.write(dev.DEV_FLOWER, [CONFIG_REG_1, reg, cmd_hi, cmd_lo]) #config ADC1
    
def adcReset(dev):
    #first, sw reset (this also puts all HMCAD registers back to default)
    spiWriteBothADCS(dev, HMCAD_ADR_RESET, 0x00, 0x01)
    #second, cycle the PD pin
    dev.write(dev.DEV_FLOWER, [PD_REG, 0, 0, 1]) #assert adc power down
    dev.write(dev.DEV_FLOWER, [PD_REG, 0, 0, 0]) #de-assert adc power down


if __name__=='__main__':

    ## configure PLL
    pll = pll_config.ClockConfig()
    pll.configure('config/Si5338-RevB-Registers-472MHz.h')

    ## setup ADC chips
    dev = flower.Flower()
    adcReset(dev)
    spiWriteBothADCS(dev, HMCAD_ADR_NUM_CHAN, 0, 2) #config to 2-chan operation, clkdivide=1
    spiWriteBothADCS(dev, HMCAD_ADR_INPUTSEL_0, 0x02, 0x02) #set IN1 to ADC1 and ADC2
    spiWriteBothADCS(dev, HMCAD_ADR_INPUTSEL_1, 0x80, 0x80) #set IN3 to ADC3 and ADC4
    spiWriteBothADCS(dev, HMCAD_ADR_LVDS_DRIVE, 0x05, 0x55) #set LVDS drive to RSDS standards
    
