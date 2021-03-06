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
if TYPE_CHECKING:
    from BaseClasses import FleetBase
from BaseClasses import HexBase as Hex
from BaseClasses import get

class UnitManager():
    def __init__(self) -> None:
        self.Units_Environmental = UnitList()
        self.Units_Neutral = UnitList()
        self.Units_Team1 = UnitList()
        self.Units_Team2 = UnitList()
        self.Units_Team3 = UnitList()
        self.Teams = {
            -1 : self.Units_Environmental,
            0  : self.Units_Neutral,
            1  : self.Units_Team1,
            2  : self.Units_Team2,
            3  : self.Units_Team3,
        }
        self.selectedUnit: weakref.ref['FleetBase.FleetBase'] = None
        
    def selectUnit(self, unit):
        if isinstance(unit, weakref.ref):
            unit = unit()
        if not ( unit is self.selectedUnit ):
            if self.selectedUnit:
                self.selectedUnit().unselect()
                self.selectedUnit = None
            if unit:
                self.selectedUnit =  weakref.ref(unit)
                self.selectedUnit().select()
        
    def isSelectedUnit(self, unit):
        if isinstance(self.selectedUnit, weakref.ref):
            if isinstance(unit, weakref.ref):
                unit = unit()
            return unit is self.selectedUnit()
        else:
            return False
        
    def endTurn(self):
        "Ends the player turn, processes all other turns and returns control back to the player"
        self.Units_Team1.endTurn()
        
        self.Units_Team2.startTurn()
        self.Units_Team2.endTurn()
        self.Units_Team3.startTurn()
        self.Units_Team3.endTurn()
        self.Units_Environmental.startTurn()
        self.Units_Environmental.endTurn()
        self.Units_Neutral.startTurn()
        self.Units_Neutral.endTurn()
        
        self.Units_Team1.startTurn()
        if self.selectedUnit:
            self.selectedUnit().highlightRanges(False)
            self.selectedUnit().highlightRanges(True)
            self.selectedUnit().diplayStats(True)
    
class UnitList(typing.List['FleetBase.FleetBase']): 
    def append(self, unit):
        # type: (FleetBase.FleetBase) -> None
        if not unit in self:
            return super().append(unit)
    
    def startTurn(self):
        for i in self:
            i.startTurn()
    
    def endTurn(self):
        for i in self:
            i.endTurn()
            
    def __str__(self) -> str:
        return f"Unit list:\n\t"+"\n\t".join([str(i) for i in self])+"\n"
