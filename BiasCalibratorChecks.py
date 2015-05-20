#!/usr/bin/env python

module_description = \
"""
 === Bias Calibrator Check Script ===============================

    Check the output from the calibrator script...
    
"""
import sys
sys.path.insert(0, '/home/daq/tracker/analysis')
from TrDAQReader import TrDAQRead
import BiasCalibrator
import LightYieldEstimator
import ROOT

#############################################################

def GenerateChannels(ChannelIDs):
    """
    List of channels to be checked:
    """
    channel_list = []

    for ChannelID in ChannelIDs: 
        channel_dict = BiasCalibrator.GenerateModuleData (ChannelID)
        channel_dict["ChannelID"] = ChannelID
        channel_dict["OK"] = True
        channel_list.append (channel_dict)

    return channel_list

def ProcessLED(Channels, PedHist):
    """
    Function to process each LED's 
    """
    
    output_list = []

    for c in Channels:
         channel_LYE = LightYieldEstimator.LightYieldEstimator(c)
         ChannelID = c["ChannelID"]
         ped = PedHist.ProjectionY("th1d_projecty",ChannelID+1,ChannelID+1,"")
         if (ped.GetEntries() < 1):
             print ("Skipping channel with no data...")
         else:
             channel_LYE.process(ped)
             for p in range(len(channel_LYE.Peaks)):
                 PeakFitResults = channel_LYE.fitPeak(ped, p)
                 channel_LYE.Peaks[p] = PeakFitResults[1]
                 #channel_LYE.PeakErrors[p] = PeakFitResults[4]
             channel_LYE.gainEstimator()
             
         output_list.append(channel_LYE.getMap())

    return output_list


#############################################################
# "" Graphing Functions ""
#############################################################

def Plot_PePeaksNoPed(Channels):
    """
    Plot the PePeaks after pedastool subtraction:
    """
    tg = ROOT.TGraph()
    ROOT.SetOwnership(tg, False)

    for c in Channels:
        if "Peaks" in c:
            Peaks = c["Peaks"]
            if len(Peaks) > 1:
                for p in range (1, len(Peaks)):
                    tg.SetPoint( tg.GetN(), c["ChannelID"], Peaks[p] - Peaks[0])
    
    return tg

def Plot_Gains(Channels):
    """
    Plot the PePeaks after pedastool subtraction:
    """
    tg = ROOT.TGraph()
    ROOT.SetOwnership(tg, False)

    for c in Channels:
        if "gain" in c:
            tg.SetPoint( tg.GetN(), c["ChannelID"], c["gain"])
    
    return tg

#############################################################
# "" Main ""
#############################################################

if __name__ == "__main__":
    
    ## Get DataFile:
    try:
        Data_LED = TrDAQRead(sys.argv[1])
        Data_NOLED = TrDAQRead(sys.argv[2])
    except IndexError:
        print ("ERROR: The LED Datafile must be passed as the first argument")
        print ("ERROR: followed by the noLED datafile.")
        sys.exit(1)

    led_peds = Data_LED["RawADCs"]
    led_fname = Data_LED["filename"]

    channels = GenerateChannels(range(3*1024, 4*1024))
    led_channels = ProcessLED(channels, led_peds)

    led_pedsubtract = Plot_PePeaksNoPed(led_channels)
    led_pedsubtract.Draw("ap")

    led_gains = Plot_Gains(led_channels)
    led_gains.Draw("ap")


    import time
    while True:
        time.sleep(5)

    #noled_peds = Data_NOLED["RawADCs"]
    #noled_fname = Data_NOLED["filename"]
    
    # Construct Canvas
    #c = ROOT.TCanvas("C1_Noise","RAWPENoise",1280,1024)
    #c.Divide(1,2)
    #c.cd(0)
    #RawADCs.Draw("colz")

    


