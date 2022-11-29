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
from ProceduralGeneration import ProceduralModels

class EnvironmentCreator(): #TODO: Clusters should scale with map-size
    ClusterNumberMin = 6
    ClusterNumberMax = 40
    ClusterSizeMin = 3
    ClusterSizeMax = 20
    ObjectTypes:'list[type[EnvironmentalObject]]' = None
    def __init__(self) -> None:
        self.ObjectTypes = [Asteroid]
    
    def generate(self, hexGrid:HexBase.HexGrid, combat:bool):
        if not self.ObjectTypes: raise Exception("No object types were given")
        clusterTotal = random.choice(range(self.ClusterNumberMin, self.ClusterNumberMax+1))
        for clusterNum in range(clusterTotal):
            for _ in range(20):
                clusterCentre = random.choice(random.choice(hexGrid.Hexes))
                if not clusterCentre.fleet: break
            if clusterCentre.fleet: continue
            self._createCluster(clusterCentre, combat, clusterTotal, clusterNum)
    
    def _createCluster(self, clusterCentre:HexBase._Hex, combat:bool, clusterTotal, clusterNum):
        #TODO: It is currently possible that fleets are completely blocked in by obstacles. There needs to be a check that ensures that all tiles are reachable
        objectType = random.choice(self.ObjectTypes)
        currentHex = clusterCentre
        entityTotal = random.choice(range(self.ClusterSizeMin, self.ClusterSizeMax+1))
        for entityNum in range(entityTotal):
            get.window().Statusbar.showMessage(f"Generating entity {entityNum}/{entityTotal} for environment cluster {clusterNum}/{clusterTotal}")
            App().processEvents()
            object = objectType()
            if not combat: objectGroup = EnvironmentalObjectGroup_Campaign()
            else: objectGroup = EnvironmentalObjectGroup_Battle()
            objectGroup.addShip(object)
            objectGroup.moveToHex(currentHex, False)
            nextHexCandidates:'list[HexBase._Hex]' = currentHex.getNeighbour()
            random.shuffle(nextHexCandidates)
            for candidate in nextHexCandidates:
                if not candidate.fleet: break
            if candidate.fleet: break
            currentHex = candidate

class EnvironmentalObjectGroup_Campaign(FleetBase.Fleet):
    def __init__(self, team=-1) -> None:
        super().__init__(team)

class EnvironmentalObjectGroup_Battle(FleetBase.Flotilla):
    def __init__(self, team=-1) -> None:
        super().__init__(team)

class EnvironmentalObject(ShipBase.ShipBase):
    def __init__(self) -> None:
        super().__init__()

class AsteroidModel(ModelBase.EnvironmentalModel):
    """
    The model should be a .obj created with blender with z facing up and x facing front\n
    If created as .gltf use `gltf2bam SingleAsteroidTest.gltf SingleAsteroidTest.bam` to convert it (adjust names as necessary) (orientation to be determined)\n
    """
    #ModelPath = "tempModels/TestStuff/TestConeFacingX.obj"
    #ModelPath = "tempModels/TestStuff/SingleAsteroidTest.obj"
    ModelPath = "tempModels/TestStuff/SingleAsteroidTest.bam" # gltf2bam SingleAsteroidTest.gltf SingleAsteroidTest.bam
    #IconPath = "tempModels/SpaceDockNar30974/dock3.jpg"

class Asteroid(EnvironmentalObject):
    Name = "Asteroid"
    ClassName = "Asteroid"
    def __init__(self, generateModel=True) -> None:
        super().__init__()
        from BaseClasses import BaseModules
        if generateModel:
            #self.setModel(AsteroidModel())
            self.setModel(ProceduralModels.ProceduralModel_Asteroid())
            if not self.Model.CouldLoadModel and self.Model.Model: self.Model.Model.setColor(ape.colour(QtGui.QColor(0x6d4207)))
        self.addModule(BaseModules.Asteroid_Hull())
