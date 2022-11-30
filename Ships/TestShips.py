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

ALL_PROCEDURAL = True

class NomadOne(ShipBase.Ship):
    Name = "Nomad One"
    ClassName = "Arc Ship"
    def __init__(self, generateModel=True) -> None:
        super().__init__()
        self.addModule(ShipModules.TestModules.TestHull_XL())
        self.addModule(ShipModules.TestModules.TestSensors_M())
        self.addModule(ShipModules.TestModules.TestEngine_XL())
        self.addModule(ShipModules.TestModules.TestThruster_XL())
        self.addModule(ShipModules.BaseModules.MicroJumpDrive()) #TODO: Should be from TestModules not from BaseModules. But only once it works
        self.addModule(ShipModules.TestModules.TestConstructionModule())
        self.addModule(ShipModules.TestModules.TestBeam_L())
        self.addModule(ShipModules.TestModules.TestBeam_L())
        self.addModule(ShipModules.TestModules.TestShield_L())
        self.addModule(ShipModules.TestModules.TestShield_M())
        if generateModel:
            self.generateProceduralModel()

class EnterpriseModel(ModelBase.ShipModel):
    ModelPath = "tempModels/NCC-1701-D.gltf"
    IconPath = "tempModels/Icons/gbfgalaxy.tga"
    def resetModel(self):
        self.Model.setHpr(0,0,0)
        self.Model.setPos(0,0,0)
        self.Model.setScale(1)
        self.Model.setH(180)
        self.Model.setP(90)
    
    def centreModel(self):
        self.resetModel()
        self.setScale(0.8/self.Model.getBounds().getRadius())
        self.Model.setPos(-self.Model.getBounds().getApproxCenter())

class Enterprise(ShipBase.Ship):
    Name = "Enterprise"
    ClassName = "Galaxy Class"
    def __init__(self, generateModel=True) -> None:
        super().__init__()
        if generateModel and not ALL_PROCEDURAL:
            self.setModel(EnterpriseModel())
        self.addModule(ShipModules.TestModules.TestHull_M())
        self.addModule(ShipModules.TestModules.TestSensors_M())
        self.addModule(ShipModules.TestModules.TestShield_L())
        self.addModule(ShipModules.TestModules.TestShield_M())
        self.addModule(ShipModules.TestModules.TestShield_S())
        self.addModule(ShipModules.TestModules.TestBeam_S())
        self.addModule(ShipModules.TestModules.TestBeam_S())
        self.addModule(ShipModules.TestModules.TestBeam_S())
        self.addModule(ShipModules.TestModules.TestBeam_S())
        self.addModule(ShipModules.TestModules.TestEngine_M())
        self.addModule(ShipModules.TestModules.TestThruster_M())
        if generateModel and ALL_PROCEDURAL:
            self.generateProceduralModel()

class PrometheusModel(ModelBase.ShipModel):
    ModelPath = "tempModels/Prometheus NX 59650/prometheus.obj"
    IconPath = "tempModels/Prometheus NX 59650/Prometheus1.jpg"
    def resetModel(self):
        self.Model.setHpr(0,0,0)
        self.Model.setPos(0,0,0)
        self.Model.setScale(1)
        self.Model.setP(90)
    
    def centreModel(self):
        self.resetModel()
        self.setScale(0.8/self.Model.getBounds().getRadius())
        self.Model.setPos(-self.Model.getBounds().getApproxCenter())

class Prometheus(ShipBase.Ship):
    Name = "Prometheus"
    ClassName = "Prometheus Class"
    def __init__(self, generateModel=True) -> None:
        super().__init__()
        if generateModel and not ALL_PROCEDURAL:
            self.setModel(PrometheusModel())
        self.addModule(ShipModules.TestModules.TestHull_M())
        self.addModule(ShipModules.TestModules.TestSensors_M())
        self.addModule(ShipModules.TestModules.TestShield_L())
        self.addModule(ShipModules.TestModules.TestShield_M())
        self.addModule(ShipModules.TestModules.TestBeam_M())
        self.addModule(ShipModules.TestModules.TestBeam_M())
        self.addModule(ShipModules.TestModules.TestEngine_L())
        self.addModule(ShipModules.TestModules.TestThruster_L())
        if generateModel and ALL_PROCEDURAL:
            self.generateProceduralModel()

class SpaceDockModel(ModelBase.ShipModel):
    ModelPath = "tempModels/SpaceDockNar30974/spacedock.obj"
    IconPath = "tempModels/SpaceDockNar30974/dock3.jpg"
    def resetModel(self):
        self.Model.setHpr(0,0,0)
        self.Model.setPos(0,0,0)
        self.Model.setScale(1)
        self.Model.setP(90)
    
    def centreModel(self):
        self.resetModel()
        self.setScale(0.8/self.Model.getBounds().getRadius())
        self.Model.setPos(-self.Model.getBounds().getApproxCenter())

class SpaceDock(ShipBase.Ship):
    Name = "Space Dock"
    ClassName = "SpaceDock Class"
    def __init__(self, generateModel=True) -> None:
        super().__init__()
        if generateModel and not ALL_PROCEDURAL:
            self.setModel(SpaceDockModel())
        self.addModule(ShipModules.TestModules.TestHull_M())
        self.addModule(ShipModules.TestModules.TestSensors_M())
        self.addModule(ShipModules.TestModules.TestShield_L())
        self.addModule(ShipModules.TestModules.TestBeam_M())
        self.addModule(ShipModules.TestModules.TestEngine_L())
        self.addModule(ShipModules.TestModules.TestThruster_L())
        self.addModule(ShipModules.TestModules.TestConstructionModule())
        if generateModel and ALL_PROCEDURAL:
            self.generateProceduralModel()




class TestModel(ModelBase.ShipModel):
    """
    The model should be a .obj created with blender with z facing up and x facing front\n
    If created as .dltf use `gltf2bam SingleAsteroidTest.gltf SingleAsteroidTest.bam` to convert it (adjust names as necessary) (orientation to be determined)\n
    """
    ModelPath = "tempModels/TestStuff/TestConeFacingX.obj"
    #ModelPath = "tempModels/TestStuff/SingleAsteroidTest.obj"
    #ModelPath = "tempModels/TestStuff/SingleAsteroidTest.bam" # gltf2bam SingleAsteroidTest.gltf SingleAsteroidTest.bam
    #IconPath = "tempModels/SpaceDockNar30974/dock3.jpg"

class TestShip(ShipBase.Ship):
    Name = "Test"
    ClassName = "Test Class"
    def __init__(self, generateModel=True) -> None:
        super().__init__()
        if generateModel:
            self.setModel(TestModel())
        self.addModule(ShipModules.TestModules.TestHull_M())
        self.addModule(ShipModules.TestModules.TestSensors_M())
        self.addModule(ShipModules.TestModules.TestShield_L())
        self.addModule(ShipModules.TestModules.TestBeam_M())
        self.addModule(ShipModules.TestModules.TestEngine_M())
        self.addModule(ShipModules.TestModules.TestThruster_M())



class ProceduralTestModel(ProceduralShips.ProceduralShip):
    #IconPath = "tempModels/SpaceDockNar30974/dock3.jpg"
    pass

class ProcTestShip(ShipBase.Ship):
    Name = "Proc Test"
    ClassName = "Proc Test Class"
    def __init__(self, generateModel=True) -> None:
        super().__init__()
        #if generateModel:
        #    self.setModel(ProceduralTestModel())
        self.addModule(ShipModules.TestModules.TestHull_M())
        self.addModule(ShipModules.TestModules.TestSensors_M())
        self.addModule(ShipModules.TestModules.TestShield_L())
        self.addModule(ShipModules.TestModules.TestShield_M())
        self.addModule(ShipModules.TestModules.TestBeam_M())
        self.addModule(ShipModules.TestModules.TestBeam_M())
        self.addModule(ShipModules.TestModules.TestBeam_M())#temp
        self.addModule(ShipModules.TestModules.TestBeam_M())#temp
        self.addModule(ShipModules.TestModules.TestEngine_L())
        self.addModule(ShipModules.TestModules.TestThruster_L())
        self.generateProceduralModel()

class ProceduralTestModel_Asteroid(ProceduralModels.ProceduralModel_Asteroid):
    #IconPath = "tempModels/SpaceDockNar30974/dock3.jpg"
    pass

class ProcTest_Asteroid(ShipBase.Ship):
    Name = "Proc Test Asteroid"
    ClassName = "Proc Test Asteroid Class"
    def __init__(self, generateModel=True) -> None:
        super().__init__()
        if generateModel:
            self.setModel(ProceduralTestModel_Asteroid())
        self.addModule(ShipModules.TestModules.TestHull_M())
        self.addModule(ShipModules.TestModules.TestSensors_M())
        self.addModule(ShipModules.TestModules.TestShield_L())
        self.addModule(ShipModules.TestModules.TestBeam_M())
        self.addModule(ShipModules.TestModules.TestEngine_M())
        self.addModule(ShipModules.TestModules.TestThruster_M())

