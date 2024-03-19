import flower_trig
import time
import setup_board

trig = flower_trig.FlowerTrig()

#trig.dev.calPulser(True,freq=1)
trig.dev.calPulser(False)
setup_board.adcGainSelect(trig.dev, 0)
trig.initPhasedTrig(power=0xfff,mask=0xffff)
trig.trigEnable(phased_trig=1)
for i in range(0x1000, -1, -256):
    print(i)
    trig.initPhasedTrig(power=i)
    print (trig.dev.readRegister(trig.dev.DEV_FLOWER, 0x57))
    time.sleep(1)
    for j in range(32,65,1):
        trig.setScalerOut(j)
        print (trig.readSingleScaler())
    trig.setScalerOut(30)
    print ('scaler pps', trig.readSingleScaler())

trig.dev.calPulser(False)
trig.trigEnable(phased_trig=0)
