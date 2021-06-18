import flower_trig
import time

trig = flower_trig.FlowerTrig()
trig.dev.calPulser(True)

for i in range(20, 1, -1):
    print (i)
    trig.initCoincTrig(1, [40,i,i,i], vppmode=0)
    print (trig.dev.readRegister(trig.dev.DEV_FLOWER, 0x57))
    time.sleep(1)
    for j in range(12):
        trig.setScalerOut(j)
        print (trig.readSingleScaler())



trig.initCoincTrig(3, [0,0,0,0], vppmode=0)
