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
        print(f"Start of turn for {self.unitList().name()}")
        self.spawnFleets()
        orders = AI_Base.Orders()
        for i in self.unitList():
            await i.AI.executeTurn(orders)
    
    def spawnFleets(self):
        self.spawnFleets_Value()
    
    def spawnFleets_Value(self):
        if self.unitList().value() < get.unitManager().Teams[1].value(adj=True)*get.menu().DifficultyOptionsWidget.EnemyTotalStrength():
            fleet = self.createNewFleetInstance()
            while self.unitList().value() < get.unitManager().Teams[1].value(adj=True)*get.menu().DifficultyOptionsWidget.EnemyTotalStrength():
                if fleet.value() >= get.unitManager().Teams[1].value(adj=True)*get.menu().DifficultyOptionsWidget.EnemyStrengthPerFleet():
                    # New fleet once the old fleet gets quite big
                    # Do note that construction ships have quite a high value and we therefore need to be careful to not spawn too many enemies per fleet
                    fleet = self.createNewFleetInstance()
                ship:'ShipBase.Ship' = random.choice(self.getValidShipTypes())()
                ship.Name = ship.ClassName[0:-1]+str(random.randint(1000,9999))
                fleet.addShip(ship=ship)
    
    def createNewFleetInstance(self) -> 'FleetBase.Fleet':
        from BaseClasses import FleetBase
        fleet = FleetBase.Fleet(self.unitList().ID)
        fleet.Name = f"{self.unitList().name()} Fleet"
        while True:
            hexList = get.hexGrid(campaign=True).getEdgeHexes()
            hex_ = random.choice(hexList)
            if fleet._navigable(hex_):
                break
        fleet.moveToHex(hex_,animate=False)
        return fleet
    
    def getValidShipTypes(self) -> 'ShipBase.Ship':
        from Ships import AI_faction_ships
        l = []
        for _ in range(5): l.append(AI_faction_ships.AI_PatrolCraft_1)
        for _ in range(5): l.append(AI_faction_ships.AI_Corvette_1)
        for _ in range(4): l.append(AI_faction_ships.AI_Frigate_1)
        for _ in range(2): l.append(AI_faction_ships.AI_Frigate_LR_1)
        for _ in range(2): l.append(AI_faction_ships.AI_Frigate_H_1)
        return l
    
    def spawnFleets_NumShips(self):
        if self.unitList().ID > 1 and self.unitList().numberOfShips() < get.unitManager().Teams[1].numberOfShips():
            fleet = self.createNewFleetInstance()
            for i in range(6 if get.unitManager().Teams[1].numberOfShips() > 4 else 3):
                ship = get.shipClasses()["TestShips: Enterprise"]()
                ship.Name = f"{ship.Name} {i}"
                fleet.addShip(ship)

class PlayerAI_Combat(PlayerAI):
    
    async def executeTurn(self):
        if self.unitList():
            orders = AI_Base.Orders()
            if self.unitList().ID == 2:
                orders["movement strategy"] = "formation"
                orders["formation leader"] = self.unitList()[0]
            orders["aggressive"] = True
            for i in self.unitList():
                await i.AI.executeTurn(orders)
