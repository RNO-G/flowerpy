import flower
import numpy

if __name__ == '__main__':

    dev = flower.Flower()
    dev.calPulser(True)

    dev.softwareTrigger(0)
    dev.softwareTrigger(1)
    dat= dev.readRam(dev.DEV_FLOWER, 0, 256)
    dev.softwareTrigger(0)

    numpy.savetxt('test.txt', numpy.array(dat))
