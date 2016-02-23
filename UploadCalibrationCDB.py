#!/usr/bin/env python
""" 
Upload a tracker calibration to the CDB, based on the script for a TOF calibration.
This script must, and can, be run only from a micenet computer
"""

Upload=False
_CDB_W_SERVER = 'http://172.16.246.25:8080' # cdb write server

import os
import sys
import json
import time
import ADCCalibrator
import FECalibrationUtils

if Upload:
    from cdb import CalibrationSuperMouse

def UploadCDB(calibpath, timestamp=None):
    """
    This function performs the upload of tracker calibration data
    given a dataset.
    """
    global Upload
    
    #Load Calibration
    Calibration = ADCCalibrator.ADCCalibration()
    Calibration.Load(calibpath)
    config = Calibration.config
    #config = json.load(open(os.path.join(calibpath,"config.json")))
    
    
    # Check the timestamp and load timestamp from orignal data
    # if it does not exist:
    if timestamp is None: 
        try:
            # Load a start date from the config (if it is present)
            if "StartDate" in Calibration.config:
                unixtime = time.gmtime(config["StartDate"])
            
            # Load from the pedestal calibration data.
            elif "pedcalib" in config["InternalLED"][0]:
                DataPath = os.path.expandvars(config["DataPath"])
                runconfig = json.load(open(os.path.join(DataPath,
                                                        config["InternalLED"][0]["pedcalib"],
                                                        "runconfig.json")))
                unixtime = time.gmtime(runconfig[0]["unixtime:"])
        except:
            print "Unable to load timestamp from config"
            Upload = False
            raise
        else:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S.0",unixtime)
            print "Using timestamp: %s"%timestamp
            
    # Now specify filename:
    filename = os.path.join(calibpath, config["MAUSCalibration"])
    try:
        _CALIFILE = open(filename,"r")
        _CALI = _CALIFILE.read()
    except:
        print "Unable to open calibration file."
        Upload = False
    
    # Setup to do upload:
    _TIMESTAMP = timestamp
    _TYPE_CA = 'trackers'
    _DEVICE = 'Trackers'
    
    if Upload:
        print "Going to perform the following upload:"
    else:
        print "Not going to perform the following upload:"
    
    print "CA:         ", _TYPE_CA
    print "DEVICE:     ", _DEVICE
    print "Valid from: ", _TIMESTAMP
    print "File:       ", filename
    
    # Logic to perform uploads if in the control room if CDB is available.
    if Upload:
        try:
            _CALI_SM = CalibrationSuperMouse(_CDB_W_SERVER)
            print _CALI_SM.set_detector(_DEVICE, _TYPE_CA, _TIMESTAMP, _CALI)
        except:
            print "Errors in upload"
            UploadOK = False
        else:
            print "Upload completed successfully"
            UploadOK = True
    
    try:
        _CALIFILE.close()
    except:
        pass
    
    # Update the status tracking infomation with the infomation that
    # this was uploaded.
    if UploadOK:
        Calibration.status = FECalibrationUtils.LoadCalibrationStatus(config["path"])
        Calibration.status["CDBUpload"] = True
        FECalibrationUtils.SaveCalibrationStatus(Calibration.status, config["path"])
        
    print "Script Completed."


if __name__ == "__main__" :
    
    print "Script to upload tracker calibration data to CDB"
    print "requires argument pointing to tracker data"
    
    calibpath = sys.argv[1]
    status = UploadCDB(calibpath=calibpath)
