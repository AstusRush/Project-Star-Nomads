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

class TestShield_L(BaseModules.Shield):
    Name = "TestShield_L"
    HP_Shields_max = 400
    HP_Shields = HP_Shields_max
    HP_Shields_Regeneration = HP_Shields_max / 8

class TestShield_S(BaseModules.Shield):
    Name = "TestShield_S"
    HP_Shields_max = 100
    HP_Shields = HP_Shields_max
    HP_Shields_Regeneration = HP_Shields_max / 8

class TestBeam_S(BaseModules.Weapon_Beam):
    Name = "TestBeam_S"
    Damage = 50
    Accuracy = 1
    ShieldFactor = 1
    HullFactor = 1