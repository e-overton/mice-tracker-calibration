"""
Functions to perform a poisson peak fit of a histogram
in root
"""

import ROOT
import math
import numpy
import TrDAQReader

def poissonGaus(x, par):
    """
    Poisson peaks, made gaussian, with a scaling factor. params:
    
    0: poission entries
    1: poisson mean
    2: gain
    3: rms
    4: rms increase (n)
    5: pedestal
    6: noise rate
    """
    
    x=x[0]
    
    # Lookup closest two peaks:
    n = (x-par[5])/float(par[2])
    
    peaks = []
    
    p = math.floor(n)
    if (p >= 0):
        peaks.append(p)
    
    p = math.ceil(n)
    if (p >= 0):
        if (len(peaks) == 0):
            peaks.append(p)
        elif (p != peaks[0]):
            peaks.append(p)
    
    returnval = 0
    
    for n in peaks:
        
        gauss_const = poisson(n, par[1])*par[0]
        gauss_mean = n*par[2] + par[5]
        gauss_sig= par[3] + n*par[4]
        
        returnval += gauss_const*gaussian(x, gauss_mean, gauss_sig)
    
    return returnval
    
    
def poisson(k, lamb):
    return (lamb**k/math.factorial(k)) * numpy.exp(-lamb)
    
def gaussian(x, mu, sig):
    return numpy.exp(-numpy.power(x - mu, 2.) / (2 * numpy.power(sig, 2.)))


if __name__ == "__main__":
    
    #plot = ROOT.TGraph()
    #pars = [1, 0.03, 5, 1.6, 0.2, 25]
    
    #for x in numpy.arange(0, 60, +0.5):
    #    plot.SetPoint(plot.GetN(), x, poissonGaus(x, pars))
        
    #plot.Draw("apl")
    
    #raw_input("")
    
    # do a test fit:
    channel = 2400
    h2d = TrDAQReader.TrDAQRead("/home/ed/MICE/tracker/data/peds/upstream/ped_20150611_171242")["RawADCs"]
    h = h2d.ProjectionY("h_prj",channel+1,channel+1,"")
    h.Draw()

    fit = ROOT.TF1("f",poissonGaus,0,255,6) 
    fit.SetParameter(0,h.GetEntries())
    fit.SetParLimits(0,0,2*h.GetEntries())
    fit.SetParameter(1,1.5)
    fit.SetParLimits(1,0.0001,10)
    fit.SetParameter(2,6)
    fit.SetParLimits(2,3,20)
    fit.SetParameter(3,1.6)
    fit.SetParLimits(3,0.5, 3.0)
    fit.SetParameter(4,0.1)
    fit.SetParLimits(4,-0.5, 0.5)
    fit.SetParameter(5,25)
    fit.SetParLimits(5,10, 50)
    
    h.Fit(fit, "","",0,100)
    
    
    raw_input("")
        
    