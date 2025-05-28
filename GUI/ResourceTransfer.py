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

from BaseClasses import ShipBase, FleetBase, BaseModules, HexBase
from Economy import BaseEconomicModules, Resources

if TYPE_CHECKING:
    from GUI import ModuleWidgets

from BaseClasses import get

class TransferWindow(AWWF):
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget']=None) -> None:
        super().__init__(parent)
        self.TransferWidget = TransferWidget(self)
        self.setCentralWidget(self.TransferWidget)
    
    def addParticipants(self, participants):
        self.TransferWidget.addParticipants(participants)
    
    def addParticipant(self, participant):
        self.TransferWidget.addParticipant(participant)

class _StorageDisplayBase(AGeWidgets.TightGridWidget):#QtWidgets.QWidget):
    def __init__(self, parent: typing.Optional['_StorageDisplayBase']=None, participants=None) -> None:
        super().__init__(parent)
        self.Frame = self.addOuterWidget(AGeWidgets.TightGridFrame(self))
    
    def addWidget(self, widget:'QtWidgets.QWidget', *args, **kwargs):
        self.Frame.addWidget(widget, *args, **kwargs)
        return widget
    
    def addOuterWidget(self, widget:'QtWidgets.QWidget', *args, **kwargs):
        super().addWidget(widget, *args, **kwargs)
        return widget
    
    def addParticipant(self, participant):
        if   isinstance(participant, HexBase._Hex):
            self.addWidget(HexStorageDisplay(self, participant))
        elif isinstance(participant, FleetBase.FleetBase):
            self.addWidget(FleetStorageDisplay(self, participant))
        elif isinstance(participant, ShipBase.ShipBase):
            self.addWidget(ShipStorageDisplay(self, participant))
        elif isinstance(participant, BaseEconomicModules.Cargo):
            self.addWidget(ModuleStorageDisplay(self, participant))
        elif isinstance(participant, Resources._ResourceDict):
            self.addWidget(ResourceDictionaryStorageDisplay(self, participant))
        elif participant is None:
            return
        else:
            NC(2,f"_StorageDisplayBase can not handle objects of type {type(participant)}",tb=True)

class TransferWidget(_StorageDisplayBase):
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget']=None, participants=None) -> None:
        super().__init__(parent)
        self.TransferSlider = self.addOuterWidget(TransferSlider(self))
        #TODO: Basic UI Setup
        
        #self.addParticipant(participants)
    
    def addParticipants(self, participants):
        if not participants: return
        for i in participants:
            self.addParticipant(i)

class TransferSlider(QtWidgets.QWidget):
    def __init__(self, parent:'TransferWidget') -> None:
        self.TransferWidget = parent
        super().__init__(parent)

class HexStorageDisplay(_StorageDisplayBase):
    def __init__(self, parent: '_StorageDisplayBase', content: 'HexBase._Hex') -> None:
        super().__init__(parent)
        self.content = weakref.ref(content)
        for i in content:
            self.addParticipant(i)
        self.addParticipant(content.ResourcesFree)
        self.addParticipant(content.ResourcesHarvestable)
        pass #TODO

class FleetStorageDisplay(_StorageDisplayBase):
    def __init__(self, parent: '_StorageDisplayBase', content: 'FleetBase.FleetBase') -> None:
        super().__init__(parent)
        self.content = weakref.ref(content)
        for i in content.Ships:
            self.addParticipant(i)
        pass #TODO

class ShipStorageDisplay(_StorageDisplayBase):
    def __init__(self, parent: '_StorageDisplayBase', content: 'ShipBase.ShipBase') -> None:
        super().__init__(parent)
        self.content = weakref.ref(content)
        for i in content.Modules:
            if isinstance(i, BaseEconomicModules.Cargo):
                self.addParticipant(i)
        pass #TODO

class ResourceDictionaryStorageDisplay(_StorageDisplayBase):
    def __init__(self, parent: '_StorageDisplayBase', content: 'Resources._ResourceDict') -> None:
        super().__init__(parent)
        self.content = weakref.ref(content)
        
        self.Label = self.addWidget(QtWidgets.QLabel(content.text()))
        
        pass #TODO

class ModuleStorageDisplay(ResourceDictionaryStorageDisplay):
    def __init__(self, parent: '_StorageDisplayBase', content: 'BaseEconomicModules.Cargo') -> None:
        self.content_CargoModule = weakref.ref(content)
        super().__init__(parent, content.storedResources())
