import flower_trig
import time
import setup_board

trig = flower_trig.FlowerTrig()

trig.dev.calPulser(False)
setup_board.adcGainSelect(trig.dev,2)
effective_disable_thresh = [120,120,120,120]
trig.initCoincTrig(3, effective_disable_thresh, effective_disable_thresh, vppmode=0)
time.sleep(2)

trig.trigEnable(coinc_trig=1)
trig.initCoincTrig(0, [8,120,120,120], [120,120,120,120],vppmode=1)
time.sleep(4)


for j in range(18):
    trig.setScalerOut(j)
    print (trig.readSingleScaler())
    trig.setScalerOut(31)
print ('scaler pps', trig.readSingleScaler())

trig.dev.write(trig.dev.DEV_FLOWER,[92,0,0,1]) #enable trig to sysout
trig.dev.write(trig.dev.DEV_FLOWER,[93,0,0,1]) #enable trig to aux SMA out



