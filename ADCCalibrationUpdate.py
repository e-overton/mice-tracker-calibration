#!/usr/bin/env python
module_description=\
"""
ADC Calibrator Update functionality.

Uses an exisiting calibration as a base point to make a new calibration.

The arguments should be as follows:

OldCalibration - Old calibration folder
NewCalibrationFolder - The path to generate the new calibration in
NewCalibrationData - The new folder to generate with this calibration in. (optional)

E. Overton, July 2015.
"""

import ADCCalibrator
import ADCCalibrationPostProcessor
import FECalibrationUtils
import copy
import ROOT
import sys
import os
import shutil
import json

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
        """ Not using this since really bad channels have ADC Pedestal & Gain = 0
        severity = 0
        flagged_ok = False
        for Issue in FEChannelOld.Issues:
            if (Issue["Issue"] == "AcceptedBad"):
                if Issue["Severity"] == 0:
                    flagged_ok = True
            
            severity = Issue["Severity"] if Issue["Severity"] > severity else severity
        
        if not flagged_ok and severity > 6:
            print "skipping channel with issues %i"%ChannelUID
            continue
        """
        
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
        PedHistNewNoLED.Fit(fitfcn, "RNQ")
        fit_chindf = fitfcn.GetChisquare()/fitfcn.GetNDF() 
             
        FEChannelNew = new.FEChannels[ChannelUID]

        # Check chisquares, then other parameters and store to the channels internal
        # state.
        issuefound = 0
        if (fit_chindf > 8):
            issuefound += 1
            FEChannelNew.Issues.append({"ChannelUID":ChannelUID,
                                        "Severity":8,
                                        "Issue":"Calibration Update",
                                        "Comment":"Fit completed with unsatisfactory chisquare: %.2f"%fit_chindf})
            if (fit_chindf > 250):
                issuefound += 1 # Make more severe.
            
        if (abs(FEChannelOld.ADC_Pedestal - FEChannelNew.ADC_Pedestal) > 3.0):
            issuefound += 1
            FEChannelNew.Issues.append({"ChannelUID":ChannelUID,
                                        "Severity":6,
                                        "Issue":"Calibration Update",
                                        "Comment":"Orignal Pedestal differences above threshold: %.2f"%\
                                        (FEChannelOld.ADC_Pedestal - FEChannelNew.ADC_Pedestal)})

        if issuefound < 2:
            # Save the parameters:
            FEChannelNew.ADC_Pedestal = fitfcn.GetParameter(1)
            FEChannelNew.ADC_Gain = FEChannelOld.ADC_Gain
        else:
            # Clear Flag...
            FEChannelNew.Issues = [i for i in FEChannelNew.Issues if i["Issue"] != "AcceptedBad"]
            

    new.status["InternalLED"] = True
  
    
def GenerateFolder(newpath, newdata, templatepath):
    """
    Use the existing calibration template to generate a new
    folder for the calibration.
    """
    
    # Copy the template files into the new files:
    shutil.copytree(templatepath, newpath)
    
    if newpath.rindex('/') == len(newpath) - 1:
        newpath = newpath[:-1]
    calibname = newpath[newpath.rindex('/')+1:]
    
    # Update the calibration configuration in the "newdata" folder
    config = json.load(open(os.path.join(newpath,"config.json")))
    config["InternalLED"][0]["pedcalib"] = newdata
    config["MAUSCalibration"] = "scifi_calibration_%s.txt"%calibname
    config["OnMon_Filename"] = "scifi_onmon_%s.root"%calibname
    json.dump(config,open(os.path.join(newpath,"config.json"), "w"))
    
    # Delete the internal status:
    status = {}
    json.dump(status,open(os.path.join(newpath,"status.json"), "w"))


def GeneratePedDifferrences(old, new):
    """
    Function to plot the pedestal differences between an old calibration
    and a new one.
    
    :type old: ADCCalibration
    :type new: ADCCalibration
    """

    hist = ROOT.TH1D("peddiff", "peddiff", 8192, -0.5, 8191.5)
    
    for ch_old, ch_new in zip( old.FEChannels, new.FEChannels):
        
        if ch_old.ChannelUID != ch_new.ChannelUID:
            print "Old and New channels do not match UID! Something is badly wrong"
        
        bin = hist.FindBin(ch_old.ChannelUID)
        hist.SetBinContent(bin, ch_old.ADC_Pedestal - ch_new.ADC_Pedestal)
        
    return hist
        
        
if __name__ == "__main__":
    
    # Test script:
    print (module_description)
    
    try:
        old_calibration_path = sys.argv[1]
        new_calibration_path = sys.argv[2]
    except:
        print "Failed to parse arguments"
        raise
        
    try:
        print "loading old config:", old_calibration_path, " ..."
        oldconfig = FECalibrationUtils.LoadCalibrationConfig(old_calibration_path)
        print " done "
    except:
        print "Failed to load old calibration directory"
        raise
    
    
    # Make a new directory if one does not already exist.
    if not os.path.isdir(new_calibration_path):
        try:
            new_data_path = sys.argv[3]
        except:
            print "Please specify the data to use when generating a new calibration directory"
            raise

        try:
            GenerateFolder(new_calibration_path, new_data_path, old_calibration_path)
        except:
            print "Error generating new calibration directory"
            raise
 
    try:
        print "loading old config:", new_calibration_path, " ..."
        newconfig = FECalibrationUtils.LoadCalibrationConfig(new_calibration_path)
        print " done "
    except:
        print "Failed to load new calibration directory"
        raise
    
    
    # Construct a main "ADC Calibtation" Object, which we will return and manipulate
    # later using a GUI....
    Calibration = ADCCalibrator.ADCCalibration()
    Calibration.Load(oldconfig)
    Calibration.LoadInternalLED()
    
    CalibrationNew = ADCCalibrator.ADCCalibration()
    CalibrationNew.Load(newconfig)
    CalibrationNew.LoadInternalLED()
    
    UpdateCalibration(Calibration, CalibrationNew)
    
    # save pe
    #peddiff = GeneratePedDifferrences(Calibration, CalibrationNew)
    #peddiff.Draw()
    #raw_input("temp pause...")
    
    
    # Flag status is checked:
    CalibrationNew.status["Checked"] = True
    
    # Store the new calibration:
    FECalibrationUtils.SaveFEChannelList(CalibrationNew.FEChannels, os.path.join(newconfig["path"], newconfig["FECalibrations"]))
    FECalibrationUtils.SaveCalibrationStatus(CalibrationNew.status, newconfig["path"])
    
    # Post Process calibration/on-mon plots:
    ADCCalibrationPostProcessor.main(newconfig)
    
    print "Done"