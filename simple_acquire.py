import flower
import numpy
import setup_board as setup
if __name__ == '__main__':

    
    dev = flower.Flower()
    setup.adcGainSelect(dev,0)

    dev.calPulser(True)

<<<<<<< HEAD
    for i in range(1000):
=======
    for i in range(100):
>>>>>>> b71dd6b92a0d4f4b720fca72305e080ab67a526e
        dev.softwareTrigger(0)
        dev.softwareTrigger(1)
        dat= dev.readRam(dev.DEV_FLOWER, 0, 256)
        testdat = numpy.array(dat)
        dev.softwareTrigger(0)
<<<<<<< HEAD
        if numpy.min(testdat) < 95:
=======
        if numpy.min(testdat) < 80:
>>>>>>> b71dd6b92a0d4f4b720fca72305e080ab67a526e
              print ( 'bad' )
              break

    numpy.savetxt('test.txt', numpy.array(dat))
    dev.calPulser(False)
