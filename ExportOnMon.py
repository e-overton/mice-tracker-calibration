#!/usr/bin/env python
module_description=\
"""
Tools to export On-Mon reference data from the calibration

E. Overton, September 2015.
"""

import ROOT
import FECalibrationUtils
import ADCCalibrator
import os
import sys
import TrDAQReader
import array
from array import array

# Using an existing ADC calibration...
def ExportOnMonReference(ADCCalibration, output_filename):
    
    # Construct a ROOT File:
    outfile = ROOT.TFile(output_filename, "RECREATE")
    
    # Make a copy of the no-led pedestals:
    NoLEDHist = ROOT.TH2D(ADCCalibration.IntNoLEDHist)
    NoLEDHist.SetNameTitle("adc_ref_noled", "ADC reference no LED; ChannelUID; ADC Counts")
    
    # Fill an TTree
    t = ROOT.TTree( 'ChInfo', 'ChannelInfo' )
    
    # Elements for the Tree:
    ChannelUID = array( 'i', [ 0 ] )
    InTracker = array( 'i', [ 0 ] )
    Good = array( 'i', [ 0 ] )
    adc_pedestal = array( 'f', [ 0. ] )
    adc_gain= array( 'f', [ 0. ] )
    
    t.Branch( 'ChannelUID', ChannelUID, 'ChannelUID/I' )
    t.Branch( 'InTracker', InTracker, 'InTracker/I' )
    t.Branch( 'Good', Good, 'Good/I' )
    t.Branch( 'adc_pedestal', adc_pedestal, 'adc_pedestal/F' )
    t.Branch( 'adc_gain', adc_gain, 'adc_gain/F' )
    
    for channel in ADCCalibration.FEChannels:
        ChannelUID[0] = channel.ChannelUID
        InTracker[0] =  channel.InTracker
        Good[0] = 1
        for issue in channel.Issues:
            if (issue["Severity"]>4):
                Good[0] = 0
        adc_pedestal[0] = channel.ADC_Pedestal
        adc_gain[0] = channel.ADC_Gain
        t.Fill()
    
    outfile.Write()
    outfile.Close()

# Go using config:    
def ExportConfig(config, output_filename):
    # Construct a main "ADC Calibtation" Object, which we will return and manipulate
    # later using a GUI....
    Calibration = ADCCalibrator.ADCCalibration()
    
    Calibration.Load(config)
    Calibration.LoadInternalLED()
    
    ExportOnMonReference(Calibration, output_filename)
    
    
if __name__=="__main__":
    print (module_description)
    
    try:
        print ("")
        path = sys.argv[1]
        print ("loading calibration from directory: %s"%path)
        print ("")
        
        print ("loading calibration config...")
        config = FECalibrationUtils.LoadCalibrationConfig(path)
        print ("... done")
        print ("")
    
    except:
        print "Failed to load valid configuration from calibration directory"
        raise
    
    output_filename =  os.path.join(config["path"],"OnMonRef.root")
    
    ExportConfig(config, output_filename )
    
        