import flower_trig
import time
import setup_board

trig = flower_trig.FlowerTrig()

trig.dev.calPulser(False)
setup_board.adcGainSelect(trig.dev, 5)
effective_disable_thresh = [120,120,120,120]
for i in range(20, 1, -1):
    print (i)
    trig.initCoincTrig(3, [i,40,i,i], [i,i,i,i], vppmode=1)
    print (trig.dev.readRegister(trig.dev.DEV_FLOWER, 0x57))
    time.sleep(1)
    for j in range(18):
        trig.setScalerOut(j)
        print (trig.readSingleScaler())
    trig.setScalerOut(31)
    print ('scaler pps', trig.readSingleScaler())

trig.dev.calPulser(False)
trig.initCoincTrig(3, effective_disable_thresh, effective_disable_thresh, vppmode=0)
