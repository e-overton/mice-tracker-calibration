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
        # update processing, unless it has been reflagged OK.:
        severity = 0
        flagged_ok = False
        for Issue in FEChannelOld.Issues:
            if (Issue["Issue"] == "AcceptedBad"):
                if Issue["Severity"] == 0:
                    flagged_ok = True
            else:
                severity = Issue["Severity"] if Issue["Severity"] > severity else severity
        
        if not flagged_ok and severity > 4:
            print "skipping channel with issues %i"%ChannelUID
            continue
        
        if FEChannelOld.ADC_Pedestal < 1.0:
            print "skipping channel with zero pedestal %i"%ChannelUID
            continue
            
        #if FEChannelOld.InTracker == 0:
        #    print ("!!! skipping over channel not in tracker ")
        #    continue
            
            
        # Find pedestal on new fit function:
        PedHistNewNoLED = new.IntNoLEDHist.ProjectionY("th1d_noled_new",ChannelUID+1,ChannelUID+1,"")
        maxbin = PedHistNewNoLED.GetMaximumBin()
        maxbin_centre = PedHistNewNoLED.GetXaxis().GetBinCenter(maxbin)
        maxbin_entries = PedHistNewNoLED.GetBinContent(maxbin)
        
        
        fitfcn = ROOT.TF1("OldFit","gaus",maxbin_centre-8.0,maxbin_centre+3.0)
        fitfcn.SetParameter(0,maxbin_entries)
        fitfcn.SetParameter(1,maxbin_centre)
        fitfcn.SetParameter(2,1.8)
        PedHistNewNoLED.Fit(fitfcn, "R")
        fit_chindf = fitfcn.GetChisquare()/fitfcn.GetNDF() 
             
        FEChannelNew = new.FEChannels[ChannelUID]
        
        issuefound = False
        
        # Check chisquares, then other parameters and store to the channels internal
        # state.
        if (fit_chindf > 8):
            issuefound = True
            FEChannelNew.Issues.append({"ChannelUID":ChannelUID,
                                        "Severity":8,
                                        "Issue":"Calibration Update",
                                        "Comment":"Fit completed with unsatisfactory chisquare: %.2f"%fit_chindf})
        else:
             
            # Save the parameters:
            FEChannelNew.ADC_Pedestal = fitfcn.GetParameter(1)
            FEChannelNew.ADC_Gain = FEChannelOld.ADC_Gain
        
            if (abs(FEChannelOld.ADC_Pedestal - FEChannelNew.ADC_Pedestal) > 0.5):
                issuefound = True
                FEChannelNew.Issues.append({"ChannelUID":ChannelUID,
                                            "Severity":6,
                                            "Issue":"Calibration Update",
                                            "Comment":"Orignal Pedestal differences above threshold: %2.f"%\
                                            (FEChannelOld.ADC_Pedestal - FEChannelNew.ADC_Pedestal)})


        if issuefound:
            # Clear Flag...
            FEChannelNew.Issues = [i for i in FEChannelNew.Issues if i["Issue"] != "AcceptedBad"]
            

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
    
    print "Done"
    
    
    