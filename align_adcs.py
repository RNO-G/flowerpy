import flower
import time

ADC1_SAMPLE_SHIFT_REG = 0x39

def acquire(dev):
    dev.softwareTrigger(0)
    dev.softwareTrigger(1)
    dat = dev.readRam(dev.DEV_FLOWER, 0, 128)
    dev.softwareTrigger(0)
    return dat

def getPeaks(dat):
    peak0 = dat[0].index(min(dat[0]))
    peak1 = dat[2].index(min(dat[2]))
    #some conditions:
    if min(dat[0]) > 115 or min(dat[2]) > 115:
        return None
    elif peak0 < 10 or peak0 > 500 or peak1 < 10 or peak1 > 500:
        return None
    else: return peak0, peak1

def align(dev, num_tries=20):
    
    dev.write(dev.DEV_FLOWER, [ADC1_SAMPLE_SHIFT_REG, 0, 0, 0x00]) #start with no adjustment
    tries=0
    while(tries < num_tries):
        tries+=1
        dat = acquire(dev)
        peaks = getPeaks(dat)
    
        if peaks is not None:
            diff = peaks[1] - peaks[0] #get difference
            if diff == 0: return 0 #aligned!
            elif diff == 1: #adc1 slower by 1 sample
                dev.write(dev.DEV_FLOWER, [ADC1_SAMPLE_SHIFT_REG, 0, 0, 0x01])
            elif diff == 2: #adc1 slower by 2 samples   
                dev.write(dev.DEV_FLOWER, [ADC1_SAMPLE_SHIFT_REG, 0, 0, 0x02])
            elif diff ==-1: #adc1 faster by 1 sample
                dev.write(dev.DEV_FLOWER, [ADC1_SAMPLE_SHIFT_REG, 0, 0, 0x05])
            elif diff ==-2: #adc1 faster by 2 samples    
                dev.write(dev.DEV_FLOWER, [ADC1_SAMPLE_SHIFT_REG, 0, 0, 0x06])
            else: return 1 #exceeds +/- 2 sample diff.

    return 2 #timeout return
            
def do(dev):
    dev.calPulser(True)
    retval = align(dev)
    if retval == 0:
        print 'adcs succesfully aligned'
    else:
        print 'problem here..'
    dev.calPulser(False)
    return retval

if __name__=='__main__':
    dev = flower.Flower()
    do(dev)
    