import flower
import pll_config
import time
import align_adcs

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
HMCAD_ADR_CGAIN_CFG = 0x33
HMCAD_ADR_DUAL_CGAIN = 0x2B

##test patterns for start-up alignment
FLOWER_TEST_PAT_1 = 0x71
FLOWER_TEST_PAT_2 = 0xAF


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
    adcGainSelect(dev, 0)
    #spiWriteBothADCS(dev, HMCAD_ADR_INVERT_INP, 0x00, 0x30) #invert inputs, 2ch mode
    adcPowerDown(dev, False) #startup!
    print ('starting up...')
    time.sleep(15)
    #configure input cross-switch selection
    spiWriteBothADCS(dev, HMCAD_ADR_INPUTSEL_0, 0x02, 0x02) #set IN1 to ADC1 and ADC2
    #spiWriteBothADCS(dev, HMCAD_ADR_INPUTSEL_0, 0x08, 0x08) #set IN1 to ADC1 and ADC2    
    spiWriteBothADCS(dev, HMCAD_ADR_INPUTSEL_1, 0x08, 0x08) #set IN3 to ADC3 and ADC4

    adcPowerDown(dev, True)
    adcPowerDown(dev, False)
    time.sleep(15)


def testPatternBitShift(dev):
    ##enable dual-word test pattern + align datastreams

    #write test-pattern values
    spiWriteBothADCS(dev, HMCAD_ADR_TP_WORD1, FLOWER_TEST_PAT_1, 0x00)
    spiWriteBothADCS(dev, HMCAD_ADR_TP_WORD2, FLOWER_TEST_PAT_2, 0x00)

    #enable test-pattern output:
    spiWriteBothADCS(dev, HMCAD_ADR_TP_MODE, 0x00, 0x20) #set dual-custom word pattern
    spiWriteBothADCS(dev, HMCAD_ADR_TP_SYNC, 0x00, 0x00) #turn off sync pattern

    #set bitshift value to 0
    dev.write(dev.DEV_FLOWER, [0x42, 0x00, 0x00, 0x00])

    ##ALIGN ADC0 BITSTREAM using test-pattern
    bitshift_good = False
    bitshift_val = 0
    while(not bitshift_good and bitshift_val < 8):
        dev.bufferClear()
        dev.softwareTrigger()
        dat = dev.readRam(dev.DEV_FLOWER, 0, 16)
        if (dat[0][0] != FLOWER_TEST_PAT_1) and (dat[0][0] != FLOWER_TEST_PAT_2):
            #increment the bitshift
            reg = dev.readRegister(dev.DEV_FLOWER, 0x42)
            dev.write(dev.DEV_FLOWER, [0x42, 0x00, reg[2], bitshift_val])
        else:
            bitshift_good = True

        bitshift_val += 1

    ##ALIGN ADC1 BITSTREAM using test-pattern
    bitshift_good = False
    bitshift_val = 0
    while(not bitshift_good and bitshift_val < 8):
        dev.bufferClear()
        dev.softwareTrigger()
        dat = dev.readRam(dev.DEV_FLOWER, 0, 16)
        if (dat[2][0] != FLOWER_TEST_PAT_1) and (dat[2][0] != FLOWER_TEST_PAT_2):
            #increment the bitshift
            reg = dev.readRegister(dev.DEV_FLOWER, 0x42)
            dev.write(dev.DEV_FLOWER, [0x42, 0x00, bitshift_val, reg[3]])
        else:
            bitshift_good = True

        bitshift_val += 1

    spiWriteBothADCS(dev, HMCAD_ADR_TP_MODE, 0x00, 0x00) #disable test-pattern output
    
    return bitshift_good, bitshift_val
        
def pllConfig(filename='config/Si5338-RevB-Registers-472MHz.h'):
    ## configure PLL (only needs done on board power cycle)
    ## PLL needs to be configured before ADC can be setup
    pll = pll_config.ClockConfig()
    pll.configure(filename)
    time.sleep(1)

def adcGainSelect(dev, gain=0):
    '''
    if gain=0, 1x. 
    if gain=1, 2.5x
    if gain=2, 5x.
    if gain=3, 10x
    if gain=4, 20x
    '''
    if gain==0:
        spiWriteBothADCS(dev, HMCAD_ADR_DUAL_CGAIN, 0x00, 0x00)
    elif gain==1:
        spiWriteBothADCS(dev, HMCAD_ADR_DUAL_CGAIN, 0x00, 0x33)
    elif gain==2:
        spiWriteBothADCS(dev, HMCAD_ADR_DUAL_CGAIN, 0x00, 0x55)
    elif gain==3:
        spiWriteBothADCS(dev, HMCAD_ADR_DUAL_CGAIN, 0x00, 0x77)
    elif gain==4:
        spiWriteBothADCS(dev, HMCAD_ADR_DUAL_CGAIN, 0x00, 0xAA)
    elif gain==5:
        spiWriteBothADCS(dev, HMCAD_ADR_DUAL_CGAIN, 0x00, 0xCC)
    else:
        print ('incorrect gain setting')

def boardStartup(dev):
    ##run this on board startup
    #setup PLL
    pllConfig()
    #ensure data-valid is low
    datValid(dev, 0)
    #setup basic ADC configuration
    configADC(dev)
    #data should ready to flow:
    datValid(dev, 1)
    
if __name__=='__main__':

    dev = flower.Flower()
    all_good=False
    max_tries=20
    count=0
    while(not all_good and count<max_tries):
        count=count+1
        boardStartup(dev)
        print ('tuning adc bitstream..')
        shift_good,_=testPatternBitShift(dev)
        print ('aligning adc samples..')
        check=align_adcs.do(dev)
        if check==0 and shift_good==True:all_good=True
        print ('done')
    
