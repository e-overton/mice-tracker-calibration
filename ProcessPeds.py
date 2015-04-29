#!/usr/bin/env python

descr = \
"""
Script to calidate calibration outputs...


"""

# Read functions:
import sys
import ROOT
sys.path.insert(0, '/home/daq/tracker/analysis')
from TrDAQReader import TrDAQRead

import LYCalib
import Base

gdump = []

def main (input_filename_noled, input_filename_led):
    
    # Load Input
    (Data_noLED, Data_LED) = loadFiles(input_filename_noled, input_filename_led)
    
    if not (Data_LED is None):
        pass
    
    if not (Data_noLED is None):
        # Generate ChannelRun:
        cr = Base.ChannelRun()
        cr.setup(7,3,45)
        print ("Channel = %i"%cr.uniqueChan )
        cr.adcHist = Data_noLED["RawADCs"].ProjectionY("th1d_projecty",\
                    cr.uniqueChan,cr.uniqueChan,"")
        
        # Contruct Pedestal Finder:
        noLEDPedestal = LYCalib.PedestalFinder()
        noLEDPedestal.loadChannel(cr)
        noLEDPedestal.findPeaks()
        gdump.append(noLEDPedestal)

    print ("Done")

# File Loading Function:
def loadFiles(input_filename_noled, input_filename_led):

    # Load no LED File:    
    if not (input_filename_noled is None):
        try:
            Data_noLED = TrDAQRead(input_filename_noled, "no_led_all")
        except IndexError:
            print ("ERROR: Unable to load no-led-file:" + input_filename_noled)
            sys.exit(1)
    else:
        Data_noLED = None
            
    # Load no LED File:    
    if not (input_filename_led is None):
        try:
            Data_LED = TrDAQRead(input_filename_noled, "led_all")
        except IndexError:
            print ("ERROR: Unable to load no-led-file:" + input_filename_led)
            sys.exit(1)
    else:
        Data_LED = None
        
    return (Data_noLED, Data_LED)


# Main Function:
if __name__ == "__main__":
    print ()
    main("/home/daq/tracker/data/peds/upstream/ped_20150421_183920", None)
    
    import time
    while (True):
        time.sleep(5)