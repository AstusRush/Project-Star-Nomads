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
import ShipModules

class EnterpriseModel(ModelBase.ShipModel):
    ModelPath = "tempModels/NCC-1701-D.gltf"
    IconPath = "tempModels/Icons/gbfgalaxy.tga"
    def resetModel(self):
        self.Model.setH(0) #TODO: Reset all rotations
        self.Model.setPos(0,0,0)
        self.Model.setScale(1)
        self.Model.setH(180)
        self.Model.setP(90)
    
    def centreModel(self):
        self.Model.setH(0)
        self.Model.setP(90)
        self.Model.setPos(0,0,0)
        self.Model.setScale(1)
        self.Model.setScale(0.8/self.Model.getBounds().getRadius())
        self.Model.setH(180)
        self.Model.setPos(-self.Model.getBounds().getApproxCenter())

class Enterprise(ShipBase.Ship):
    Name = "Enterprise"
    ClassName = "Galaxy Class"
    def __init__(self) -> None:
        super().__init__()
        self.Model = EnterpriseModel()
        self.setModel(self.Model)
        self.addModule(ShipModules.TestModules.TestHull_M(self))
        self.addModule(ShipModules.TestModules.TestSensors_M(self))
        self.addModule(ShipModules.TestModules.TestShield_L(self))
        self.addModule(ShipModules.TestModules.TestShield_M(self))
        self.addModule(ShipModules.TestModules.TestShield_S(self))
        self.addModule(ShipModules.TestModules.TestBeam_S(self))
        self.addModule(ShipModules.TestModules.TestBeam_S(self))
        self.addModule(ShipModules.TestModules.TestBeam_S(self))
        self.addModule(ShipModules.TestModules.TestBeam_S(self))
        self.addModule(ShipModules.TestModules.TestEngine_M(self))
        self.addModule(ShipModules.TestModules.TestThruster_M(self))

class PrometheusModel(ModelBase.ShipModel):
    ModelPath = "tempModels/Prometheus NX 59650/prometheus.obj"
    IconPath = "tempModels/Prometheus NX 59650/Prometheus1.jpg"
    def resetModel(self):
        self.Model.setH(0) #TODO: Reset all rotations
        self.Model.setPos(0,0,0)
        self.Model.setScale(1)
        self.Model.setP(90)
    
    def centreModel(self):
        self.Model.setH(0)
        self.Model.setP(90)
        self.Model.setPos(0,0,0)
        self.Model.setScale(1)
        self.Model.setScale(0.8/self.Model.getBounds().getRadius())
        self.Model.setPos(-self.Model.getBounds().getApproxCenter())

class Prometheus(ShipBase.Ship):
    Name = "Prometheus"
    ClassName = "Prometheus Class"
    def __init__(self) -> None:
        super().__init__()
        self.Model = PrometheusModel()
        self.setModel(self.Model)
        self.addModule(ShipModules.TestModules.TestHull_M(self))
        self.addModule(ShipModules.TestModules.TestSensors_M(self))
        self.addModule(ShipModules.TestModules.TestShield_L(self))
        self.addModule(ShipModules.TestModules.TestShield_M(self))
        self.addModule(ShipModules.TestModules.TestBeam_M(self))
        self.addModule(ShipModules.TestModules.TestBeam_M(self))
        self.addModule(ShipModules.TestModules.TestEngine_L(self))
        self.addModule(ShipModules.TestModules.TestThruster_L(self))

