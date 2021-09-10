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
from heapq import heappush, heappop

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
if TYPE_CHECKING:
    from BaseClasses import FleetBase
from BaseClasses import HexBase
from BaseClasses import ModelBase

class ShipBase():
  #region init and destroy
    def __init__(self) -> None:
        self.fleet = None # type: weakref.ref['FleetBase.FleetBase']
        self.Model: ModelBase = None
        self.Node = p3dc.NodePath(p3dc.PandaNode(f"Central node of ship {id(self)}"))
        self.Node.reparentTo(render())
  #endregion init and destroy
  #region model
    def reparentTo(self, fleet):
        # type: (FleetBase.FleetBase) -> None
        self.fleet = weakref.ref(fleet)
        self.Node.reparentTo(fleet.Node)
        self.Node.setPos(0,0,0)
    
    def makeModel(self, modelPath):
        model = ModelBase.ModelBase(modelPath)
        self.setModel(model)
    
    def setModel(self, model: ModelBase.ModelBase):
        self.Model = model
        self.Model.Node.reparentTo(self.Node)
        self.Model.Node.setPos(0,0,0)
        
    def setPos(self, *args):
        self.Model.Node.setPos(*args)
  #endregion model
  #region ...
    #def ___(self,):
  #endregion ...
  #region ...
    #def ___(self,):
  #endregion ...

class Ship(ShipBase):
    pass
