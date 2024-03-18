import flower
import flower_trig
import numpy
import setup_board as setup
import time
import numpy as np
import os


if __name__ == '__main__':

    try:os.remove('rfphasedtest.txt')
    except:pass
    dev = flower.Flower()
    dev.boardInit()
    trig = flower_trig.FlowerTrig()
    setup.adcGainSelect(dev,0)
    dev.calPulser(True,freq=1)
    dev.bufferClear()
    print (dev.checkBuffer()) #should return 0

    #setup trigger
    trig.initPhasedTrig(power=1800,mask=0x0002)
    trig.trigEnable(phased_trig=1)
    dev.bufferClear()
    count=0
    while(not dev.checkBuffer() and count<10):
        time.sleep(0.1)
        count=count+1
    dev.read_triggering_things()
    is_event=dev.checkBuffer()
    print (is_event) #should return 1 if an event

    dat= dev.readRam(dev.DEV_FLOWER, 0, 256)
    pp=np.max(dat[0])-np.min(dat[0])
    if pp>5 and is_event:
        numpy.savetxt('rfphasedtest.txt', numpy.array(dat, dtype=int))
    dev.calPulser(False)
    trig.trigEnable() #turns off all triggers
    dev.bufferClear()
    
