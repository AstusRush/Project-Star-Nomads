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
from BaseClasses.ShipBase import ShipBase
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

IMP_ENVOBJGR = [("PSN get","from BaseClasses import get"),("PSN FleetBase","from BaseClasses import FleetBase"),("PSN EnvironmentalObjectGroups","from Environment import EnvironmentalObjectGroups")]
IMP_ENVOBJGRCAMP = IMP_ENVOBJGR + [("PSN EnvironmentalFleetConstructor","""
def createEnvironmentalFleet(d:dict):
    fleet = EnvironmentalObjectGroups.EnvironmentalObjectGroup_Campaign(d["Team"])
    fleet.Name = d["Name"]
    fleet.addShips(d["Ships"])
    fleet.moveToHex(get.hexGrid().getHex(d["Coordinates"]), False)
    
    return fleet
""")]

class EnvironmentalObjectGroup_Campaign(FleetBase.Fleet):
    def __init__(self, team=-1) -> None:
        super().__init__(team)
    
    def arrangeShips(self):
        super().arrangeShips()
        if self.ResourceManager.storedResources():
            self.TeamRing.show()
    
    def tocode_AGeLib(self, name="", indent=0, indentstr="    ", ignoreNotImplemented = False) -> typing.Tuple[str,dict]:
        ret, imp = "", {}
        # ret is the ship data that calls a function which is stored as an entry in imp which constructs the ship
        # Thus, ret, when executed, will be this ship. This can then be nested in a list so that we can reproduce entire fleets.
        imp.update(IMP_ENVOBJGRCAMP)
        ret = indentstr*indent
        if name:
            ret += name + " = "
        ret += f"createEnvironmentalFleet(\n"
        r,i = AGeToPy._topy(self.tocode_AGeLib_GetDict(), indent=indent+2, indentstr=indentstr, ignoreNotImplemented=ignoreNotImplemented)
        ret += f"{r}\n{indentstr*(indent+1)})"
        imp.update(i)
        return ret, imp

class EnvironmentalObjectGroup_Battle(FleetBase.Flotilla):
    def __init__(self, team=-1) -> None:
        super().__init__(team)
