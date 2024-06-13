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
import math

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
#if TYPE_CHECKING:
from BaseClasses import FleetBase
from BaseClasses import ShipBase
from BaseClasses import get
from BaseClasses import HexBase
from BaseClasses import ModelBase
from BaseClasses import BaseModules
from ProceduralGeneration import ProceduralModels

class EnvironmentalObject(ShipBase.ShipBase):
    def __init__(self) -> None:
        super().__init__()

class Asteroid(EnvironmentalObject):
    Name = "Asteroid"
    ClassName = "Asteroid"
    def __init__(self, generateModel=True) -> None:
        super().__init__()
        if generateModel:
            #self.setModel(AsteroidModel())
            self.setModel(ProceduralModels.ProceduralModel_Asteroid())
            if not self.Model.CouldLoadModel and self.Model.Model: self.Model.Model.setColor(ape.colour(QtGui.QColor(0x6d4207)))
        self.addModule(BaseModules.Asteroid_Hull())
    
    def setModel(self, model: 'typing.Union[ModelBase.ModelBase,None]'):
        if model is None:
            model = ProceduralModels.ProceduralModel_Asteroid()
        return super().setModel(model)
