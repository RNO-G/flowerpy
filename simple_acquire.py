import flower
import numpy
import setup_board as setup
if __name__ == '__main__':

    
    dev = flower.Flower()
    setup.adcGainSelect(dev,0)

    dev.calPulser(True)

    for i in range(100):
        dev.softwareTrigger(0)
        dev.softwareTrigger(1)
        dat= dev.readRam(dev.DEV_FLOWER, 0, 256)
        testdat = numpy.array(dat)
        dev.softwareTrigger(0)
        if numpy.min(testdat) < 80:
              print ( 'bad' )
              break

    numpy.savetxt('test.txt', numpy.array(dat))
    dev.calPulser(False)
