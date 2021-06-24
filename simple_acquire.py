import flower
import numpy
import setup_board as setup
if __name__ == '__main__':

    
    dev = flower.Flower()
    setup.adcGainSelect(dev,5)

    dev.calPulser(False)

    dev.softwareTrigger(0)
    dev.softwareTrigger(1)
    dat= dev.readRam(dev.DEV_FLOWER, 0, 256)
    dev.softwareTrigger(0)

    numpy.savetxt('test.txt', numpy.array(dat))
