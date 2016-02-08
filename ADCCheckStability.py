#!/usr/bin/env python
module_description=\
"""
Tools to plot tracker stability and compare.

E. Overton, Feb 2016.
"""

import sys
import FECalibrationUtils
import FrontEndChannel
import ADCCalibrator
import ROOT
import math
import os

def ADCCheckStability(OldCalibration, NewCalibration):
    """
    This function should loop over each channel to compare
    against and monitor stability.
    """
    
    # Plots to return:
    h_dy_res = ROOT.TH1D("h_dy_res", "h_dy_res", 500,-0.25,0.25)
    h_ly_res = ROOT.TH1D("h_ly_res", "h_ly_res", 500,-0.25,0.25)
    h_pdiff = ROOT.TH1D("h_pdiff", "h_piff", 8192,-0.55,8191.5)
    
    # Try to find the Old Calibration UID:
    skipped_channels = 0
    for newc in NewCalibration.FEChannels:
        assert isinstance(newc, FrontEndChannel.FrontEndChannel)
        
        # Skip channels not in detector, or bad.
        if (newc.InTracker == 0) or (newc.ADC_Gain < 1) or (newc.ADC_Pedestal < 1):
            skipped_channels += 1
            continue
        
        oldc = OldCalibration.FEChannels[newc.ChannelUID]
        assert isinstance(oldc, FrontEndChannel.FrontEndChannel)
        assert newc.ChannelUID == oldc.ChannelUID
        
        # Fill the plots (Light_Yield also includes dark counts):
        h_dy_res.Fill(newc.Dark_Yield - oldc.Dark_Yield)
        h_ly_res.Fill(newc.Light_Yield - newc.Dark_Yield - oldc.Light_Yield + oldc.Dark_Yield)
        h_pdiff.SetBinContent(h_pdiff.FindBin(newc.ChannelUID), newc.ADC_Pedestal - oldc.ADC_Pedestal)
          
    # Distribution Checks:
    status_dy = (h_dy_res.GetRMS() < 0.01) and (abs(h_dy_res.GetMean()) < 0.01)
    status_ly = (h_ly_res.GetRMS() < 0.02) and (abs(h_ly_res.GetMean()) < 0.02) 
    
    # Outlier Checks (more than 32 channels ourside specific range):
    if (h_dy_res.GetEntries() - h_dy_res.Integral(h_dy_res.FindBin(-0.05), 
                                                  h_dy_res.FindBin(+0.05))) > 32:
        status_dy = False

    if (h_ly_res.GetEntries() - h_ly_res.Integral(h_ly_res.FindBin(-0.08), 
                                                  h_ly_res.FindBin(+0.08))) > 32:
        status_ly = False
    
    
    status = status_ly and status_dy
    
    return status, {"status_dy": status_dy, "h_dy_res": h_dy_res,
                    "status_ly": status_dy, "h_ly_res": h_ly_res,
                    "h_peddiff": h_pdiff}
    
    return h_ly_res
    
    
if __name__ == "__main__":
    print (module_description)
    
    try:
        old_calibration_path = sys.argv[1]
        new_calibration_path = sys.argv[2]
    except:
        print "Failed to parse arguments"
        raise
        
    try:
        print "loading old config:", old_calibration_path, " ...", 
        old_config = FECalibrationUtils.LoadCalibrationConfig(old_calibration_path)
        print " done "
        print "loading new config:", new_calibration_path, " ...", 
        new_config = FECalibrationUtils.LoadCalibrationConfig(new_calibration_path)
        print " done "
    except:
        print "Failed to load old calibration directory"
        raise
    
    CalibrationOld = ADCCalibrator.ADCCalibration()
    CalibrationOld.Load(old_config)
    
    CalibrationNew = ADCCalibrator.ADCCalibration()
    CalibrationNew.Load(new_config)
    
    status, data = ADCCheckStability(CalibrationOld, CalibrationNew)
    
    # Update the status data - this script checked it:
    CalibrationNew.status = FECalibrationUtils.LoadCalibrationStatus(new_config["path"])
    CalibrationNew.status["Checked"] = True
    CalibrationNew.status["Quality"] = status
    CalibrationNew.status["CheckedBy"] = "ADCStabilityCheck"
    FECalibrationUtils.SaveCalibrationStatus(CalibrationNew.status, new_config["path"])
    
    # Generate a plot of the results
    c = ROOT.TCanvas("c", "c", 1000,350)
    c.Divide(3,1)
    c.cd(1)
    data["h_dy_res"].Draw()
    c.cd(2)
    data["h_ly_res"].Draw()
    c.cd(3)
    data["h_peddiff"].Draw()
    c.SaveAs(os.path.join(new_config["path"], "StabilityCheck.pdf"))
    c.SaveAs(os.path.join(new_config["path"], "StabilityCheck.png"))
    
    if not status:
        sys.exit(1)