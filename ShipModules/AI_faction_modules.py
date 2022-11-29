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

class Hull_S(BaseModules.Hull):
    Name = "Hull S"
    Evasion = 0.15
    HP_Hull_max = 45
    HP_Hull = HP_Hull_max
    HP_Hull_Regeneration = HP_Hull_max / 20
    NoticeableDamage = HP_Hull_max / 10

class Hull_M(BaseModules.Hull):
    Name = "Hull M"
    Evasion = 0.1
    HP_Hull_max = 100
    HP_Hull = HP_Hull_max
    HP_Hull_Regeneration = HP_Hull_max / 20
    NoticeableDamage = HP_Hull_max / 10

class Sensor_M(BaseModules.Sensor):
    Name = "Standard Sensor"
    LowRange = 16
    MediumRange = 8
    HighRange = 3
    PerfectRange = 1

class Shield_XS(BaseModules.Shield):
    Name = "Shield XS"
    HP_Shields_max = 75
    HP_Shields = HP_Shields_max
    HP_Shields_Regeneration = HP_Shields_max / 3

class Shield_S(BaseModules.Shield):
    Name = "Shield S"
    HP_Shields_max = 160
    HP_Shields = HP_Shields_max
    HP_Shields_Regeneration = HP_Shields_max / 4

class Shield_M(BaseModules.Shield):
    Name = "Shield M"
    HP_Shields_max = 240
    HP_Shields = HP_Shields_max
    HP_Shields_Regeneration = HP_Shields_max / 5

class Shield_L(BaseModules.Shield):
    Name = "Shield L"
    HP_Shields_max = 600
    HP_Shields = HP_Shields_max
    HP_Shields_Regeneration = HP_Shields_max / 6

class Shield_XL(BaseModules.Shield):
    Name = "Shield XL"
    HP_Shields_max = 1520
    HP_Shields = HP_Shields_max
    HP_Shields_Regeneration = HP_Shields_max / 8

class Beam_XXS(BaseModules.Weapon_Beam):
    Name = "Beam XXS"
    Damage = 15
    Accuracy = 0.85
    ShieldFactor = 1
    HullFactor = 1
    Range = 2

class Beam_XS(BaseModules.Weapon_Beam):
    Name = "Beam XS"
    Damage = 25
    Accuracy = 0.85
    ShieldFactor = 1
    HullFactor = 1
    Range = 2

class Beam_S(BaseModules.Weapon_Beam):
    Name = "Beam S"
    Damage = 50
    Accuracy = 0.85
    ShieldFactor = 1
    HullFactor = 1
    Range = 2

class Beam_M(BaseModules.Weapon_Beam):
    Name = "Beam M"
    Damage = 75
    Accuracy = 0.95
    ShieldFactor = 1
    HullFactor = 1
    Range = 2

class Beam_L(BaseModules.Weapon_Beam):
    Name = "Beam L"
    Damage = 120
    Accuracy = 1
    ShieldFactor = 1
    HullFactor = 1
    Range = 3

class Beam_XL(BaseModules.Weapon_Beam):
    Name = "Beam XL"
    Damage = 160
    Accuracy = 1
    ShieldFactor = 1
    HullFactor = 1
    Range = 4

class Beam_XXL(BaseModules.Weapon_Beam):
    Name = "Beam XXL"
    Damage = 240
    Accuracy = 0.9
    ShieldFactor = 1
    HullFactor = 1
    Range = 5

class Engine_S(BaseModules.Engine): # FTL Engine
    Name = "Engine S"
    Thrust = 14
    RemainingThrust = 14

#class Engine_M(BaseModules.Engine): # FTL Engine
#    Name = "Engine M"
#    Thrust = 20
#    RemainingThrust = 20

class Thruster_S(BaseModules.Thruster): # Sublight Thruster
    Name = "Thruster S"
    Thrust = 14
    RemainingThrust = 14

#class Thruster_M(BaseModules.Thruster): # Sublight Thruster
#    Name = "Thruster M"
#    Thrust = 20
#    RemainingThrust = 20
