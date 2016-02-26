#!/usr/bin/env python
module_description=\
"""
Tool to generate a summary of a calibration and store the results
in a summary html file.

Areguments are : rootdir, path to calibration root directory.
"""

import xml.dom.minidom as dom
import FECalibrationUtils
import ADCCalibrator
import os
import sys

colours = {"None":"black", "OK":"green", "Warn":"orange", "BAD":"red"}
statuslist = ["InternalLED","Quality","Checked by",
                  "In CDB", "Calib ID", "BadCh ID"]

def AddTextNode(doc, node, name, text, colour=None, link=None):
    """
    Make adding text nodes eaisier
    """
    
    assert isinstance(doc, dom.Document) 
    e = doc.createElement(name)
    t = doc.createTextNode(text)
    
    if colour!=None:
        f = doc.createElement("font")
        f.setAttribute("color", colour)
        f.appendChild(t)
        t=f

    if link != None:
        a = doc.createElement("a")
        a.setAttribute("href", link)
        a.appendChild(t)
        t = a    
    
        
    e.appendChild(t)
    node.appendChild(e)
    
def AddImage(doc, node, path, link=None):
    """
    Make adding text nodes eaisier
    """
    assert isinstance(doc, dom.Document) 
    i = doc.createElement("img")
    i.setAttribute("src", path)
    if link != None:
        a = doc.createElement("a")
        a.setAttribute("href", link)
        a.appendChild(i)
        i = a
    node.appendChild(i)
    
def GenerateStatusInfo(Calibration):
    """
    Generates a more detailed status set, for humans!
    """
    output = {}
    
    # Check Internal LED:
    try:
        if Calibration.status["InternalLED"] is True:
            output["InternalLED"] = ["Found", "OK"]
        else:
            output["InternalLED"] = ["NotFound", "BAD"]
    except:
        output["InternalLED"] = ["NotFound", "BAD"]
        
    # Check the "Checked" Flag
    try:
        if Calibration.status["Checked"] is True:
            if "Quality" in Calibration.status and \
            Calibration.status["Quality"] is True:
                output["Quality"] = ["Good", "OK"]
            else:
                output["Quality"] = ["Bad", "Bad"]
        else:
            output["Quality"] = ["Unchecked", "Warn"]
    except:
        output["Quality"] = ["Unchecked", "Warn"]
        
    # Check the CheckedBy flag:
    try:
        output["Checked by"] = [Calibration.status["CheckedBy"], "None"]
    except:
        output["Checked by"] = ["Unknown", "None"]
        
    # Check if uploaded to CDB:
    try:
        if Calibration.status["Uploaded"] is True:
            output["In CDB"] = ["Yes", "OK"]
            if "MAUSCalibID" in Calibration.status:
                output["Calib ID"] = ["%i"%Calibration.status["MAUSCalibID"], "None"]
            else:
                output["Calib ID"] = ["-", "None"]
            if "MAUSBadChID" in Calibration.status:
                output["BadCh ID"] = ["%i"%Calibration.status["MAUSBadChID"], "None"]
            else:
                output["BadCh ID"] = ["-", "None"]
        else:
            output["In CDB"] = ["No", "None"]
            output["Calib ID"] = ["-", "None"]
            output["BadCh ID"] = ["-", "None"]
    except:
        output["In CDB"] = ["No", "None"]
        output["Calib ID"] = ["-", "None"]
        output["BadCh ID"] = ["-", "None"]    
    
    return output
    

    

def CalibrationSummary (path):
    """
    Generate the HTML document for a calibration.
    """
    # Generate XHTML nodes:
    doc = dom.parseString('<html xmlns="http://www.w3.org/1999/xhtml"><head></head><body/></html>')
    dt = dom.getDOMImplementation('').createDocumentType('html', '-//W3C//DTD XHTML 1.0 Strict//EN', 'http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd')
    doc.insertBefore(dt, doc.documentElement)
    
    # Gead header and body
    head = doc.getElementsByTagName('head')[0]
    body = doc.getElementsByTagName('body')[0]
    
    # Load the calibration:
    if path.rindex('/') == len(path) - 1:
        path = path[:-1]
    calibname = path[path.rindex('/')+1:]
    # Write the title of the document:
    AddTextNode(doc, head, "title", "Calibration Summary: %s" %calibname)
    AddTextNode(doc, body, "h1", "Calibration Summary: %s" %calibname)
    
    try:
        Calibration = ADCCalibrator.ADCCalibration()
        Calibconfig = FECalibrationUtils.LoadCalibrationConfig(path)
        Calibration.Load(Calibconfig)
    except:
        AddTextNode(doc, body, "h2", "Failed to load: %s" %calibname, colour="red")
        
    # Generate a status table ####################################################:
    AddTextNode(doc, body, "h2", "Calibration Status", "blue")
    tablestatus = doc.createElement("table")
    
    """
    status_list = ["InternalLED", "Checked", "CheckedBy", 
                   "Quality", "PostProcessed", "Uploaded"]
    
    try:
        for status in status_list:
            tr = doc.createElement("tr")
            AddTextNode(doc, tr, "th", status)
            if status in Calibration.status:
                if Calibration.status[status] is True:
                    AddTextNode(doc, tr, "th", "Done", colour="green")
                elif Calibration.status[status] is False:
                    AddTextNode(doc, tr, "th", "NotDone", colour="orange")
                else:
                    try:
                        AddTextNode(doc, tr, "th", Calibration.status[status])
                    except:
                        AddTextNode(doc, tr, "th", "ParserError", colour="orange")
            else:
                AddTextNode(doc, tr, "th", "Unknown", colour="orange")
            tablestatus.appendChild(tr)
        body.appendChild(tablestatus)
    except:
        AddTextNode(doc, body, "p", "Error generating status table", colour="red")
    """
    statusinfo = GenerateStatusInfo(Calibration)    
    for status in statuslist:
        tr = doc.createElement("tr")
        AddTextNode(doc, tr, "th", status)
        try:
            thisinfo = statusinfo[status]
            AddTextNode(doc, tr, "th", thisinfo[0],colours[thisinfo[1]])
        except:
            AddTextNode(doc, tr, "th", "unknown","orange")
        tablestatus.appendChild(tr)
        
    body.appendChild(tablestatus)
    
    
    # Generate Plots ####################################################:
    if os.path.isfile(os.path.join(path,"Noise_US.png")):
        
        #AddTextNode(doc, body, "h2", "Calibration Plots")
        AddTextNode(doc, body, "h3", "Upstream Noise Rates")
        AddImage(doc, body, "Noise_US.png", link="Noise_US.pdf")
        AddTextNode(doc, body, "br", "")
        AddTextNode(doc, body, "p", "Figure 1: Summary of the 2.p.e noise rates in the upstream"
                                    " detector stations. Vertical axis is probability/trigger")
        AddTextNode(doc, body, "h3", "Downstream Noise Rates")
        AddImage(doc, body, "Noise_DS.png", link="Noise_DS.pdf")
        AddTextNode(doc, body, "br", "")
        AddTextNode(doc, body, "p", "Figure 2: Summary of the 2.p.e noise rates in the downstream"
                                    " detector stations. Vertical axis is probability/trigger")
        AddTextNode(doc, body, "h3", "Upstream LED Light Yield")
        AddImage(doc, body, "LEDYield_US.png", link="LEDYield_US.pdf")
        AddTextNode(doc, body, "br", "")
        AddTextNode(doc, body, "p", "Figure 3: Summary of the light yield from the internal LED"
                                    "system in the upstream stations. Vertical axis is in"
                                    "photo-electrons.")
        AddTextNode(doc, body, "h3", "Downstream LED Light Yield")
        AddImage(doc, body, "LEDYield_DS.png", link="LEDYield_DS.pdf")
        AddTextNode(doc, body, "br", "")
        AddTextNode(doc, body, "p", "Figure 4: Summary of the light yield from the internal LED"
                                    "system in the downstream stations. Vertical axis is in"
                                    "photo-electrons.")
        
    # Consistency Checks ##################################################:
    if os.path.isfile(os.path.join(path,"StabilityCheck.png")):
        # 
        AddTextNode(doc, body, "h3", "Stability Check")
        AddImage(doc, body, "StabilityCheck.png", link="StabilityCheck.pdf")
        AddTextNode(doc, body, "br", "")
        AddTextNode(doc, body, "p", "Figure 5: Summary of the changes between this and the reference"
                                    " calibration")
        
    AddTextNode(doc, body, "h3", "Bad Channel Summary")
    tablebad = doc.createElement("table")
    tr = doc.createElement("tr")
    AddTextNode(doc, tr, "th", "ChannelUID")
    AddTextNode(doc, tr, "th", "Tracker")
    AddTextNode(doc, tr, "th", "Station")
    AddTextNode(doc, tr, "th", "Plane")
    AddTextNode(doc, tr, "th", "PlaneChannel")
    AddTextNode(doc, tr, "th", "Comment")
    tablebad.appendChild(tr)
    
    # Consistency Checks ##################################################:
    for channel in Calibration.FEChannels:
        if channel.ADC_Pedestal < 0.1 and channel.InTracker:
            tr = doc.createElement("tr")
            AddTextNode(doc, tr, "th", str(channel.ChannelUID))
            AddTextNode(doc, tr, "th", str(channel.Tracker))
            AddTextNode(doc, tr, "th", str(channel.Station))
            AddTextNode(doc, tr, "th", str(channel.Plane))
            AddTextNode(doc, tr, "th", str(channel.PlaneChannel))
            
            txt_issues = doc.createElement("th")
            for issue in channel.Issues:
                AddTextNode(doc, txt_issues, "p", str(issue["Comment"]))
            tr.appendChild(txt_issues)
            
            tablebad.appendChild(tr)
    body.appendChild(tablebad)
    
    # save:
    with open(os.path.join(path, "status.xhtml"), "w") as f:
        doc.writexml(f)
    #print doc.toprettyxml()
    
    return Calibration


def GenerateIndexSummart(rootpath):
    """
    This generates an index.xml page 
    
    Path to folder of calibrations, which need an index
    generating.
    """
    
    # Create xhtml nodes..
    doc = dom.parseString('<html xmlns="http://www.w3.org/1999/xhtml"><head></head><body/></html>')
    dt = dom.getDOMImplementation('').createDocumentType('html', '-//W3C//DTD XHTML 1.0 Strict//EN', 'http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd')
    doc.insertBefore(dt, doc.documentElement)
    
    # Gead header and body
    head = doc.getElementsByTagName('head')[0]
    body = doc.getElementsByTagName('body')[0]
    AddTextNode(doc, head, "title", "Calibration Index")
    AddTextNode(doc, body, "h1", "Calibration Index")
    
    # Status fields to check:
    #status_list = ["InternalLED", "Checked", "CheckedBy", 
    #               "Quality", "PostProcessed", "Uploaded"]
    
    # Generate master table:
    mastertable = doc.createElement("table")
    tr = doc.createElement("tr")
    AddTextNode(doc, tr, "th", "Calibration")
    for status in statuslist:
        AddTextNode(doc, tr, "th", status)
    mastertable.appendChild(tr)
   
    # Generate Folderlist - sort by name
    folder_list = [o for o in os.listdir(rootpath) if os.path.isdir(os.path.join(rootpath,o))]
    for folder in sorted(folder_list):
        
        # Generate new line in table:
        tr = doc.createElement("tr") 
        AddTextNode(doc, tr, "th", folder, link="%s/status.xhtml"%folder)
        
        # Process folder - get Calibration - Make status table
        try:
            Calibration = CalibrationSummary(os.path.join(rootpath,folder))
        except:
            AddTextNode(doc, tr, "th", "Error Processing", colour="red")
        else:
            statusinfo = GenerateStatusInfo(Calibration)    
            for status in statuslist:
                try:
                    thisinfo = statusinfo[status]
                    AddTextNode(doc, tr, "th", thisinfo[0],colours[thisinfo[1]])
                except:
                    AddTextNode(doc, tr, "th", "unknown","orange")
            
            
            """        
            # Process status string:
            for status in status_list:
                if status in Calibration.status:
                    if Calibration.status[status] is True:
                        AddTextNode(doc, tr, "th", "Done", colour="green")
                    elif Calibration.status[status] is False:
                        AddTextNode(doc, tr, "th", "NotDone", colour="orange")
                    else:
                        try:
                            AddTextNode(doc, tr, "th", Calibration.status[status])
                        except:
                            AddTextNode(doc, tr, "th", "ParserError", colour="orange")
                else:
                    AddTextNode(doc, tr, "th", "Unknown", colour="orange")
            """    
        # Append to table
        mastertable.appendChild(tr)
    
    body.appendChild(mastertable)
    with open(os.path.join(rootpath, "summary.xhtml"), "w") as f:
        doc.writexml(f)
    #print doc.toprettyxml() 
            


    
if __name__ == "__main__":
    
    try:
        print ("")
        rootpath = sys.argv[1]
        print ("loading root directory: %s"%rootpath)
        print ("")
    
    except:
        print "Failed to load root directory argument."
        raise
    
    GenerateIndexSummart(rootpath)
    