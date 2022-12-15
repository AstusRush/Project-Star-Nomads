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

# Game Imports
from BaseClasses import get
from BaseClasses import HexBase
from BaseClasses import ShipBase
from BaseClasses import ModelBase
from BaseClasses import BaseModules
from BaseClasses import FleetBase
from GUI import ModuleWidgets

class Economic(BaseModules._Economic):
    Buildable = False
    # Modules for economic purposes like educating and entertaining people (civilians and crew), harvesting or processing resources, growing food, and researching stuff.
    #MAYBE: Researching could be tied to other modules like sensors to scan stuff or special experimental weapons to test stuff or experimental shields to test stuff or... you get the idea
    Name = "Economic Module"
    
    def __init__(self) -> None:
        super().__init__()
        self.Widget:'ModuleWidgets.EconomicWidget' = None
        self.FullWidget:'ModuleWidgets.EconomicWidget' = None
    
    def getFullInterface(self):
        self.FullWidget = ModuleWidgets.EconomicWidget(self)
        return self.FullWidget

class Cargo(Economic):
    # Used to store resources
    Name = "Cargo Module"
    Buildable = False
    
    def __init__(self) -> None:
        super().__init__()
        self.Widget:'ModuleWidgets.CargoWidget' = None
        self.FullWidget:'ModuleWidgets.CargoWidget' = None
    
    def getFullInterface(self):
        self.FullWidget = ModuleWidgets.CargoWidget(self)
        return self.FullWidget
