"""
Functions to perform a poisson peak fit of a histogram
in root
"""

import ROOT
import math
import numpy
import TrDAQReader
import array
import ROOT

def poissonGaus(x, par):
    """
    Poisson peaks, made gaussian, with a scaling factor. params:
    
    0: poission entries
    1: poisson mean
    2: gain
    3: rms
    4: rms increase (n)
    5: pedestal
    """
    
    x=x[0]
    returnval = 0
    
    peaks = range(7)
    for n in peaks:
        
        prob = poisson(n, par[1])
        #if prob < 0.005:
        #    continue
        
        gauss_const = prob*par[0]
        gauss_mean = n*par[2] + par[5]
        gauss_sig= par[3] + n*par[4]
        
        returnval += gauss_const*gaussian(x, gauss_mean, gauss_sig)
    
    return returnval
    
    
def poisson(k, lamb):
    return (lamb**k/math.factorial(k)) * numpy.exp(-lamb)


def gaussian(x, mu, sig):
    return numpy.exp(-numpy.power(x - mu, 2.) / (2 * numpy.power(sig, 2.)))


class CombinedFitChiSquare( ROOT.TPyMultiGenFunction ):
    """
    Class object to calculate the combined chisquare of two 
    simultaneously fitted histograms. This enables a single
    minimiser to operate on both LED ON (light) and LED OFF (dark)
    data.
    """
    
    def __init__(self, h_dark, h_light):
        """
        Object constructor.
        :type h_dark: ROOT.TH1D
        :argument h_dark: Histogram of a single channel, no led
        :type h_light: ROOT.TH1D
        :argument h_light: Histogram of a single channel, led
        """
        
        # Construct parent object
        ROOT.TPyMultiGenFunction.__init__( self, self )
        
        # Fill in binned data for the fit.
        range_dark = ROOT.Fit.DataRange()
        range_dark.SetRange(10,100)
        opt = ROOT.Fit.DataOptions()
        self.data_dark = ROOT.Fit.BinData(opt, range_dark)
        ROOT.Fit.FillData(self.data_dark, h_dark)
        
        range_light = ROOT.Fit.DataRange()
        range_light.SetRange(10,100)
        self.data_light = ROOT.Fit.BinData(opt, range_light)
        ROOT.Fit.FillData(self.data_light, h_light)
        
        # Construct fit objects:
        self.f_dark = ROOT.TF1("f_dark",poissonGaus,0,255,6)
        self.f_dark_wrapped = ROOT.Math.WrappedMultiTF1(self.f_dark)
        self.f_light = ROOT.TF1("f_light",poissonGaus,0,255,6)
        self.f_light_wrapped = ROOT.Math.WrappedMultiTF1(self.f_light)
        
        # Construct chi-square evaluation magic:
        self.c_dark = ROOT.Fit.Chi2Function(self.data_dark, self.f_dark_wrapped)
        self.c_light = ROOT.Fit.Chi2Function(self.data_light, self.f_light_wrapped)

    def NDim(self):
        """
        Returns number of dimensions for fitting.
        """
        return 8

    def DoEval(self, x):
        """
        Calculate the combined chisquare residual between
        the fit and the 
        
        :type x: [float]
        :argument x: The parameters of the combined poisson/gausfit:
        
        x[0]: dark integral
        x[1]: light integral
        x[2]: dark poisson mean
        x[3]: light poisson mean
        x[4]: gain
        x[5]: rms
        x[6]: rms increase
        x[7]: pedestal
        """
        pars_dark = [x[0], x[2], x[4], x[5], x[6], x[7]]
        chi_dark = self.c_dark(array.array('d',pars_dark))
        
        pars_light = [x[1], x[3], x[4], x[5], x[6], x[7]]
        chi_light = self.c_light(array.array('d',pars_light))
        
        ret =  chi_light + chi_dark
        #print 'PYTHON MyFCN2::DoEval val=',chi_dark, ', ', chi_light
        
        return ret;


        
def combinedfit(h_dark, h_light, ipar=None):
    """
    Setup and perform the fit function

    :type h_dark: ROOT.TH1D
    :argument h_dark: Histogram of a single channel, no led
    :type h_light: ROOT.TH1D
    :argument h_light: Histogram of a single channel, led
    
    returns: {fitter, combinedchisqare}
    """
    
    import time

    t0 = time.time()
    
    fitter = ROOT.Fit.Fitter()
    combfit = CombinedFitChiSquare(h_dark, h_light)
    
    # Setup initial fit parameters (if not specified):
    if ipar is None:
        ipar = [h_dark.GetEntries(),
                h_light.GetEntries(),
                0.025, 1.3,
                8.0, 1.8, 0.4,
                h_dark.GetMean()]
    else:
        ipar[7] = h_dark.GetMean()

    #Convert to doubles array for ROOT:
    ipar = array.array('d',ipar)
    
    # Apply settings/limits.
    fitter.Config().SetParamsSettings(len(ipar),ipar)
    fitter.Config().ParSettings(0).SetLimits(0,ipar[0]*10)
    fitter.Config().ParSettings(1).SetLimits(0,ipar[1]*10)
    fitter.Config().ParSettings(2).SetLimits(0,5)
    fitter.Config().ParSettings(3).SetLimits(0,5)
    fitter.Config().ParSettings(4).SetLimits(3,20)
    fitter.Config().ParSettings(5).SetLimits(0.2,5.5)
    fitter.Config().ParSettings(6).SetLimits(0,1.0)
    fitter.Config().ParSettings(7).SetLimits(ipar[7]-3,ipar[7]+3)
    
    fitter.Config().SetMinimizer("Minuit2","Migrad");
    
    #fitter.FitFCN(c, 8, 0,
    #             self.data_dark.Size()+self.data_light.Size(),True)
    
    #combfit.DoEval(ipar)
    
    fitter.FitFCN(combfit, ipar, combfit.data_dark.Size()+combfit.data_light.Size(), True)
    
    t1 = time.time()

    print "time elapsed: ",  t1-t0
    
    fitpar = {"pedestal": fitter.Result().Parameter(7),
              "gain": fitter.Result().Parameter(4),
              "dark_pe": fitter.Result().Parameter(2),
              "light_pe": fitter.Result().Parameter(3)}
    
    return {"fit": fitter, "fitpar": fitpar}

def drawfits(fitter, h_dark, h_light):
    
    f_dark = ROOT.TF1("f_dark",poissonGaus,0,255,6)
    f_light = ROOT.TF1("f_light",poissonGaus,0,255,6)
    
    fitter.Result().Print(ROOT.cout,True)
    
    c = ROOT.TCanvas("c","c", 800, 600)
    c.Divide(2,1)
    
    c.cd(1)
    h_dark.Draw()
    f_dark.SetParameter(0,fitter.Result().Parameter(0))
    f_dark.SetParameter(1,fitter.Result().Parameter(2))
    f_dark.SetParameter(2,fitter.Result().Parameter(4))
    f_dark.SetParameter(3,fitter.Result().Parameter(5))
    f_dark.SetParameter(4,fitter.Result().Parameter(6))
    f_dark.SetParameter(5,fitter.Result().Parameter(7))
    f_dark.Draw("Same")
    
    c.cd(2)
    h_light.Draw()
    f_light.SetParameter(0,fitter.Result().Parameter(1))
    f_light.SetParameter(1,fitter.Result().Parameter(3))
    f_light.SetParameter(2,fitter.Result().Parameter(4))
    f_light.SetParameter(3,fitter.Result().Parameter(5))
    f_light.SetParameter(4,fitter.Result().Parameter(6))
    f_light.SetParameter(5,fitter.Result().Parameter(7))
    f_light.Draw("Same")
    
    #raw_input("test")
    
        

if __name__ == "__main__":
    
    import os
    import sys
    
    # Test the new class stuff...
    base_dir = "/home/ed/MICE/tracker/data/pedcalib/20150917_0918"
    
    adcs_dark = TrDAQReader.TrDAQRead(os.path.join(base_dir, "pedcalib_0.upstream.root"))["RawADCs"]
    adcs_light = TrDAQReader.TrDAQRead(os.path.join(base_dir, "pedcalib_1.upstream.root"))["RawADCs"]
    
    channel = 129
    adc_dark = adcs_dark.ProjectionY("h_dprj",channel+1,channel+1,"")
    adc_light = adcs_light.ProjectionY("h_lprj",channel+1,channel+1,"")
    
    result = combinedfit(adc_dark, adc_light)
    
    drawfits (result["fit"], adc_dark, adc_light)
    
    #sys.exit(0)
    
    # do a test fit:
    
    #h2d = TrDAQReader.TrDAQRead("/home/ed/MICE/tracker/data/peds/upstream/ped_20150611_171242")["RawADCs"]
    h = adc_light #h2d.ProjectionY("h_prj",channel+1,channel+1,"")
    h.Draw()

    fit = ROOT.TF1("f",poissonGaus,0,255,6) 
    fit.SetParameter(0,h.GetEntries())
    fit.SetParLimits(0,0,2*h.GetEntries())
    fit.SetParameter(1,1.5)
    fit.SetParLimits(1,0.0001,10)
    fit.SetParameter(2,2)
    fit.SetParLimits(2,3,20)
    fit.SetParameter(3,1.6)
    fit.SetParLimits(3,0.5, 3.0)
    fit.SetParameter(4,0.1)
    fit.SetParLimits(4,0.0, 1.0)
    fit.SetParameter(5,25)
    fit.SetParLimits(5,10, 50)
    
    h.Fit(fit, "","",0,100)
    
    
    raw_input("")
        
    # Call profiler:
    import time
    t0 = time.time()
    
    [poissonGaus([35], [1000, 3.5, 6, 1.6, 0.1, 25]) for i in range(10000)]
    
    t1 = time.time()
    
    print "time_elapsed ", t1-t0
    
