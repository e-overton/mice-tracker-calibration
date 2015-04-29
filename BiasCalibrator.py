#!/usr/bin/env python

module_description = \
"""
 === Bias Calibrator Script =====================================

    From a calibration campaign, run a bias calibration of
    the collected data.

    Arguments: <Campaign directory>
    
"""
####################################################################
# Modules
import sys
import ROOT
from _abcoll import Iterable
sys.path.insert(0, '/home/daq/tracker/analysis')
from TrDAQReader import TrDAQRead
import os
import json
import math
import LightYieldEstimator

# Defines:
valid_dataset_keys = ['LEDState', 'bias', 'filename', 'filepath']


####################################################################
def main ():
    """ 
    Run the main functionality of the script
    """  
    print (module_description)
    # Calibration setup:
    calibration_dir = ""

    # check arguments:
    if (len(sys.argv) < 2):
        print ("Incorrect arguments.")
        print ("usage: [calibration_dir]")
        sys.exit (1)
    else:
        calibration_dir = sys.argv[1]
        print ("Looking to calibration dir: %s"%calibration_dir )
    
    calibration_file = os.path.join(calibration_dir, "campaign.json")
    campaign = GetCampaignFromJSON ( calibration_file, calibration_dir)
    
    print ("Got Campaign, Now Loading Data.." )
    campaign = LoadCampaign(campaign)
    
    # Fill the bunched modules:
    print ("Data Loaded, now processing modules.." )
    # Modules
    modules = []
    for board in [6]:
        for bank in range(1):
            for module in range (2):
                modules.append( [c+module*64+bank*128+board*512 for c in range (64)] )
                
    FillModuleChannels(campaign, modules)
    
    for dataset in campaign:
        dataset["biascalib"]["allpeds"] = None
    with open(os.path.join(calibration_dir, "calib_step1.json"), "w") as outfile:
        json.dump(campaign, outfile, skipkeys=True)
        
    plotModule(campaign, 0)
    #testDarkCount(campaign)

####################################################################
def LoadCampaign(campaign, check_keys=valid_dataset_keys):
    """ 
    Load histograms for each element of the campaign, and
    store in orignal data structure, under the key "biascalib".
    Remove elements of the campaign which do not contain all the
    required keys
    
    Campaign: a calibration campagin
    Check_keys: a set of keys which must exist for loading.
    
    Retuns: a new list containing the loaded data:
    """
    
    led_runs = []
    no_led_runs = []
    
    for run in campaign:
        # Check the run has data collected
        if not all(valid_key in run for valid_key in check_keys):
            print ("Data missing for calibration bias run")
            continue
            
        if run['LEDState'] == "OFF":
            no_led_runs.append(run)
        else:
            led_runs.append(run)
    
    # Run the LED runs first, followed by the no LED runs.
    # this ensures that LED Data is available for analysis...
    load_campagin = led_runs + no_led_runs
    missing_files = 0     
    for dataset in load_campagin:       
        # Check that the bias calibrations dictionary exists in the
        # existing data structure.
        if not ("biascalib" in dataset):
            dataset["biascalib"] = {}
                  
        # Load File
        try:
            title = "allpeds_Bias_" + str(dataset["bias"]) + ("_led" if dataset["LEDState"]=="ON" else "_noled")
            dataset["biascalib"]["allpeds"] = TrDAQRead(dataset["filepath"], title)["RawADCs"]
        except IndexError:
            print ("ERROR: Unable to load no-led-file:" + dataset["filepath"])
            missing_files += 1
            continue
    
    return load_campagin
        

####################################################################
def FillModuleChannels(loaded_campaign, module_list):
    """
    Take a campaign of loaded data, combined with a list of modules:
        the module object is a dictionary, with a top level list of the
        assosiated "unique channels".
    
    returns: a new list of modules, each module is a map containing:
        runs - array of each run, each run is a dictionary containing:
        bias/led states, channel[] of peaks/dark count/ states
    """
    
    for module_id in range ( len(module_list) ):
        #for module in module_list:
        module = module_list[module_id]
        
        # Iterate over every dataset that was loaded, to pull out
        # each unique channel from that dataset in every module.
        for dataset in loaded_campaign:
            
            allpeds = dataset["biascalib"]["allpeds"]            
            lye_channels = []
            
            # Loop over each unique channel:
            for channel_id in range ( len(module) ):
                #for channel in module:
                channel = module[channel_id]
                
                # The pedastool histogram object, which will be analysed:
                ped = allpeds.ProjectionY("th1d_projecty",channel,channel,"")                
                bias = GetChannelBias(dataset, channel)
                led_state = GetLEDState(dataset, channel)
                
                # If not LED run, identify matching LED data...
                led_run = None
                if not led_state:
                    led_run = GetMatchedBiasDataset(loaded_campaign, channel, bias, True)
                if (led_run is channel):
                    print ("overlapping led detected...")
                
                print ("Running channel: %i, bias: %.2f, led: %s, ledrun: %r"%\
                        (channel, bias, dataset['LEDState'], not (led_run is None) ) )
                
                
                led_lye = None
                if not (led_run is None):
                    led_chan = led_run["biascalib"]["modules"][module_id][channel_id]
                    led_lye = LightYieldEstimator.LightYieldEstimator()
                    led_lye.loadMap(led_chan)
                    
                # Process the pedastools:
                # TODO: Use LED Peaks
                lye = LightYieldEstimator.LightYieldEstimator()
                lye.process(ped, led_lye)
                lye_map= lye.getMap()
                lye_map["channel"] = channel
                lye_channels.append( lye_map )
                
            # Append module to dataset:
            if not ("modules" in dataset["biascalib"]):
                dataset["biascalib"]["modules"] = []
                
            dataset["biascalib"]["modules"].append(lye_channels)
                
        
    
    
####################################################################
def GetMatchedBiasDataset(loaded_campaign, unique_channel, bias, LEDState):
    """
    Look over the existing datasets to identify those with matching
    bias and LED state.
    
    TODO: Implement individual lookup of biases / multuple LED States
    """

    for dataset in loaded_campaign:            
            # Look for correct LED
            if (GetLEDState(dataset, unique_channel) == LEDState):
                if ( math.fabs(GetChannelBias(dataset, unique_channel)  - bias) < 1E-6):
                    return dataset
                
    return None

def GetChannelBias(dataset, unique_channel):
    """
    Extract the bias for the unique_channel from the dataset.
    """
    if dataset['bias'] is Iterable:
        return dataset['bias'][unique_channel]
    else:
        return dataset['bias']
    
def GetLEDState(dataset, unique_channel):
    """
    Extract the LED State for the channel using the LEDMask..
    if it is available...
    """
    if dataset['LEDState'] == "ON":
        if ("LEDMask" in dataset):
            return dataset["LEDMask"][unique_channel]
        else:
            return True
    else:
        return False

####################################################################
def GetCampaignFromJSON(filename, rootPath=None):
    """ 
    Get the calibration campagin data from a specific directory
    and return the python structure to it, or if this failed,
    False
    """  
    # Try to load the 
    output = False
    f =  open(filename, "r")

    try:
        output = json.load(f)
    except:
        output = False
        raise
    finally:
        f.close()
    
    if not (rootPath is None):
        for run in output:
            try:
                filename = run["filename"]
                print (filename)
                run["filepath"] = os.path.join(rootPath, filename)
            except:
                continue
                
    return output

####################################################################
####################################################################
####################################################################
# Odd scripts

def testDarkCount(campaign):
    
    tg = ROOT.TGraph()
    
    for dataset in campaign:
        bias = dataset["bias"]
        led = dataset["LEDState"]
        chans = dataset["biascalib"]["modules"][0]
        
        if (led == "OFF"):
            for chan in chans:
                tg.SetPoint(tg.GetN(), bias, chan["darkcounts"])
    
    
    tg.Draw("ap")
                
    import time
    while True:
        time.sleep(5)

def plotModule(campaign, module_id):
    
    # Generate graphs:
    tg_lightyield = ROOT.TGraph()
    tg_darkcount = ROOT.TGraph()
    h_breakdown = ROOT.TH1D("h_breakdown", "h_breakdown", 50, 4.0, 8.0)
    
    for dataset in campaign:
        bias = dataset["bias"]
        led = dataset["LEDState"]
        chans = dataset["biascalib"]["modules"][module_id]
        
        if (led == "OFF"):
            for c_i in range( len(chans) ):
                chan = chans[c_i]
                if chan["ChannelState"] == "Breakdown":
                    h_breakdown.Fill(bias)
                else:
                    tg_darkcount.SetPoint(tg_darkcount.GetN(), bias, chan["darkcounts"])
                    
                    # Find complimentary run:
                    led_ds = GetMatchedBiasDataset(campaign, chan["channel"], bias, True)
                    if not (led_ds is None):
                        led_channel = led_ds ["biascalib"]["modules"][module_id][c_i]
                        lightyield = led_channel["pe"] - chan["pe"]
                        tg_lightyield.SetPoint(tg_lightyield.GetN(), bias, lightyield)
            
    c1 = ROOT.TCanvas()
    c1.Divide(2,2)
    c1.cd(1)
    tg_darkcount.Draw("ap")
    c1.cd(2)
    tg_lightyield.Draw("ap")
    c1.cd(3)
    h_breakdown.Draw()
                
    import time
    while True:
        time.sleep(5)

####################################################################
if __name__ == "__main__":
    
    main()
    
    ##################################################################
    # testing code:
    
    #campaign = GetCampaignFromJSON ("/home/ed/MICE/tracker/calib/20150416d/calib_step1.json" )
    #plotModule(campaign, 0)