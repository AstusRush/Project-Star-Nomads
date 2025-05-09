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

class _EnvironmentCreator():
    ClusterNumberMin = 30
    ClusterNumberMax = 50
    ClusterTypes:'list[type[_ClusterType]]' = None
    def __init__(self) -> None:
        pass#self.ClusterTypes = []
    
    def generate(self, hexGrid:HexBase.HexGrid, combat:bool):
        if not self.ClusterTypes: raise Exception("No cluster types were given")
        clusterTotal = int(np.prod(hexGrid.Size)/(2500/random.randint(self.ClusterNumberMin, self.ClusterNumberMax+1)))
        edges = set(hexGrid.getEdgeHexes())
        #cancelText = None # If a string is given instead of None then a cancel button appears
        cancelText = "Abort Map Generation"
        with get.engine().interactionsDisabled(True):
            get.camera().resetCameraPosition()
            get.camera().zoomCameraFullyOut()
            pd = QtWidgets.QProgressDialog("Generating...", cancelText, 0, clusterTotal*10)
            pd.setWindowTitle("Generating Map...")
            pd.setWindowModality(QtCore.Qt.WindowModal)
            get.engine().processAndRender()
            for clusterNum in range(clusterTotal):
                for _ in range(20):
                    clusterCentre = random.choice(random.choice(hexGrid.Hexes))
                    if clusterCentre in edges: continue
                    if not (clusterCentre.fleet or clusterCentre.content): break
                if (clusterCentre.fleet or clusterCentre.content): continue
                self._createCluster(clusterCentre, combat, clusterTotal, clusterNum, np.prod(hexGrid.Size), edges, pd, updateBarForEachEntity=False)
                if pd.wasCanceled(): break
            get.engine().fastRender()
            pd.setValue(int(clusterTotal*10))
        if platform.system() == 'Windows':
            get.window().activateWindow() # ensures that wasd-navigation and other shortcuts work on windows after loading new map
            #VALIDATE: This might work but it is also possible that for wasd-navigation to work the panda3d window needs to get focus instead
    
    def _createCluster(self, clusterCentre:HexBase._Hex, combat:bool, clusterTotal, clusterNum, numHexes, edges, pd:QtWidgets.QProgressDialog, updateBarForEachEntity):
        """
        Creates a new cluster
        if updateBarForEachEntity is false it only updates the progressbar every 5 clusters for massively increased performance
        """
        #NOTE: updateBarForEachEntity should be False as otherwise rendering the new screen every time slows down the process way too much
        clusterType:'_ClusterType' = random.choice(self.ClusterTypes)()
        currentHex = clusterCentre
        entityTotal = clusterType.getClusterSize(numHexes)
        if not updateBarForEachEntity and (clusterNum%5==1):
            get.window().Statusbar.showMessage(f"Generating environment cluster {clusterNum+1}/{clusterTotal}")
            pd.setValue(int(clusterNum*10))
            pd.setLabelText(f"Generating environment cluster {clusterNum+1}/{clusterTotal}"+("        " if clusterNum==0 else ""))
            App().processEvents()
            get.engine().fastRender()
        for entityNum in range(entityTotal):
            #TODO: Use https://doc.qt.io/qtforpython-5/PySide2/QtWidgets/QProgressDialog.html#PySide2.QtWidgets.PySide2.QtWidgets.QProgressDialog
            if updateBarForEachEntity:
                get.window().Statusbar.showMessage(f"Generating entity {entityNum+1}/{entityTotal} for environment cluster {clusterNum+1}/{clusterTotal}")
                pd.setValue(int(clusterNum*10+(entityNum/entityTotal)*10))
                #NOTE: The if else in the next line ensures that the dialogue is a bit wider when it opens so that it does not snap wider for double digits etc
                pd.setLabelText(f"Generating entity {entityNum+1}/{entityTotal} for environment cluster {clusterNum+1}/{clusterTotal}"+("        " if clusterNum==0 and entityNum<2 else ""))
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
                if not (candidate.fleet or candidate.content) and not candidate in edges: break
            if (candidate.fleet or candidate.content) or candidate in edges: break
            currentHex = candidate
            if pd.wasCanceled(): break
            if updateBarForEachEntity: get.engine().fastRender()


class EnvironmentCreator_Battle(_EnvironmentCreator):
    #ClusterNumberMin = 12
    #ClusterNumberMax = 45
    ClusterTypes:'list[type[_ClusterType]]' = None
    def __init__(self) -> None:
        self.ClusterTypes = [ClusterType_Asteroid_S, ClusterType_Asteroid_M, ClusterType_Asteroid_L,ClusterType_Nebula,ClusterType_AsteroidAndNebula]


class EnvironmentCreator_Sector(_EnvironmentCreator):
    #ClusterNumberMin = 12
    #ClusterNumberMax = 45
    ClusterTypes:'list[type[_ClusterType]]' = None
    def __init__(self) -> None:
        self.ClusterTypes = [ClusterType_Asteroid_S, ClusterType_Asteroid_M, ClusterType_AsteroidHarvestable,ClusterType_Nebula,ClusterType_AsteroidAndNebula]


class _ClusterType:
    ClusterSizeMin = 3
    ClusterSizeMax = 20
    ObjectTypes:'list[type[EnvironmentalObjects.EnvironmentalObject]]' = None
    
    def getClusterSize(self, numHexes):
        #return max(int(self.ClusterSizeMin*0.75), int(numHexes/(2500/random.randint(self.ClusterSizeMin, self.ClusterSizeMax))) + 1)
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

class ClusterType_Nebula(_ClusterType):
    ClusterSizeMin = 3
    ClusterSizeMax = 20
    ObjectTypes:'list[type[EnvironmentalObjects.EnvironmentalObject]]' = None
    def __init__(self) -> None:
        self.ObjectTypes = [EnvironmentalObjects.Nebula_Movement]

class ClusterType_AsteroidAndNebula(_ClusterType):
    ClusterSizeMin = 3
    ClusterSizeMax = 20
    ObjectTypes:'list[type[EnvironmentalObjects.EnvironmentalObject]]' = None
    def __init__(self) -> None:
        self.ObjectTypes = [EnvironmentalObjects.Asteroid, EnvironmentalObjects.Nebula_Movement]


""" AGeIDE Code to experiment with the formulas for cluster
display()
for d in (200,500,1000,2000,2500):
	dpl("#",d,end="\n\n")
	for i in (25,35,50,75):
		
		s = (i,i)
		a =     int(np.prod(s)/(d/12 ) )
		a = (a, int(np.prod(s)/(d/45) ))
		
		dpl(i,a) # num clusters
		
		a =     int(np.prod(s)/(d/3) +1)
		a = (a, int(np.prod(s)/(d/20)+1 ))
		
		dpl(i,a) # size clusters
		dpl()
"""
