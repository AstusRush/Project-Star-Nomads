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
else:
    # These imports make Python happy
    #sys.path.append('../AstusPandaEngine')
    from AGeLib import *

from BaseClasses import get
from BaseClasses import BaseModules
from Economy import Resources
from Economy import BaseEconomicModules

if TYPE_CHECKING:
    from BaseClasses import ShipBase
    from BaseClasses import FleetBase

#############################################################################
#region EconomyManager

class _BaseEconomyManager:
    def __init__(self) -> None:
        pass

class FleetEconomyManager(_BaseEconomyManager):
    def __init__(self, fleet:'FleetBase.FleetBase') -> None:
        super().__init__()
        self.fleet:'weakref.ref[FleetBase.FleetBase]' = weakref.ref(fleet)
        self.ResourceManager = FleetResourceManager(fleet)

class ShipEconomyManager(_BaseEconomyManager):
    def __init__(self, ship:'ShipBase.ShipBase') -> None:
        super().__init__()
        self.ship:'weakref.ref[ShipBase.ShipBase]' = weakref.ref(ship)
        self.ResourceManager = ShipResourceManager(ship)

#endregion EconomyManager
#############################################################################
#region ResourceManager

class _BaseResourceManager:
    def __init__(self) -> None:
        pass

class FleetResourceManager(_BaseResourceManager):
    def __init__(self, fleet:'FleetBase.FleetBase') -> None:
        super().__init__()
        self.fleet:'weakref.ref[FleetBase.FleetBase]' = weakref.ref(fleet)
    
    def storedResources(self) -> 'Resources._ResourceDict':
        d = Resources._ResourceDict()
        for ship in self.fleet().Ships:
            d += ship.ResourceManager.storedResources()
        return d
    
    def capacity(self) -> float:
        cap = 0
        for ship in self.fleet().Ships:
            cap += ship.ResourceManager.capacity()
        return cap
    
    def add(self, r:'Resources._ResourceDict') -> 'Resources._ResourceDict':
        """
        Try to put as many resources from a _ResourceDict into this fleet and returns everything that did not fit as a new _ResourceDict\n
        the given _ResourceDict is not altered!
        """
        for ship in self.fleet().Ships:
            r = ship.ResourceManager.add(r)
        return r
    
    def subtract(self, r:'Resources._ResourceDict') -> 'Resources._ResourceDict':
        return self.add(-r)
    
    def fillFromModule(self, moduleToEmpty:'BaseEconomicModules.Cargo') -> 'bool':
        """
        Try to empty `moduleToEmpty` and put all resources in cargo modules in this fleet.\n
        Returns True if the module was successfully emptied.
        Returns False if the module could not be emptied fully.
        """
        for ship in self.fleet().Ships:
            if not moduleToEmpty.storedResources(): return True
            ship.ResourceManager.fillFromModule(moduleToEmpty)
        return not moduleToEmpty.storedResources()
    
    def getTransferWidget(self) -> QtWidgets.QWidget: #REMINDER: Update type hint once the method is implemented
        raise NotImplementedError("#CRITICAL: GUI to Transfer Resources")

class ShipResourceManager(_BaseResourceManager):
    def __init__(self, ship:'ShipBase.ShipBase') -> None:
        super().__init__()
        self.ship:'weakref.ref[ShipBase.ShipBase]' = weakref.ref(ship)
    
    def storedResources(self) -> 'Resources._ResourceDict':
        d = Resources._ResourceDict()
        for module in self.ship().Modules:
            if isinstance(module, BaseEconomicModules.Cargo):
                d += module.storedResources()
        return d
    
    def capacity(self) -> float:
        cap = 0
        for module in self.ship().Modules:
            if isinstance(module, BaseEconomicModules.Cargo):
                cap += module.Capacity
        return cap
    
    def add(self, r:'Resources._ResourceDict') -> 'Resources._ResourceDict':
        """
        Try to put as many resources from a _ResourceDict into this ship and returns everything that did not fit as a new _ResourceDict\n
        the given _ResourceDict is not altered!
        """
        for module in self.ship().Modules:
            if isinstance(module, BaseEconomicModules.Cargo):
                r = module.storedResources().fillFrom(r)
        return r
    
    def subtract(self, r:'Resources._ResourceDict') -> 'Resources._ResourceDict':
        return self.add(-r)
    
    def fillFromModule(self, moduleToEmpty:'BaseEconomicModules.Cargo') -> 'bool':
        """
        Try to empty `moduleToEmpty` and put all resources in cargo modules on this ship.\n
        Returns True if the module was successfully emptied.
        Returns False if the module could not be emptied fully.
        """
        for module in self.ship().Modules:
            if not moduleToEmpty.storedResources(): return True
            if isinstance(module, BaseEconomicModules.Cargo) and module is not moduleToEmpty:
                module.storedResources().transferMax(moduleToEmpty.storedResources())
        return not moduleToEmpty.storedResources()
    
    def getTransferWidget(self) -> QtWidgets.QWidget: #REMINDER: Update type hint once the method is implemented
        raise NotImplementedError("#CRITICAL: GUI to Transfer Resources")

#endregion ResourceManager
#############################################################################
