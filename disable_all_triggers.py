import flower_trig

trig = flower_trig.FlowerTrig()

trig.dev.calPulser(False)
effective_disable_thresh = [120,120,120,120]
trig.initCoincTrig(3, effective_disable_thresh, effective_disable_thresh, vppmode=0)
trig.trigEnable() #defaults are 0


trig.dev.write(trig.dev.DEV_FLOWER,[92,0,0,0]) #disable trig to sysout
trig.dev.write(trig.dev.DEV_FLOWER,[93,0,0,0]) #disable trig to aux SMA out



