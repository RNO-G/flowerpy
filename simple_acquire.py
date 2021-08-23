import flower
import numpy
import setup_board as setup

if __name__ == '__main__':

    
    dev = flower.Flower()
    setup.adcGainSelect(dev,0)

    dev.bufferClear()
    print (dev.readRegister(dev.DEV_FLOWER, 0x7))
    print dev.checkBuffer()
    
    for i in range(4):
        dev.bufferClear()
        dev.softwareTrigger()
        dat= dev.readRam(dev.DEV_FLOWER, 0, 256)
        testdat = numpy.array(dat)
        if numpy.min(testdat) < 80:
              print ( 'bad' )
              break

    numpy.savetxt('test.txt', numpy.array(dat, dtype=int))
    dev.calPulser(False)
