#!/usr/bin/env python
"""
Quick Script to swap round banks in the Calibration file

"""

import json

# Load the existing calibration file:
input_filename="scifi_calibration_2015-06-18.txt"
output_filename="scifi_calibration_2015-07-28.txt"

#JSON Reader:
with open(input_filename, "r") as f:
    calibration = json.load(f)
with open(input_filename, "r") as f:
    calibration_old = json.load(f)
    
# Swap Directives: - array of [old,new] calibrations:
swap_banks = [[32,36],[33,37],[34,38],[35,39]]

# Make the opposite swaps happen:
opposite_swaps = [[s[1],s[0]] for s in swap_banks]
swap_banks.extend(opposite_swaps)

# Perform swaps
for c in calibration:
    this_bank = c["bank"]
    for s in swap_banks:
        if s[0] == this_bank:
            c["bank"] = s[1]
            
# Check the swaps:
for c in calibration:
    for o in calibration_old:
        if o["bank"] == c["bank"] and o["channel"] == c["channel"]:
            if  abs(o["adc_pedestal"] - c["adc_pedestal"]) > 0.001 and\
                abs(o["adc_gain"] - c["adc_gain"]) > 0.001:
                
                print "Channel changed %i, %i"%(o["bank"],o["channel"])
            
with open (output_filename, "w") as f:
    json.dump(calibration, f)

# Thats all folks.
    