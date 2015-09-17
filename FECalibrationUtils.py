#!/usr/bin/env python
module_description=\
"""
Utilities for doing the front end calibrations...

Basic Functionality:
Load config directory.

"""

########################################################################
# Channel Definitions:
CHAN_PER_MOD = 64
CHAN_PER_BANK = 128
MOD_PER_BOARD = 8
BANK_PER_BOARD = 4
NUM_BOARDS = 16
NUM_CHANS = NUM_BOARDS*MOD_PER_BOARD*CHAN_PER_MOD

########################################################################
# Tracker Definitions:
N_Station = 5
N_Plane = 3
N_Tracker=2

# Imports:
import os
import sys
import csv
import json
import tempfile  # For editing data
import subprocess # For editing data

from FrontEndChannel import FrontEndChannel
import TrDAQReader


########################################################################
def LoadMappingFile (fname):
    
    # Map output
    M = [{} for i in range(8192)]

    # Load Map:
    with open(fname, "r") as f:
        for line in f:
            # Load and split line...
            words = line.split()
            board = int(words[0])
            bank = int(words[1])
            elchannel = int(words[2])
            channelUID = board*512 + bank*128 + elchannel
            # Output Map
            M[channelUID]["ChannelUID"] = channelUID
            M[channelUID]["Board"] = board
            M[channelUID]["Bank"] = bank
            M[channelUID]["BankChannel"] = elchannel
            M[channelUID]["Tracker"] = int(words[3])
            M[channelUID]["Station"] = int(words[4]) -1
            M[channelUID]["Plane"] = int(words[5])
            M[channelUID]["PlaneChannel"] = int(words[6])

    return M


########################################################################
# Generate FEChannel List
########################################################################
# Generate a list of front end channels, with no mapping applied.
def GenerateFEChannelList():
    
    # Channel Definitions:    
    FEChannels = []
    
    for chan in range (NUM_CHANS):
        
        FEChan = FrontEndChannel()
        
        # Populate electronics numbers.
        FEChan.ChannelUID = chan
        FEChan.ModuleUID = chan/CHAN_PER_MOD
        FEChan.Module = FEChan.ModuleUID % MOD_PER_BOARD
        FEChan.BankUID = chan/CHAN_PER_BANK
        FEChan.Bank = FEChan.BankUID % BANK_PER_BOARD
        FEChan.Board = FEChan.ModuleUID / MOD_PER_BOARD
        FEChan.ModuleChannel = chan % CHAN_PER_MOD
        FEChan.BankChannel = chan % CHAN_PER_BANK
        FEChannels.append( FEChan )
    
    return FEChannels

# Load an existing list:
def LoadFEChannelList(filename):
    
    with open(filename,"r") as f:
        channels_dict = json.load(f)
        
    return [FrontEndChannel(channel) for channel in channels_dict]


# Load an existing list:
def SaveFEChannelList(FEChannels, filename):
    
    with open(filename,"w") as f:
        
        json.dump([C.getMap() for C in FEChannels], f)
        
    return
       

########################################################################
# Update Tracker Mapping
########################################################################
# Use a mapping object to re-map the internal mapping of the channels.
def UpdateTrackerMapping(FEChannels, TrackerMapping):
    
    for FEChan in FEChannels:
        
        # Identify the map, which links from the channel UID
        # to internal naming:
        errors = 0
        try:
            Mapping = TrackerMapping[FEChan.ChannelUID]
            FEChan.Tracker = Mapping["Tracker"]
            FEChan.Station = Mapping["Station"]
            FEChan.Plane = Mapping["Plane"]
            FEChan.PlaneChannel = Mapping["PlaneChannel"]
        except KeyError:
            #print "Skipping channel excluded from tracker"
            FEChan.InTracker = 0
            errors += 1
        else:
            FEChan.InTracker = 1
            
        if (errors > 1500):
            raise Exception ("More than 1500 channels missing from detector, intolerable")
        
    return FEChannels

            
########################################################################
# Load Calibration Directory
########################################################################
# Function to load an existing calibration directory for use:
def LoadCalibrationConfig(path):
    
    # Find the Configuration File:
    config_filename = os.path.join(path,"config.json")
    print ("Attempting to load configuration: %s"%config_filename)
    
    # Attempt to load configuration:
    try:
        with open(config_filename,"r") as f:
            config = json.load(f)
    except:
        print ("Unable to load calibration file")
        
    # Set infomation on loaded path:
    config["config_filename"] = config_filename
    config["path"] = path
    
    return config

########################################################################
# Load Calibration Status
########################################################################
# Function to load an existing calibration status for use:
def LoadCalibrationStatus(path):
    
    # Find the Configuration File:
    config_filename = os.path.join(path,"status.json")
    print ("Attempting to load status: %s"%config_filename)
    
    # Attempt to load configuration:
    try:
        with open(config_filename,"r") as f:
            status = json.load(f)
    except:
        print ("Unable to load status file - Generating an empty status to start from")
        return {}
    else:
        return status
    
def SaveCalibrationStatus(status, path):
    
    # Find the Configuration File:
    config_filename = os.path.join(path,"status.json")
    print ("Attempting to save status: %s"%config_filename)
    
    # Attempt to load configuration:
    try:
        with open(config_filename,"w") as f:
            json.dump(status,f)
    except:
        print ("Unable to save status file - Generating an empty status to start from")

    return


########################################################################
# Apply Bias Data, from an exisitng csv file
########################################################################
# Load a CSV file containing bias data and store to master objects...
def ApplyBiasData(FEChannels, biases_filename):

    # Read in the CSV data:
    with open(biases_filename) as csvfile:
        Biases = csv.DictReader(csvfile)
    
        # Loop over the biases and apply to the channels:
        for Bias in Biases:
            for FEChannel in FEChannels:
                if FEChannel.Board == int(Bias["Board"]) and\
                   FEChannel.Module == int(Bias["MCM"]):
                
                    # Apply Bias:
                    FEChannel.Bias = float(Bias["Bias"])
    
    return FEChannels

########################################################################
# Apply list of bad channels from an existing list..
########################################################################
# Load a CSV file containing a list of bad channels, with reasons.
def ApplyBadChannels(FEChannels, bad_filename):

    # Read in the CSV data:
    with open(bad_filename) as csvfile:
        BadChannels = csv.DictReader(csvfile)
    
        # Loop over the biases and apply to the channels:
        for BadChannel in BadChannels:
            
            # Look for ChannelUIDs and apply to stack:
            try:
                ChannelUID = int(BadChannel["ChannelUID"])
                FEChannel = FEChannels[ChannelUID]
                
                # Check the channel, UID should be the same as the array inex.:
                assert( FEChannel.ChannelUID == ChannelUID)
                
                # Apply the issue to the list:
                FEChannel.Issues.append(BadChannel)
                FEChannel.Status = "BAD"
                
            except:
                raise
    
    return FEChannels

########################################################################
# Function to manually edit the data in a specific channel:
########################################################################
def EditChannelData(FEChannels, ChannelUID):
    
    # The orignal data we want to edit:
    orignal_data = FEChannels[ChannelUID]
    new_data = None
    
    tempfilename = "tempchannel.json"
    
    # Open a tempfile to parse into:
    with open(tempfilename, mode="w") as tmp:
        
        # Store the data in a tempfile:
        json.dump(orignal_data.getMap() ,tmp, sort_keys = True, indent = 4)
        tmp.flush()
        
    # Open the datafile in Gedit:
    subprocess.call(["gedit", tmp.name])
    
    # Reload the data: 
    with open(tempfilename, mode="r") as tmp:
        
        #tmp.seek(0,0)
        #tmp.flush()
        new_data = json.load(tmp)
        tmp.seek(0,0)
        for line in tmp:
            print (line)
        
        
    print "Done.. Editing data."
    if not (new_data is None):
        # Updating data:
        print "Updating data"
        FEChannels[ChannelUID] = FrontEndChannel(new_data)
    
    #import pprint
    #pprint.pprint(FEChannels[ChannelUID].getMap())
    
    return FEChannels

########################################################################
# Function to export the recorded ADC calibration in a MAUS friendly
# format for use...
########################################################################
def ExportADCCalibrationMAUS(FEChannels, output_filename):
    """
    Generate a list of dictionarys for calibration data, using
    the data stored in the FEChannels. Some (final) sanity checks are made
    during this process
    
    "bank", "channel", "adc_pedestal", "adc_gain", "tdc_pedestal", "tdc_gain"
    """
    
    output_list = []

    # ADC Gain limits:
    low_gain = 2
    high_gain = 30
    
    for FEChannel in FEChannels:
        
        Filled = False
        
        # A VLSB bank contains two modules, channels 0-127 (inclusive)
        # Fix the numbering:
        output = {}
        output["bank"] = FEChannel.BankUID
        output["channel"] = FEChannel.BankChannel

        output["adc_pedestal"] = FEChannel.ADC_Pedestal
        output["adc_gain"] = FEChannel.ADC_Gain
        
        # Check the adc gain is within limits...
        if (output["adc_gain"] < low_gain) or (output["adc_gain"] > high_gain):
            if output["adc_gain"] > 1E-3:
                print ("Bad Gain found - Channel %i"%FEChannel.ChannelUID)
            output["adc_pedestal"] = 0.0
            output["adc_gain"] = 0.0
           
             
        # Put "nothing" in the tdc data. This should  mean no data can be recovered, 
        # which is good because there is no calibration yet.
        output["tdc_pedestal"] = 0.0
        output["tdc_gain"] = 0.0
        
        output_list.append(output)

    # Set json encodrt to round to 2 decimal places:
    json.encoder.FLOAT_REPR = lambda o: format(o, '.2f')
    # Write the output list
    try:
        with open(output_filename,"w") as f:
            json.dump(output_list,f)
    except:
        print ("Unable to save status file - Generating an empty status to start from")

    json.encoder.FLOAT_REPR = lambda o: format(o, '.6f')
    
    print ("Saved maus calibration to: %s"%output_filename)
    
    return

if __name__ == "__main__":
    
    print (module_description)
    
    config = LoadCalibrationConfig(sys.argv[1])
    status = LoadCalibrationStatus(sys.argv[1])
    
    
########################################################################
# Function to load a pedcalib run:
########################################################################

def LoadPedCalib(folder_path):
    """
    Function to load a folder containing pedestal calibration
    data, using the metadata.
    """
    with open(os.path.join(folder_path, "runconfig.json"),"r") as f:
        runconfig = json.load(f)
    
    # Output histograms [noled, led]
    histograms = [None,None]
    
    for run in runconfig:
        ledid = 1 if len(run["led_pattern:"]) > 0 else 0
        
        for filename in [run["tmp_filename_upstream"],\
                         run["tmp_filename_downstream"]]:
            
            loaded_hists = TrDAQReader.TrDAQRead(os.path.join(folder_path,filename))
            if (histograms[ledid] is None):
                histograms[ledid] = loaded_hists["RawADCs"]
            else:
                histograms[ledid].Add(loaded_hists["RawADCs"])
                
    return histograms
            
        
        
    