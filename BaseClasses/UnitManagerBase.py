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
from BaseClasses import AI_Player

class UnitManager():
    Strategic:bool = False
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
        for teamID, team in self.Teams.items():
            team.ID = teamID
            if teamID > 1:
                team.AI = AI_Player.PlayerAI_Campaign(team) if self.Strategic else AI_Player.PlayerAI_Combat(team)
        self.selectedUnit: weakref.ref['FleetBase.FleetBase'] = None
    
    def destroy(self):
        self.unselectAll()
        for team in list(self.Teams.values()):
            team.destroy()
    
    def unselectAll(self):
        if self.selectedUnit:
            self.selectedUnit().unselect()
            self.selectedUnit = None
    
    def selectUnit(self, unit):
        if isinstance(unit, weakref.ref):
            unit = unit()
        if self.selectedUnit:
            if self.selectedUnit() is unit:
                self.selectedUnit().highlightRanges(True)
            elif not unit and self.selectedUnit().IsMoving:
                self.selectedUnit().IsMoving = False
            else:
                self.selectedUnit().unselect()
                self.selectedUnit = None
        elif unit:
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
        base().taskMgr.add(self._endTurn())
    
    async def _endTurn(self):
        "Ends the player turn, processes all other turns and returns control back to the player"
        try: self.Units_Team1.endTurn()
        except: NC(1,f"Could not fully execute `self.Units_Team1.endTurn()`. This might lead to instability.",exc=True)
        
        for teamID, team in self.Teams.items():
            if teamID != 1: # Team 1 is the Player
                try: await team.startTurn()
                except: NC(1,f"Could not fully handle the start of the Turn of {team.name()} ({teamID=}). This might lead to instability.",exc=True)
                try: team.endTurn()
                except: NC(1,f"Could not fully handle the start of the Turn of {team.name()} ({teamID=}). This might lead to instability.",exc=True)
        # try: await self.Units_Team2.startTurn()
        # except: NC(1,f"Could not fully execute `await self.Units_Team2.startTurn()`. This might lead to instability.",exc=True)
        # try: self.Units_Team2.endTurn()
        # except: NC(1,f"Could not fully execute `self.Units_Team2.endTurn()`. This might lead to instability.",exc=True)
        # try: await self.Units_Team3.startTurn()
        # except: NC(1,f"Could not fully execute `await self.Units_Team3.startTurn()`. This might lead to instability.",exc=True)
        # try: self.Units_Team3.endTurn()
        # except: NC(1,f"Could not fully execute `self.Units_Team3.endTurn()`. This might lead to instability.",exc=True)
        # try: await self.Units_Environmental.startTurn()
        # except: NC(1,f"Could not fully execute `await self.Units_Environmental.startTurn()`. This might lead to instability.",exc=True)
        # try: self.Units_Environmental.endTurn()
        # except: NC(1,f"Could not fully execute `self.Units_Environmental.endTurn()`. This might lead to instability.",exc=True)
        # try: await self.Units_Neutral.startTurn()
        # except: NC(1,f"Could not fully execute `await self.Units_Neutral.startTurn()`. This might lead to instability.",exc=True)
        # try: self.Units_Neutral.endTurn()
        # except: NC(1,f"Could not fully execute `self.Units_Neutral.endTurn()`. This might lead to instability.",exc=True)
        
        try: await self.Units_Team1.startTurn()
        except: NC(1,f"Could not fully execute `await self.Units_Team1.startTurn()`. This might lead to instability.",exc=True)
        if self.selectedUnit:
            self.selectedUnit().highlightRanges(False)
            self.selectedUnit().highlightRanges(True)
            self.selectedUnit().displayStats(True)
        self.checkAndHandleTeamDefeat()
    
    def checkAndHandleTeamDefeat(self):
        pass
    
    def isAllied(self, team1:int, team2:int) -> bool:
        return team2 in self.getAllies(team1)
    
    def getAllies(self, team:int) -> typing.List[int]:
        return [team,] #TODO: implement Alliances
    
class UnitList(typing.List['FleetBase.FleetBase']):
    AI:AI_Player.PlayerAI = None
    _name:str = ""
    ID:int = 0
    
    def name(self):
        if not self._name:
            return f"team {self.ID}"
        else:
            return self._name
    
    def append(self, unit):
        # type: (FleetBase.FleetBase) -> None
        if not unit in self:
            return super().append(unit)
    
    def destroy(self):
        #if hasattr(self, "AI"):
        #    del self.AI # raises attribute error...
        for i in self.copy():
            i.destroy()
        self.clear()
    
    async def startTurn(self):
        for i in self:
            i.startTurn()
        if self.AI:
            await self.AI.executeTurn()
    
    def endTurn(self):
        for i in self:
            i.endTurn()
    
    def __str__(self) -> str:
        return f"Unit list:\n\t"+"\n\t".join([str(i) for i in self])+"\n"
    
    def numberOfShips(self):
        return sum([len(fleet.Ships) for fleet in self])


class CampaignUnitManager(UnitManager):
    Strategic = True
    
    def checkAndHandleTeamDefeat(self):
        if self.Teams[1].numberOfShips() == 0:
            NC(1,"You have lost!",DplStr="You have lost!")

class CombatUnitManager(UnitManager):
    Strategic = False
    
    def checkAndHandleTeamDefeat(self):
        if self.Teams[1].numberOfShips() == 0 or sum([v.numberOfShips() for k,v in self.Teams.items() if k > 1 and not self.isAllied(1,k)]) == 0:
            get.engine().endBattleScene()
            return
