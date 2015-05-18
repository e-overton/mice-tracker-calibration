#!/usr/bin/env python

module_description = \
"""
 === Bias Calibrator Script =====================================

    From a calibration campaign, run a bias calibration of
    the collected data.

    Arguments: Campaign directory, Midpoint Skip(optional)
    
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
import numpy

# Channel Definitions:
CHAN_PER_MOD = 64
MOD_PER_BOARD = 8
NUM_BOARDS = 16
NUM_CHANS = NUM_BOARDS*MOD_PER_BOARD*CHAN_PER_MOD

# Defines:
valid_dataset_keys = ['LEDState', 'bias', 'filename', 'filepath']
cmp_tol = 1E-6


####################################################################
def main ():
    """ 
    Run the main functionality of the script
    """  
    print (module_description)
    # Calibration setup:
    calibration_dir = ""
    skip = False

    # check arguments:
    if (len(sys.argv) < 2):
        print ("Incorrect arguments.")
        print ("usage: [calibration_dir]")
        sys.exit (1)
    else:
        calibration_dir = sys.argv[1]
        print ("Looking to calibration dir: %s"%calibration_dir )
    if (len(sys.argv) == 3):
        print ("Skipping to midpoint")
        skip = True
    
    campaign = None
    ChannelIDs = range(0,4096)
    ModuleIDs = GenerateModules(ChannelIDs)
    tempfilename = "stage1.json"
    
    if not skip:
        calibration_file = os.path.join(calibration_dir, "campaign.json")
        campaign = GetCampaignFromJSON ( calibration_file, calibration_dir)
    
        print ("Got Campaign, Now Loading Data..")
        campaign = LoadCampaign(campaign)
    
        print ("Setting up channels")
        for dataset in campaign:
            SetupDatasetChannels(dataset)
    
        print ("Processing Channels")
        ProcessChannels(campaign, ChannelIDs)
        
        print ("Storing JSON dunp of module processing:")
        #Strip the junk:
        for dataset in campaign:
            dataset.pop("allpeds",None)
        #Write:
        
        with open( os.path.join(calibration_dir, tempfilename), 'w') as outfile:
            json.dump(campaign, outfile)
        
    else:
        calibration_file = os.path.join(calibration_dir, tempfilename)
        campaign = GetCampaignFromJSON (calibration_file)
        
    #CalibrateModules_Highest(campaign, ModuleIDs, 0.02)
    #scan_bias, scan_points = GetBiasScan(campaign, 3075, "darkcounts", False)
    CalibrateModules_Weight(campaign, ModuleIDs, LinearWeight, {"target":0.023})
    # Note: david uses a 2% target for the noise in Lab7. This was a 140ns integration
    # gate, in the hall we are using a 1.65ns integration gate, so this has been
    # scaled accordingly.
    
    # Dump output:
    for m in ModuleIDs:
        print ("board: %i, bank: %i, bias: %f"%(m["ModuleID"]/MOD_PER_BOARD, m["ModuleID"]%MOD_PER_BOARD, m["OptimumBias"]))
    
    return {"Campaign":campaign, "Modules":ModuleIDs}
    
    #print (scan_bias)
    #print (scan_points)
    

####################################################################
def LoadCampaign(campaign, check_keys=valid_dataset_keys):
    """ 
    Load Pedastools for every valid dataset in the campaign,
    
    Retuns: a new list containing the loaded data:
    """
    
    for run in campaign:
        # Check the run has data collected
        if not all(valid_key in run for valid_key in check_keys):
            print ("Data missing for calibration bias run")
            continue
    
    # Run the LED runs first, followed by the no LED runs.
    # this ensures that LED Data is available for analysis...
    missing_files = 0     
    for dataset in campaign:                 
        # Load File
        try:
            title = "allpeds_Bias_" + str(dataset["bias"]) + ("_led" if dataset["LEDState"]=="ON" else "_noled")
            dataset["allpeds"] = TrDAQRead(dataset["filepath"], title)["RawADCs"]
        except IndexError:
            print ("ERROR: Unable to load no-led-file:" + dataset["filepath"])
            missing_files += 1
            continue
    
    return campaign

def SetupDatasetChannels(dataset, biases=None, LEDIntensity=None ):
    """
    Construct the channels for analysis in each dataset:
        Bias can be either None (use dataset), or a scalar, or a list for each channel.
        LEDIntensity represents the ammount the LED is on for a given channel.
        
        returns: dataset containing the populated channels..
        
    """
    
    # Check Bias Length..
    # Note this is either a scalar, reresenting the entire bias state, or
    # an array, with a bias for each ChannelID
    if biases is None:
        biases = dataset['bias']    
    if biases is Iterable:
        if len(biases) != NUM_CHANS:
            print "ERROR: Invalid bias list"
            
    # Setup the LED Intensity:
    # Note this is either a scalar, reresenting the entire LED state, or
    # an array, with an intensity for each ChannelID
    if LEDIntensity is None:
        LEDIntensity = dataset["LEDIntensity"] if "LEDIntensity" in dataset else 1.0    
    if LEDIntensity is Iterable:
        if len(LEDIntensity) != NUM_CHANS:
            print "ERROR: Invalid ledIntensity list"
    # If LED Is off, turn off led:
    if dataset["LEDState"] == "OFF":
            LEDIntensity = 0.0
    
    
    # Setup the channel entry:
    dataset["channels"] = []
    for ChannelID in range(NUM_CHANS):
        
        channel_dict = GenerateModuleData (ChannelID)
        channel_dict["ChannelID"] = ChannelID
        channel_dict["OK"] = True
        
        # Removed, replaced by GenerateModuleData.
        # Fill in data for each module:
        #ModuleID = ChannelID/CHAN_PER_MOD
        #Board = ModuleID/MOD_PER_BOARD
        #Module = ModuleID%MOD_PER_BOARD
        #Channel = ChannelID%(CHAN_PER_MOD*MOD_PER_BOARD)
        #channel_dict = {"ChannelID":ChannelID, "ModuleID":ModuleID,\
        #                "Channel":Channel, "Module":Module, "Board":Board,\
        #                "OK":True}
                        
        # Get Bias:
        if biases is Iterable:
            channel_dict["bias"] = biases[ChannelID]
        else:
            channel_dict["bias"] = biases
            
        # Get LED Intensity:
        if LEDIntensity is Iterable:
            channel_dict["LEDIntensity"] = LEDIntensity[ChannelID]
        else:
            channel_dict["LEDIntensity"] = LEDIntensity
            
        # Append to the list:
        dataset["channels"].append(channel_dict)
        
    return dataset
        
####################################################################
def ProcessChannels(campaign, channel_list=None):
    """
    Take a dataset and process each channel in the list (if it is available).
    Does the LED data first, and looks to this for the peak locations on
    no LED data.
    """

    if channel_list is None:
        channel_list = range (NUM_CHANS)
    
    # Iterate over each channel which requires processing, doing the
    # LED Data first:
    for ChannelID in channel_list:
        
        # Ordered list for processing campaign data:
        DatasetIDOrdered = []
        for state in [True, False]:
            for DatasetID in range(len(campaign)):
                if state == (False if campaign[DatasetID]["channels"][ChannelID]["LEDIntensity"] < 1E-6 else True):
                    DatasetIDOrdered.append(DatasetID)
    
        # Loop over the ordered campaign IDs
        for DatasetID in DatasetIDOrdered:
            
            # Load histogram of channel:
            ped = campaign[DatasetID]["allpeds"].ProjectionY("th1d_projecty",ChannelID+1,ChannelID+1,"")
            if (ped.GetEntries() < 1):
                print ("Skipping channel with no data...")
                continue
            
            # Load Channel into Light Yield Estimator:
            channel_LYE = LightYieldEstimator.LightYieldEstimator(campaign[DatasetID]["channels"][ChannelID])
            
            # Look for LED Data:
            led_state = False if campaign[DatasetID]["channels"][ChannelID]["LEDIntensity"] < 1E-6 else True
            led_channel_run = None
            if not led_state:
                led_channel_run = GetMatchedChannel(campaign, channel_LYE.ChannelID, channel_LYE.bias, True)
            if (led_channel_run is campaign[DatasetID]["channels"][ChannelID]):
                print ("overlapping led detected...")
            
            #print ("Running channel: %i, bias: %.2f, led: %s, ledrun: %r"%\
            #       (channel_LYE.ChannelID, channel_LYE.bias, led_state, not (led_channel_run is None) ) )
            led_lye = None if led_channel_run is None else LightYieldEstimator.LightYieldEstimator(led_channel_run)
            channel_LYE.process(ped, led_lye)
            campaign[DatasetID]["channels"][ChannelID] = channel_LYE.getMap()
            

def CheckChannelQuality(campaign, channel_list=None):
    """
    Look at the channel RMS to identiy those which
    are not working...
    TODO: Incomplete..
    """

    if channel_list is None:
        channel_list = range (NUM_CHANS)
    
    DefunctState = None
    DefunctChannels = []
    
    for ChannelID in channel_list:
        
        # Loop over data taking to find the LED and NOLED rms.
        rms_noled = []
        rms_led = []
        for DatasetID in range(len(campaign)):
            
            channel = campaign[DatasetID]["channels"][ChannelID]
            if channel["LEDIntensity"] > 1E-6:
                rms_led.append(channel["RMS"])
            else:
                rms_noled.append(channel["RMS"])
                
        # Look at the RMS values to determine the if there is no
        # connection
        
    
#def InterpolateDarkCounts(campaign, ChannelID, bias):
       

####################################################################    
def GenerateModules (channel_list):
    """
    Generate the standard modules for a list of channels..
    """
    
    modules = []
    for ChannelID in channel_list:
        
        ModuleID = GenerateModuleData(ChannelID)["ModuleID"]
        Module = None
        
        ## Search/Create module to add to list:
        for m in modules:
            # Identify modules for calibration:
            if m["ModuleID"] == ModuleID:
                Module = m
        if Module is None:
            # Make new module:
            m = GenerateModuleData(ChannelID)
            m["ChannelIDs"] = []
            modules.append(m)
            Module = modules[-1]
        
        # Add Channel to existing module:
        Module["ChannelIDs"].append(ChannelID)
        
    return modules
        
####################################################################
def CalibrateModules_Highest(campaign, Modules, GoodRatio):
    """
    Iterate over a list of modules, and determine the optimum bias
    settings...
    """
    # 
    for Module in Modules:
        bestBias = 0.0    
        bestRatio = 0.0
        
        for Dataset in campaign:
            # Determine state:
            LEDState = True
            BiasState = True
            scanbias = None
            darkcounts = []
            for ChannelID in Module["ChannelIDs"]:
                channel = Dataset["channels"][ChannelID]
                
                # Check the bias is matched:
                if scanbias is None:
                    scanbias = channel["bias"]
                elif math.fabs(scanbias - channel["bias"]) > cmp_tol:
                    BiasState = False
                    break
                
                # Check the LED is off:
                if channel["LEDIntensity"] > cmp_tol:
                    LEDState = False
                    break
                    
                darkcounts.append(channel["darkcounts"])
            
            # If LED/Bias states are bad. Move to next dataset.
            if (not BiasState) or (not LEDState):
                continue
            
            # Check the values against conditions:
            avg_darkcount = numpy.mean(darkcounts)
            
            
            if (avg_darkcount > 0.15):
                break
            
            if ( avg_darkcount< GoodRatio) and (avg_darkcount> bestRatio ):
                bestBias = scanbias
                bestRatio = avg_darkcount
        
        # Set best bias:
        #Module["OptimumBias"] = bestBias
        #Module["bestRatio"] = bestRatio

####################################################################
def CalibrateModules_Weight(campaign, Modules, DarkWeightFunc, FuncArgs, DefunctChannels = []):
    """
    Use a wrighting function to obtain the optimum biases,
    the function will return a low value when close to optimum..
    """
    
    # Bias Scan points:
    Biases = numpy.arange(4,8,0.05) # between 4-8v 0.05v incremenets,
    # NB: numpy useses linear interpolation to find optimums...
    
    # Iterate over all modules and channels in the selected list:
    for Module in Modules:
        
        ModuleWeights = [0 for i in range(len(Biases))]
        
        Module["ChannelWeights"] = []
        
        for ChannelID in Module["ChannelIDs"]:
            
            # Skip defunct channels:
            if ChannelID in DefunctChannels:
                continue
            
            # Lookup the bis and darkcount scans:
            scan_bias, scan_darkcounts = GetBiasScan(campaign, ChannelID, "darkcounts", False)
            
            # The darkcounts should never decrease as a function of
            # applied bias, so enforce that it does not:
            for i in range (1, len(scan_darkcounts)):
                if scan_darkcounts[i] < scan_darkcounts[i-1]:
                    scan_darkcounts[i] = scan_darkcounts[i-1]
                    
            # The dark counts, using numpys interpolate functionality:
            DarkCounts = numpy.interp(Biases, scan_bias, scan_darkcounts)
            ChannelWeights = [DarkWeightFunc(c, FuncArgs) for c in DarkCounts]
            
            # Using an actual fit to the data to estimate the darkcounts...
            # Not used... Did noy work.
#             TG = ROOT.TGraph()
#             for i in range(len(scan_bias)):
#                 if (i>0):
#                     if (scan_bias[i-1]>0.1) and (scan_bias[i]<0.05):
#                         scan_bias[i] = scan_bias[i-1]
#                         continue
#                 TG.SetPoint(TG.GetN(), scan_bias[i], scan_darkcounts[i])
#                   
#             TF = ROOT.TF1("biasfit","expo+[2]", 0, 10)
#             TF.FixParameter(2,numpy.mean(scan_darkcounts[0:4]))
#             TG.Fit(TF)
#             TF.SetParLimits(2,0,0.1)
#             TG.Fit(TF)
#               
#             offset = TF.GetParameter(2)
#             DarkCounts = [TF.Eval(Bias) - offset for Bias in Biases]
#             ChannelWeights = [DarkWeightFunc(c, FuncArgs) for c in DarkCounts]
        
            # Add the determined channel weights to the module:
            Module["ChannelWeights"].append(ChannelWeights)
                
        # Combine the ModuleWeights - but with some outlier rejection:
        for w in range(len(ModuleWeights)):
            weights = [Module["ChannelWeights"][i][w] for i in range(len(Module["ChannelWeights"]))]
            weights.sort()
            
            weights_chopped = weights[10:-10]
            mean = numpy.mean(weights_chopped)
            stddev = numpy.std(weights_chopped)
            
            weights_filtered = [v for v in weights if (math.fabs(v-mean) < 2.5*stddev)]
            ModuleWeights[w] = numpy.mean(weights_filtered)
                
        # The lowest weight is the optimum module configuration:
        Module["ModuleWeights"] = ModuleWeights
        Module["Biases"] = Biases
        OptimumBiasID = numpy.argmin(ModuleWeights)
        OptimumBias = Biases[OptimumBiasID]
        print ("Optimum Bias: %f"%OptimumBias)
        Module["OptimumBias"] = OptimumBias
        
           

####################################################################
def LinearWeight(darkcounts, FuncArgs):
    target = FuncArgs["target"]
    return math.fabs(target-darkcounts)

def LinerAsyWeight(darkcounts, FuncArgs):
    target = FuncArgs["target"]
    if (target>darkcounts):
        return math.fabs(target-darkcounts)
    else:
        return 2.0*math.fabs(target+darkcounts)


####################################################################
def GenerateModuleData (ChannelID):
        
    ModuleID = ChannelID/CHAN_PER_MOD
    Board = ModuleID/MOD_PER_BOARD
    Module = ModuleID%MOD_PER_BOARD
        
    return {"ModuleID":ModuleID, "Module":Module, "Board":Board}

####################################################################
def GetChannelID(Channel, Module, Board=None):
    if Board is None:
        return Channel + Module*CHAN_PER_MOD
    else:
        return Channel + (Module+Board*MOD_PER_BOARD) * CHAN_PER_MOD

####################################################################
def GetMatchedChannel(campaign, ChannelID, bias, LEDAvail):
    """
    Scan through a data campaign, to find a mactching channel ID
    configuration. LEDState is a bool, indicating if the LED is on or not...
    """

    for dataset in campaign:
        
        channel = dataset["channels"][ChannelID]
        if (math.fabs(channel["bias"] - bias) <1E-6):
            #Compare LED State:
            if (LEDAvail == (False if channel["LEDIntensity"] < 1E-6 else True)):
                return channel         
    return None

####################################################################
def GetBiasScan(campaign, ChannelID, ChannelKey ,LEDAvail=None):
    """
    Return a zipped list, containing both a bias points and
    the value of the "channel" key entry in the channel dictionary
    only for LEDAvail...
    """
    
    bias_points = []
    key_points = []

    for dataset in campaign:
        
        channel = dataset["channels"][ChannelID]
        
        # Append data only if matching LED State:
        if (LEDAvail is None) or (LEDAvail == (channel["LEDIntensity"] > 1E-6)):
            bias_points.append(channel["bias"])
            key_points.append(channel[ChannelKey])
            
    # Reorder the list:
    bias_points, key_points = (list(t) for t in zip(*sorted(zip(bias_points, key_points))))
    
    #Return the sorted list:
    return bias_points, key_points

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