#!/usr/bin/env python3 

import flower_trig
import time
import setup_board
import sys 


gain_select = int(sys.argv[1]) 
thresh_0 = int(sys.argv[2]) 
thresh_1 = int(sys.argv[3]) 
thresh_2 = int(sys.argv[4]) 
thresh_3 = int(sys.argv[5]) 

trig = flower_trig.FlowerTrig()

setup_board.adcGainSelect(trig.dev, gain_select)
trig.initCoincTrig(2, [thresh_0,thresh_1,thresh_2,thresh_3], [int(thresh_0*0.75),int(thresh_1*0.75), int(thresh_2*0.75), int(thresh_3*0.75)], vppmode=1)
time.sleep(1)
for j in range(18):
   trig.setScalerOut(j)
   print (trig.readSingleScaler())
trig.setScalerOut(31)
print ('scaler pps', trig.readSingleScaler())

