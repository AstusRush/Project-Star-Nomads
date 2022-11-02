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
from BaseClasses import ListLoader
from BaseClasses import ModelBase
from ProceduralGeneration import GeomBuilder

class _ProceduralModel(ModelBase.ModelBase):
    IconPath = ""
    ModelPath = ""
    def __init__(self, loadImmediately=True, seed:int=None) -> None:
        if seed is None:
            seed = np.random.randint(1000000)
        self.rng = np.random.default_rng(seed)
        super().__init__(loadImmediately)
    
    def _init_model(self):
        super()._init_model()
        #if self.CouldLoadModel:
    
    def setColour(self):
        pass
    
    def getModel(self):
        return self.generateModel()
    
    def destroy(self):
        super().destroy()
        #if hasattr(self,"Model") and self.Model:
        #    self.Model.removeNode()
        #if hasattr(self,"Node") and self.Node:
        #    self.Node.removeNode()
    
    def resetModel(self):
        super().resetModel()
        #self.Model.setHpr(0,0,0)
        #self.Model.setPos(0,0,0)
        #self.Model.setScale(1)
        #self.Model.setH(180) # Required for .obj that I create with blender regardless of whether their front is x or -x (z is up)
    
    def centreModel(self):
        super().centreModel()
        #self.resetModel()
        ##REMINDER: Use the next line to make shields (adjust the scale factor here accordingly so that the shields have a decend distance to the ship but are smaller than 1.0 to avoid clipping)
        #self.setScale(0.8/self.Model.getBounds().getRadius())
        #self.Model.setPos(-self.Model.getBounds().getApproxCenter())
    
    def setScale(self, value:float):
        super().setScale(value)
        ##TODO: Implement ship sizes somehow. I am not shure if this should be in conjunctions with the model or the ship nor where this should be applied...
        #self.Model.setScale(value)
    
    def tocode_AGeLib(self, name="", indent=0, indentstr="    ", ignoreNotImplemented = False) -> typing.Tuple[str,dict]:
        raise NotImplementedError() #CRITICAL: How do we save the instructions for generating models?
        #ret, imp = "", {}
        ## ret is the ship data that calls a function which is stored as an entry in imp which constructs the ship
        ## Thus, ret, when executed, will be this ship. This can then be nested in a list so that we can reproduce entire fleets.
        #imp.update(IMP_MODELBASE)
        #get.shipModels()
        #ret = indentstr*indent
        #if name:
        #    ret += name + " = "
        #if hasattr(self,"INTERNAL_NAME"):
        #    ret += f"get.shipModels()[\"{self.INTERNAL_NAME}\"]()"
        #else:
        #    ret += f"createShip({self.IconPath},{self.ModelPath})"
        #return ret, imp
    
    def generateModel(self):
        raise NotImplementedError("generateModel must be implemented in the subclass of _ProceduralModel")

class ProceduralModel_Asteroid(_ProceduralModel):
    def generateModel(self):
        gb = GeomBuilder.GeomBuilder('asteroid')
        res = get.menu().GraphicsOptionsWidget.AsteroidResolution()
        gb.add_asteroid(phi_resolution=res, theta_resolution=res, rng=self.rng)
        node = p3dc.NodePath(gb.get_geom_node())
        return node

class ProceduralModel_Planet(_ProceduralModel):
    def generateModel(self):
        raise NotImplementedError("#TODO: Procedurally generate planets")

class ProceduralModel_Star(_ProceduralModel):
    def generateModel(self):
        raise NotImplementedError("#TODO: Procedurally generate stars")

class ProceduralModel_Skybox(_ProceduralModel):
    def generateModel(self):
        raise NotImplementedError("#TODO: Procedurally generate skyboxes")

class ProceduralModel_Nebula(_ProceduralModel):
    def generateModel(self):
        raise NotImplementedError("#TODO: Procedurally generate nebulas")

class ProceduralModel_Sphere(_ProceduralModel):
    def generateModel(self):
        gb = GeomBuilder.GeomBuilder('sphere')
        gb.add_sphere([1,1,1,1], (0,0,0), 1, 60, 20)
        node = p3dc.NodePath(gb.get_geom_node())
        return node
