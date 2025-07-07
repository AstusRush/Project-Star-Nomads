"""
TODO
"""
"""
    Copyright (C) 2021  Robin Albers
"""
# Python standard imports
import datetime
import platform
import os
import sys
import time
import random
import typing
import weakref
import inspect
import importlib
import textwrap

# External imports
import numpy as np

# Panda imports
import panda3d as p3d
import panda3d.core as p3dc
import direct as p3dd
from direct.interval.IntervalGlobal import Sequence as p3ddSequence
from direct.showbase.DirectObject import DirectObject
from direct.gui.OnscreenText import OnscreenText
from direct.task.Task import Task

# AGe and APE imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # These imports make the IDE happy
    from ...AstusPandaEngine.AGeLib import *
    from ...AstusPandaEngine import AstusPandaEngine as ape
    from ...AstusPandaEngine.AstusPandaEngine import engine, base, render, loader
    from ...AstusPandaEngine.AstusPandaEngine import window as _window
else:
    # These imports make Python happy
    #sys.path.append('../AstusPandaEngine')
    from AGeLib import *
    import AstusPandaEngine as ape
    from AstusPandaEngine import engine, base, render, loader
    from AstusPandaEngine import window as _window

if TYPE_CHECKING:
    from BaseClasses import ShipBase, FleetBase, BaseModules, HexBase
    from GUI import ModuleWidgets

from BaseClasses import get

class EconomyDisplay(QtWidgets.QSplitter):
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget']) -> None:
        super().__init__(parent=parent)
        self.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.TopScrollWidget = QtWidgets.QScrollArea(self)
        self.TopScrollWidget.setWidgetResizable(True)
        super().addWidget(self.TopScrollWidget)
        #TODO: Rename Fleets (All Fleets including enemies. After all it is up to the player how they call the enemy fleets. The enemy crew will still call their fleet however they want.)
        self.TopView = AGeWidgets.TightGridWidget(self)
        self.TopScrollWidget.setWidget(self.TopView)
        self._init_TopView()
        
        self.BottomScrollWidget = QtWidgets.QScrollArea(self)
        self.BottomScrollWidget.setWidgetResizable(True)
        super().addWidget(self.BottomScrollWidget)
        self.BottomView = AGeWidgets.TightGridWidget(self)
        self.BottomScrollWidget.setWidget(self.BottomView)
        self._init_BottomView()
        
        get.app().S_HexSelectionChanged.connect(lambda: self.updateInfo())
        get.app().S_NewTurnStarted.connect(lambda: self.updateInfo())
        
        #TODO: Overhaul button position
        self.TransferButton = super().addWidget(AGeWidgets.Button(self,"Transfer Resources", lambda: self.openTransferWindow()))
    
    def openTransferWindow(self):
        hex_ = get.hexGrid().SelectedHex
        if hex_:
            from GUI import ResourceTransfer
            get.engine().TransferWindow = ResourceTransfer.TransferWindow()
            get.engine().TransferWindow.addParticipant(hex_)
            get.engine().TransferWindow.show()
    
    def _init_TopView(self):
        self.TEMP_FleetResourceLabel = self.TopView.addWidget(QtWidgets.QLabel())
    
    def _init_BottomView(self):
        self.TEMP_HexResourceLabel = self.BottomView.addWidget(QtWidgets.QLabel())
    
    def updateInfo(self):
        hex_ = get.hexGrid().SelectedHex
        if not hex_:
            self.TEMP_FleetResourceLabel.setText("")
            self.TEMP_HexResourceLabel.setText("")
            return
        text = f"{hex_.Name}"
        if hex_.ResourcesFree: text += hex_.ResourcesFree.text("\nFree floating Resources:")
        if hex_.ResourcesHarvestable: text += hex_.ResourcesHarvestable.text("\nHarvestable Resources:")
        self.TEMP_HexResourceLabel.setText(text)
        
        text = ""
        if hex_.fleet:
            fleet = hex_.fleet()
            if text: text += "\n\n"
            text += f"{fleet.Name}"
            text +=  fleet.ResourceManager.storedResources().text("\nResources in the fleet:")
        for i in hex_.content:
            if not i: continue
            fleet = i()
            if text: text += "\n\n"
            text += f"{fleet.Name}"
            text +=  fleet.ResourceManager.storedResources().text("\nResources in the fleet:")
        self.TEMP_FleetResourceLabel.setText(text)
