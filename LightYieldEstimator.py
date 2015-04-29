#!/usr/bin/env python

module_description = \
"""
 === Light Yield Estimator ======================================

    Module to process a TH1D and find appropriate light yields...
    
    Much of this code was stolen from Adeys LYCalib routine.
    
"""

import ROOT
import sys
sys.path.insert(0, '/home/daq/tracker/analysis')
from TrDAQReader import TrDAQRead
import numpy
import math

#Compare tolerence (for comparing floats)
cmp_tol = 1E-6

spectrum = ROOT.TSpectrum()

class LightYieldEstimator:
    """
    Object to process the light yields and return the status of the channel
    TODO: Insert method to precicely find location of every peak.
    TODO: Evaluate integrals of each peak.
    """
    
    ####################################################################
    ChannelState = "INVALID"
    Peaks = []
    Integrals = []
    gain = 0.
    offset = 0.
    darkcounts = 0.
    pe = 0.
    
    ####################################################################
    def __init__(self):
        self.reset()
        #self.spectrum = ROOT.TSpectrum()
        
    ####################################################################  
    def reset(self):
        self.ChannelState = "INVALID"
        self.Peaks = []
        self.Integrals = []
        self.gain = 0.
        self.offset = 0.
        self.darkcounts = 0.
        self.pe = 0.
        
    def getMap(self):
        return self.__dict__
        
    def loadMap(self,readdict):
        for key in readdict:
            setattr(self, key, readdict[key])
        
        
    ####################################################################
    def process(self,channel_histogram, ledLYE=None):
        """
        Process a histogram to locate each of the photo peaks and
        then use this to estimate stuff:
        """
        self.reset();        
        ch = channel_histogram
        
        # Check entries for empty histogram:
        if( ch.GetEntries() == 0):
            print ("NoData Detected.")
            self.ChannelState = "NoData"
            return
        
        # If the max bin is set, then the channel is probably in beakdown:
        if self.detectBreakdown(ch):
            print ("Breakdown Detected.")
            self.ChannelState = "Breakdown"
            return
        
        # Using a ROOT TSpectrum, find the PE peaks in this channel's
        # ADC distribution, then store the positions of the peaks in self.Peaks
        # 2 = minimum peak sigma, 0.0025  = minimum min:max peak height ratio - see TSpectrum
        nPeaks = spectrum.Search(ch,2,"", 0.0025 );
        
        # If one peaks was found, then its probable that things were under biased..
        if (nPeaks == 0):
            print ("NoPeaks Detected.")
            self.ChannelState = "NoPeaks"
            return
        
        # Load and re-order the peaks...
        temp_peaks = spectrum.GetPositionX()
        for p in range(nPeaks): 
                if (temp_peaks[p] > 1.0):
                    self.Peaks.append(temp_peaks[p])
        self.Peaks.sort()
        
        if (nPeaks == 1):
            self.ChannelState = "NoPEPeaks"
            if (ledLYE is None):
                return
            elif( len(ledLYE.Peaks) < 2):
                return

        
        # If availalbe use LED LYE:
        if not (ledLYE is None):
            # Check for more peaks than LED peaks:
            if ( (len (self.Peaks) > len (ledLYE.Peaks) ) and \
                 (len (self.Peaks) < 5) ) or ( len (ledLYE.Peaks) < 2):
                print ("Peak mismatch.. more for noled!")
                self.ChannelState = "LEDPeakMisMatch"
                return
            
            # Copy values LED found:         
            self.gain = ledLYE.gain
            self.offset = ledLYE.offset
            self.Peaks = ledLYE.Peaks
        else:
            # Estimate pedastools, then fit (not needed):
            #self.gain = self.gainEstimator()      
            # Fit the pedastool peaks:     
            pedfit = self.fitPedastroolSinges(ch)
            self.Peaks[0] = pedfit[1]
            self.Peaks[1] = pedfit[4]
            # Repeat gain measurement with improved
            # peak estimation.
            self.gain = self.gainEstimator()
            self.offset = self.Peaks[0]
        
            
        self.ChannelState = "PEPeaks"
        # Calculate Dark Count:
        self.darkcounts = self.getDarkCount(ch)
        #print ("Gain = %.3f"%self.gain)
        
        # Estimate the average npe:
        self.pe = (ch.GetMean() - self.offset)/self.gain
        
        

    ####################################################################
    def gainEstimator(self, peaks=None):
        """
        Estimate the gain of the channel based on the peak locations..
        
        method: take median of the peak distances.
        """
        steps = []
        if peaks is None:
            peaks = self.Peaks
        
        if len(peaks)==1:
            return .0
        
        for p in range (1, len(peaks)):
            steps.append(peaks[p] - peaks[p-1])
        
        # Take median of peaks:
        gain_median = numpy.median(steps)
        
        if len(steps) == 2:
            return steps[0]
        else:
            # Remove steps which are not within tolerence:
            tolerence = gain_median*0.2
            steps_filtered = [s for s in steps if math.fabs(s-gain_median) < tolerence]
        
            return numpy.mean(steps_filtered)
            #gain_mean = numpy.mean(steps)
    
    ####################################################################
    def fitPedastroolSinges(self, hist, peaks=None):
        """
        Function to fit the Pedastool and singles peak..
        returns fit parameters : ped gaus N, ped gaus mean, ped gaus sigma,
                                 single gaus N, single gaus mean, single gaus sigma
                                 + errors.
        """
        
        extpeaks = True
        
        if peaks is None:
            peaks = self.Peaks
            extpeaks = False
            
        # Fit function:
        fitFunction = ROOT.TF1("pedfit","gaus(0) + gaus(3)", peaks[0] - (self.gain/2.0), peaks[0] + (3.0*self.gain/2.0))
        
        # Th1f peaks:
        if extpeaks:
            fitFunction.FixParameter(1,peaks[0])
            fitFunction.FixParameter(4,peaks[1])
        else:
            fitFunction.SetParameter(1,peaks[0])
            fitFunction.SetParLimits(1, peaks[0] - (self.gain/2.0) , peaks[0] + (self.gain/2.0))
            fitFunction.SetParameter(4,peaks[1])
            fitFunction.SetParLimits(4, peaks[1] - (self.gain/2.0) , peaks[1] + (self.gain/2.0))
        
        fitFunction.SetParameter(2,2.0)
        fitFunction.SetParLimits(2, 0.2 , 3.0)
        fitFunction.SetParameter(5,2.0)
        fitFunction.SetParLimits(5, 0.2 , 3.0)
        hist.Fit(fitFunction,"QN")
        
        
        return ([fitFunction.GetParameter(i) for i in range(6)]\
                + [fitFunction.GetParError(i) for i in range(6)])
        
    
    ####################################################################
    def getDarkCount(self, hist, peaks=None):
        """
        Evaluate the dark count for a historam with peaks specified.      
        """
        if peaks is None:
            peaks = self.Peaks
        
        try:    
            threshBin = hist.FindBin(peaks[1] - (self.gain/2.0))
            upperBin = hist.GetNbinsX()
            darkCount = hist.Integral(threshBin,upperBin)/hist.Integral(1,upperBin)
        except:
            pass
            
        return darkCount   
        
    ####################################################################
    def detectBreakdown(self,hist):
        """
        Detect that the module is in breakdown...
        TODO: Improve with check for most populated bin (highest...)
        """
        threshBin = hist.FindBin(240)
        upperBin = hist.GetNbinsX()
        return ( hist.Integral(threshBin,upperBin) >  cmp_tol)
    
    
if __name__ == "__main__":
    
    #Test script:
    channels = [3636,3979]
    
    allpeds = TrDAQRead(sys.argv[1])["RawADCs"]
    
    allpeds.Draw("COL")
    
    lye = LightYieldEstimator()
    
    for channel in channels:
        chan_hist = allpeds.ProjectionY("th1d_projecty",channel,channel,"")
        lye.process(chan_hist)
        print ("channel: %i, state: %s, peaks: %i"%(channel, lye.ChannelState, len (lye.Peaks)))
        print (lye.getMap())
        
    import time
    while True:
        time.sleep(5)
    