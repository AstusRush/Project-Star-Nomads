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

from ApplicationClasses import Scene
from BaseClasses import HexBase, FleetBase, ShipBase, ModelBase, UnitManagerBase, get
from GUI import Windows, WidgetsBase

class EngineClass(ape.APE):
    def start(self):
        self.Scene:'Scene.CampaignScene' = None
        self.BattleScene:'Scene.BattleScene' = None
        self.UnitManager:'UnitManagerBase.UnitManager' = None
        self.BattleUnitManager:'UnitManagerBase.UnitManager' = None
        self.FleetsInBattle:typing.List[FleetBase.Fleet] = []
        self.base.start()
        self.startCampaignScene()
        self.CurrentlyInBattle = False
    
    def startCampaignScene(self):
        self.UnitManager = UnitManagerBase.UnitManager()
        self.Scene = Scene.CampaignScene()
        self.Scene.start()
    
    def startBattleScene(self, fleets:typing.List[FleetBase.Fleet]):
        if self.CurrentlyInBattle: raise Exception("A battle is already happening")
        self.CurrentlyInBattle = True
        self.UnitManager.unselectAll()
        self.FleetsInBattle = fleets
        self.Scene.pause()
        self.BattleUnitManager = UnitManagerBase.UnitManager()
        self.BattleScene = Scene.BattleScene()
        self.BattleScene.start()
        for fleet in fleets:
            flotilla = FleetBase.Flotilla(fleet.Team)
            flotilla.Name = f"Flotilla of {fleet.Name}"
            for ship in fleet.Ships:
                flotilla.addShip(ship)
            while True:
                hex_ = random.choice(random.choice(self.BattleScene.HexGrid.Hexes))
                if flotilla._navigable(hex_):
                    break
            flotilla.moveToHex(hex_,animate=False)
        self.BattleScene.Camera.moveToHex(random.choice(self.BattleUnitManager.Teams[1]).hex())
    
    def endBattleScene(self):
        self.BattleUnitManager.unselectAll()
        for fleet in self.FleetsInBattle:
            fleet.battleEnded()
        self.BattleUnitManager.destroy()
        self.BattleUnitManager = None
        self.BattleScene.end()
        self.BattleScene = None
        self.Scene.continue_()
        self.CurrentlyInBattle = False
    
    def getSceneRootNode(self):
        if self.BattleScene:
            return self.BattleScene.HexGrid.Root
        else:
            return self.Scene.HexGrid.Root
    
    def getHex(self, i:typing.Tuple[int,int]) -> 'HexBase._Hex':
        if self.BattleScene:
            return self.BattleScene.HexGrid.getHex(i)
        else:
            return self.Scene.HexGrid.getHex(i)
    
    def getUnitManager(self, campaign = None) -> 'UnitManagerBase.UnitManager':
        if campaign is None:
            campaign = not bool(self.BattleScene)
            
        return self.UnitManager if campaign else self.BattleUnitManager

class AppClass(ape.APEApp):
    pass
