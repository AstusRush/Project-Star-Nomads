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
        self.CurrentTurnOfTeam = 1
        self.CurrentlyHandlingTurn = False
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
        self.Units_Environmental._name = "The Universe"
        self.Units_Neutral._name = "The Neutrals"
        self.Units_Team1._name = "The Star Nomads"
        self.Units_Team2._name = "The Buccaneers"
        self.Units_Team3._name = "The Star Raiders"
        for teamID, team in self.Teams.items():
            team.ID = teamID
            if teamID > 1:
                team.AI = AI_Player.PlayerAI_Campaign(team) if self.Strategic else AI_Player.PlayerAI_Combat(team)
        self.selectedUnit: 'weakref.ref[FleetBase.FleetBase]' = None
    
    def destroy(self):
        self.unselectAll()
        for team in list(self.Teams.values()):
            team.destroy()
    
    def unselectAll(self):
        if self.selectedUnit:
            self.selectedUnit().unselect()
            self.selectedUnit = None
    
    def selectUnit(self, fleet):
        if isinstance(fleet, weakref.ref):
            fleet = fleet()
        if self.selectedUnit:
            if self.selectedUnit() is fleet:
                self.selectedUnit().highlightRanges(True)
            elif not fleet and self.selectedUnit().IsMoving:
                self.selectedUnit().IsMoving = False
            else:
                self.selectedUnit().unselect()
                self.selectedUnit = None
        elif fleet:
            self.selectedUnit =  weakref.ref(fleet)
            self.selectedUnit().select()
    
    def isSelectedUnit(self, unit):
        if isinstance(self.selectedUnit, weakref.ref):
            if isinstance(unit, weakref.ref):
                unit = unit()
            return unit is self.selectedUnit()
        else:
            return False
    
    def isCurrentTurnOfTeam(self, team:int) -> bool:
        return self.CurrentTurnOfTeam == team
    
    def endTurn(self):
        if not self.CurrentlyHandlingTurn:
            self.CurrentlyHandlingTurn = True
            NC(10,"Processing AI turns", log=False)
            base().taskMgr.add(self._endTurn())
        else:
            NC(10,"Please wait...", log=False)
    
    async def _endTurn(self):
        "Ends the player turn, processes all other turns and returns control back to the player"
        try: self.Units_Team1.endTurn()
        except: NC(1,f"Could not fully execute `self.Units_Team1.endTurn()`. This might lead to instability.",exc=True)
        
        for teamID, team in self.Teams.items():
            if teamID != 1: # Team 1 is the Player
                self.CurrentTurnOfTeam = teamID
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
        await self._endTurn_handleOther()
    
    async def _endTurn_handleOther(self):
        await self._endTurn_startPlayerTurn()
    
    async def _endTurn_startPlayerTurn(self):
        self._Fleets_that_need_combat_handling = []
        self.CurrentTurnOfTeam = 1
        try: await self.Units_Team1.startTurn()
        except: NC(1,f"Could not fully execute `await self.Units_Team1.startTurn()`. This might lead to instability.",exc=True)
        if self.selectedUnit:
            self.selectedUnit().highlightRanges(False)
            self.selectedUnit().highlightRanges(True)
            self.selectedUnit().displayStats(True)
        self.checkAndHandleTeamDefeat()
        self.CurrentlyHandlingTurn = False
        print("Start of player turn")
        NC(10,"New turn has started", log=False)
        get.app().S_NewTurnStarted.emit()
    
    def checkAndHandleTeamDefeat(self):
        pass
    
    def isAllied(self, team1:int, team2:int) -> bool:
        return team2 in self.getAllies(team1)
    
    def isHostile(self, team1:int, team2:int) -> bool:
        return not self.isAllied(team1,team2) and not team1 == -1 and not team2 == -1
    
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
    
    def value(self, adj=False) -> float:
        """
        Returns the sum of all the value of all ships of this team.\n
        If adj is True and this is the player team 20 will be deducted from the return value to adjust for the initial construction module.
        This is used to adjust the spawning behaviour of enemies to not wipe out the player o game start.
        """
        if adj and self.ID == 1: return sum([i.value() for i in self]) - 24
        return sum([i.value() for i in self])
    
    def threat(self) -> float:
        return sum([i.threat() for i in self])


class CampaignUnitManager(UnitManager):
    Strategic = True
    Teams:'dict[int,UnitList[FleetBase.Fleet]]' = None #This is not understood by the linter... how can we make it understand?
    
    def checkAndHandleTeamDefeat(self):
        if self.Teams[1].numberOfShips() == 0:
            NC(1,"You have lost!",DplStr="You have lost!")
    
    async def _endTurn_handleOther(self):
        await self._endTurn_prepareAICombat()
    
    async def _endTurn_prepareAICombat(self):
        self._Fleets_that_need_combat_handling:'list[FleetBase.Fleet]' = []
        for teamID, team in self.Teams.items():
            if teamID == 1: continue
            for fleet in team:
                if fleet.getAttackableHexes():
                    self._Fleets_that_need_combat_handling.append(fleet)
        await self._endTurn_handleAICombat()
    
    async def _endTurn_handleAICombat(self):
        print("_endTurn_handleAICombat")
        self._Fleets_that_need_combat_handling:'list[FleetBase.Fleet]' = [i for i in self._Fleets_that_need_combat_handling if not i.isDestroyed()]
        if not self._Fleets_that_need_combat_handling:
            print("player turn")
            await self._endTurn_startPlayerTurn()
        else:
            attackingFleet = random.choice(self._Fleets_that_need_combat_handling)
            self._Fleets_that_need_combat_handling.remove(attackingFleet)
            targetOptions:'list[FleetBase.Fleet]' = []
            for i in attackingFleet.getAttackableHexes():
                if any([i.Team == 1 for i in attackingFleet.getInvolvedFleetsForPotentialBattle(attackingFleet.hex(),i)]):
                    targetOptions.append(i)
            if targetOptions:
                target = random.choice(targetOptions)
                await attackingFleet.attack(target, performOutOfTurn=True)
            else:
                await self._endTurn_handleAICombat()

class CombatUnitManager(UnitManager):
    Strategic = False
    Teams:'dict[int,UnitList[FleetBase.Flotilla]]' = None #This is not understood by the linter... how can we make it understand?
    
    def checkAndHandleTeamDefeat(self):
        if self.Teams[1].numberOfShips() == 0 or sum([v.numberOfShips() for k,v in self.Teams.items() if k > 1 and self.isHostile(1,k)]) == 0:
            get.engine().endBattleScene()
            return
