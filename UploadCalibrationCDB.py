#!/usr/bin/env python
""" 
Upload a tracker calibration to the CDB, based on the script for a TOF calibration.
This script must, and can, be run only from a micenet computer
"""

Upload=True
_CDB_W_SERVER = 'http://172.16.246.25:8080' # cdb write server
#_CDB_R_SERVER = 'http://cdb.mice.rl.ac.uk'
#_CDB_W_SERVER = 'http://cdb.mice.rl.ac.uk:8080'
_CDB_R_SERVER = 'http://cdb.mice.rl.ac.uk'

import os
import sys
import json
import time
import ADCCalibrator
import FECalibrationUtils

if Upload:
    #from cdb import CalibrationSuperMouse
    import cdb

import cdb

def UploadCDB(calibpath, timestamp=None):
    """
    This function performs the upload of tracker calibration data
    given a dataset.
    """
    global Upload
    
    #Load Calibration
    Calibration = ADCCalibrator.ADCCalibration()
    config = FECalibrationUtils.LoadCalibrationConfig(calibpath)
    Calibration.Load(config)
    #config = Calibration.config
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
    
    ################################################################################
    # Do the upload of scifi_calibration:
    filename = os.path.join(calibpath, config["MAUSCalibration"])
    try:
        _CALIFILE = open(filename,"r")
        _CALI = _CALIFILE.read()
        UploadCalibration = Upload
    except:
        print "Unable to open calibration file."
        UploadCalibration = False
    
    # Specify and print upload parameters:
    _TIMESTAMP = timestamp
    _TYPE_CA = 'trackers'
    _DEVICE = 'TRACKERS'
    
    if UploadCalibration:
        print "Going to perform the following upload:"
    else:
        print "Not going to perform the following upload:"
    print "CA:         ", _TYPE_CA
    print "DEVICE:     ", _DEVICE
    print "Valid from: ", _TIMESTAMP
    print "File:       ", filename
    
    # Logic to perform uploads if in the control room if CDB is available.
    if UploadCalibration:
        try:
            _CALI_SM = cdb.CalibrationSuperMouse(_CDB_W_SERVER)
            print _CALI_SM.set_detector(_DEVICE, _TYPE_CA, _TIMESTAMP, _CALI)
        except:
            print "Errors in upload"
            UploadCalibrationOK = False
        else:
            print "Upload completed successfully"
            UploadCalibrationOK = True
    else:
        UploadCalibrationOK = False
    
    try:
        _CALIFILE.close()
    except:
        pass

    ###################################################################################
    # Do the upload of scifi_bad_channels:
    badchfilename = os.path.join(calibpath, config["MAUSBadChannels"])
    try:
        _BADFILE = open(badchfilename,"r")
        _BADCH = _BADFILE.read()
        UploadBadCh = Upload
    except:
        print "Unable to open bad channels file."
        UploadBadCh = False
    
    # Specify and print upload parameters:
    _TYPE_BC = 'bad_chan'
    
    if UploadBadCh:
        print "Going to perform the following upload:"
    else:
        print "Not going to perform the following upload:"
    print "CA:         ", _TYPE_BC
    print "DEVICE:     ", _DEVICE
    print "Valid from: ", _TIMESTAMP
    print "File:       ", badchfilename

    if UploadBadCh:
        try:
            _CALI_SM = cdb.CalibrationSuperMouse(_CDB_W_SERVER)
            print _CALI_SM.set_detector(_DEVICE, _TYPE_BC, _TIMESTAMP, _BADCH)
        except:
            print "Errors in upload"
            UploadBadChOK = False
        else:
            print "Upload completed successfully"
            UploadBadChOK = True
    else:
        UploadBadChOK = False

    ##################################################################################
    # Determine IDs of uploads:
    _CALI_ID = 0
    _BAD_ID = 0

    #UploadCalibrationOK, UploadBadChOK = True, True

    if UploadCalibrationOK or UploadBadChOK:
        calibs_read = cdb.Calibration(_CDB_R_SERVER)
        try:
            _TS_Start = time.strftime("%Y-%m-%d %H:%M:%S.0",unixtime-10000)
            _TS_End = time.strftime("%Y-%m-%d %H:%M:%S.0",unixtime+10000)
        except:
            _TS_Start = "2015-01-01 00:00:00.0"
            _TS_End = "2030-01-01 00:00:00.0"

        _IDS = calibs_read.get_ids(_TS_Start, _TS_End)

        for _id in sorted(_IDS):
            c =_IDS.get(_id)
            if c['device'] == _DEVICE:
                try:
                    if UploadCalibrationOK and c['calibration_type'] == _TYPE_CA:
                        _CALI_ID = int(c['id']) if int(c['id']) >_CALI_ID  else _CALI_ID
                    if UploadBadChOK and c['calibration_type'] == _TYPE_BC:
                        _BAD_ID  = int(c['id']) if int(c['id']) > _BAD_ID else _BAD_ID
                except:
                    print "Error reading calibration ID from cdb"
                    continue

    if _CALI_ID > 0:
        print "Newest Calibration ID: %i"%_CALI_ID
    else:
        print "Unable to find newest calibration ID - set to zero"

    if _BAD_ID > 0:
        print "Newest Bad Channels ID: %i"%_BAD_ID
    else:
        print "Unable to find newest calibration ID - set to zero"
            

    ##########################################################################################
    # Update the status tracking infomation with the infomation that
    # this was uploaded.
    if UploadCalibrationOK or UploadBadChOK:
        Calibration.status = FECalibrationUtils.LoadCalibrationStatus(config["path"])
        Calibration.status["CDBUpload"] = True
        if _CALI_ID > 0:
            Calibration.status["MAUSCalibID"] = _CALI_ID
        if _BAD_ID > 0:
            Calibration.status["MAUSBadChID"] = _BAD_ID
        FECalibrationUtils.SaveCalibrationStatus(Calibration.status, config["path"])
        
    print "Script Completed."


if __name__ == "__main__" :
    
    print "Script to upload tracker calibration data to CDB"
    print "requires argument pointing to tracker data"
    
    calibpath = sys.argv[1]
    status = UploadCDB(calibpath=calibpath)
