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
from ProceduralGeneration import ProceduralModels
from ProceduralGeneration import ProceduralShips
import ShipModules

class AI_PatrolCraft_1(ShipBase.Ship):
    #Name = "Enterprise"
    ClassName = "Patrol Craft 1"
    def __init__(self, generateModel=True) -> None:
        super().__init__()
        self.addModule(ShipModules.AI_faction_modules.Hull_S())
        self.addModule(ShipModules.AI_faction_modules.Sensor_M())
        self.addModule(ShipModules.AI_faction_modules.Engine_XS())
        self.addModule(ShipModules.AI_faction_modules.Thruster_XS())
        self.addModule(ShipModules.AI_faction_modules.Shield_XS())
        self.addModule(ShipModules.AI_faction_modules.Beam_XXS())
        self.addModule(ShipModules.AI_faction_modules.Beam_XXS())
        self.generateProceduralModel()

class AI_Corvette_1(ShipBase.Ship):
    #Name = "Enterprise"
    ClassName = "Corvette 1"
    def __init__(self, generateModel=True) -> None:
        super().__init__()
        self.addModule(ShipModules.AI_faction_modules.Hull_M())
        self.addModule(ShipModules.AI_faction_modules.Sensor_M())
        self.addModule(ShipModules.AI_faction_modules.Engine_S())
        self.addModule(ShipModules.AI_faction_modules.Thruster_S())
        self.addModule(ShipModules.AI_faction_modules.Shield_S())
        self.addModule(ShipModules.AI_faction_modules.Beam_XS())
        self.addModule(ShipModules.AI_faction_modules.Beam_XS())
        self.addModule(ShipModules.AI_faction_modules.Beam_XS())
        self.generateProceduralModel()

class AI_Frigate_1(ShipBase.Ship):
    #Name = "Enterprise"
    ClassName = "Frigate 1"
    def __init__(self, generateModel=True) -> None:
        super().__init__()
        self.addModule(ShipModules.AI_faction_modules.Hull_M())
        self.addModule(ShipModules.AI_faction_modules.Sensor_M())
        self.addModule(ShipModules.AI_faction_modules.Engine_S())
        self.addModule(ShipModules.AI_faction_modules.Thruster_S())
        self.addModule(ShipModules.AI_faction_modules.Shield_M())
        self.addModule(ShipModules.AI_faction_modules.Beam_S())
        self.addModule(ShipModules.AI_faction_modules.Beam_S())
        self.addModule(ShipModules.AI_faction_modules.Beam_M())
        self.generateProceduralModel()

class AI_Frigate_LR_1(ShipBase.Ship):
    #Name = "Enterprise"
    ClassName = "Artillery Frigate 1"
    def __init__(self, generateModel=True) -> None:
        super().__init__()
        self.addModule(ShipModules.AI_faction_modules.Hull_M())
        self.addModule(ShipModules.AI_faction_modules.Sensor_M())
        self.addModule(ShipModules.AI_faction_modules.Engine_S())
        self.addModule(ShipModules.AI_faction_modules.Thruster_S())
        self.addModule(ShipModules.AI_faction_modules.Shield_M())
        self.addModule(ShipModules.AI_faction_modules.Beam_XL())
        self.generateProceduralModel()

class AI_Frigate_H_1(ShipBase.Ship):
    #Name = "Enterprise"
    ClassName = "Heavy Frigate 1"
    def __init__(self, generateModel=True) -> None:
        super().__init__()
        self.addModule(ShipModules.AI_faction_modules.Hull_M())
        self.addModule(ShipModules.AI_faction_modules.Sensor_M())
        self.addModule(ShipModules.AI_faction_modules.Engine_XS())
        self.addModule(ShipModules.AI_faction_modules.Thruster_XS())
        self.addModule(ShipModules.AI_faction_modules.Shield_L())
        self.addModule(ShipModules.AI_faction_modules.Beam_L())
        self.addModule(ShipModules.AI_faction_modules.Beam_L())
        self.addModule(ShipModules.AI_faction_modules.Beam_L())
        self.generateProceduralModel()
