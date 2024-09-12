import flower_trig
import time
import setup_board

trig = flower_trig.FlowerTrig()

#trig.dev.calPulser(True,freq=1)
#trig.dev.calPulser(False)
#setup_board.adcGainSelect(trig.dev, 0)
trig.initPhasedTrig(power=0xfff,servo=0xfff,mask=0x100,offset=0)
trig.trigEnable(phased_trig=1)
for i in range(2000, 0, -50):
    print(i)
    trig.initPhasedTrig(power=i,offset=0,mask=0x100)
    print (trig.dev.readRegister(trig.dev.DEV_FLOWER, 0x57))
    time.sleep(1)
    for j in range(10,30,1):
        trig.setScalerOut(j)
        print('%i,%i'%(2*j,2*j+1),trig.readSingleScaler())
    trig.setScalerOut(0)
    print ('scaler pps', trig.readSingleScaler())
trig.initPhasedTrig(power=0xfff,offset=0,mask=0x000)
trig.dev.calPulser(False)
trig.trigEnable(phased_trig=0)
