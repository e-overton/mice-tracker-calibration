#!/usr/bin/env python

module_description=\
"""
ADC Calibrator tools.


E. Overton, July 2015.
"""

# Generic python imports:
import os
import sys
import math

# Load ROOT objects
import ROOT

# Objects for ADC Calibrations:
import FECalibrationUtils
import FrontEndChannel
import TrDAQReader
from LightYieldEstimator import LightYieldEstimator
import ConfigParser
import PoissonPeakFitter


# Copy of all data needed for adc calibrations:
class ADCCalibration:

    def __init__(self):

        # Status of calibration
        self.status = None
        
        # Front end channel calibrations
        self.FEChannels = None
        
        # External LED hisrograms (0-8192 channels)
        # ROOT Objects - not json compatile, could need stripping
        self.ExtLEDHist = None
        self.ExtNoLEDHist = None
        
        # Internal LED Histograms (0-8192 channels)
        # ROOT Objects - not json compatile, could need stripping
        self.IntLEDHist = None
        self.IntNoLEDHist = None
        
        # Store of the config:
        self.config = None


    def Load(self,config):
        """
        Load a calibration from a config.
        """    
        self.config = config
        
        # Load the status:
        self.status = FECalibrationUtils.LoadCalibrationStatus(config["path"])
        
        #Try to load an existing calibration - or make a fresh
        try:
            self.FEChannels = FECalibrationUtils.LoadFEChannelList(os.path.join(config["path"],self.config["FECalibrations"]))
            print ("Loaded existing FECalibrations %s"%self.config["FECalibrations"])
        except:
            self.FEChannels = FECalibrationUtils.GenerateFEChannelList()
            print ("No existing FECalibrations found... Generated some empty data")

   
    def LoadExtras(self):
        # Load and apply bias settings:    
        if not ("BiasStored" in  self.status) or ( self.status["BiasStored"] == False):
            self.ApplyBiases()
            
        # Apply bad channels list to the data:
        if not ("BadFE" in  self.status) or ( self.status["BadFE"] == False):
            self.ApplyBadFrontEnds()
            
        # Apply tracker mapping to data:
        if not ("Mapped" in self.status) or (self.status["Mapped"] == False):
            self.ApplyMapping()

        
    def ApplyBiases(self):
        try:
            bias_path = os.path.join(self.config["path"], self.config["Biases_Filename"])
            FECalibrationUtils.ApplyBiasData(self.FEChannels, bias_path)
            self.status["BiasStored"] = True
            print ("Loaded Biases from file: %s"%bias_path)
        except:
            print ("Failed to load Biases, no problem, igonoring.")

            
    def ApplyBadFrontEnds(self):    
        try:
            badfe_filename = os.path.join(config["path"], config["BadFE_Filename"])
            FECalibrationUtils.ApplyBadChannels(self.FEChannels, badfe_filename)
            self.status["BadFE"] = True
            print ("Loaded Bad FE channels from: %s"%badfe_filename)
        except:
            print ("Failed to Bad FE channels, no problem, igonoring.")

    
    def ApplyMapping(self):    
        try:
            mapping_filename = os.path.join(self.config["path"], self.config["Mapping_Filename"])
            TrackerMap = FECalibrationUtils.LoadMappingFile (mapping_filename)
            FECalibrationUtils.UpdateTrackerMapping(self.FEChannels, TrackerMap)
            self.status["Mapped"] = True
            print ("Loaded Mapping from: %s"%mapping_filename)
        except:
            print "Failed to load Mapping file, essensial, terminating."
            raise 

    
    def LoadInternalLED(self):
        """
        Load the internal LED data collected, as pointed to by
        the calibration
        """
        if not (self.IntLEDHist is None or self.IntNoLEDHist is None):
            print ("Led data is already present")
            return
        
        try:
            print ("Attempting to load internal led files ...")
            
            # Evaluate DataPath into a string
            DataPath = os.path.expandvars(self.config["DataPath"])
            
            if len(self.config["InternalLED"]) == 0:
                raise ("No Files to load!")
            elif "pedcalib" in self.config["InternalLED"][0]:
                self.IntNoLEDHist, self.IntLEDHist =\
                    FECalibrationUtils.LoadPedCalib(os.path.join(DataPath,self.config["InternalLED"][0]["pedcalib"]))
            else:
            
                # Load the LED list:
                leds_dict = self.config["InternalLED"]
                for d in leds_dict:
                    d["filepath"] = os.path.join(DataPath,d["filename"])
                
                # Load the files:
                internal_files = [d for d in leds_dict if d["led"]]
                self.IntLEDHist = TrDAQReader.TrMultiDAQRead(internal_files , "InternalLED")
                notinternal_files = [d for d in leds_dict if not d["led"]]
                self.IntNoLEDHist = TrDAQReader.TrMultiDAQRead(notinternal_files , "InternalNoLED")
                
                
            if ( self.IntNoLEDHist is None ) or ( self.IntLEDHist is None):
                print ("error loading internal led files")
            else:
                print ("... done loading external files")
        
        except:
            print ("Error loading the internal LED data")
            raise
        
    def LoadExternalLED(self):
        """
        Load the external LED data collected, as pointed to by
        the calibration
        """
        if not ( self.ExtLEDHist is None or self.ExtNoLEDHist is None):
            print ("External Led data is already present")
            return
        
        try:
            print ("Attempting to load external led files ...")
            
            # Load the external LED list:
            leds_dict = config["ExternalLED"]
            for d in leds_dict:
                d["filepath"] = os.path.join(os.path.expandvars(config["DataPath"]),d["filename"])
            
            # Load the files:
            external_files = [d for d in leds_dict if d["led"]]
            self.ExtLEDHist = TrDAQReader.TrMultiDAQRead(external_files , "ExternalLED")
            notexternal_files = [d for d in leds_dict if not d["led"]]
            self.ExtNoLEDHist = TrDAQReader.TrMultiDAQRead(notexternal_files , "ExternalNoLED")
            print ("... done loading external files")
            
        except:
            print ("Error loading the external LED data")
            raise
        
    def ProcessExternalLED(self):
        """
        Function to do the main processing of the external LED data.
        """
        if ("ExternalLED" in self.status) and (self.status["ExternalLED"] == True):
            print ("External Led data is already processed")
            return
        
        try:
            # Use the files to generate an LYE calibration:
            for FEChannel in self.FEChannels:
                
                # Channel to process:
                ChannelUID = FEChannel.ChannelUID
            
                # Get single channel hisrogram, and nuke all channels below 15,
                # to stop peaks being found there in the event there is hits there.
                PedHist_LED = self.ExtLEDHist.ProjectionY("th1d_led",ChannelUID+1,ChannelUID+1,"")
                for i in range (15):
                    PedHist_LED.SetBinContent(i, 0.0)
                
                # Check for data, if no data then flag it in the "Issues" array.
                if (PedHist_LED.GetEntries() < 1):
                        FEChannel.Issues.append({"ChannelUID":ChannelUID, "Severity":10,\
                                                "Issue":"ExternalLED","Comment":"Missing external LED data"})
                        continue
                    
                # Data Available, do the fitting processes:
                # Run std processing on the pedestal histagram.
                LightYield_LED = LightYieldEstimator()
                LightYield_LED.process(PedHist_LED)
        
                # Check the state of the output:
                if LightYield_LED.ChannelState != "PEPeaks":
                    FEChannel.Issues.append({"ChannelUID":ChannelUID, "Severity":4,\
                                             "Issue":"ExternalLED","Comment":"Failed to find LED Peaks"})
                    continue
                
                # Fit each peak, and try to improve location:
                for p in range(len(LightYield_LED.Peaks)):
                    PeakFitResults = LightYield_LED.fitPeak(PedHist_LED, p)
                    # Check each result, and copy only if good:
                    if (abs(PeakFitResults[1] - LightYield_LED.Peaks[p]) < 3.0) \
                        and (not math.isnan(PeakFitResults[1])):
                        LightYield_LED.Peaks[p] = PeakFitResults[1]
                    else:
                        print "Warning - Bad LED Fit..."
                        
                # Compute the gain from the peaks, and store object to
                # main FE channel Data structure...
                LightYield_LED.gain = LightYield_LED.gainEstimator()
                FEChannel.ADC_Pedestal = LightYield_LED.offset
                FEChannel.ADC_Gain = LightYield_LED.gain
                
                std_peaks = [LightYield_LED.offset + i*LightYield_LED.gain for i in range(5)]
                LightYield_LED.peakIntegrals(PedHist_LED, std_peaks)
                
                FEChannel.LightYieldExtLED = LightYield_LED.getMap()

                # Generate and process the NOLED Data:
                PedHist_NoLED = Calibration.ExtNoLEDHist.ProjectionY("th1d_noled",ChannelUID+1,ChannelUID+1,"")
                for i in range (15):
                    PedHist_NoLED.SetBinContent(i, 0.0)
                
                # Check for data, if no data then flag it in the "Issues" array.
                if (PedHist_NoLED.GetEntries() < 1):
                        FEChannel.Issues.append("Missing external NoLED data")
                        continue
                
                LightYield_NoLED = LightYieldEstimator()
                LightYield_NoLED.process(PedHist_NoLED, LightYield_LED)
                
                # Finally generate some estimates on noises:
                # note that the peaks are generated from the calibration for
                # consistency.
                LightYield_NoLED.peakIntegrals(PedHist_NoLED, std_peaks)
                
                # Done - save map!
                FEChannel.LightYieldExtNoLED = LightYield_NoLED.getMap()
                
                # Finally compare two histograms to identify defunct channels
                # (ie. those not connected).
                p_value =  PedHist_NoLED.Chi2Test(PedHist_LED, "UUP")
                
            # Done with external LED, update statuses:
            Calibration.status["ExternalLED"] = True
            
        except:
            print ("Error processing the external LED data")
            raise
        
    
            
    # TODO: It may be possible to include the external LED stuff in here also,
    # but there is no motivation for this at this time.

# Main function for running the ADC Calibrations,
# requires a configuration file loaded.
def main(config, ForceIntLEDLoad=True):
    
    # Construct a main "ADC Calibtation" Object, which we will return and manipulate
    # later using a GUI....
    Calibration = ADCCalibration()
    
    # Load the basic calibration (status and channel) data from a specified config:
    Calibration.Load(config)
    
    # Apply Bias, Bad channels and Mapping
    Calibration.LoadExtras()
        
    # Disable external LED processing:
    # WARNING: Remove in final version.
    Calibration.status["ExternalLED"] = True
    
    # Now try to load some of the external LED Data, and process:
    if not ("ExternalLED" in Calibration.status) or (Calibration.status["ExternalLED"] == False):
        print ("Attempting to load external led files ...")
        Calibration.LoadExternalLED()
        Calibration.ProcessExternalLED()
            
        
    # Next task, process internal LED:
    if not ("InternalLED" in Calibration.status) or (Calibration.status["InternalLED"] == False)\
        or ForceIntLEDLoad:
        print ("Attempting to load internal led files ...")
        Calibration.LoadInternalLED()
            
    # Next task, process internal LED:
    if not ("InternalLED" in Calibration.status) or (Calibration.status["InternalLED"] == False):        
          
        # Use the files to generate an LYE calibration:
        poisson_ipar = None
        for FEChannel in Calibration.FEChannels:
            
            # Channel to process:
            ChannelUID = FEChannel.ChannelUID
            print "Processing channel: ", ChannelUID
            
            # Wrap in a try loop to catch and skip errors...
            try:
                # Get single channel hisrogram, and nuke all channels below 15,
                # to stop peaks being found there in the event there is hits there.
                PedHist_LED = Calibration.IntLEDHist.ProjectionY("th1d_led",ChannelUID+1,ChannelUID+1,"")
                for i in range (10):
                    PedHist_LED.SetBinContent(i, 0.0)
                
                # Check for data, if no data then flag it in the "Issues" array.
                if (PedHist_LED.GetEntries() < 1):
                        FEChannel.Issues.append({"ChannelUID":ChannelUID, "Severity":4,\
                                             "Issue":"InternalLED","Comment":"Failed to find LED Data"})
                        continue
                    
                # Generate and process the NOLED Data:
                PedHist_NoLED = Calibration.IntNoLEDHist.ProjectionY("th1d_noled",ChannelUID+1,ChannelUID+1,"")
                for i in range (15):
                    PedHist_NoLED.SetBinContent(i, 0.0)
                    
                # Check for data, if no data then flag it in the "Issues" array.
                if (PedHist_NoLED.GetEntries() < 1):
                        FEChannel.Issues.append({"ChannelUID":ChannelUID, "Severity":4,\
                                             "Issue":"InternalLED","Comment":"Missing internal NoLED data"})
                        continue
                
                LightYield_LED = LightYieldEstimator()
                LightYield_NoLED = LightYieldEstimator()
                
                # Attempt Poisson fitting of data:
                dopoissonfit = True
                poissonfit = None
                if dopoissonfit:
                    #Do the fit:
                    poissonfit = PoissonPeakFitter.combinedfit(PedHist_NoLED, PedHist_LED, poisson_ipar)
                    #PoissonPeakFitter.drawfits(poissonfit["fit"], PedHist_NoLED, PedHist_LED)
                    poissonfit["fit"].Result().Print(ROOT.cout,True)
                    
                    # Check the status of the result
                    if poissonfit["fit"].Result().Status() == 0:
                        
                        # Sotore and check fit result, only update ipar if chisq looks good.
                        FEChannel.InternalPoissonFitResult =  poissonfit["fitpar"]
                        
                        if FEChannel.InternalPoissonFitResult["ndf"] > 0:
                            chi_ndf = FEChannel.InternalPoissonFitResult["chisq"]/FEChannel.InternalPoissonFitResult["ndf"]
                        else:
                            chi_ndf = 100
            
                        if chi_ndf> 5.0:
                            FEChannel.Issues.append({"ChannelUID":ChannelUID, "Severity":6,\
                                             "Issue":"PoissonFit","Comment":"high chisquare/ndf for fit: %i"%
                                             chi_ndf})
                        else:
                            poisson_ipar = [poissonfit["fit"].Result().Parameter(i) for i in range(8)]
                    else:
                        FEChannel.Issues.append({"ChannelUID":ChannelUID, "Severity":7,\
                                             "Issue":"PoissonFit","Comment":"Failed to Fit LED Data, status: %i"%
                                             poissonfit["fit"].Result().Status()})
                        poissonfit = None
                
                # Data Available, do the fitting processes:
                # Run std processing on the pedestal histagram.
                # Use the poisson result(if available), and skip peak finding.
                LightYield_LED.process(PedHist_LED, poissonfit=poissonfit)
                
                # Fit each peak, and try to improve location:
                if poissonfit is None:
                    for p in range(len(LightYield_LED.Peaks)):
                        PeakFitResults = LightYield_LED.fitPeak(PedHist_LED, p)
                        # Check each result, and copy only if good:
                        if (abs(PeakFitResults[1] - LightYield_LED.Peaks[p]) < 3.0) \
                            and (not math.isnan(PeakFitResults[1])):
                            LightYield_LED.Peaks[p] = PeakFitResults[1]
                        else:
                            print "Warning - Bad LED Fit..."
                        
                # Check the state of the output:
                if LightYield_LED.ChannelState != "PEPeaks":
                    FEChannel.Issues.append({"ChannelUID":ChannelUID, "Severity":4,\
                                             "Issue":"InternalLED","Comment":"Failed to find LED Peaks"})
                    continue 
                   
                # Compute the gain from the peaks, and store object to
                # main FE channel Data structure...
                LightYield_LED.gain = LightYield_LED.gainEstimator()
                LightYield_LED.offset = LightYield_LED.Peaks[0]
                    
                LightYield_NoLED.process(PedHist_NoLED, LightYield_LED, poissonfit=poissonfit)
                
                FEChannel.ADC_Pedestal = LightYield_LED.offset
                FEChannel.ADC_Gain = LightYield_LED.gain
                
                std_peaks = [LightYield_LED.offset + i*LightYield_LED.gain for i in range(5)]
                LightYield_LED.peakIntegrals(PedHist_LED, std_peaks)
            
                FEChannel.LightYieldIntLED = LightYield_LED.getMap()
                
                # Finally generate some estimates on noises:
                # note that the peaks are generated from the calibration for
                # consistency.
                LightYield_NoLED.peakIntegrals(PedHist_NoLED, std_peaks)
                
                # Done - save map!
                FEChannel.LightYieldIntNoLED = LightYield_NoLED.getMap()
                
                p_value =  PedHist_NoLED.Chi2Test(PedHist_LED, "UUP")
                
                if (p_value > 0.03):
                    FEChannel.Issues.append({"ChannelUID":ChannelUID, "Severity":6,\
                                             "Issue":"InternalLED","Comment":"LED pedestal matches no LED pedestal."})
            except KeyboardInterrupt:
                raise
            except:
                FEChannel.Issues.append({"ChannelUID":ChannelUID, "Severity":10,\
                                             "Issue":"Data","Comment":"Failed to process channel"})
                
        # Done with external LED, update statuses:
        Calibration.status["InternalLED"] = True
        
        # Update Channel Staturses
        for FEChannel in Calibration.FEChannels:
            try:
                if len(FEChannel.Issues) == 0:
                    FEChannel.Status = "GOOD"  
            except:
                continue
        
    # Final Task, return Calibration:
    return Calibration

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
    
    # Save output:
    FECalibrationUtils.SaveFEChannelList(Calibration.FEChannels, os.path.join(config["path"], config["FECalibrations"]))
    # Save Status:
    FECalibrationUtils.SaveCalibrationStatus(Calibration.status, config["path"])
    
    
    #raw_input("Script complete, press enter to continue")
    print ("ADC Calibration complete, Exiting.")
