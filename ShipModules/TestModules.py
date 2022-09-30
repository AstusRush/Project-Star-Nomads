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

class TestHull_1(BaseModules.Hull):
    def __init__(self, ship:ShipBase.ShipBase) -> None:
        super().__init__(ship)
        self.Evasion = 0.1
        self.HP_Hull_max = 200
        self.HP_Hull = self.HP_Hull_max
        self.HP_Hull_Regeneration = self.HP_Hull_max / 20
        self.NoticeableDamage = self.HP_Hull_max / 10
    
    def handleNewTurn(self):
        self.healAtTurnStart()
    
    def healAtTurnStart(self):
        regenFactor = 1 if not self.ship().WasHitLastTurn else 0.5
        self.HP_Hull = min(self.HP_Hull + self.HP_Hull_Regeneration*regenFactor , self.HP_Hull_max)
