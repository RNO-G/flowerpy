#!/usr/bin/python
#
#   EJO     10/2017
#
import flower
import sys
import time
import tools.bf as bf

#remote update block accepted commands to fw
ru_cmd_map = {
    'TRIG_COND_READONLY'   :  0x0,
    'WATCHDOG_TIME_VALUE'  :  0x2,
    'WATCHDOG_ENABLE'      :  0x3,
    'PAGE_SELECT_ADDR'     :  0x4,
    'AnF'                  :  0x5,
    }

ru_error = {
    'WATCHDOG_TIMEOUT'     :  1,
    'CRC_ERROR'            :  2,
    'NSTAT_ERROR'          :  3,
    }
    
def enableRemoteFirmwareBlock(dev, bus, enable=False):
    dev.write(bus, [0x6E, 0x00, 0x00, (0x00 | enable)])
    dev.write(bus, [0x75, 0x00, 0x00, 0x00])
    
def readRemoteConfigData(dev, bus, cmd):
    dev.write(bus, [0x75, 0x00, 0x00, (0x00 | (0x7 & cmd))])
    data_low = dev.readRegister(bus, address=0x68)
    data_hi  = dev.readRegister(bus, address=0x69)
    dev.write(bus, [0x75, 0x00, 0x00, 0x00])
    return (data_low[2] << 8) | data_low[3], (data_hi[2] << 8) | data_hi[3]

def readRemoteConfigStatus(dev, bus):
    status = dev.readRegister(bus, address=0x67)
    return status

def writeRemoteConfiguration(dev, bus, cmd, value=0x00000000):
    cmd_byte = 0x00 | (0x7 & cmd)
    dev.write(bus, [0x75, 0x00, 0x00, cmd_byte])
    value_byte_0 = int(value & 0x000000FF)
    value_byte_1 = int(((value & 0x0000FF00) >> 8) & 0xFF)
    value_byte_2 = int(((value & 0x00FF0000) >> 16) & 0xFF)
    value_byte_3 = int(((value & 0xFF000000) >> 24) & 0xFF)
    dev.write(bus, [0x76, 0x00, value_byte_1, value_byte_0])
    dev.write(bus, [0x77, 0x00, value_byte_3, value_byte_2]) #byte3 ignored for EPCQ64
    dev.write(bus, [0x75, 0x00, 0x01, cmd_byte]) #toggle write
    dev.write(bus, [0x75, 0x00, 0x00, 0x00])

def readTrigCondition(dev, bus, verbose=True):
    cond = readRemoteConfigData(dev, bus, ru_cmd_map['TRIG_COND_READONLY'])[0]
    bf_cond = bf.bf(cond) #trigger condition is lower 5 bits
    if verbose:
        print ('--------------')
        print ('FPGA remote upgrade trigger condition:', cond, \
            ' // bits:', bf_cond[0], bf_cond[1], bf_cond[2], bf_cond[3], bf_cond[4])
    if bf_cond[0] == 1:
        return ru_error['CRC_ERROR']
    elif bf_cond[1] == 1:
        return ru_error['NSTAT_ERROR']
    elif bf_cond[4] == 1:
        return ru_error['WATCHDOG_TIMEOUT']
    elif bf_cond[2] == 1 or bf_cond[3] ==1:
        if verbose:
            print ('FPGA trig conditions look good')
        return 0
    else:
        print ('weird, no trig condition received')
        return -1
    
def triggerReconfig(dev, bus):
    dev.write(bus, [0x75, 0x01, 0x00, 0x00])

def reconfigure(dev, bus, AnF=1, epcq_address = 0x01000000,
                watchdog_value=1024, watchdog_enable=1, verbose=True, exit_on_trig_error=False):

    #trig_condition = readTrigCondition(dev, bus, verbose=verbose)
    #if trig_condition != 0 and exit_on_trig_error == True:
    #    return trig_condition

    #write the AnF bit
    writeRemoteConfiguration(dev, bus, ru_cmd_map['AnF'], AnF)
    if verbose:
        print ('Reading back AnF value', \
            readRemoteConfigData(dev, bus, ru_cmd_map['AnF']))

    #enable watchdog feature
    writeRemoteConfiguration(dev, bus, ru_cmd_map['WATCHDOG_ENABLE'], watchdog_enable)
    if verbose:
        print ('Reading back watchdog enable value', \
            readRemoteConfigData(dev, bus, ru_cmd_map['WATCHDOG_ENABLE']))

    #set watchdog timeout value
    writeRemoteConfiguration(dev, bus, ru_cmd_map['WATCHDOG_TIME_VALUE'], watchdog_value)
    if verbose:
        print ('Reading back watchdog timeout value', \
            readRemoteConfigData(dev, bus, ru_cmd_map['WATCHDOG_TIME_VALUE']))
        
    #set application start address
    writeRemoteConfiguration(dev, bus, ru_cmd_map['PAGE_SELECT_ADDR'], epcq_address)
    if verbose:
        print ('Reading back EPCQ firmware image address', \
            readRemoteConfigData(dev, bus, ru_cmd_map['PAGE_SELECT_ADDR']))

    triggerReconfig(dev, bus)
    return 0

###-----------------------------------------------------------------------
###  run FPGA reconfiguration
# to load application firmware image on MASTER board: $ ./reconfigureFPGA.py -a 1
# to load application firmware image on SLAVE board: $ ./reconfigureFPGA.py -a 0
#
# program should return '0' if reconfiguration looks successful
###-----------------------------------------------------------------------
if __name__=='__main__':
    import sys
    from optparse import OptionParser

    parser = OptionParser()
    usage = "usage: %prog [options]"
    #option for loading application firmware image
    parser.add_option("-a", "--application", action="store_const", dest="application", const=True)
    (options, args) = parser.parse_args()

    if options.application:
        AnF = 1
        epcq_address = 0x00200000
        print ('-------------------------------')
        print ('loading application firmware...')
        print ('-------------------------------')
    else:
        AnF = 0
        epcq_address = 0x00000000
        print ('-------------------------------')
        print ('loading factory firmware...')
        print ('-------------------------------')

    dev=flower.Flower()
    enableRemoteFirmwareBlock(dev, dev.DEV_FLOWER, False)
    enableRemoteFirmwareBlock(dev, dev.DEV_FLOWER, True)
    retval=reconfigure(dev, dev.DEV_FLOWER, AnF=AnF, epcq_address=epcq_address)
    print ('-------------')
    print ('reprogramming firmware...')
    print ('-------------')
    time.sleep(30)
    enableRemoteFirmwareBlock(dev, dev.DEV_FLOWER, False)  #need to disable/re-enable remote blocks to get
    enableRemoteFirmwareBlock(dev, dev.DEV_FLOWER, True)   #updated trig configuration status
    retval=readTrigCondition(dev, dev.DEV_FLOWER)
    enableRemoteFirmwareBlock(dev, dev.DEV_FLOWER, False)
    time.sleep(5)
    dev.identify()
    time.sleep(1)

    sys.exit(retval)  #return 0 if successful (verify by reading back firmware version/date)
