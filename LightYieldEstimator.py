#!/usr/bin/env python

module_description = \
"""
 === Light Yield Estimator ======================================

    Module to process a TH1D and find appropriate light yields...
    
    Much of this code was stolen from Adeys LYCalib routine.
    
"""

import ROOT
import sys
#sys.path.insert(0, '/home/ed/tracker/analysis')
sys.path.insert(0, '/home/ed/MICE/tracker/analysis/')
from TrDAQReader import TrDAQRead
import numpy
import math

#Compare tolerence (for comparing floats)
cmp_tol = 1E-6

spectrum = ROOT.TSpectrum()
#spectrum.SetResolution(10) # does not seem to help

mode = "New"

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
    darkcounts_old = 0.
    pe = 0.
    
    ####################################################################
    #def __init__(self):
    #    self.reset()
    #    #self.spectrum = ROOT.TSpectrum()
        
    def __init__(self, Map=None):
        self.reset()
        if not (Map is None):
            self.loadMap(Map)
        
    ####################################################################  
    def reset(self):
        self.ChannelState = "INVALID"
        self.Peaks = []
        self.Integrals = []
        self.gain = 0.
        self.offset = 0.
        self.darkcounts = 0.
        self.darkcounts_old = 0.
        self.pe = 0.
        
        
    def getMap(self):
        return self.__dict__
        
    def loadMap(self,readdict):
        for key in readdict:
            setattr(self, key, readdict[key])
        
        
    ####################################################################
    def process(self, channel_histogram, ledLYE=None):
        """
        Process a histogram to locate each of the photo peaks and
        then use this to estimate stuff:
        """
        self.reset();        
        ch = channel_histogram
        
        # Measure mean and RMS values:
        self.RMS = channel_histogram.GetRMS()
        self.Mean = channel_histogram.GetMean()
        
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
        nPeaks = spectrum.Search(ch, 1.95,"", 0.005 )
        #nPeaks = spectrum.Search(ch, 1.6,"nobackground,noMarkov", 0.001 )
        
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
            #self.darkcounts = self.estimateDarkCount(ch)
            self.ChannelState = "NoPEPeaks"
            if (ledLYE is None):
                self.darkcounts = self.estimateDarkCount(ch)
                return
            elif( len(ledLYE.Peaks) < 2):
                self.darkcounts = self.estimateDarkCount(ch)
                return

        
        # If availalbe use LED LYE:
        if not (ledLYE is None):
            # Check for more peaks than LED peaks:
            if ( (len (self.Peaks) > len (ledLYE.Peaks) ) and \
                 (len (self.Peaks) < 5) ) or ( len (ledLYE.Peaks) < 2):
                print ("Peak mismatch.. more for noled!")
                self.ChannelState = "LEDPeakMisMatch"
                #self.darkcounts = self.estimateDarkCount(ch)
                return
            
            # Copy values LED found:         
            self.gain = ledLYE.gain
            self.offset = ledLYE.offset
            self.Peaks = ledLYE.Peaks
        else:
            # Estimate pedastools, then fit (not needed):
            self.gain = self.gainEstimator()      
            # Fit the pedastool peaks:     
            #pedfit = self.fitPedastroolSinges(ch)
            
            # Commented pedfit results, seem to be wrong!
            #self.Peaks[0] = pedfit[1]
            #self.Peaks[1] = pedfit[4]
            
            # Repeat gain measurement with improved
            # peak estimation.
            self.gain = self.gainEstimator()
            self.offset = self.Peaks[0]
        
            
        self.ChannelState = "PEPeaks"
        # Calculate Dark Count:
        self.darkcounts_old = self.getDarkCount(ch)
        self.darkcounts = self.estimateDarkCount(ch)
        #self.darkcounts = self.darkcounts_old
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
            fitFunction.SetParLimits(1, peaks[0] - (self.gain) , peaks[0] + (self.gain))
            fitFunction.SetParameter(4,peaks[1])
            fitFunction.SetParLimits(4, peaks[1] - (self.gain) , peaks[1] + (self.gain))
        
        fitFunction.SetParameter(2,2.0)
        fitFunction.SetParLimits(2, 0.2 , 3.0)
        fitFunction.SetParameter(5,2.0)
        fitFunction.SetParLimits(5, 0.2 , 3.0)
        #hist.Fit(fitFunction,"QN")
        hist.Fit(fitFunction,"")
        
        self.PedSinglesParams = [fitFunction.GetParameter(i) for i in range(6)]\
                + [fitFunction.GetParError(i) for i in range(6)]
        
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
            threshBin = hist.FindBin(peaks[1])# - (self.gain/2.0))
            upperBin = hist.GetNbinsX()
            darkCount = hist.Integral(threshBin,upperBin)/hist.Integral(1,upperBin)
        except:
            pass
            
        return darkCount

    ####################################################################
    def fitPeak(self, hist, peak):
        """
        Fit an individual peak.
        """
        peaks = self.Peaks
        print ("Fitting peak: %i from channel %i"%(peak, self.ChannelID))
        
        fitFunction = ROOT.TF1("pedfit","gaus", peaks[peak] - self.gain/3.0, peaks[peak] + self.gain/3.0)
        hist.Fit(fitFunction, "", "", peaks[peak] - self.gain/3.0, peaks[peak] + self.gain/3.0)
        
        return ([fitFunction.GetParameter(i) for i in range(3)]\
                + [fitFunction.GetParError(i) for i in range(3)])

    ####################################################################
    def estimateDarkCount(self,hist,peaks=None):
        """
        Estimate the dark count using eds strategy...
        1) Fit first PE peak
        2) Count entries above 1.5 sigmas
        3) Subtract estimates from gaus.
        4) Calculate dark count from this...
        """
        MINBIN = 2
        MAXBIN = 128
        
        if peaks is None:
            peaks = self.Peaks
        
        # 1)  Peak +- some adc counts
        fitFunction = ROOT.TF1("pedfit","gaus", MINBIN, MAXBIN)
        hist.Fit(fitFunction,"","",peaks[0]-14, peaks[0] + 3.0)
        ped_mean = fitFunction.GetParameter(1)
        ped_sigma = fitFunction.GetParameter(2)
        
        # 2)
        #threshold = math.floor(ped_mean + 1.6*ped_sigma)
        
        threshold_bin = hist.FindBin(ped_mean + 1.0*ped_sigma)
        counts_over_threshold = hist.Integral(threshold_bin, MAXBIN)
        counts= hist.Integral(MINBIN, MAXBIN)
        
        
        threshold = hist.GetBinCenter(threshold_bin)
        ped_over_threshold = fitFunction.Integral(threshold, hist.GetBinCenter(MAXBIN))
        
        if counts > 0.5:
            dc = (counts_over_threshold-ped_over_threshold)/counts
            return dc/2. if dc/2. > 0.0001 else 0.0001
        else:
            return 0
        
    ####################################################################
    def detectBreakdown(self,hist):
        """
        Detect that the module is in breakdown...
        TODO: Improve with check for most populated bin (highest...)
        """
        threshBin = hist.FindBin(240)
        upperBin = hist.GetNbinsX()
        lowBin = 5
        ratio = (hist.Integral(threshBin,upperBin) + hist.Integral(0,lowBin) / hist.GetEntries())
        return ( ratio >  0.01 ) # More than 1% in lowest 2 bins or upper 15 bins..
    
    def getPedastroolSingesFcn(self):
        fitFunction = ROOT.TF1("pedfit","gaus(0) + gaus(3)", peaks[0] - (self.gain/2.0), peaks[1] + (self.gain/2.0))
        
        for i in range(6):
            fitFunction.SetParameter(i, self.PedSinglesParams[i])
            fitFunction.SetParError(i, self.PedSinglesParams[i+6])
        
        return fitFunction
    
if __name__ == "__main__":
    
    #Test script:
    channels = [3500]
    
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
    
