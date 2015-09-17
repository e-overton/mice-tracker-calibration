#!/usr/bin/env python
module_description=\
"""
ADC Calibrator Update functionality.

Uses an exisiting calibration as a base point to make a new calibration.

E. Overton, July 2015.
"""

import ADCCalibrator
import FECalibrationUtils
import copy
import ROOT
import sys
import os

def UpdateCalibration(old, new):
    """
    old - Input of the old calibration values:
    new - The new calibration to be generated
    
    Note: Both calibrations must be loaded with internal LED Data..
    """
    
    # Some sanity checks to ensure all is well:
    if not ("PostProcessed" in  old.status) or ( old.status["PostProcessed"] == False):
        print ("Old calibration was not post proccessed... please ensure this was"
               "part of the workflow was complete before using as a base" )
        return False
    
    if not ("InternalLED" in  old.status) or ( old.status["InternalLED"] == False):
        print ("Internal LED Data is missing from Old Calibration" )
        return False
    
    #if not ("InternalLED" in  new.status) or ( new.status["InternalLED"] == False):
    if (new.IntLEDHist is None):
        print ("Internal LED Data is missing from New Calibration" )
        return False
    
    # Copy the existing calibration data over:
    new.FEChannels = copy.deepcopy(old.FEChannels)
    
    # Update the status to reflect what has been copied:
    for key in ["BiasStored", "ExternalLED", "Mapped", "BadFE"]:
        if key in old.status:
            new.status[key] = old.status[key]
            
    # Make a canvas to draw on:
    c1 = ROOT.TCanvas("c_comp","compare", 800, 600)
    c1.Divide(2,1)
    
    # Perform updates by comparing the datasets:
    for ChannelUID in range(FECalibrationUtils.NUM_CHANS):
        
        print ("Processing Channel %i"%ChannelUID)
        
        # Load each channel from the internalLED data:
        PedHistOldLED = old.IntLEDHist.ProjectionY("th1d_led_old",ChannelUID+1,ChannelUID+1,"")
        for i in range (10):
            PedHistOldLED.SetBinContent(i, 0.0)
            
        FEChannelOld = old.FEChannels[ChannelUID]
        
        # If the channel is registered with issues, skip the
        # update processing:
        skip = False
        for Issue in FEChannelOld.Issues:
            if (Issue["Severity"] > 5):
                print ("!!! skipping over channel with issues: ")
                print FEChannelOld.Issues
                skip = True
        
        if skip:
            continue
            
        if FEChannelOld.InTracker == 0:
            print ("!!! skipping over channel not in tracker ")
            continue
            
        # Check the P-value from the comparrison of the histograms to 
        # see if the channel really needs updating:
        # Not tested - may uncomment later.
        #Prob = PedHistOldLED.Chi2Test("UU")
        #if Prob > 0.05:
        #    continue
        
        # Try fitting the existing histogram with a double gauss, starting
        # parameters guessed from the old calibration.
        upthresh = FEChannelOld.ADC_Pedestal + 1.5 *  FEChannelOld.ADC_Gain
        oldfitfcn = ROOT.TF1("OldFit","gaus+gaus(3)",0,upthresh)
        oldfitfcn.SetParameter(0,PedHistOldLED.GetBinContent(int(FEChannelOld.ADC_Pedestal)))
        oldfitfcn.SetParameter(1,FEChannelOld.ADC_Pedestal)
        oldfitfcn.SetParameter(2,2)
        oldfitfcn.SetParameter(3,PedHistOldLED.GetBinContent(int(FEChannelOld.ADC_Pedestal+FEChannelOld.ADC_Gain)))
        oldfitfcn.SetParameter(4,FEChannelOld.ADC_Pedestal+FEChannelOld.ADC_Gain)
        oldfitfcn.SetParameter(5,2)
        
        c1.cd(1)
        PedHistOldLED.Fit(oldfitfcn, "R")
        oldfit_chindf = oldfitfcn.GetChisquare()/oldfitfcn.GetNDF()
        
        # Load each channel from the new internalLED data:
        PedHistNewLED = new.IntLEDHist.ProjectionY("th1d_led_new",ChannelUID+1,ChannelUID+1,"")
        for i in range (10):
            PedHistNewLED.SetBinContent(i, 0.0)
            
        FEChannelNew = new.FEChannels[ChannelUID]
        
        # Construct a fit function to fit, using the last set of
        # fit perameters which were recorded. Then Fit.
        newfitfcn = ROOT.TF1("NewFit","gaus+gaus(3)",0,upthresh)
        for i in range (6):
            newfitfcn.SetParameter(i,oldfitfcn.GetParameter(i))
        
        c1.cd(2)
        PedHistNewLED.Fit(newfitfcn, "R")
        newfit_chindf = newfitfcn.GetChisquare()/newfitfcn.GetNDF()
        
        issuefound = False
        
        # Check chisquares, then other parameters and store to the channels internal
        # state.
        if (oldfit_chindf > 8) or (newfit_chindf > 8):
            issuefound = True
            FEChannelNew.Issues.append({"ChannelUID":ChannelUID,
                                        "Severity":8,
                                        "Issue":"Calibration Update",
                                        "Comment":"Fit completed with unsatisfactory chisquare: %.2f, %2.f"%(oldfit_chindf,newfit_chindf)})
        else:
             
            # Save the parameters:
            FEChannelNew.ADC_Pedestal = newfitfcn.GetParameter(1)
            FEChannelNew.ADC_Gain = newfitfcn.GetParameter(4) - newfitfcn.GetParameter(1)
            
            ped_odiff = FEChannelOld.ADC_Pedestal - oldfitfcn.GetParameter(1)
            gain_odiff = FEChannelOld.ADC_Gain + oldfitfcn.GetParameter(1) - oldfitfcn.GetParameter(4)
            
            ped_ndiff = FEChannelOld.ADC_Pedestal - FEChannelNew.ADC_Pedestal
            gain_ndiff = FEChannelOld.ADC_Gain - FEChannelNew.ADC_Gain
        
        
            if (abs(ped_odiff) > 0.5) or (abs(gain_odiff) > 0.5):
                issuefound = True
                FEChannelNew.Issues.append({"ChannelUID":ChannelUID,
                                            "Severity":6,
                                            "Issue":"Calibration Update",
                                            "Comment":"Orignal Pedestal differences above threshold: %.2f, %2.f"%(ped_odiff,gain_odiff)})
            
            if (abs(ped_ndiff) > 0.5) or (abs(gain_ndiff) > 0.5):
                issuefound = True
                FEChannelNew.Issues.append({"ChannelUID":ChannelUID,
                                            "Severity":6,
                                            "Issue":"Calibration Update",
                                            "Comment":"New Pedestal differences above threshold: %.2f, %2.f"%(ped_ndiff,gain_ndiff)})
        
        #if (issuefound):
        #    c1.Update()
        #    raw_input("we found an issue!")
    new.status["InternalLED"] = True  
        
if __name__ == "__main__":
    
    # Test script:
    print (module_description)
    
    try:
        print ("")
        path = sys.argv[1]
        newpath = sys.argv[2]
        print ("loading calibration from directory: %s"%path)
        print ("")
        
        print ("loading calibration config...")
        config = FECalibrationUtils.LoadCalibrationConfig(path)
        print ("... done")
        print ("")
        
        print ("loading calibration config...")
        newconfig = FECalibrationUtils.LoadCalibrationConfig(newpath)
        print ("... done")
        print ("")
    
    except:
        print "Failed to load valid configuration from calibration directory"
        raise
    
    
    # Construct a main "ADC Calibtation" Object, which we will return and manipulate
    # later using a GUI....
    Calibration = ADCCalibrator.ADCCalibration()
    Calibration.Load(config)
    Calibration.LoadInternalLED()
    
    CalibrationNew = ADCCalibrator.ADCCalibration()
    CalibrationNew.Load(newconfig)
    CalibrationNew.LoadInternalLED()
    
    UpdateCalibration(Calibration, CalibrationNew)
    
    # Store the new calibration:
    FECalibrationUtils.SaveFEChannelList(CalibrationNew.FEChannels, os.path.join(newconfig["path"], newconfig["FECalibrations"]))
    FECalibrationUtils.SaveCalibrationStatus(CalibrationNew.status, newconfig["path"])
    
    
    