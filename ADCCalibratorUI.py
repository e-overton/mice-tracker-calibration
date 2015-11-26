#!/usr/bin/env python

module_description = \
"""
 === ADC Calibrator GUI Script =====================================

    Creates a GUI to make checking and correcting the ADC calibrations
    possible
    
    Edward Overton, 9/7/15
    
"""

import os
import sys
import ROOT

import ADCCalibrator
import FECalibrationUtils
import LightYieldEstimator

class ADCUIMainFrame( ROOT.TGMainFrame ):
    
    # Data Objects:
    # The ADC Calibration we are trying to use...
    Calibration = None
    config = None
    
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

        """
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
        # Append
        self.AddFrame(self.fMenuBar,  ROOT.TGLayoutHints(ROOT.kLHintsExpandX, 0, 0, 1, 0))
        """
              
        ##############################################################################
        # Main GUI Generation:
        ##############################################################################
        
        self.vMainFrame = ROOT.TGHorizontalFrame(self, 120, 200)
        
        ##############################################################################
        # Sidebar:
        ############################################################################## 
        
        self.fSideBar = ROOT.TGVerticalFrame( self.vMainFrame, 220, 300)
        
        ##############################################################################
        # Radio Buttons for internal/external LEDs.
        self.bg_datasel =  ROOT.TGButtonGroup(self.fSideBar,"Plot Selector",ROOT.kVerticalFrame)
        self.bg_datasel_extled = ROOT.TGRadioButton(self.bg_datasel,ROOT.TGHotString("Ext LED ON"))
        self.bg_datasel_extnoled = ROOT.TGRadioButton(self.bg_datasel,ROOT.TGHotString("Ext LED OFF"))
        self.bg_datasel_intled = ROOT.TGRadioButton(self.bg_datasel,ROOT.TGHotString("Int LED ON"))
        self.bg_datasel_intnoled = ROOT.TGRadioButton(self.bg_datasel,ROOT.TGHotString("Int LED OFF"))
        self.fSideBar.AddFrame(self.bg_datasel, ROOT.TGLayoutHints(ROOT.kLHintsExpandX | ROOT.kLHintsTop,2,2,2,2))
        
        ##############################################################################
        # Plot 2dhist plot:
        self._pedPlotDispatch = ROOT.TPyDispatcher(self.PlotPedHist)
        self.bPedDraw = ROOT.TGTextButton(self.fSideBar,"Plot Peds")
        self.bPedDraw.Connect("Clicked()", "TPyDispatcher", self._pedPlotDispatch, "Dispatch()" )
        self.fSideBar.AddFrame( self.bPedDraw, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        
        ##############################################################################
        # Section for the electronics selectors:
        
        self.fChannelSelector = ROOT.TGGroupFrame(self.fSideBar,"Channel Selector")
        self._boardChanUpdate = ROOT.TPyDispatcher(self.UpdateBankCounter)
        self._uniqueChanUpdate = ROOT.TPyDispatcher(self.UpdateUniqueCounter)
        
        self.fBoard = ROOT.TGHorizontalFrame( self.fChannelSelector, 30, 200)
        self.lBoard = ROOT.TGLabel( self.fBoard, "Board:  " )
        self.fBoard.AddFrame( self.lBoard, ROOT.TGLayoutHints(ROOT.kLHintsLeft))
        self.sBoard = ROOT.TGNumberEntry(self.fBoard, 0, 16, -1,\
                                         ROOT.TGNumberFormat.kNESInteger,\
                                         ROOT.TGNumberFormat.kNEANonNegative,\
                                         ROOT.TGNumberFormat.kNELLimitMinMax,\
                                         0, 15 )
        self.sBoard.Connect("ValueSet(Long_t)", "TPyDispatcher", self._boardChanUpdate, "Dispatch()" )
        self.sBoard.GetNumberEntry().Connect("ReturnPressed()", "TPyDispatcher", self._boardChanUpdate, "Dispatch()" )
        
        self.fBoard.AddFrame( self.sBoard, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        self.fChannelSelector.AddFrame( self.fBoard, ROOT.TGLayoutHints(ROOT.kLHintsRight | ROOT.kLHintsTop | ROOT.kLHintsCenterY,6,6,6,6))
        
        self.fBank = ROOT.TGHorizontalFrame( self.fChannelSelector, 30, 200)
        self.lBank = ROOT.TGLabel( self.fBank, "Bank:  " )
        self.fBank.AddFrame( self.lBank, ROOT.TGLayoutHints(ROOT.kLHintsLeft))
        self.sBank = ROOT.TGNumberEntry(self.fBank, 0, 4,-1,\
                                          ROOT.TGNumberFormat.kNESInteger,\
                                          ROOT.TGNumberFormat.kNEANonNegative,\
                                          ROOT.TGNumberFormat.kNELLimitMinMax,\
                                          0, 7 )
        self.sBank.Connect("ValueSet(Long_t)", "TPyDispatcher", self._boardChanUpdate, "Dispatch()" )
        self.sBank.GetNumberEntry().Connect("ReturnPressed()", "TPyDispatcher", self._boardChanUpdate, "Dispatch()" )
        self.fBank.AddFrame( self.sBank, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        self.fChannelSelector.AddFrame( self.fBank, ROOT.TGLayoutHints(ROOT.kLHintsRight | ROOT.kLHintsTop | ROOT.kLHintsCenterY,6,6,6,6))
        
        self.fBankChannel = ROOT.TGHorizontalFrame( self.fChannelSelector, 30, 200)
        self.lBankChannel = ROOT.TGLabel( self.fBankChannel, "BankChannel:  " )
        self.fBankChannel.AddFrame( self.lBankChannel, ROOT.TGLayoutHints(ROOT.kLHintsLeft))
        self.sBankChannel = ROOT.TGNumberEntry(self.fBankChannel, 0, 8,-1,\
                                                 ROOT.TGNumberFormat.kNESInteger,\
                                                 ROOT.TGNumberFormat.kNEANonNegative,\
                                                 ROOT.TGNumberFormat.kNELLimitMinMax,\
                                                 0, 63 )
        self.sBankChannel.Connect("ValueSet(Long_t)", "TPyDispatcher", self._boardChanUpdate, "Dispatch()" )
        self.sBankChannel.GetNumberEntry().Connect("ReturnPressed()", "TPyDispatcher", self._boardChanUpdate, "Dispatch()" )
        self.fBankChannel.AddFrame( self.sBankChannel, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        self.fChannelSelector.AddFrame( self.fBankChannel, ROOT.TGLayoutHints(ROOT.kLHintsRight | ROOT.kLHintsTop | ROOT.kLHintsCenterY,6,6,6,6))
        
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
        
        self.bAutoIncrement = ROOT.TGCheckButton(self.fChannelSelector, "Auto Increment",1)
        self.fChannelSelector.AddFrame( self.bAutoIncrement, ROOT.TGLayoutHints(ROOT.kLHintsRight | ROOT.kLHintsTop | ROOT.kLHintsCenterY,6,6,6,6))
        
        self.fSideBar.AddFrame(self.fChannelSelector, ROOT.TGLayoutHints(ROOT.kLHintsExpandX | ROOT.kLHintsTop,2,2,2,2))
        
        
        ##############################################################################
        # Button Pressing Options:
        self._plotChannelHist = ROOT.TPyDispatcher(self.PlotChannelHist)
        self.bChanHDraw = ROOT.TGTextButton(self.fSideBar,"Plot Channel")
        self.bChanHDraw.Connect("Clicked()", "TPyDispatcher", self._plotChannelHist, "Dispatch()" )
        self.fSideBar.AddFrame( self.bChanHDraw, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        
        self._plotPeaks = ROOT.TPyDispatcher(self.PlotPeaks)
        self.bPeaksDraw = ROOT.TGTextButton(self.fSideBar,"Plot Peaks")
        self.bPeaksDraw.Connect("Clicked()", "TPyDispatcher", self._plotPeaks, "Dispatch()" )
        self.fSideBar.AddFrame( self.bPeaksDraw, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        
        self._plotGain = ROOT.TPyDispatcher(self.PlotADCGain)
        self.bGainDraw = ROOT.TGTextButton(self.fSideBar,"Plot Gains")
        self.bGainDraw.Connect("Clicked()", "TPyDispatcher", self._plotGain, "Dispatch()" )
        self.fSideBar.AddFrame( self.bGainDraw, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        
        self._plotPedestal = ROOT.TPyDispatcher(self.PlotADCPedestal)
        self.bPedDraw = ROOT.TGTextButton(self.fSideBar,"Plot Pedestal")
        self.bPedDraw.Connect("Clicked()", "TPyDispatcher", self._plotPedestal, "Dispatch()" )
        self.fSideBar.AddFrame( self.bPedDraw, ROOT.TGLayoutHints(ROOT.kLHintsRight))

        self._plotNPeaks = ROOT.TPyDispatcher(self.PlotNPeaks)
        self.bNPeaksDraw = ROOT.TGTextButton(self.fSideBar,"Plot Num Peaks")
        self.bNPeaksDraw.Connect("Clicked()", "TPyDispatcher", self._plotNPeaks, "Dispatch()" )
        self.fSideBar.AddFrame( self.bNPeaksDraw, ROOT.TGLayoutHints(ROOT.kLHintsRight))

        self._plotNoiseRates = ROOT.TPyDispatcher(self.PlotNoiseRates)
        self.bNoiseRDraw = ROOT.TGTextButton(self.fSideBar,"Plot Noise Rates")
        self.bNoiseRDraw.Connect("Clicked()", "TPyDispatcher", self._plotNoiseRates, "Dispatch()" )
        self.fSideBar.AddFrame( self.bNoiseRDraw, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        
        self._updatfromfit = ROOT.TPyDispatcher(self.UpdateFromFit)
        self.bupdatefromfit = ROOT.TGTextButton(self.fSideBar,"Update from fit")
        self.bupdatefromfit.Connect("Clicked()", "TPyDispatcher", self._updatfromfit, "Dispatch()" )
        self.fSideBar.AddFrame( self.bupdatefromfit, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        
        self._repeatfit = ROOT.TPyDispatcher(self.RepeatLastFit)
        self.brepeatfit = ROOT.TGTextButton(self.fSideBar,"Repeat last fit")
        self.brepeatfit.Connect("Clicked()", "TPyDispatcher", self._repeatfit, "Dispatch()" )
        self.fSideBar.AddFrame( self.brepeatfit, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        
        self._nextbad = ROOT.TPyDispatcher(self.FindNextBadChannel)
        self.bnextbad = ROOT.TGTextButton(self.fSideBar,"Find next bad")
        self.bnextbad.Connect("Clicked()", "TPyDispatcher", self._nextbad, "Dispatch()" )
        self.fSideBar.AddFrame( self.bnextbad, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        
        self._flagbad = ROOT.TPyDispatcher(self.FlagAsBad)
        self.bflagbad = ROOT.TGTextButton(self.fSideBar,"Flag Bad Channel")
        self.bflagbad.Connect("Clicked()", "TPyDispatcher", self._flagbad, "Dispatch()" )
        self.fSideBar.AddFrame( self.bflagbad, ROOT.TGLayoutHints(ROOT.kLHintsRight))

        self._flagok = ROOT.TPyDispatcher(self.FlagAsOK)
        self.bflagok = ROOT.TGTextButton(self.fSideBar,"Flag OK Channel")
        self.bflagok.Connect("Clicked()", "TPyDispatcher", self._flagok, "Dispatch()" )
        self.fSideBar.AddFrame( self.bflagok, ROOT.TGLayoutHints(ROOT.kLHintsRight))

        self._editChannel = ROOT.TPyDispatcher(self.EditChannel)
        self.bEditChannel = ROOT.TGTextButton(self.fSideBar,"Edit Channel")
        self.bEditChannel.Connect("Clicked()", "TPyDispatcher", self._editChannel, "Dispatch()" )
        self.fSideBar.AddFrame( self.bEditChannel, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        
        self._saveAll = ROOT.TPyDispatcher(self.SaveAll)
        self.bSaveAll = ROOT.TGTextButton(self.fSideBar,"SaveAll")
        self.bSaveAll.Connect("Clicked()", "TPyDispatcher", self._saveAll, "Dispatch()" )
        self.fSideBar.AddFrame( self.bSaveAll, ROOT.TGLayoutHints(ROOT.kLHintsRight))
        
        ##############################################################################
        # Attach to canvas:
        self.vMainFrame.AddFrame(self.fSideBar, ROOT.TGLayoutHints( ROOT.kLHintsLeft | ROOT.kLHintsExpandY,2,2,2,2));
        ##############################################################################
        # Central Canvas:
        ############################################################################## 

        self.Canvas    = ROOT.TRootEmbeddedCanvas( 'Canvas', self.vMainFrame, 400, 400 )      
        self.vMainFrame.AddFrame( self.Canvas, ROOT.TGLayoutHints(ROOT.kLHintsExpandX | ROOT.kLHintsExpandY, 2,0,2,2));
        
        self.AddFrame( self.vMainFrame, ROOT.TGLayoutHints(ROOT.kLHintsExpandX | ROOT.kLHintsExpandY))
        ###############################################################################
        # Done, now Draw:
        self.SetWindowName( 'Calibration GUI' )
        self.MapSubwindows()
        self.Resize( self.GetDefaultSize() )
        self.MapWindow()
        ################################################################################
        
    def SetCalibration(self, Calibration):
        self.Calibration = Calibration
        
    def SetConfig(self, config):
        self.config = config
        
    def UpdateUniqueCounter(self):
        # use the unique number to update the moduel/board/channel:
        unique_chan = int(self.sUniqueChannel.GetNumberEntry().GetIntNumber())
        print ("unique channel: %i"%unique_chan)
        board = unique_chan/(4*128)
        rem = unique_chan%(4*128)
        bank = rem/128
        bank_chan = rem%128
        print ("board: %i  module: %i  channel: %i"%(board, bank, bank_chan ))
        self.sBoard.GetNumberEntry().SetIntNumber(board)
        self.sBank.GetNumberEntry().SetIntNumber(bank)
        self.sBankChannel.GetNumberEntry().SetIntNumber(bank_chan)
        
    def IncrementUniqueCounter(self):
        # Increment and update.
        unique_chan = int(self.sUniqueChannel.GetNumberEntry().GetIntNumber())
        self.sUniqueChannel.GetNumberEntry().SetIntNumber(unique_chan+1)
        self.UpdateUniqueCounter()

    def UpdateBankCounter(self):
        # use the unique number to update the moduel/board/channel:
        board = int(self.sBoard.GetNumberEntry().GetIntNumber())
        bank = int(self.sBank.GetNumberEntry().GetIntNumber())
        bank_chan = int(self.sBankChannel.GetNumberEntry().GetIntNumber())
        print ("board: %i  module: %i  channel: %i"%(board, bank, bank_chan ))
        unique_chan = 4*128*board + 128*bank + bank_chan
        self.sUniqueChannel.GetNumberEntry().SetIntNumber(unique_chan)
        
        
    def PlotPedHist(self):
        """
        Make a plot of a pedastool hist, using the selected ID:
        """
        try:
            # External LED
            if (self.bg_datasel_extled.IsDown()):
                self.Calibration.ExtLEDHist.Draw("COL")
            elif (self.bg_datasel_extnoled.IsDown()):
                self.Calibration.ExtNoLEDHist.Draw("COL")
            elif (self.bg_datasel_intled.IsDown()):
                self.Calibration.IntLEDHist.Draw("COL")
            elif (self.bg_datasel_intnoled.IsDown()):
                self.Calibration.IntNoLEDHist.Draw("COL")
    
            self.Canvas.GetCanvas().Update()
            
        except Exception as e:
            print "Error plotting ped hist"
            print e.message
        
    def PlotChannelHist(self,nchans=None):
        """
        Plot a single channel, and highlight the calibrated PE peaks etc...
        """
        
        if nchans is None: 
            # Check auto increment function:
            if (self.bAutoIncrement.IsDown()):
                self.IncrementUniqueCounter()
        else:
            for n in range(nchans):
                self.IncrementUniqueCounter()
        
        # Channel Identifier:
        ChannelID = int(self.sUniqueChannel.GetNumberEntry().GetIntNumber())
        
        SourceHist = None
        SourceLYE = None
        FEChannel = self.Calibration.FEChannels[ChannelID]
        
        try:
            # External LED
            if (self.bg_datasel_extled.IsDown()):
                SourceHist = self.Calibration.ExtLEDHist.ProjectionY("th1d_projecty",ChannelID+1,ChannelID+1,"")
                SourceLYE = LightYieldEstimator.LightYieldEstimator(FEChannel.LightYieldExtLED)
                
            # External NoLED
            elif (self.bg_datasel_extnoled.IsDown()):
                SourceHist = self.Calibration.ExtNoLEDHist.ProjectionY("th1d_projecty",ChannelID+1,ChannelID+1,"")
                SourceLYE = LightYieldEstimator.LightYieldEstimator(FEChannel.LightYieldExtNoLED)
            
            # Internal LED:    
            elif (self.bg_datasel_intled.IsDown()):
                SourceHist = self.Calibration.IntLEDHist.ProjectionY("th1d_projecty",ChannelID+1,ChannelID+1,"")
                SourceLYE = LightYieldEstimator.LightYieldEstimator(FEChannel.LightYieldIntLED)
            
            # Internal NoLED    
            elif (self.bg_datasel_intnoled.IsDown()):
                SourceHist = self.Calibration.IntNoLEDHist.ProjectionY("th1d_projecty",ChannelID+1,ChannelID+1,"")
                SourceLYE = LightYieldEstimator.LightYieldEstimator(FEChannel.LightYieldIntNoLED)
            
            else:
                raise Exception ("No Button Selected")
        
            SourceHist.SetNameTitle("h", "Channel %i"%ChannelID)
            SourceHist.Draw()
            self.th = SourceHist
            self.th.GetXaxis().SetRangeUser(0,100)
        
            # Add peak markers:
            max_h = SourceHist.GetBinContent(SourceHist.GetMaximumBin())
            
            self.tl = []
            for p in SourceLYE.Peaks:
                tl = ROOT.TLine(p,0, p, max_h)
                tl.SetLineColor(ROOT.kRed)
                tl.Draw("l")
                self.tl.append(tl)
                
            for i in range(5):
                pos = FEChannel.ADC_Pedestal + i*FEChannel.ADC_Gain
                tl = ROOT.TLine(pos, 0, pos, max_h)
                tl.SetLineColor(ROOT.kBlue)
                tl.Draw("l")
                self.tl.append(tl)
                
            self.Canvas.GetCanvas().Update()
        
        
        except Exception as e:
            print "Error plotting ped hist"
            print e.message
        
    
    def PlotPeaks(self):
        """
        Plot the location of the peaks from the LED systems:
        """
        self.tgpoints = ROOT.TGraph()
        
        for FEChannel in Calibration.FEChannels:
            
            try:
                peaks = None
                
                if (self.bg_datasel_extled.IsDown()):
                    peaks = FEChannel.LightYieldExtLED["Peaks"]
                elif (self.bg_datasel_extnoled.IsDown()):
                    peaks = FEChannel.LightYieldExtNoLED["Peaks"]
                elif (self.bg_datasel_intled.IsDown()):
                    peaks = FEChannel.LightYieldIntLED["Peaks"]
                elif (self.bg_datasel_intnoled.IsDown()):
                    peaks = FEChannel.LightYieldIntNoLED["Peaks"]
                    
                if not peaks is None:    
                    for p in range(1,len(peaks)):
                        self.tgpoints.SetPoint(self.tgpoints.GetN(), FEChannel.ChannelUID, peaks[p] - peaks[0])
            
           
            except Exception as e:
                print "Error plotting ped hist"
                print e.message
                continue
        
        self.tgpoints.Draw("ap")
        self.Canvas.GetCanvas().Update()
        
    def PlotNPeaks(self):
        """
        Plot number of peaks discovered for each channel:
        """
        self.th3 = ROOT.TH1D("InTracker","InTracker",8192, -0.5, 8191.5)
        self.th = ROOT.TH1D("NumPeaks","NumPeaks",8192, -0.5, 8191.5)
        self.th4 = ROOT.TH1D("BadChans","BadChans",8192, -0.5, 8191.5)
        
        
        for FEChannel in Calibration.FEChannels:
        
            try:
                self.th3.SetBinContent(FEChannel.ChannelUID+1,10*FEChannel.InTracker)
                channel_issue_severity = 0
                for Issue in FEChannel.Issues:
                    print (Issue)
                    if int(Issue["Severity"]) > 5:
                        channel_issue_severity = 8
                self.th4.SetBinContent(FEChannel.ChannelUID+1,channel_issue_severity)
                    
            except:
                print(FEChannel.Issues)
                raise
            
            
            try:
                peaks = None
                
                if (self.bg_datasel_extled.IsDown()):
                    peaks = FEChannel.LightYieldExtLED["Peaks"]
                elif (self.bg_datasel_extnoled.IsDown()):
                    peaks = FEChannel.LightYieldExtNoLED["Peaks"]
                elif (self.bg_datasel_intled.IsDown()):
                    peaks = FEChannel.LightYieldIntLED["Peaks"]
                elif (self.bg_datasel_intnoled.IsDown()):
                    peaks = FEChannel.LightYieldIntNoLED["Peaks"]
                
                if not peaks is None:    
                    self.th.SetBinContent(FEChannel.ChannelUID+1, len(peaks))
            
            except Exception as e:
                print "Error plotting ped hist"
                print e.message
                continue
        
        self.th3.Draw()
        self.th3.SetFillColor(ROOT.kGreen-7)
        self.th4.Draw("SAME")
        self.th4.SetFillColor(ROOT.kRed)
        self.th.Draw("SAME")
        self.th.SetFillColor(ROOT.kYellow)
        self.Canvas.GetCanvas().Update()
        
    def PlotADCGain(self):
        """
        Plot the gain of ever channel
        """
        
        self.tgpoints = ROOT.TGraph()
        
        for FEChannel in Calibration.FEChannels:
            
            self.tgpoints.SetPoint(self.tgpoints.GetN(), FEChannel.ChannelUID, FEChannel.ADC_Gain)
            
        self.tgpoints.Draw("ap")
        self.Canvas.GetCanvas().Update()
        
    def PlotADCPedestal(self):
        """
        Plot the pedestal of ever channel
        """
        
        self.tgpoints = ROOT.TGraph()
        
        for FEChannel in Calibration.FEChannels:
            
            self.tgpoints.SetPoint(self.tgpoints.GetN(), FEChannel.ChannelUID, FEChannel.ADC_Pedestal)
            
        self.tgpoints.Draw("ap")
        self.Canvas.GetCanvas().Update()
        
        
    def PlotNoiseRates(self):
        """
        Plot number of peaks discovered for each channel:
        """
        self.th3 = ROOT.TH1D("InTracker","InTracker",8192, -0.5, 8191.5)
        self.th = ROOT.TH1D("NoiseRate1pe","NoiseRate1pe",8192, -0.5, 8191.5)
        self.th2 = ROOT.TH1D("NoiseRate2pe","NoiseRate2pe",8192, -0.5, 8191.5)
        self.th4 = ROOT.TH1D("BadChans","BadChans",8192, -0.5, 8191.5)
        
        for FEChannel in Calibration.FEChannels:
            
            try:
                self.th3.SetBinContent(FEChannel.ChannelUID+1,1*FEChannel.InTracker)
                channel_issue_severity = 0
                for Issue in FEChannel.Issues:
                    print (Issue)
                    if int(Issue["Severity"]*0.1) > channel_issue_severity:
                        channel_issue_severity = Issue["Severity"]*0.1
                self.th4.SetBinContent(FEChannel.ChannelUID+1,channel_issue_severity)
                    
            except:
                print ("Exception caught... in PlotNoiseRates Channel Issues...")
            
            
            try:
                SourceLYE = None
                
                if (self.bg_datasel_extled.IsDown()):
                    SourceLYE = LightYieldEstimator.LightYieldEstimator(FEChannel.LightYieldExtLED)
                elif (self.bg_datasel_extnoled.IsDown()):
                    SourceLYE = LightYieldEstimator.LightYieldEstimator(FEChannel.LightYieldExtNoLED)
                elif (self.bg_datasel_intled.IsDown()):
                    SourceLYE = LightYieldEstimator.LightYieldEstimator(FEChannel.LightYieldIntLED)
                elif (self.bg_datasel_intnoled.IsDown()):
                    SourceLYE = LightYieldEstimator.LightYieldEstimator(FEChannel.LightYieldIntNoLED)
                
                if not SourceLYE is None:
                    integrals = SourceLYE.Integrals
                    self.th.SetBinContent(FEChannel.ChannelUID+1, sum(integrals[2:])/sum(integrals))
                    self.th2.SetBinContent(FEChannel.ChannelUID+1, sum(integrals[3:])/sum(integrals))
            
            except Exception as e:
                print "Error plotting ped hist"
                print e.message
                continue
            
        self.th3.Draw()
        self.th3.SetFillColor(ROOT.kGreen-7)
        self.th3.SetLineWidth(0)
        
        try:
            self.th4.Draw("SAME")
        except:
            pass
        
        self.th.Draw("SAME")
        self.th.SetFillColor(ROOT.kYellow)
        self.th2.Draw("SAME")
        self.th2.SetFillColor(ROOT.kBlue-3)
        self.Canvas.GetCanvas().Update()
        
    # Function to update the fitted values by hand...
    def UpdateFromFit(self):

        # Extract fit data:
        fitfunc = self.th.GetFunction("PrevFitTMP")
        if not fitfunc:
            fitfunc = self.th.GetFunction("gaus+gaus(3)")
        
        if fitfunc:
            
            # Estimate gain/pedestal:
            pedestal = fitfunc.GetParameter(1)
            gain = fitfunc.GetParameter(4) - fitfunc.GetParameter(1)
            
            print("modifying gain/pedestal to: %.3f, %.3f"%(pedestal,gain))
            
            # Update Channel:
            ChannelID = int(self.sUniqueChannel.GetNumberEntry().GetIntNumber())
            channel = self.Calibration.FEChannels[ChannelID]
            
            channel.ADC_Pedestal = pedestal
            channel.ADC_Gain = gain
            
            # Update issues:
            for issue in channel.Issues:
                if issue["Severity"] == 4 and issue["Issue"] ==  "InternalLED":
                    issue["Severity"] = 0  
                    issue["Comment"] += ", Hand Fitted."
                elif issue["Severity"] > 0 and issue["Issue"] ==  "Calibration Update":
                    issue["Severity"] = 0  
                    issue["Comment"] += ", Hand Fitted."
                    
        # Store fit values:
        self.fitvalues = [fitfunc.GetParameter(i) for i in range(6)]
        self.PlotChannelHist(0)
        
    # repeat using the last fit as a seed:    
    def RepeatLastFit(self):
        
        try:
            upthresh = self.fitvalues[1] + (self.fitvalues[4] - self.fitvalues[1])*1.3
        
            self.fitfunction = ROOT.TF1("PrevFitTMP","gaus+gaus(3)",0,upthresh)
            [self.fitfunction.SetParameter(i, self.fitvalues[i]) for i in range(6)]
            self.th.Fit(self.fitfunction, "R")
        except:
            raise
        
        self.Canvas.GetCanvas().Update()
        
    def EditChannel(self):
        
        ChannelID = int(self.sUniqueChannel.GetNumberEntry().GetIntNumber())
        
        print ("Editing Channel: %i"%ChannelID)
        
        self.Calibration.FEChannels = FECalibrationUtils.EditChannelData(self.Calibration.FEChannels, ChannelID)
        
    def FindNextBadChannel(self):
        
        ChannelID = int(self.sUniqueChannel.GetNumberEntry().GetIntNumber())
        for ChannelUID in range(ChannelID+1, FECalibrationUtils.NUM_CHANS):
            stop = False
            accepted = False
            if self.Calibration.FEChannels[ChannelUID].InTracker:
                for Issue in self.Calibration.FEChannels[ChannelUID].Issues:
                    if (Issue["Issue"] == "AcceptedBad"):
                        accepted = True
                    if (Issue["Severity"] > 2):
                        stop = True
            if not accepted and stop:
                break
            
        self.sUniqueChannel.GetNumberEntry().SetIntNumber(ChannelUID)
        self.UpdateUniqueCounter()
        self.PlotChannelHist(0)
        
    def FlagAsBad(self):
        
        ChannelID = int(self.sUniqueChannel.GetNumberEntry().GetIntNumber())
        channel = self.Calibration.FEChannels[ChannelID]
        
        channel.ADC_Pedestal = 0.
        channel.ADC_Gain = 0.
        
        channel.Issues.append({"ChannelUID":channel.ChannelUID, "Severity":10,\
                                 "Issue":"AcceptedBad","Comment":"Channel Flagged as Bad. Masked out in ped/gain"})
        
        self.PlotChannelHist(0)
        
        
    def FlagAsOK(self):
        
        ChannelID = int(self.sUniqueChannel.GetNumberEntry().GetIntNumber())
        channel = self.Calibration.FEChannels[ChannelID]
        
        channel.Issues.append({"ChannelUID":channel.ChannelUID, "Severity":0,\
                                 "Issue":"AcceptedBad","Comment":"Channel Flagged as OK."})
        
        self.PlotChannelHist(0)
        
    def SaveAll(self):
        
        FECalibrationUtils.SaveFEChannelList(self.Calibration.FEChannels,\
                                             os.path.join(self.config["path"],self.config["FECalibrations"]))
        
if __name__ == "__main__":
    
    # Print Description:
    print (module_description)
    
    # Try to load the calibration...
    try:
        print ("")
        path = sys.argv[1]
        print ("loading calibration from directory: %s"%path)
        print ("")
        
        print ("loading calibration config...")
        config = FECalibrationUtils.LoadCalibrationConfig(path)
        print ("... done")
        print ("")
    
    except:
        print "Failed to load valid configuration from calibration directory"
        raise
    
    # Run the main calibraton now:
    Calibration = ADCCalibrator.ADCCalibration()
    Calibration.Load(config)
    Calibration.LoadInternalLED()
    
    #Calibration.Load(config)
    #Calibration = ADCCalibrator.main (config)
    #Calibration.LoadInternalLED()
    
    # Create window:
    window = ADCUIMainFrame( ROOT.gClient.GetRoot(), 800, 600 )
    window.SetCalibration(Calibration)
    window.SetConfig(config)
    
    raw_input("Script complete, press enter to continue")
    
    print ("Exiting.")
