'Dispatch()'#!/usr/bin/env python

module_description = \
"""
 === Bias Calibrator GUI Script =====================================

    Creates a GUI to make checking a calibration much eaisier..
    
"""


import os, sys, ROOT
import multiprocessing
import BiasCalibrator
import LightYieldEstimator
import numpy
import math


class BiasUIMainFrame( ROOT.TGMainFrame ):
    
    # Data Objects:
    campaign = None
    modules = None
    
    # Main Menu Items lookup table:
    class MainMenuItems:
        OPEN = 1
        SAVE = 2
        EXIT = 3
        
    #MainMenuItems = MainMenuItems
    
    # Main INIT function:
    def __init__( self, parent, width, height ):
        ROOT.TGMainFrame.__init__( self, parent, width, height)
        
        ##############################################################################
        # Menu Consruction
        ##############################################################################
        
        # Create menubar and popup menus. The hint objects are used to place
        # and group the different menu widgets with respect to eachother.
        #self.fMenuDock = ROOT.TGDockableFrame(self);
        #self.fMenuDock = ROOT.TGMenuBar(self,100,20,ROOT.kHorizontalFrame)
        
        #self.fMenuDock.SetWindowName("GuiTest Menu")

        # Menu Item:
        self.fMenuBarLayout = ROOT.TGLayoutHints(ROOT.kLHintsTop | ROOT.kLHintsExpandX)
        self.fMenuBarItemLayout = ROOT.TGLayoutHints(ROOT.kLHintsTop | ROOT.kLHintsLeft, 0, 4, 0, 0)
        self.fMenuBarHelpLayout = ROOT.TGLayoutHints(ROOT.kLHintsTop | ROOT.kLHintsRight)
        self.fMenuBar = ROOT.TGMenuBar(self, 1, 1, ROOT.kHorizontalFrame)
        # File:
        self.fMenuFile = ROOT.TGPopupMenu(ROOT.gClient.GetRoot())
        self.fMenuFile.AddEntry("&Open...", self.MainMenuItems.OPEN)
        self.fMenuFile.AddEntry("&Save", self.MainMenuItems.OPEN)
        self.fMenuBar.AddPopup("&File", self.fMenuFile, self.fMenuBarItemLayout)
        
        #    fMenuFile->AddEntry("S&ave as...", M_FILE_SAVEAS);
        #    fMenuFile->AddEntry("&Close", -1);
        #    fMenuFile->AddSeparator();
        #    fMenuFile->AddEntry("&Print", M_FILE_PRINT);
        #    fMenuFile->AddEntry("P&rint setup...", M_FILE_PRINTSETUP);
        #    fMenuFile->AddSeparator();
        #    fMenuFile->AddEntry("E&xit", M_FILE_EXIT);
        
        # Append
        self.AddFrame(self.fMenuBar,  ROOT.TGLayoutHints(ROOT.kLHintsExpandX, 0, 0, 1, 0))
        #self.AddFrame(self.fMenuDock, ROOT.TGLayoutHints(ROOT.kLHintsExpandX, 0, 0, 1, 0))
              
        ##############################################################################
        # Main GUI Generation:
        ##############################################################################
        
        self.vMainFrame = ROOT.TGHorizontalFrame(self, 120, 200)
        
        ##############################################################################
        # Sidebar:
        ############################################################################## 
        
        self.fSideBar = ROOT.TGVerticalFrame( self.vMainFrame, 220, 300)
        
        ##############################################################################
        # Pedstaool Data Selector:
        ##############################################################################
        self.fPedDataSelector = ROOT.TGGroupFrame(self.fSideBar,"Pedastool Selector")
        
        #Dispatchers:
        self._pedPlotDispatch = ROOT.TPyDispatcher(self.PlotPedHist)
        
        # Selector:
        self.sPedList = ROOT.TGListBox(self.fPedDataSelector, 90)
        self.sPedList.Resize(200, 100)
        self.fPedDataSelector.AddFrame( self.sPedList, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        
        # Plotter:
        self.bPedDraw = ROOT.TGTextButton(self.fPedDataSelector,"Plot Peds")
        self.bPedDraw.Connect("Clicked()", "TPyDispatcher", self._pedPlotDispatch, "Dispatch()" )
        self.fPedDataSelector.AddFrame( self.bPedDraw, ROOT.TGLayoutHints(ROOT.kLHintsRight))

        
        self.fSideBar.AddFrame(self.fPedDataSelector, ROOT.TGLayoutHints(ROOT.kLHintsExpandX | ROOT.kLHintsTop,2,2,2,2))
        
        ##############################################################################
        # Channel selector input:
        ##############################################################################
        self.fChannelSelector = ROOT.TGGroupFrame(self.fSideBar,"Channel Selector")
        
        # Dispatchers:
        self._moduleChanUpdate = ROOT.TPyDispatcher(self.UpdateModuleCounter)
        self._uniqueChanUpdate = ROOT.TPyDispatcher(self.UpdateUniqueCounter)
        
        self._plotChannelHist = ROOT.TPyDispatcher(self.PlotChannelHist)
        self._plotChannelCounts = ROOT.TPyDispatcher(self.PlotChannelDarkCounts)
        self._plotChannelLightYield = ROOT.TPyDispatcher(self.PlotChannelLightYield)
        self._plotChannelDCLightYield = ROOT.TPyDispatcher(self.PlotChannelDarkCountsLightYield)
        self._plotChannelTest = ROOT.TPyDispatcher(self.PlotChannelDCDiff)
        
        self.fBoard = ROOT.TGHorizontalFrame( self.fChannelSelector, 30, 200)
        self.lBoard = ROOT.TGLabel( self.fBoard, "Board:  " )
        self.fBoard.AddFrame( self.lBoard, ROOT.TGLayoutHints(ROOT.kLHintsLeft))
        self.sBoard = ROOT.TGNumberEntry(self.fBoard, 0, 8, -1,\
                                         ROOT.TGNumberFormat.kNESInteger,\
                                         ROOT.TGNumberFormat.kNEANonNegative,\
                                         ROOT.TGNumberFormat.kNELLimitMinMax,\
                                         0, 15 )
        self.sBoard.Connect("ValueSet(Long_t)", "TPyDispatcher", self._moduleChanUpdate, "Dispatch()" )
        self.sBoard.GetNumberEntry().Connect("ReturnPressed()", "TPyDispatcher", self._moduleChanUpdate, "Dispatch()" )
        
        self.fBoard.AddFrame( self.sBoard, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        self.fChannelSelector.AddFrame( self.fBoard, ROOT.TGLayoutHints(ROOT.kLHintsRight | ROOT.kLHintsTop | ROOT.kLHintsCenterY,6,6,6,6))
        
        self.fModule = ROOT.TGHorizontalFrame( self.fChannelSelector, 30, 200)
        self.lModule = ROOT.TGLabel( self.fModule, "Module:  " )
        self.fModule.AddFrame( self.lModule, ROOT.TGLayoutHints(ROOT.kLHintsLeft))
        self.sModule = ROOT.TGNumberEntry(self.fModule, 0, 8,-1,\
                                          ROOT.TGNumberFormat.kNESInteger,\
                                          ROOT.TGNumberFormat.kNEANonNegative,\
                                          ROOT.TGNumberFormat.kNELLimitMinMax,\
                                          0, 7 )
        self.sModule.Connect("ValueSet(Long_t)", "TPyDispatcher", self._moduleChanUpdate, "Dispatch()" )
        self.sModule.GetNumberEntry().Connect("ReturnPressed()", "TPyDispatcher", self._moduleChanUpdate, "Dispatch()" )
        self.fModule.AddFrame( self.sModule, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        self.fChannelSelector.AddFrame( self.fModule, ROOT.TGLayoutHints(ROOT.kLHintsRight | ROOT.kLHintsTop | ROOT.kLHintsCenterY,6,6,6,6))
        
        self.fModuleChannel = ROOT.TGHorizontalFrame( self.fChannelSelector, 30, 200)
        self.lModuleChannel = ROOT.TGLabel( self.fModuleChannel, "ModuleChannel:  " )
        self.fModuleChannel.AddFrame( self.lModuleChannel, ROOT.TGLayoutHints(ROOT.kLHintsLeft))
        self.sModuleChannel = ROOT.TGNumberEntry(self.fModuleChannel, 0, 8,-1,\
                                                 ROOT.TGNumberFormat.kNESInteger,\
                                                 ROOT.TGNumberFormat.kNEANonNegative,\
                                                 ROOT.TGNumberFormat.kNELLimitMinMax,\
                                                 0, 63 )
        self.sModuleChannel.Connect("ValueSet(Long_t)", "TPyDispatcher", self._moduleChanUpdate, "Dispatch()" )
        self.sModuleChannel.GetNumberEntry().Connect("ReturnPressed()", "TPyDispatcher", self._moduleChanUpdate, "Dispatch()" )
        self.fModuleChannel.AddFrame( self.sModuleChannel, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        self.fChannelSelector.AddFrame( self.fModuleChannel, ROOT.TGLayoutHints(ROOT.kLHintsRight | ROOT.kLHintsTop | ROOT.kLHintsCenterY,6,6,6,6))
        
        self.fUniqueChannel = ROOT.TGHorizontalFrame( self.fChannelSelector, 30, 200)
        self.lUniqueChannel = ROOT.TGLabel( self.fUniqueChannel, "UniqueChannel:  " )
        self.fUniqueChannel.AddFrame( self.lUniqueChannel, ROOT.TGLayoutHints(ROOT.kLHintsLeft))  
        self.sUniqueChannel = ROOT.TGNumberEntry(self.fUniqueChannel, 0, 8,-1,\
                                                 ROOT.TGNumberFormat.kNESInteger,\
                                                 ROOT.TGNumberFormat.kNEANonNegative,\
                                                 ROOT.TGNumberFormat.kNELLimitMinMax,\
                                                 0, 8127 )
        self.sUniqueChannel.Connect("ValueSet(Long_t)", "TPyDispatcher", self._uniqueChanUpdate, "Dispatch()" )
        self.sUniqueChannel.GetNumberEntry().Connect("ReturnPressed()", "TPyDispatcher", self._uniqueChanUpdate, "Dispatch()" )
        self.fUniqueChannel.AddFrame( self.sUniqueChannel, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        self.fChannelSelector.AddFrame( self.fUniqueChannel, ROOT.TGLayoutHints(ROOT.kLHintsRight | ROOT.kLHintsTop | ROOT.kLHintsCenterY,6,6,6,6))
        
        # Buttons:
        self.bChanHDraw = ROOT.TGTextButton(self.fChannelSelector,"Plot Channel")
        self.bChanHDraw.Connect("Clicked()", "TPyDispatcher", self._plotChannelHist, "Dispatch()" )
        self.fChannelSelector.AddFrame( self.bChanHDraw, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        
        self.bChanDCDraw = ROOT.TGTextButton(self.fChannelSelector,"Plot Channel Dark Counts")
        self.bChanDCDraw.Connect("Clicked()", "TPyDispatcher", self._plotChannelCounts, "Dispatch()" )
        self.fChannelSelector.AddFrame( self.bChanDCDraw, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        
        self.bChanLYDraw = ROOT.TGTextButton(self.fChannelSelector,"Plot Channel Light Yield")
        self.bChanLYDraw.Connect("Clicked()", "TPyDispatcher", self._plotChannelLightYield, "Dispatch()" )
        self.fChannelSelector.AddFrame( self.bChanLYDraw, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        
        self.bChanDLYDraw = ROOT.TGTextButton(self.fChannelSelector,"Plot Dark - Light Yield")
        self.bChanDLYDraw.Connect("Clicked()", "TPyDispatcher", self._plotChannelDCLightYield, "Dispatch()" )
        self.fChannelSelector.AddFrame( self.bChanDLYDraw, ROOT.TGLayoutHints(ROOT.kLHintsRight))

        self.bChanTestDraw = ROOT.TGTextButton(self.fChannelSelector,"Test")
        self.bChanTestDraw.Connect("Clicked()", "TPyDispatcher", self._plotChannelTest, "Dispatch()" )
        self.fChannelSelector.AddFrame( self.bChanTestDraw, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        
        self.fSideBar.AddFrame(self.fChannelSelector, ROOT.TGLayoutHints(ROOT.kLHintsExpandX | ROOT.kLHintsTop,2,2,2,2))
        ##############################################################################
        # Module Bias Selector:
        ##############################################################################
        
        self.fModuleBias = ROOT.TGGroupFrame(self.fSideBar,"ModuleBiases")
        
        #Dispachers:
        self._plotModuleOptimumBiasDarkCounts = ROOT.TPyDispatcher(self.PlotModuleOptimumBiasDarkCounts)
        self._plotOptimumBiasDarkCounts = ROOT.TPyDispatcher(self.PlotOptimumBiasDarkCounts)
        
        self.bModHDC = ROOT.TGTextButton(self.fModuleBias,"Plot Module Dark Counts")
        self.bModHDC.Connect("Clicked()", "TPyDispatcher", self._plotModuleOptimumBiasDarkCounts, "Dispatch()" )
        self.fModuleBias.AddFrame( self.bModHDC, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        
        self.bHDC = ROOT.TGTextButton(self.fModuleBias,"Plot Dark Counts")
        self.bHDC.Connect("Clicked()", "TPyDispatcher", self._plotOptimumBiasDarkCounts, "Dispatch()" )
        self.fModuleBias.AddFrame( self.bHDC, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        
        
        
        self.fSideBar.AddFrame(self.fModuleBias, ROOT.TGLayoutHints(ROOT.kLHintsExpandX | ROOT.kLHintsTop,2,2,2,2))
        ##############################################################################
        # Plot Selector:
        ##############################################################################
        



        self.vMainFrame.AddFrame(self.fSideBar, ROOT.TGLayoutHints( ROOT.kLHintsLeft | ROOT.kLHintsExpandY,2,2,2,2));
        
        ##############################################################################
        # Central Canvas:
        ############################################################################## 

        self.Canvas    = ROOT.TRootEmbeddedCanvas( 'Canvas', self.vMainFrame, 400, 400 )      
        self.vMainFrame.AddFrame( self.Canvas, ROOT.TGLayoutHints(ROOT.kLHintsExpandX | ROOT.kLHintsExpandY, 2,0,2,2));
        #self.AddFrame(self.vMainFrame, ROOT.TGLayoutHints(ROOT.kLHintsExpandX | ROOT.kLHintsExpandY))
        
        

        self.AddFrame( self.vMainFrame, ROOT.TGLayoutHints(ROOT.kLHintsExpandX | ROOT.kLHintsExpandY))

        self.SetWindowName( 'Calibration GUI' )
        self.MapSubwindows()
        self.Resize( self.GetDefaultSize() )
        self.MapWindow()

    def __del__(self):
        self.Cleanup()
    
    ##############################################################################
    # Campaign Operations
    ##############################################################################    
    
    def SetCampaignData(self, campaign):
        """
        Extract the data stored within the campaign to set the GUI to browse it:
        """
        # Copy the elements over
        self.campaign = campaign
        # Update the list box:
        #self.sPedList.RemoveAll()
        for i in range(len(campaign)):
            name = "ped_" + str(campaign[i]["bias"]) + ("_led" if campaign[i]["LEDState"]=="ON" else "_noled")
            self.sPedList.AddEntry(name, i)
            
    def SetModuleData(self, modules):
        """
        Set module data:
        """
        # Copy the elements over
        self.modules = modules
        # Update the list box:
        #self.sPedList.RemoveAll()
        #for i in range(len(campaign)):
        #    name = "ped_" + str(campaign[i]["bias"]) + ("_led" if campaign[i]["LEDState"]=="ON" else "_noled")
        #    self.sPedList.AddEntry(name, i)
        

    def UpdateUniqueCounter(self):
        # use the unique number to update the moduel/board/channel:
        unique_chan = int(self.sUniqueChannel.GetNumberEntry().GetIntNumber())
        print ("unique channel: %i"%unique_chan)
        board = unique_chan/(8*64)
        rem = unique_chan%(8*64)
        module = rem/64
        module_chan = rem%64
        print ("board: %i  module: %i  channel: %i"%(board, module, module_chan ))
        self.sBoard.GetNumberEntry().SetIntNumber(board)
        self.sModule.GetNumberEntry().SetIntNumber(module)
        self.sModuleChannel.GetNumberEntry().SetIntNumber(module_chan)
    
    def UpdateModuleCounter(self):
        # use the unique number to update the moduel/board/channel:
        board = int(self.sBoard.GetNumberEntry().GetIntNumber())
        module = int(self.sModule.GetNumberEntry().GetIntNumber())
        module_chan = int(self.sModuleChannel.GetNumberEntry().GetIntNumber())
        print ("board: %i  module: %i  channel: %i"%(board, module, module_chan ))
        unique_chan = 8*64*board + 64*module + module_chan
        self.sUniqueChannel.GetNumberEntry().SetIntNumber(unique_chan)
     
    ##############################################################################
    # Plot operations
    ##############################################################################
    
    def PlotPedHist(self):
        """
        Make a plot of a pedastool hist, using the selected ID:
        """
        try:
            # Selected element:
            cid = self.sPedList.GetSelected()
            hist = self.campaign[cid]["allpeds"]
            #self.Canvas.GetCanvas().cd(0)
            hist.Draw("COL")
            self.Canvas.GetCanvas().Update()
        except:
            print "Error plotting ped hist"
    
    def PlotChannelHist(self):
        ChannelID = int(self.sUniqueChannel.GetNumberEntry().GetIntNumber())
        DatasetID = self.sPedList.GetSelected()
        
        # Get histogram:
        self.hist = self.campaign[DatasetID]["allpeds"].ProjectionY("th1d_projecty",ChannelID+1,ChannelID+1,"")
        #self.Canvas.GetCanvas().cd(0)
        self.hist.Draw("")
        self.hist.GetXaxis().SetRangeUser(0,100)
        
        # Identify additional data:
        channel = self.campaign[DatasetID]["channels"][ChannelID]
        self.pt = ROOT.TPaveText( 0.7, 0.5, 0.95, 0.75, "NDC" )
        self.pt.AddText("Channel Status: %s"%channel["ChannelState"] )
        if channel["ChannelState"] == "PEPeaks":
            self.pt.AddText("Counts>1pe: %.3f"%channel["darkcounts"] )
            self.pt.AddText("LightYield: %.3f"%channel["pe"] )
            for p in range(len(channel["Peaks"])):
                self.pt.AddText("Peak %i: %.3f"%(p, channel["Peaks"][p] ) )
                                       
        self.pt.Draw()
        
        # Add peak markers:
        max_h = self.hist.GetBinContent(self.hist.GetMaximumBin())
        
        self.tl = []
        for p in channel["Peaks"]:
            tl = ROOT.TLine(p,0, p, max_h)
            tl.SetLineColor(ROOT.kRed)
            tl.Draw("l")
            self.tl.append(tl)
            
        # Add TFIT:
#         try:
#             fitfunc = ROOT.TF1("pedfit","gaus(0) + gaus(3)", 0, 255)
#             for i in range(6):
#                 fitfunc.SetParameter(i, channel["PedSinglesParams"][i])
#                 fitfunc.SetParError(i, channel["PedSinglesParams"][i+6])
#                 fitfunc.Draw("SAME")
#                 self.fitfunc = fitfunc
#         except:
#             pass
        
        self.Canvas.GetCanvas().Update()
        
    def PlotChannelDarkCounts(self):
        ChannelID = int(self.sUniqueChannel.GetNumberEntry().GetIntNumber())
        scan_bias, scan_darkcounts = BiasCalibrator.GetBiasScan(self.campaign, ChannelID, "darkcounts", False)
        
        self.tg = ROOT.TGraph()
        for i in range (len (scan_bias)):
            self.tg.SetPoint(self.tg.GetN(), scan_bias[i], scan_darkcounts[i])
        self.tg.Draw("apl")
        self.tg.SetTitle("Dark Counts for channel %i; Bias(V); Dark Count Fraction"%ChannelID)
        
        self.Canvas.GetCanvas().Update()
        
    def PlotChannelLightYield(self):
        ChannelID = int(self.sUniqueChannel.GetNumberEntry().GetIntNumber())
        scan_bias_nolight, scan_lightoff = BiasCalibrator.GetBiasScan(self.campaign, ChannelID, "pe", False)
        scan_bias_light, scan_lighton = BiasCalibrator.GetBiasScan(self.campaign, ChannelID, "pe", True)
        
         
        self.tg = ROOT.TGraph()
        for i in range (len (scan_bias_nolight)):
            i_match = None
            for j in range(len (scan_bias_light)):
                if math.fabs(scan_bias_nolight[i] - scan_bias_light[j])\
                 < BiasCalibrator.cmp_tol:
                    i_match = j
            if not (i_match is None):
                self.tg.SetPoint(self.tg.GetN(), scan_bias_nolight[i],\
                                  scan_lighton[i] - scan_lightoff[i_match])
        self.tg.Draw("apl")
        self.tg.SetTitle("Dark Counts for channel %i; Bias(V); Light Yield (npe)"%ChannelID)
        
        self.Canvas.GetCanvas().Update()
        
    def PlotChannelDarkCountsLightYield(self):
        ChannelID = int(self.sUniqueChannel.GetNumberEntry().GetIntNumber())
        scan_bias_nolight, scan_lightoff = BiasCalibrator.GetBiasScan(self.campaign, ChannelID, "pe", False)
        scan_bias_light, scan_lighton = BiasCalibrator.GetBiasScan(self.campaign, ChannelID, "pe", True)
        scan_bias_dc, scan_dc = BiasCalibrator.GetBiasScan(self.campaign, ChannelID, "darkcounts", False)
         
        self.tg = ROOT.TGraph()
        for i in range (len (scan_bias_nolight)):
            i_match = None
            i_darkcounts = None
            for j in range(len (scan_bias_light)):
                if math.fabs(scan_bias_nolight[i] - scan_bias_light[j])\
                 < BiasCalibrator.cmp_tol:
                    i_match = j
            for j in range(len (scan_bias_light)):
                if math.fabs(scan_bias_nolight[i] - scan_bias_dc[j])\
                 < BiasCalibrator.cmp_tol:
                    i_darkcounts = j
            
            if not (i_match is None) and not (i_darkcounts is None):
                self.tg.SetPoint(self.tg.GetN(),scan_dc[i_darkcounts],\
                                  scan_lighton[i] - scan_lightoff[i_match])
        self.tg.Draw("apl")
        self.tg.SetTitle("Dark Counts for channel %i; Dark Counts; Light Yield (npe)"%ChannelID)
        
        self.Canvas.GetCanvas().Update()
        
    def PlotModuleOptimumBiasDarkCounts(self):
        # Find optimum module:
        ChannelID = int(self.sUniqueChannel.GetNumberEntry().GetIntNumber())
        ModuleID = BiasCalibrator.GenerateModuleData(ChannelID)["ModuleID"]
        
        Module = None
        for m in self.modules:
            if m["ModuleID"] == ModuleID:
                Module = m
        
        if not Module is None:
            OptimumBias = Module["OptimumBias"]
            self.hist = ROOT.TH1D("DCOpt","Dark Counts for ModuleID %i at Bias %.3f; Fraction Dark Counts"%(ModuleID, OptimumBias),40,0,0.2)
            for this_ChannelID in Module["ChannelIDs"]:
                scan_bias, scan_darkcounts =  BiasCalibrator.GetBiasScan(self.campaign, this_ChannelID, "darkcounts", False)
                DarkCount = numpy.interp(OptimumBias, scan_bias, scan_darkcounts)
                zero_counts = min(scan_darkcounts[0:8])
                self.hist.Fill(DarkCount-zero_counts)
            self.hist.Draw()
            
        self.Canvas.GetCanvas().Update()
        
    def PlotOptimumBiasDarkCounts(self):
        #
        self.hist = ROOT.TH2D("","", BiasCalibrator.NUM_CHANS/BiasCalibrator.CHAN_PER_MOD,\
                             0, BiasCalibrator.NUM_CHANS-1, 40, 0, 0.2)
        
        for ModuleID in range(BiasCalibrator.NUM_CHANS/BiasCalibrator.CHAN_PER_MOD):
            Module = None
            for m in self.modules:
                if m["ModuleID"] == ModuleID:
                    Module = m
                
            if not Module is None:
                OptimumBias = Module["OptimumBias"]       
                for this_ChannelID in Module["ChannelIDs"]:
                    scan_bias, scan_darkcounts =  BiasCalibrator.GetBiasScan(self.campaign, this_ChannelID, "darkcounts", False)
                    DarkCount = numpy.interp(OptimumBias, scan_bias, scan_darkcounts)
                    zero_counts = min(scan_darkcounts[0:8])
                    self.hist.Fill(this_ChannelID,DarkCount-zero_counts)
            
        self.hist.Draw("COL")
        self.Canvas.GetCanvas().Update()

    # Temporary test plot to see difference between adeys method
    # and new method...
    def PlotChannelDCDiff(self):
        #
        ChannelID = int(self.sUniqueChannel.GetNumberEntry().GetIntNumber())
        scan_bias_dc, scan_dc = BiasCalibrator.GetBiasScan(self.campaign, ChannelID, "darkcounts", False)
        scan_bias_dco, scan_dco = BiasCalibrator.GetBiasScan(self.campaign, ChannelID, "darkcounts_old", True)
        
         
        self.tg = ROOT.TGraph()
        for i in range (len (scan_bias_dc)):
            i_match = None
            for j in range(len (scan_bias_dc)):
                if math.fabs(scan_bias_dco[i] - scan_bias_dc[j])\
                 < BiasCalibrator.cmp_tol:
                    i_match = j
            if not (i_match is None):
                self.tg.SetPoint(self.tg.GetN(), scan_dc[i], scan_dco[i_match])
        self.tg.Draw("apl")
        self.tg.SetTitle("Dark Counts for channel %i; DC; DC_Old"%ChannelID)
        
        self.Canvas.GetCanvas().Update()
        

if __name__ == "__main__":
    
    print (module_description)
        
    
    window = BiasUIMainFrame( ROOT.gClient.GetRoot(), 800, 600 )
    
    rundata = BiasCalibrator.main()
    
    if not  "allpeds" in rundata["Campaign"][0]:
        rundata["Campaign"] = BiasCalibrator.LoadCampaign(rundata["Campaign"])
    
    window.SetCampaignData(rundata["Campaign"])
    window.SetModuleData(rundata["Modules"])
    
    #BiasCalibrator.SetupDatasetChannels(campaign[0])
    
    
    import time
    while window:
        time.sleep(1)
