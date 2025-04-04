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
from Environment import EnvironmentalObjects
from Economy import Resources
from Economy import BaseEconomicModules
from ProceduralGeneration import ProceduralModels

class HarvestableEnvironmentalObject(EnvironmentalObjects.EnvironmentalObject):
    pass

class ResourceAsteroid(HarvestableEnvironmentalObject):
    Name = "Resource Rich Asteroid"
    ClassName = "Asteroid"
    def __init__(self, generateModel=True) -> None:
        super().__init__()
        self.IsBlockingTilePartially  = True
        self.IsBlockingTileCompletely = False
        self.IsBackgroundObject       = True
        self.addModule(BaseModules.Asteroid_Hull())
        self.addModule(BaseEconomicModules.Asteroid_Resources())
        resourceScale = 4
        resourceType = random.randint(0,100)
        if resourceType <= 50:
            self.ResourceTypeName = "Ore"
            self.ResourceManager.addDirect(Resources.Ore(random.randint(1,10)*resourceScale))
        elif resourceType <= 75:
            self.ResourceTypeName = "Crystals"
            self.ResourceManager.addDirect(Resources.Crystals(random.randint(1,8)*resourceScale))
        else:
            self.ResourceTypeName = "RareOre"
            self.ResourceManager.addDirect(Resources.Ore(random.randint(2,4)*resourceScale))
            self.ResourceManager.addDirect(Resources.RareOre(random.randint(1,5)*resourceScale))
        if generateModel:
            self.setModel(ProceduralModels.ProceduralModel_Asteroid(resourceTypeName=self.ResourceTypeName))
            if not self.Model.CouldLoadModel and self.Model.Model: self.Model.Model.setColor(ape.colour(QtGui.QColor(0x6d4207)))
    
    def setModel(self, model: 'typing.Union[ModelBase.ModelBase,None]'):
        if model is None:
            model = ProceduralModels.ProceduralModel_Asteroid(resourceTypeName=self.ResourceTypeName)
        return super().setModel(model)

class Debris(HarvestableEnvironmentalObject):
    Name = "Debris"
    ClassName = "Debris"
    def __init__(self, generateModel=True) -> None:
        super().__init__()
        self.IsBlockingTilePartially  = False
        self.IsBlockingTileCompletely = False
        self.IsBackgroundObject       = True
        self.addModule(BaseModules.Hull())
        self.addModule(BaseEconomicModules.Debris_Resources())
        if generateModel:
            #self.setModel(ProceduralModels.ProceduralModel_Debris())
            self.setModel(ProceduralModels.ProceduralModel_Asteroid())
            if not self.Model.CouldLoadModel and self.Model.Model: self.Model.Model.setColor(ape.colour(QtGui.QColor(0x6d4207)))
    
    def setModel(self, model: 'typing.Union[ModelBase.ModelBase,None]'):
        if model is None:
            #model = ProceduralModels.ProceduralModel_Debris()
            model = ProceduralModels.ProceduralModel_Asteroid()
        return super().setModel(model)
    
    def handleNewCampaignTurn(self):
        #TODO: Instead of checking this in the turn of team -1 it should be checked after harvesting resources
        #       but I am currently hesitant to implement that in the harvesting method as this could lead to a whole bunch of Problems later on
        #       so, for the moment, I am going to leave the code for that here as this is, while not the prettiest from the players perspective
        #       at least completely future-proof and robust
        super().handleNewCampaignTurn()
        if not bool(self.ResourceManager.storedResources()):
            self.destroy()
