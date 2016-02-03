#!/usr/bin/env python
module_description=\
"""
Tools to plot tracker noise rates from calibrations...

E. Overton, September 2015.

"""
import sys
import FECalibrationUtils
import FrontEndChannel
import ADCCalibrator
import ROOT

def PlotPlaneNoiseRates(FEChannels, npe_cut = 2.0):
    """
    Generate a plot for each station with an npe cut
    :type FEChannels: FrontEndChannel[]
    """
    
    assert isinstance(Calibration, ADCCalibrator.ADCCalibration)
    
    h = {}
    trk_name = ["US", "DS"]
    for tracker in ["US", "DS"]:
        for station in range (1,6):
            for plane in range (3):
                hname = "pe_%s_%i_%i_%.1f"%(tracker, station, plane, npe_cut)
                h[hname] = ROOT.TH1D(hname, hname, 215, -0.5, 214.5)
                hname = "ly_%s_%i_%i"%(tracker, station, plane)
                h[hname] = ROOT.TH1D(hname, hname, 215, -0.5, 214.5)
    
    for c in Calibration.FEChannels:
        assert isinstance(c, FrontEndChannel.FrontEndChannel)
        # Skip channels not in detector, or bad.
        if (c.InTracker == 0) or (c.ADC_Gain < 1) or (c.ADC_Pedestal < 1):
            continue

        # Extract histogram:
        pedh = Calibration.IntNoLEDHist.ProjectionY("th1d_noled",c.ChannelUID+1,c.ChannelUID+1,"")
        threshold = c.ADC_Gain*npe_cut + c.ADC_Pedestal
        fraction = pedh.Integral(pedh.FindBin(threshold), 254)/float(pedh.GetEntries())
        
        noiseh =h["pe_%s_%i_%i_%.1f"%(trk_name[c.Tracker], c.Station+1, c.Plane, npe_cut)]
        noiseh.SetBinContent(noiseh.FindBin(c.PlaneChannel), fraction)
        
        ledh = Calibration.IntLEDHist.ProjectionY("th1d_led",c.ChannelUID+1,c.ChannelUID+1,"")
        ly = (ledh.GetMean() - pedh.GetMean())/c.ADC_Gain
        lyh = h["ly_%s_%i_%i"%(trk_name[c.Tracker], c.Station+1, c.Plane)]
        lyh.SetBinContent(lyh.FindBin(c.PlaneChannel), ly)
        
        
    return h
    
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
    
    Calibration = ADCCalibrator.ADCCalibration()
    Calibration.Load(config)
    Calibration.LoadInternalLED()
    npe_cut = 2.0
    
    plots = PlotPlaneNoiseRates(Calibration.FEChannels, npe_cut)
    
    c = []
    
    for tracker in ["US", "DS"]:
        c.append(ROOT.TCanvas(tracker, tracker, 600, 900))
        c[-1].Divide (3,5)
        for station in range (1,6):
            for plane in range (3):
                c[-1].cd((station-1)*3 + plane + 1)
                hname = "pe_%s_%i_%i_%.1f"%(tracker, station, plane, npe_cut)
                plots[hname].Draw()
                plots[hname].GetYaxis().SetRangeUser(0,0.01)
        c[-1].SaveAs("20150926_%s_noise.pdf"%tracker)
                
    for tracker in ["US", "DS"]:
        c.append(ROOT.TCanvas(tracker+"ly", tracker+"ly", 600, 900))
        c[-1].Divide (3,5)
        for station in range (1,6):
            for plane in range (3):
                c[-1].cd((station-1)*3 + plane + 1)
                hname = "ly_%s_%i_%i"%(tracker, station, plane)
                plots[hname].Draw()
                plots[hname].GetYaxis().SetRangeUser(0,1.8)
        c[-1].SaveAs("20150926_%s_ledyield.pdf"%tracker)
    
    raw_input("Sleepig")