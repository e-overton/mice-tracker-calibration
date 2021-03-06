Tracker Calibration Tools
=========================

This toolkit should prove the nesseseary tools and workflow to allow the
detectors to be calibrated. Please follow the instructions to operate
the calibration functionality.

Version Control via git.


Requirements:
pyROOT.



Workflow:
---------

**BIAS CALIBRATION:**

1) Use the automatic bias data collection script located
   in the base folder/scripts/RunCalibration.py
   This script will take a few hours to run and collect a
   bias sweep for cryostats in either the upstream or downstream
   detectors.
   

2) Use the BiasCalibratorUI to find the optimum biases for the
   VLPC modules. Run this script with the argument pointed at the
   output directory from the automated data collection script.
   
   Scan over the calibration values to ensure the values which are
   found are correct. Note you will need to record these values by
   hand.
   
   From this process you should generate a:
   > Tracker XML Files for bias setting in the C&M Software
   
   Plus for the ADC calibration you will need:
   > Biases.txt - List of each modules bias setting.
   > BadFE.txt - List of bad front end channels (do not make normal peaks).
   Note these files are made by hand.

**ADC CALIBRATION FROM SCRATCH:**

1) Make a new working folder like 2015-01a, using the
   config there as a template. Copy the Biases.txt and BadFE.txt
   files into the folder for using. Modify config.json as needed.
   
   Then launch ADCCalibrator, with first argument as the fodler
   created for calibrations. This will try to automatically fit all
   the data.
   
   Note that using the external LED data has been cut out, 
   however it can be re-enabled by un-commenting lines in the ADCCalibrator 
   script.
   
   
2) Validate the data by looking over it. This can be completed using
   the ADCCalibratorUI script, which makes a nice GUI. Hand edit values which
   are incorrect using the "Edit Channel" Button.
   
   Note there is a fast way to correct lots of channels. Perform a
   manual fit with the ROOT "fit pannel", use the custom fit function
   as "gaus + gaus(3)". The left gaus should be the pedestal, the second
   gaus should be the 1.pe peak. If the fit looks good, press "Update from fit"
   to set the gain/pedestal from the fit.
   On the next channel press "Repeat last fit" to use the previous fit
   paramters as a starting point in this fit. Again, if the fit looks
   satisfactory, then press "Upate from fit" to save the parameters to
   the channel.
   
3) Finally run ADCCalibratorPostProcessor with argument as the folder
   to run a final analysis on the data and generate the output files for
   processing.
   This will also export online monitoring plots...
   
**ADC CALIBRATION FROM UPDATE:**

1) Make a new working folder like 2015-01a, using the
   config there as a template. Copy the Biases.txt and BadFE.txt
   files into the folder for using. Modify config.json as needed,
   Note that InternalLED should point at the new internal LED data.
   
2) Launch ADCCalibrationUpdate with the arguments:
   <old calibration folder> <new calibration folder>
   This will use the old calibration to generate a new calibration.
   
   eg: python ADCCalibrationUpdate 2015-01-a 20150912
   
3) Validate the calibration using the ADCCalibratiorUI script,
   giving the argument as the new calibration folder.
   
   eg: python ADCCalibratiorUI 20150912
   
4) Finally run ADCCalibratorPostProcessor with argument as the folder
   to run a final analysis on the data and generate the output files for
   processing.
   This will also export online monitoring plots...  
   
   
  
