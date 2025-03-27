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

if TYPE_CHECKING:
    from BaseClasses import ShipBase, FleetBase, BaseModules, HexBase


IMP_MODELBASE = [("PSN get","from BaseClasses import get"),("PSN ModelBase","from BaseClasses import ModelBase"),("PSN ModelConstructor","""
def createModel(IconPath,ModelPath):
    Model = ModelBase.ModelBase()
    Model.IconPath = IconPath
    Model.ModelPath = ModelPath
    Model._init_model()
    return Model
""")]

class ModelBase():
    IconPath = "" #TODO: we need a default icon for ships
    ModelPath = "Models/Simple Geometry/cube.ply"
    LengthFactor = 1
    def __init__(self, loadImmediately=True, ship:'ShipBase.ShipBase'=None) -> None:
        self.Model:p3dc.NodePath = None
        self.Node:p3dc.NodePath = None
        self.CouldLoadModel = False
        self.ship:'typing.Union[weakref.ref[ShipBase.ShipBase],None]' = weakref.ref(ship) if ship else None
        if loadImmediately:
            self._init_model()
    
    def _init_model(self):
        if hasattr(self,"Model") and self.Model:
            self.Model.removeNode()
        if hasattr(self,"Node") and self.Node:
            self.Node.removeNode()
        self.Node = p3dc.NodePath(p3dc.PandaNode(f"Central node of model: {id(self)}"))
        try:
            self.Node.reparentTo(render())
            try:
                self.Model:p3dc.NodePath = self.getModel()
                self.CouldLoadModel = True
            except:
                self.CouldLoadModel = False
                NC(2,f"Could not load model {self.ModelPath}. Loading a cube instead...", exc=True, unique=True)
                self.Model:p3dc.NodePath = ape.loadModel("Models/Simple Geometry/cube.ply")
        except:
            self.CouldLoadModel = False
            self.Node.removeNode()
            self.Node, self.Model = None, None
            raise
        try:
            self.Model.reparentTo(self.Node)
            self.setColour()
        except:
            self.CouldLoadModel = False
            self.Model.removeNode()
            self.Node.removeNode()
            self.Node, self.Model = None, None
            raise
    
    def setColour(self):
        self.Model.setColor((1,1,1,1))
    
    def applyTeamColour(self):
        pass # Not supported for the base model and therefore ignored
    
    def getModel(self):
        return ape.loadModel(self.ModelPath)
    
    def destroy(self):
        if hasattr(self,"Model") and self.Model:
            self.Model.removeNode()
        if hasattr(self,"Node") and self.Node:
            self.Node.removeNode()
        self.ship = None
    
    def resetModel(self):
        self.Model.setHpr(0,0,0)
        self.Model.setPos(0,0,0)
        self.Model.setScale(1)
        self.Model.setH(180) # Required for .obj that I create with blender regardless of whether their front is x or -x (z is up)
        #b = self.Model.getTightBounds()
        #self.LengthFactor = (b[0].x-b[1].x)/(b[0].y-b[1].y)
        #self.LengthFactor = ((b[0].x-b[1].x)*(b[0].y-b[1].y)*(b[0].z-b[1].z))
    
    def centreModel(self):
        self.resetModel()
        #REMINDER: Use the next line to make shields (adjust the scale factor here accordingly so that the shields have a decent distance to the ship but are smaller than 1.0 to avoid clipping)
        self.setScale(0.8/self.Model.getBounds().getRadius())
        self._centreModel()
    
    def _centreModel(self):
        self.Model.setPos(-self.Model.getBounds().getApproxCenter())
    
    def setScale(self, value:float):
        self.Model.setScale(value)
    
    def tocode_AGeLib(self, name="", indent=0, indentstr="    ", ignoreNotImplemented = False) -> typing.Tuple[str,dict]:
        ret, imp = "", {}
        # ret is the ship data that calls a function which is stored as an entry in imp which constructs the ship
        # Thus, ret, when executed, will be this ship. This can then be nested in a list so that we can reproduce entire fleets.
        imp.update(IMP_MODELBASE)
        get.shipModels()
        ret = indentstr*indent
        if name:
            ret += name + " = "
        if hasattr(self,"INTERNAL_NAME"):
            ret += f"get.shipModels()[\"{self.INTERNAL_NAME}\"]()"
        else:
            ret += f"createShip({self.IconPath},{self.ModelPath})"
        return ret, imp

class ShipModel(ModelBase):
    def __init__(self) -> None:
        super().__init__()
        self.centreModel()

class EnvironmentalModel(ModelBase):
    def __init__(self) -> None:
        super().__init__()
        self.centreModel()
