import flower
import flower_trig
import numpy
import setup_board as setup
import time

if __name__ == '__main__':

    
    dev = flower.Flower()
    dev.boardInit()
    trig = flower_trig.FlowerTrig()
    setup.adcGainSelect(dev,0)

    dev.bufferClear()
    print (dev.checkBuffer()) #should return 0

    #setup trigger
    trig.initCoincTrig(0, [10,10,10,10],[120,120,120,120], vppmode=1)
    trig.trigEnable(coinc_trig=1)
    
    while(not dev.checkBuffer() ):
        time.sleep(0.1)

    print (dev.checkBuffer()) #should return 1 if an event

    dat= dev.readRam(dev.DEV_FLOWER, 0, 256)
    numpy.savetxt('rftest.txt', numpy.array(dat, dtype=int))

    trig.trigEnable() #turns off all triggers
    dev.bufferClear()
    
