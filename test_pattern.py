import setup_board
import flower
import numpy
import sys
import time

if __name__ == '__main__':

    dev = flower.Flower()

    #test pattern of
    #setup_board.spiWriteBothADCS(dev, setup_board.HMCAD_ADR_TP_WORD1, 0x71, 0x00)
    #setup_board.spiWriteBothADCS(dev, setup_board.HMCAD_ADR_TP_WORD2, 0xAF, 0x00)

    setup_board.spiWriteBothADCS(dev, setup_board.HMCAD_ADR_TP_MODE, 0x00, 0x20) #0x00, 0x20 for dual pattern
    setup_board.spiWriteBothADCS(dev, setup_board.HMCAD_ADR_TP_SYNC, 0x00, 0x00)

    dev.write(dev.DEV_FLOWER, [0x42, 0x00, 0x00, 0x02])

    #sys.exit()
    
    
    dev.softwareTrigger(1)
    print dev.readRam(dev.DEV_FLOWER,0)
    dev.softwareTrigger(0)
    
    #turn off test pattern
    setup_board.spiWriteBothADCS(dev, setup_board.HMCAD_ADR_TP_MODE, 0x00, 0x00)

    dev.calPulser(False)
    
    dev.softwareTrigger(1)
    dat= dev.readRam(dev.DEV_FLOWER,0)
    print dat
    dev.softwareTrigger(0)

    numpy.savetxt('test.txt', numpy.array(dat))
