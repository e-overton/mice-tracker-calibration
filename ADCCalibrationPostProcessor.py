#!/usr/bin/env python

module_description=\
"""
ADC Calibration post processing tools. This should take a
checked calibration to make a final calibraion (with added
infomation, such as noise rates etc..).


E. Overton, August 2015.
"""

import FECalibrationUtils
import FrontEndChannel
import ExportOnMon
import TrDAQReader
from ADCCalibrator import ADCCalibration
import sys
import os
import ROOT

# Main function for doing the post processing:
def main(config):
        
    # Construct a main "ADC Calibtation" Object, which we will return and manipulate
    # later using a GUI....
    Calibration = ADCCalibration()
    
    #Try to load an existing calibration:
    Calibration.Load(config)
    Calibration.LoadInternalLED()
    
    # Load the status object to determine the state
    # of the calibration:
    Calibration.status = FECalibrationUtils.LoadCalibrationStatus(config["path"])
            
    # Check the data was checked:
    if not ("Checked" in Calibration.status) or (Calibration.status["Checked"] == False):
        print ("ERROR: The data needs checking before the final step, please check and then edit the status file")
        sys.exit(1)
        
    
    # Final Processing Loop:
    if not ("PostProcessed" in Calibration.status) or (Calibration.status["PostProcessed"] == False):
        print ("INFO: Beginning Final Processing Loop..")
        
        # Load the internal LED Data:
        print ("Attempting to load internal led files ...")
            
        if ( Calibration.IntNoLEDHist is None ) or ( Calibration.IntLEDHist is None):
            print ("error loading internal led files")
        else:
            print ("... done loading external files")
        
        
        # List to hold the UIDs
        bad_uids = []
        
        # Noise 2pe Threshold:
        bad_noiselimit = 0.008 # 0.8% Probability.
        
        
        # Use the files to generate an LYE calibration:
        for FEChannel in Calibration.FEChannels:
            
            # Channel to process:
            ChannelUID = FEChannel.ChannelUID
            
            # Clear any maus bad channel flags:
            FEChannel.Issues = [i for i in FEChannel.Issues if i["Issue"] != "MAUSBadChannel"]
            
            # Check the channel has good/calibrated peds:
            if (FEChannel.ADC_Pedestal > 1.): 
            
                PedHist_LED = Calibration.IntLEDHist.ProjectionY("th1d_led",ChannelUID+1,ChannelUID+1,"")
                PedHist_NoLED = Calibration.IntNoLEDHist.ProjectionY("th1d_noled",ChannelUID+1,ChannelUID+1,"")
            
                # Check the light yield:
                FEChannel.Light_Yield = (PedHist_LED.GetMean()-FEChannel.ADC_Pedestal)/FEChannel.ADC_Gain
                FEChannel.Dark_Yield = (PedHist_NoLED.GetMean()-FEChannel.ADC_Pedestal)/FEChannel.ADC_Gain
                
                # Check the noise:
                threshold_1pe = FEChannel.ADC_Pedestal + FEChannel.ADC_Gain
                FEChannel.noise_1pe_rate = PedHist_NoLED.Integral(\
                    PedHist_NoLED.FindBin(threshold_1pe), 255)/PedHist_NoLED.GetEntries()
                    
                threshold_2pe = FEChannel.ADC_Pedestal + 2.*FEChannel.ADC_Gain
                FEChannel.noise_2pe_rate = PedHist_NoLED.Integral(\
                    PedHist_NoLED.FindBin(threshold_2pe), 255)/PedHist_NoLED.GetEntries()
                    
                # Check constraints for channel
                if (FEChannel.noise_2pe_rate > bad_noiselimit) and FEChannel.InTracker:
                    bad_uids.append(ChannelUID)
                    FEChannel.Issues.append({"ChannelUID":ChannelUID,
                                        "Severity":5,
                                        "Issue":"MAUSBadChannel",
                                        "Comment":"Noise above %.2f"%(bad_noiselimit*100.)})
                    print "Noisey"
                
            # Else
            elif FEChannel.InTracker:
                bad_uids.append(ChannelUID)
                FEChannel.Issues.append({"ChannelUID":ChannelUID,
                                        "Severity":5,
                                        "Issue":"MAUSBadChannel",
                                        "Comment":"No Pedestal, Dead"})
                print "No signal!"
                    

                    
        Calibration.status["PostProcessed"] = True
    
    # Save output:
    FECalibrationUtils.SaveFEChannelList(Calibration.FEChannels, os.path.join(config["path"], config["FECalibrations"]))
    # Save Status:
    FECalibrationUtils.SaveCalibrationStatus(Calibration.status, config["path"])
    # Save Calibration:
    FECalibrationUtils.ExportADCCalibrationMAUS(Calibration.FEChannels, os.path.join(config["path"], config["MAUSCalibration"]))
    
    # Handle Bad channels if a filename is specified.
    if "MAUSBadChannels" in config:
        FECalibrationUtils.ExportBadChannelsMAUS(Calibration.FEChannels, os.path.join(config["path"], config["MAUSBadChannels"]))
    
    #Make on-mon plots:
    if "OnMon_Filename" in config:
        ExportOnMon.ExportConfig(config, os.path.join(config["path"],config["OnMon_Filename"]))
                
    return Calibration


def Plotter(Calibration):
    
    # Output Plots:
    TH1D_threshold_1pe = ROOT.TH1D("","",256, -0.5, 255.5)
    TH1D_threshold_2pe = ROOT.TH1D("","",256, -0.5, 255.5)
    
    TH1D_noise_1pe = ROOT.TH1D("","",100, 0, 0.1)
    TH1D_noise_2pe = ROOT.TH1D("","",100, 0, 0.01)
    
    for FEChannel in Calibration.FEChannels:
        
        threshold_1pe = FEChannel.ADC_Pedestal + FEChannel.ADC_Gain
        TH1D_threshold_1pe.Fill(threshold_1pe)
        TH1D_noise_1pe.Fill(FEChannel.noise_1pe_rate)
        
        threshold_2pe = FEChannel.ADC_Pedestal + 2.*FEChannel.ADC_Gain
        TH1D_threshold_2pe.Fill(threshold_2pe)
        TH1D_noise_2pe.Fill(FEChannel.noise_2pe_rate)
        
    
    c1 = ROOT.TCanvas("c","c",800, 600)
    #c1.Divide(1,2)
    #c1.cd(1)
    
    TH1D_threshold_1pe.Draw()
    TH1D_threshold_2pe.Draw("same")
    
    #c1.cd(2)
    
    #TH1D_noise_1pe.Draw()
    #TH1D_noise_2pe.Draw("same")
    
    raw_input("Enter to contine")
    

########################################################################
# Call main function in object.
if __name__ == "__main__":
    
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
    
    # Run the main calibraton now:
    Calibration = main (config)
    
    #Plotter(Calibration)
    #raw_input("Script complete, press enter to continue")
    print ("Script complete,Exiting.")
    
    