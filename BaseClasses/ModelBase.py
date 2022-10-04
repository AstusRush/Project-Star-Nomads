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
#if TYPE_CHECKING:
from BaseClasses import HexBase

class ModelBase():
    IconPath = ""
    "tempModels/NCC-1701-D.gltf"
    def __init__(self) -> None:
        self.Model:p3dc.NodePath = None
        self._init_model()
        
    def _init_model(self):
        self.Node = p3dc.NodePath(p3dc.PandaNode(f"Central node of model: {id(self)}"))
        try:
            self.Node.reparentTo(render())
            try:
                self.Model:p3dc.NodePath = loader().loadModel(self.ModelPath)
            except:
                self.Model:p3dc.NodePath = loader().loadModel("Models/Simple Geometry/cube.ply")
                NC(2,f"Could not load model {self.ModelPath}. Loading a cube instead...", exc=True)
        except:
            self.Node.removeNode()
            raise
        try:
            self.Model.reparentTo(self.Node)
            self.Model.setColor(ape.colour((1,1,1,1)))
        except:
            self.Model.removeNode()
            self.Node.removeNode()
            raise
        
    def resetModel(self):
        self.Model.setH(0) #TODO: Reset all rotations
        self.Model.setPos(0,0,0)
        self.Model.setScale(1)
        
    def centreModel(self):
        self.resetModel()
        #REMINDER: Use the next line to make shields (adjust the scale factor here accordingly so that the shields have a decend distance to the ship but are smaller than 1.0 to avoid clipping)
        self.Model.setScale(0.8/self.Model.getBounds().getRadius())
        self.Model.setPos(-self.Model.getBounds().getApproxCenter())

class ShipModel(ModelBase):
    def __init__(self) -> None:
        super().__init__()
        self.centreModel()
