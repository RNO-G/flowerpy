import flower_trig
import time
import setup_board
import numpy as np
import matplotlib.pyplot as plt

#Script to find per-channel thresholds which give a roughly equal per-channel trigger rate
#and a total trigger rate af about 1Hz

def get_channel_thresh(desired_rate, channel, trig, thresh_low = 17, thresh_high = 35, num_ave = 1):
    for tval in range(thresh_low, thresh_high):
        thresh_list = [tval, tval, tval, tval]
        servo_list = [int(x*servo_frac) for x in thresh_list]
        trig.initCoincTrig(1, thresh_list, servo_list, vppmode=0, coinc_window = 3)

        time.sleep(1)

        #Now read out the trigger rate
        averate = 0
        for i in range(num_ave):
            time.sleep(0.1)
            averate += trig.readCoincTrigChannelScaler(channel=channel)/num_ave

        if averate < desired_rate:
            print(f"channel {channel} has rate {averate} at threshold {tval}")
            return tval
     
    return np.nan  #If no threshold in the input range gives a low enough rate, return nan

if __name__ == "__main__":
    trig = flower_trig.FlowerTrig()
    
    coinc_rates = []
    single_chan_rates = []

    num_ave_final = 10
    servo_frac = 0.75
    num_chans = 4 
    thresh_low = 17
    thresh_high = 35

    #initialize looping variables
    per_channel_rate = 2500
    print(f"Initial per-channel trigger rate is {per_channel_rate}")
    loop_counter = 0
    coinc_rate = 1000
    while (coinc_rate > 5) or (coinc_rate == 0):
        loop_counter += 1
        print(f"Going into loop {loop_counter}")

        thresh_list = []
        for chan in range(num_chans): 
            #Get threshold for each channel corresponding to set rate
            thresh_list.append(get_channel_thresh(per_channel_rate, chan, trig, thresh_low = thresh_low, thresh_high = thresh_high, num_ave=1))

        servo_list = [int(x*servo_frac) for x in thresh_list]

        trig.initCoincTrig(1, thresh_list, servo_list, vppmode=0, coinc_window = 3)
        time.sleep(1)

        coinc_rate = 0
        for i in range(num_ave_final):
            time.sleep(0.1)
            coinc_rate += trig.readCoincTrigScaler()/num_ave_final

        print(f"Trigger rate with thresholds {thresh_list} is {coinc_rate:.3f}")
        single_chan_rates.append(per_channel_rate)
        coinc_rates.append(coinc_rate)

        if coinc_rate < 0.5:
            per_channel_rate *= (1 + 2/loop_counter)
        elif (coinc_rate > 5):
            per_channel_rate /= (1 + 2/loop_counter)
        
        print(f"New per-channel rate goal is {per_channel_rate}")