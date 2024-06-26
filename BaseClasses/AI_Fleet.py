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
from BaseClasses import get
from BaseClasses import HexBase
from BaseClasses import AI_Base
if TYPE_CHECKING:
    from BaseClasses import ShipBase
    from BaseClasses import FleetBase
    from BaseClasses import UnitManagerBase
    from BaseClasses import AI_Player

class BaseFleetAI(AI_Base.AI_Base):
    def __init__(self, fleet:'FleetBase.FleetBase') -> None:
        super().__init__()
        self.fleet = weakref.ref(fleet)
    
    def getRandomReachableHex(self) -> HexBase._Hex: #CRITICAL: What happens if we find none?! This currently happens rarely but it is still bad! Do I handle this case correctly now?
        if hexes:=list(self.fleet().getReachableHexes()):
            return random.choice(hexes)
        else:
            NC(4,"Could not find a hex to move to!",tb=True,input=f"Fleet:\n{self.fleet()}\n\nHex:\n{self.fleet().hex()}\n\nReachable:\n{self.fleet().getReachableHexes()}\n\nAdjacent:\n{self.fleet().hex().getNeighbour()}")
            return self.fleet().hex()

class FleetAI(BaseFleetAI):
    fleet:'weakref.ref[FleetBase.Fleet]' = None
    
    async def executeTurn(self, orders:AI_Base.Orders):
        if self.fleet().isDestroyed(): return
        attackableHexes:typing.List[HexBase._Hex] = []
        moved, isClose = False, False
        onlyPlayer = get.unitManager().isHostile(self.fleet().Team,1) and not any([(i.fleet().Team == 1) for i in self.fleet().hex().getDisk(8) if i.fleet])
        if (closestEnemy:=self.fleet().findClosestEnemy(onlyPlayer=onlyPlayer, shareIntel=bool(random.randint(0,2)))):
            isClose, moved = self.fleet().moveClose(closestEnemy.hex(), 1)
            if get.engine().DebugPrintsEnabled: print(f"{self.fleet().Name} tries to move to a close enemy {isClose=} {moved=}")
            if not isClose and (closestEnemy:=self.fleet().findClosestEnemy(onlyPlayer=onlyPlayer, shareIntel=bool(random.randint(0,2)))):
                isClose, moved = self.fleet().moveClose(closestEnemy.hex(), 5)
                if get.engine().DebugPrintsEnabled: print(f"{self.fleet().Name} tries to move to a close enemy {isClose=} {moved=}")
        if self.fleet().MovePoints >= 1 and not moved and (not isClose or (closestEnemy and closestEnemy.Team != 1)):
            for _ in range(6):
                destinationHex = self.getRandomReachableHex()
                if attackableHexes := self.getAttackableHexes(destinationHex, orders) :
                    break
            self.fleet().moveTo_AI(destinationHex)
        return
        #TODO: This would currently break everything as the UnitManager can not pause to wait for a battle to conclude...
        #       I am uncertain in general as to how to handle this... But at least the code exists in some form for when I am ready
        if attackableHexes:
            attackHex = random.choice(attackableHexes)
            await self.fleet().attack(attackHex, orders)
    
    def getAttackableHexes(self, destinationHex:HexBase._Hex, orders:AI_Base.Orders) -> typing.List[HexBase._Hex]:
        # The following might look a bit confusing... We try to land next to a hostile fleet to attack it
        attackableHexes:typing.List[HexBase._Hex] = [i for i in list(destinationHex.getNeighbour()) if i.fleet]
        attackableHexes:typing.List[HexBase._Hex] = [get.unitManager().isHostile(self.fleet().Team, i.fleet().Team) for i in attackableHexes]
        return attackableHexes

class FlotillaAI(BaseFleetAI):
    fleet:'weakref.ref[FleetBase.Flotilla]' = None
    
    async def executeTurn(self, orders:AI_Base.Orders):
        if self.fleet().isDestroyed(): return
        #TODO: The next line should only be activated once the attack-method waits for the attack-animation to end before returning
        #if attackableHexes := self.getAttackableHexes(self.fleet().hex(), orders): await self.fleet().attack(random.choice(attackableHexes), orders) #TODO: This should be randomized but it should always trigger when fleeing
        #TODO: if multiple ships in the fleet are heavily damaged we should try to flee and try to seek help
        if orders["movement strategy"] == "formation" and orders["formation leader"] is not self.fleet():
            isClose, moved = self.fleet().moveClose(orders["formation leader"].hex(), self.fleet().MovePoints_max)
        attackableHexes:typing.List[HexBase._Hex] = self.getAttackableHexes(self.fleet().hex(), orders)
        if self.fleet().MovePoints >= 1:
            destinationHex = self.getMovementCandidate(orders)
            attackableHexes = self.getAttackableHexes(destinationHex, orders)
            if orders["aggressive"] and not attackableHexes and (closestEnemy:=self.fleet().findClosestEnemy()):
                # If we can not find anything to attack we should try to move in the direction of the closest (detectable (in the future)) enemy
                isClose, moved = self.fleet().moveClose(closestEnemy.hex(), self.fleet().getAttackRange()[0])
                if get.engine().DebugPrintsEnabled: print(f"{self.fleet().Name} tries to move to a close enemy {isClose=} {moved=}")
                attackableHexes = self.getAttackableHexes(self.fleet().hex(), orders)
            else:
                self.fleet().moveTo_AI(destinationHex)
        if attackableHexes:
            attackHex = random.choice(attackableHexes)
            await self.fleet().attack(attackHex, orders)
    
    def getMovementCandidate(self, orders:AI_Base.Orders) -> HexBase._Hex:
        for _ in range(6):
            destinationHex = self.getRandomReachableHex() #TODO: we can surly do better than random can't we?
            if attackableHexes := self.getAttackableHexes(destinationHex, orders):
                break
        return destinationHex
    
    def getAttackableHexes(self, destinationHex:HexBase._Hex, orders:AI_Base.Orders) -> typing.List[HexBase._Hex]:
        return list(self.fleet().getAttackableHexes(destinationHex))
