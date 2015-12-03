#!/usr/bin/env python
"""
Class to store the front end calibration infomation.

Should store the following infomation:
> Electronic Location (ChannelUID, Module(for bias), Bank, Board, EChannel)
> Tracker Location (Tracker, Station, Plane, Pchannel)
> Bias Voltage
> Issues [] - List of issues.
> Status
> For ADC calibration:
  > LYEstimator - LEDData.
  > LYEstimator - noLEDData.
  > ADC_Pedestal
  > ADC_Gain
  > Light_Yield
  > 1_pe_rate.


"""


#import TrackerMapping
import LightYieldEstimator

########################################################################
# Class Definition:
########################################################################

class FrontEndChannel:
    
    
    ####################################################################
    # Constructor:
    #   Map is a dict generated from the menber variables which can
    #   be used to initilize the object with, if present.
    def __init__(self, Map=None):
        
        ####################################################################
        # Member Variables:
        ####################################################################
        self.ClassName = "FrontEndChannel"
         
        # Unique Identfier:
        self.ChannelUID = 0
        
        # Electronics Identifier:
        self.Module = 0
        self.ModuleUID = 0 # unique identfier (0 to 127)
        self.Bank = 0
        self.BankUID = 0 # unique bank (also geoid) - 0 to 63
        self.Board = 0
        self.ModuleChannel = 0
        self.BankChannel = 0
        
        # Tracker Identifier:
        self.InTracker = 0
        self.Tracker = 0
        self.Station = 0
        self.Plane = 0
        self.PlaneChannel = 0
        
        # Channel Status:
        self.Status = "NODATA"
        self.Issues = []
        
        # Light Yields / ADC calibrations:
        self.LightYieldExtLED = None
        self.LightYieldExtNoLED = None
        self.LightYieldIntLED = None
        self.LightYieldIntNoLED = None
        self.ADC_Pedestal = 0
        self.ADC_Gain = 0
        self.Light_Yield = 0
        self.Dark_Yield = 0
        self.noise_1pe_rate = 0
        self.noise_2pe_rate = 0
        
        if not (Map is None):
            self.loadMap(Map)
        else:
            self.Issues = []
    
    # getMap - allows the objects members to be extracted as a python
    # dictionary.
    def getMap(self):
        return self.__dict__
    
    # loadMap - allows the object to be loaded from a dictoinary.
    def loadMap(self,readdict):
        for key in readdict:
            setattr(self, key, readdict[key])
    
