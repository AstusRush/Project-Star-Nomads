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

class TransferWindow(AWWF):
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget']=None) -> None:
        super().__init__(parent)
        pass

class _StorageDisplayBase(QtWidgets.QWidget):
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget']=None, participants=None) -> None:
        super().__init__(parent)
        #TODO
    
    def addParticipant(self, participant):
        pass

class TransferWidget(_StorageDisplayBase):
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget']=None, participants=None) -> None:
        super().__init__(parent)
        #TODO: Basic UI Setup
        
        self.addParticipant(participants)
    
    def addParticipants(self, participants):
        if not participants: return
        for i in participants:
            if isinstance(HexBase._Hex):
                self.addParticipant(i)
    
    def addParticipant(self, participant):
        pass

class TransferSlider(QtWidgets.QWidget):
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget']=None) -> None:
        super().__init__(parent)
        pass

class HexStorageDisplay(_StorageDisplayBase):
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget']=None) -> None:
        super().__init__(parent)
        pass

class FleetStorageDisplay(_StorageDisplayBase):
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget']=None) -> None:
        super().__init__(parent)
        pass

class ShipStorageDisplay(_StorageDisplayBase):
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget']=None) -> None:
        super().__init__(parent)
        pass

class ModuleStorageDisplay(_StorageDisplayBase):
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget']=None) -> None:
        super().__init__(parent)
        pass

class ResourceDictionaryStorageDisplay(_StorageDisplayBase):
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget']=None) -> None:
        super().__init__(parent)
        pass
