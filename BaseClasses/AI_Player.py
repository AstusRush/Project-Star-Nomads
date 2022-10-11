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
from BaseClasses import AI_Base
from BaseClasses import AI_Fleet


class PlayerAI(AI_Base.AI_Base):
    def __init__(self, unitList:'UnitManagerBase.UnitList') -> None:
        self.unitList = weakref.ref(unitList)

class PlayerAI_Campaign(PlayerAI):
    
    async def executeTurn(self):
        return
        #TODO: This would currently break everything as the UnitManager can not pause to wait for a battle to conclude...
        #       I am uncertain in general as to how to handle this... But at least the code exists in some form for when I am ready
        orders = AI_Base.Orders()
        for i in self.unitList():
            await i.AI.executeTurn(orders)

class PlayerAI_Combat(PlayerAI):
    
    async def executeTurn(self):
        if self.unitList():
            orders = AI_Base.Orders()
            if self.unitList().ID is 2:
                orders["movement strategy"] = "formation"
                orders["formation leader"] = self.unitList()[0]
            orders["aggressive"] = True
            for i in self.unitList():
                await i.AI.executeTurn(orders)
