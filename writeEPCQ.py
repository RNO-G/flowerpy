#!/usr/bin/python
#
#   EJO     10/2017
#   write new firmware image to NuPhase board EEPROM
#----------------------------------------
import flower
import sys
import time
import reconfigureFPGA as reconfig
import tools.bf as bf

directory = '/home/rno-g/flowerpy/firmware/'

filename = directory+'output_file_auto.rpd'

FILEMAP_START_ADDR = 0x00000000
FILEMAP_END_ADDR   = 0x00175E77 #this value needs to be updated for each new firmware version
TARGET_START_ADDR  = 0x00200000 #address where application firmware image is stored - STATIC, DO NOT CHANGE!!

def setMode(dev, bus, mode):
    #mode = 1 to write to 256 byte firmware block FIFO
    #mode = 0 to read from block FIFO and cmd the ASMI_PARALLEL block
    dev.write(bus, [0x72, 0x00, 0x00 | mode, 0x00]) 
    updated_mode = dev.readRegister(bus, 0x72)[2]
    return updated_mode

def initWrite(dev, bus):
    current_mode = setMode(dev, bus, 0)
    dev.write(bus, [0x72, 0x01, 0x00 | current_mode, 0x00]) #clear FIFO
    dev.write(bus, [0x72, 0x00, 0x00 | current_mode, 0x00]) #make sure cmd fsm in 'idle' state
    ##FIFO should be empty
    #status = readStatusReg(dev, bus, check_done=False)
    #if status[3] == 0:
        
    current_mode = setMode(dev, bus, 1) #put block into write mode
    return current_mode

def makeAddrList(addr):
    sector_addr_list = []
    sector_addr_list.append(int((0x000000FF & addr)))
    sector_addr_list.append(int((0x0000FF00 & addr) >> 8))
    sector_addr_list.append(int((0x00FF0000 & addr) >> 16))
    sector_addr_list.append(int((0xFF000000 & addr) >> 24))
    return sector_addr_list

def readStatusReg(dev, bus, check_done=True):
    #
    # read remote upgrade status register
    #     set check_done=True if you want to return EPCQ done/busy condition
    #
    status = bf.bf(dev.readRegister(bus, 0x67)[3])
    if check_done:
        if status[1] == True:
            return 'busy'
        elif status[2] == True:
            return 'done'
        else:
            #print 'uh oh'
            return None
    else:
        return status

def sectorClear(dev, bus, sector_addr):
    current_mode = setMode(dev, bus, 0)
    sector_addr_list = makeAddrList(sector_addr)
    #write EPCQ address
    dev.write(bus, [0x73, 0x00, sector_addr_list[1], sector_addr_list[0]])
    dev.write(bus, [0x74, 0x00, sector_addr_list[3], sector_addr_list[2]])
    dev.write(bus, [0x72, 0x00, 0x00 | current_mode, 0x04]) #send sector-clear cmd
    while(readStatusReg(dev, bus) != 'done'):
        time.sleep(0.2)
    current_mode = setMode(dev, bus, 1)
    return current_mode

def clearApplicationImage(dev, bus, hw_start_addr, image_end_addr):
    current_address = hw_start_addr + 1 - 0x10000 ##clear one sector ahead
    print 'clearing EEPROM:'
    while(current_address < (image_end_addr + hw_start_addr + 0x10000)):
        sys.stdout.write('   clearing sector address...0x{:x}  \r'.format(current_address-1))
        sys.stdout.flush()                   
        sectorClear(dev, bus, current_address)
        current_address = current_address + 0x10000
    sys.stdout.write('   clearing sector address...0x{:x}  \n\n'.format(current_address-1))
    print 'DONE WITH EEPROM CLEAR'

def readEPCQBlock(dev, bus, addr, read_data=True):
    current_mode = setMode(dev, bus, 0)
    addr_list = makeAddrList(addr)
    dev.write(bus, [0x73, 0x00, addr_list[1], addr_list[0]])
    dev.write(bus, [0x74, 0x00, addr_list[3], addr_list[2]])
    dev.write(bus, [0x72, 0x00, 0x00 | current_mode, 0x01])
    while(readStatusReg(dev, bus) != 'done'):
        time.sleep(0.1)
    current_mode = setMode(dev, bus, 1)
    ##------------------------
    ## save to list
    if read_data:
        byte_list=[]
        for i in range(4096):
            dev.write(bus, [0x79, 0x00, 0x00, 0x01])
            addr=[]
            addr.append(int((0x0000FF & i)))
            addr.append(int((0x00FF00 & i) >> 8))
            addr.append(int((0xFF0000 & i) >> 16))
            dev.write(bus, [0x78, addr[2], addr[1], addr[0]])
            dev.write(bus, [0x79, 0x00, 0x00, 0x03])
            dat = dev.readRegister(bus, 0x6A)
            byte_list.extend((dat[3], dat[2]))
            dat = dev.readRegister(bus, 0x6B)
            byte_list.extend((dat[3], dat[2]))
        dev.write(bus, [0x79, 0x00, 0x00, 0x00])
        return byte_list

def verifyEPCQContents(dev, bus, addr, file_byte_list):
    epcq_byte_list = readEPCQBlock(dev, bus, addr)
    if len(epcq_byte_list) != len(file_byte_list):
        return None
    byte_errors = 0
    for i in range(len(file_byte_list)):
        if epcq_byte_list[i] != file_byte_list[i]:
            print 'MISMATCH FOUND (addr, loc, epcq value, file value): ', hex(addr), i, epcq_byte_list[i], file_byte_list[i], '   '
            byte_errors = byte_errors + 1

    return byte_errors
    
def writeChunk(dev, bus, byte_list, sector_addr):
    current_mode = setMode(dev, bus, 1)
    dev.write(bus, [0x6F, 0x00, 0x00, 0x01]) #activate write enable to FIFO
    for i in range(0, len(byte_list), 4):
        #--------------------------
        ## Write to FIFO
        ## MSB --> first byte written
        dev.write(bus, [0x70, 0x00, (0xFF & byte_list[i+2]), (0xFF & byte_list[i+3])]) 
        dev.write(bus, [0x71, 0x00, (0xFF & byte_list[i]),   (0xFF & byte_list[i+1])])
        dev.write(bus, [0x6F, 0x00, 0x00, 0x03]) # toggle write clock
        dev.write(bus, [0x6F, 0x00, 0x00, 0x01]) # de-toggle write clock

    #send last dummy byte-list (needed since FIFO empty flag apparently goes high on last entry, not *after* last entry read)
    dev.write(bus, [0x70, 0x00, 0xFF, 0xFF])
    dev.write(bus, [0x71, 0x00, 0xFF, 0xFF])
    dev.write(bus, [0x6F, 0x00, 0x00, 0x03]) # toggle write clock
    dev.write(bus, [0x6F, 0x00, 0x00, 0x01]) # de-toggle write clock   
    dev.write(bus, [0x6F, 0x00, 0x00, 0x00])  # deactivate write enable
    #-----------------------
    ## Read bytes from FIFO, toggle write to EEPROM via ASMI_PARALLEL IP core
    current_mode = setMode(dev, bus, 0)
    sector_addr_list = makeAddrList(sector_addr)
    #write EPCQ address
    dev.write(bus, [0x73, 0x00, sector_addr_list[1], sector_addr_list[0]])
    dev.write(bus, [0x74, 0x00, sector_addr_list[3], sector_addr_list[2]])
    #toggle bulk write to EPCQ
    dev.write(bus, [0x72, 0x00, 0x00 | current_mode, 0x02])
    #dev.write(bus, [0x72, 0x00, 0x00 | current_mode, 0x00])
    while(readStatusReg(dev, bus) != 'done'):
        time.sleep(0.001)
    #status = readStatusReg(dev, bus, check_done=False)  
    #print 'after', status[4], status[3]
    current_mode = setMode(dev, bus, 1) #exit test mode
    
def writeFirmwareToEPCQ(dev, bus, filename, FILEMAP_START_ADDR, FILEMAP_END_ADDR, verify=False):
    ###
    # write the firmware image
    # [2017.11.3] added verification feature in which file contents are compared to EPCQ readback (increases program time ~3x)
    ###
    start_time = time.time()
    with open(filename, 'rb') as binary_rpd_file:
        binary_rpd_file.seek(0,2)  # Seek the end
        num_bytes = binary_rpd_file.tell()
        print '------------------------'
        print 'Reading raw programming file:', filename
        print 'Filesize:', num_bytes, 'bytes'
        if verify:
            print 'program readback verification: ON'
        else:
            print 'program readback verification: OFF'
        print '------------------------\n'
        
        binary_rpd_file.seek(0,0) # go back to beginning of file
        
        current_address = FILEMAP_START_ADDR
        binary_rpd_file.seek(current_address) # go to start of firmware image in file
        current_byte_in_cycle = 0
        verify_bytes = []
        
        while (current_address < (FILEMAP_END_ADDR+256+1)):
            #--------------
            epcq_address   = current_address + TARGET_START_ADDR
            read_256bytes  = binary_rpd_file.read(256)
            write_256bytes = []
            for i in range(256):
                write_256bytes.append(ord(read_256bytes[i]))
                if verify and ((i+1) % 4) == 0 and i > 0:
                    verify_bytes.extend((write_256bytes[i], write_256bytes[i-1], write_256bytes[i-2], write_256bytes[i-3]))
            #--------------
            initWrite(dev, bus)
            writeChunk(dev, bus, write_256bytes, epcq_address)
            #--------------
            if verify and (current_address - FILEMAP_START_ADDR + 256) % 16384 == 0 and current_address > 0:
                verify_epcq_addr = current_address - (16384 - 256) + TARGET_START_ADDR
                verify_retval = verifyEPCQContents(dev, bus, verify_epcq_addr, verify_bytes)
                if verify_retval > 0:
                    print 'byte mismatch(es) found:', verify_retval
                verify_bytes=[]
            #--------------
            now=time.time()
            _min, _sec = divmod((now-start_time), 60)
            #--------------
            ## print to terminal
            if current_address % pow(2,14) == 0:
                sys.stdout.write('{:.2f} MB written to device; now at EEPROM address 0x{:x}. Time elapsed (min:sec) {:}:{:.0f}         \r'.format((current_address-FILEMAP_START_ADDR)*1e-6, epcq_address, int(_min), _sec))
                sys.stdout.flush()
            #--------------
            current_address = current_address + 256
            
    sys.stdout.write('{:.2f} MB written to device; now at EEPROM address 0x{:x}. Time elapsed (min:sec) {:d}:{:.0f}         \n\n'.format((current_address-FILEMAP_START_ADDR-256)*1e-6, epcq_address, int(_min), _sec))               
    setMode(dev, bus, 0)


###-----------------------------------------------------------------
### load new application firmware image
#
###-----------------------------------------------------------------
    
if __name__=='__main__':
    import sys
    
    
    dev=flower.Flower()
    bus = dev.DEV_FLOWER
   
    print '\n RUNNING REMOTE FIRMWARE IMAGE UPDATE '
    reconfig.enableRemoteFirmwareBlock(dev, bus, False)
    reconfig.enableRemoteFirmwareBlock(dev, bus, True)
    print '\n***************************\n'
    clearApplicationImage(dev, bus, TARGET_START_ADDR, FILEMAP_END_ADDR)
    #dat = readEPCQBlock(dev, bus, TARGET_START_ADDR)
    #for i in range(len(dat)):
    #    if dat[i] != 0xFF:
    #        print 'clear error', i, dat[i]
    print '\n***************************\n'
    time.sleep(1)
    writeFirmwareToEPCQ(dev,bus,filename,FILEMAP_START_ADDR, FILEMAP_END_ADDR)
    reconfig.enableRemoteFirmwareBlock(dev,bus,False)
    print '***************************\n'
    print 'seemed to process successfully'
    
