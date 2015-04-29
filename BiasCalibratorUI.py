'Dispatch()'#!/usr/bin/env python

module_description = \
"""
 === Bias Calibrator GUI Script =====================================

    Creates a GUI to make checking a calibration much eaisier..
    
"""


import os, sys, ROOT
import multiprocessing


class BiasUIMainFrame( ROOT.TGMainFrame ):
    
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
        # Channel selector input:
        ##############################################################################
        self.fChannelSelector = ROOT.TGGroupFrame(self.fSideBar,"Channel Selector")
        
        # Dispatchers:
        self._moduleChanUpdate = ROOT.TPyDispatcher(self.UpdateModuleCounter)
        self._uniqueChanUpdate = ROOT.TPyDispatcher(self.UpdateUniqueCounter)
        
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
        
        self.fSideBar.AddFrame(self.fChannelSelector, ROOT.TGLayoutHints(ROOT.kLHintsExpandX | ROOT.kLHintsTop,2,2,2,2))
        
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
        

if __name__ == "__main__":
    
    print (module_description)
    
    window = BiasUIMainFrame( ROOT.gClient.GetRoot(), 800, 600 )
    
    import time
    while window:
        time.sleep(1)