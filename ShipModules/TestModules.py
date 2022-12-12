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

class TestHull_M(BaseModules.Hull):
    Name = "TestHull_M"
    Evasion = 0.1
    HP_Hull_max = 100
    HP_Hull = HP_Hull_max
    HP_Hull_Regeneration = HP_Hull_max / 20
    NoticeableDamage = HP_Hull_max / 10

class TestHull_L(BaseModules.Hull):
    Name = "TestHull_L"
    Evasion = 0.05
    HP_Hull_max = 200
    HP_Hull = HP_Hull_max
    HP_Hull_Regeneration = HP_Hull_max / 20
    NoticeableDamage = HP_Hull_max / 10

class TestHull_XL(BaseModules.Hull):
    Name = "TestHull_XL"
    Evasion = 0.01
    HP_Hull_max = 400
    HP_Hull = HP_Hull_max
    HP_Hull_Regeneration = HP_Hull_max / 20
    NoticeableDamage = HP_Hull_max / 10

class TestSensors_M(BaseModules.Sensor):
    Name = "TestSensors_M"
    LowRange = 20
    MediumRange = 12
    HighRange = 4
    PerfectRange = 1

class TestShield_S(BaseModules.Shield):
    Name = "TestShield_S"
    HP_Shields_max = 200
    HP_Shields = HP_Shields_max
    HP_Shields_Regeneration = HP_Shields_max / 5

class TestShield_M(BaseModules.Shield):
    Name = "TestShield_M"
    HP_Shields_max = 400
    HP_Shields = HP_Shields_max
    HP_Shields_Regeneration = HP_Shields_max / 6

class TestShield_L(BaseModules.Shield):
    Name = "TestShield_L"
    HP_Shields_max = 800
    HP_Shields = HP_Shields_max
    HP_Shields_Regeneration = HP_Shields_max / 8

class TestBeam_S(BaseModules.Weapon_Beam):
    Name = "TestBeam_S"
    Damage = 30
    Accuracy = 1
    ShieldFactor = 1
    HullFactor = 1
    Range = 2

class TestBeam_M(BaseModules.Weapon_Beam):
    Name = "TestBeam_M"
    Damage = 75
    Accuracy = 1
    ShieldFactor = 1
    HullFactor = 1
    Range = 3

class TestBeam_L(BaseModules.Weapon_Beam):
    Name = "TestBeam_L"
    Damage = 100
    Accuracy = 1
    ShieldFactor = 1
    HullFactor = 1
    Range = 4

class TestEngine_M(BaseModules.Engine): # FTL Engine
    Name = "TestEngine_M"
    Thrust = 12
    RemainingThrust = 12

class TestEngine_L(BaseModules.Engine): # FTL Engine
    Name = "TestEngine_L"
    Thrust = 20
    RemainingThrust = 20

class TestEngine_XL(BaseModules.Engine): # FTL Engine
    Name = "TestEngine_XL"
    Thrust = 50
    RemainingThrust = 50

class TestThruster_M(BaseModules.Thruster): # Sublight Thruster
    Name = "TestThruster_M"
    Thrust = 12
    RemainingThrust = 12

class TestThruster_L(BaseModules.Thruster): # Sublight Thruster
    Name = "TestThruster_L"
    Thrust = 20
    RemainingThrust = 20

class TestThruster_XL(BaseModules.Thruster): # Sublight Thruster
    Name = "TestThruster_XL"
    Thrust = 50
    RemainingThrust = 50

class TestConstructionModule(BaseModules.ConstructionModule): # ConstructionModule
    Name = "TestConstructionModule"
