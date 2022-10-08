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
if TYPE_CHECKING:
    from BaseClasses import ShipBase
    from BaseClasses import FleetBase
    from BaseClasses import UnitManagerBase
from BaseClasses import get
from BaseClasses import HexBase

class PlayerAI():
    def __init__(self, unitList:'UnitManagerBase.UnitList') -> None:
        self.unitList = weakref.ref(unitList)
    
    async def executeTurn(self):
        for i in self.unitList():
            if i.isDestroyed(): continue
            for _ in range(6):
                destinationHex = random.choice(list(i.getReachableHexes()))
                if list(i.getAttackableHexes(destinationHex)):
                    break
            i.moveTo(destinationHex)
            attackHexList = list(i.getAttackableHexes())
            if attackHexList:
                attackHex = random.choice(attackHexList)
                await i.attack(attackHex)

class AI_Base():
    def __init__(self) -> None:
        pass
