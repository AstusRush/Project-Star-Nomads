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
from Environment import EnvironmentalObjects
from Environment import EnvironmentalObjectGroups
from Economy import HarvestableObjects

class _EnvironmentCreator(): #TODO: Clusters should scale with map-size
    ClusterNumberMin = 6
    ClusterNumberMax = 40
    ClusterTypes:'list[type[_ClusterType]]' = None
    def __init__(self) -> None:
        pass#self.ClusterTypes = []
    
    def generate(self, hexGrid:HexBase.HexGrid, combat:bool):
        if not self.ClusterTypes: raise Exception("No cluster types were given")
        clusterTotal = random.choice(range(self.ClusterNumberMin, self.ClusterNumberMax+1))
        for clusterNum in range(clusterTotal):
            for _ in range(20):
                clusterCentre = random.choice(random.choice(hexGrid.Hexes))
                if not clusterCentre.fleet: break
            if clusterCentre.fleet: continue
            self._createCluster(clusterCentre, combat, clusterTotal, clusterNum)
    
    def _createCluster(self, clusterCentre:HexBase._Hex, combat:bool, clusterTotal, clusterNum):
        #TODO: It is currently possible that fleets are completely blocked in by obstacles. There needs to be a check that ensures that all tiles are reachable
        clusterType:'_ClusterType' = random.choice(self.ClusterTypes)()
        currentHex = clusterCentre
        entityTotal = clusterType.getClusterSize()
        for entityNum in range(entityTotal):
            #TODO: Use https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QProgressDialog.html#PySide2.QtWidgets.PySide2.QtWidgets.QProgressDialog
            get.window().Statusbar.showMessage(f"Generating entity {entityNum}/{entityTotal} for environment cluster {clusterNum}/{clusterTotal}")
            App().processEvents()
            object = clusterType.getObjectType()()
            if not combat: objectGroup = EnvironmentalObjectGroups.EnvironmentalObjectGroup_Campaign()
            else: objectGroup = EnvironmentalObjectGroups.EnvironmentalObjectGroup_Battle()
            objectGroup.Name = object.Name
            objectGroup.addShip(object)
            objectGroup.moveToHex(currentHex, False)
            nextHexCandidates:'list[HexBase._Hex]' = currentHex.getNeighbour()
            random.shuffle(nextHexCandidates)
            for candidate in nextHexCandidates:
                if not candidate.fleet: break
            if candidate.fleet: break
            currentHex = candidate


class EnvironmentCreator_Battle(_EnvironmentCreator):
    ClusterNumberMin = 6
    ClusterNumberMax = 40
    ClusterTypes:'list[type[_ClusterType]]' = None
    def __init__(self) -> None:
        self.ClusterTypes = [ClusterType_Asteroid_S, ClusterType_Asteroid_M, ClusterType_Asteroid_L]


class EnvironmentCreator_Sector(_EnvironmentCreator):
    ClusterNumberMin = 6
    ClusterNumberMax = 40
    ClusterTypes:'list[type[_ClusterType]]' = None
    def __init__(self) -> None:
        self.ClusterTypes = [ClusterType_Asteroid_S, ClusterType_Asteroid_M, ClusterType_AsteroidHarvestable]


class _ClusterType:
    ClusterSizeMin = 3
    ClusterSizeMax = 20
    ObjectTypes:'list[type[EnvironmentalObjects.EnvironmentalObject]]' = None
    
    def getClusterSize(self):
        return random.randint(self.ClusterSizeMin, self.ClusterSizeMax)
    
    def getObjectType(self) -> 'type[EnvironmentalObjects.EnvironmentalObject]':
        return random.choice(self.ObjectTypes)

class ClusterType_Asteroid(_ClusterType):
    ClusterSizeMin = 3
    ClusterSizeMax = 20
    ObjectTypes:'list[type[EnvironmentalObjects.EnvironmentalObject]]' = None
    def __init__(self) -> None:
        self.ObjectTypes = [EnvironmentalObjects.Asteroid]

class ClusterType_Asteroid_S(ClusterType_Asteroid):
    ClusterSizeMin = 3
    ClusterSizeMax = 6

class ClusterType_Asteroid_M(ClusterType_Asteroid):
    ClusterSizeMin = 6
    ClusterSizeMax = 10

class ClusterType_Asteroid_L(ClusterType_Asteroid):
    ClusterSizeMin = 10
    ClusterSizeMax = 20

class ClusterType_Asteroid_XL(ClusterType_Asteroid):
    ClusterSizeMin = 15
    ClusterSizeMax = 25

class ClusterType_AsteroidHarvestable(_ClusterType):
    ClusterSizeMin = 3
    ClusterSizeMax = 10
    ObjectTypes:'list[type[EnvironmentalObjects.EnvironmentalObject]]' = None
    def __init__(self) -> None:
        self.ObjectTypes = [EnvironmentalObjects.Asteroid, HarvestableObjects.ResourceAsteroid]
