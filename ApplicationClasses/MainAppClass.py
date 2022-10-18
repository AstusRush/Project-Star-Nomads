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
from BaseClasses import HexBase, FleetBase, ShipBase, ModelBase, BaseModules, UnitManagerBase, get
from GUI import Windows, WidgetsBase

class EngineClass(ape.APE):
    def start(self):
        self._NumHexGridsCampaign, self._NumHexGridsBattle = 0, 0
        self._HexToLookAtAfterBattle = (0,0)
        self.Scene:'Scene.CampaignScene' = None
        self.BattleScene:'Scene.BattleScene' = None
        self.UnitManager:'UnitManagerBase.CampaignUnitManager' = None
        self.BattleUnitManager:'UnitManagerBase.CombatUnitManager' = None
        self.FleetsInBattle:typing.List[FleetBase.Fleet] = []
        self.base.start()
        self.startCampaignScene()
        self.CurrentlyInBattle = False
    
    def startCampaignScene(self):
        self.UnitManager = UnitManagerBase.CampaignUnitManager()
        self.Scene = Scene.CampaignScene()
        self.Scene.start()
    
    def startBattleScene(self, fleets:typing.List[FleetBase.Fleet]):
        if self.CurrentlyInBattle: raise Exception("A battle is already happening")
        #TODO: What happens when no player fleet is involved?!
        #self._CameraPositionBeforeBattle = self.Scene.Camera.CameraCenter.getPos()
        self._HexToLookAtAfterBattle = fleets[0].hex().Coordinates
        self.setHexInteractionFunctions()
        self.CurrentlyInBattle = True
        self.UnitManager.unselectAll()
        self.FleetsInBattle = fleets
        self.Scene.pause()
        self.BattleUnitManager = UnitManagerBase.CombatUnitManager()
        self.BattleScene = Scene.BattleScene()
        self.BattleScene.start()
        for fleet in fleets:
            fleet_parts = self.splitFleetIntoFlotillas(fleet)
            for num, ships in enumerate(fleet_parts):
                flotilla = FleetBase.Flotilla(fleet.Team)
                flotilla.Name = f"Flotilla {num} of {fleet.Name}"
                for ship in ships:
                    flotilla.addShip(ship)
                while True:
                    #TODO: This should be a bit more structured
                    hex_ = random.choice(random.choice(self.BattleScene.HexGrid.Hexes))
                    if flotilla._navigable(hex_):
                        break
                flotilla.moveToHex(hex_,animate=False)
        self.BattleScene.Camera.moveToHex(random.choice(self.BattleUnitManager.Teams[1]).hex())
    
    def endBattleScene(self):
        self.BattleUnitManager.unselectAll()
        salvage = 0
        for fleet in self.FleetsInBattle:
            salvage += fleet.battleEnded()
        salvageMessage = self.distributeSalvage(salvage)
        self.BattleUnitManager.destroy()
        self.BattleUnitManager = None
        self.BattleScene.end()
        self.BattleScene = None
        self.Scene.continue_()
        self.CurrentlyInBattle = False
        #self.Scene.Camera.CameraCenter.setPos(self._CameraPositionBeforeBattle)
        self.Scene.Camera.moveToHex(self.getHex(self._HexToLookAtAfterBattle))
        NC(3, f"The battle has ended!\n{salvageMessage}") #TODO: Give more information about the battle
    
    def distributeSalvage(self, salvage:float) -> str:
        if salvage > 0:
            construction_modules:typing.List[BaseModules.ConstructionModule] = []
            for fleet in self.FleetsInBattle:
                if fleet.Team == 1 and not fleet.isDestroyed():
                    for ship in fleet.Ships:
                        for module in ship.Modules:
                            if isinstance(module,BaseModules.ConstructionModule):
                                construction_modules.append(module)
            if construction_modules:
                for i in construction_modules:
                    i.ConstructionResourcesStored += salvage/len(construction_modules)
                return f"Total salvage rewarded: {salvage}\nSalvage rewarded to each construction module: {salvage/len(construction_modules)}"
            else:
                return f"There were {salvage} units of salvage but no construction module to gather and store it."
        return "There was nothing to salvage..."
    
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
    
    def getHexGrid(self, campaign = None) -> 'HexBase.HexGrid':
        if campaign is None:
            campaign = not bool(self.BattleScene)
        return self.Scene.HexGrid if campaign else self.BattleScene.HexGrid
        # if self.BattleScene:
        #     return self.BattleScene.HexGrid
        # else:
        #     return self.Scene.HexGrid
    
    def getUnitManager(self, campaign = None) -> 'UnitManagerBase.UnitManager':
        if campaign is None:
            campaign = not bool(self.BattleScene)
        return self.UnitManager if campaign else self.BattleUnitManager
    
    def setHexInteractionFunctions(self,
                                    onLMB:   typing.Union[typing.Callable[['HexBase._Hex'],None],typing.Tuple[bool,bool]] = None,
                                    onRMB:   typing.Union[typing.Callable[['HexBase._Hex'],None],typing.Tuple[bool,bool]] = None,
                                    onHover: typing.Union[typing.Callable[['HexBase._Hex'],None],None] = None,
                                    onClear: typing.Union[typing.Callable[[None],None],None] = None,
                                    ):
        """
        This method is used to change the mouse interaction rules on the hex grid.\n
        onLMB and onRMB must be either `None` or a function that takes a hex and returns two bools.\n
        - The first bool decides whether the clicked hex should be selected afterwards.\n
        - The second bool decides whether the onLMB, onRMB, and onHover functions should all be set to `None` afterwards.\n
        onHover must be either `None` or a function that takes a hex. The return value of that function is currently not used but should be `None` in case a use-case arises in the future.\n
        If any of these parameters is none the corresponding function will be reset to the default behaviour.\n
        onClear is called when the hex interaction functions get reset.\n
        These functions also get reset when new functions are set via this method or when a different hex gets selected.
        """
        self.getHexGrid().clearInteractionFunctions
        self.getHexGrid().OnLMBDo = onLMB
        self.getHexGrid().OnRMBDo = onRMB
        self.getHexGrid().OnHoverDo = onHover
        self.getHexGrid().OnClearDo = onClear
    
    def splitFleetIntoFlotillas(self, fleet:'FleetBase.FleetBase') -> typing.List[typing.List['ShipBase.ShipBase']]:
        #TODO: It would be great if we were to group the ships according to their types and movement
        if fleet.Team != 1 and len(fleet.Ships) >= 6:
            sNum = len(fleet.Ships) // 3
            sRem = len(fleet.Ships) % 3
            ships = []
            for i in range(sNum):
                ships.append(fleet.Ships[i::sNum])
            for i in ships:
                for j in i:
                    if j not in fleet.Ships:
                        NC(1,"One ship would not be in the fleet.Ships!")
                        return [fleet.Ships]
            if sum([len(i) for i in ships]) != len(fleet.Ships):
                NC(3,"One ship would be in two flotillas!")
                return [fleet.Ships]
            return ships
        else:
            return [fleet.Ships]
    
    def _getNumOfGridsFormatted(self):
        return f"There have been a total of {self._NumHexGridsCampaign} campaign grids and {self._NumHexGridsBattle} battle grids since this application started."
    
    def _increaseAndGetNumOfGridsOfType(self, type_:str):
        if type_ == "Campaign":
            self._NumHexGridsCampaign += 1
            return self._NumHexGridsCampaign
        elif type_ == "Battle":
            self._NumHexGridsBattle += 1
            return self._NumHexGridsBattle
        else:
            raise Exception(f"{type_} is an unknown hex grid type! Only Campaign and Battle are valid options!")
    
    def save(self, name="LastSave"):
        #REMINDER: The name of the Save File must be not only a valid file name but also a valid python file name
        if self.CurrentlyInBattle:
            NC(2,"Currently, saving is only possible on the campaign map")
            return
        name += ".py"
        self._save(name)
    
    def _save(self, name="LastSave.py"):
        wd = os.path.dirname(__file__).rsplit(os.path.sep,1)[0]
        saveFolder = os.path.join(wd,"SavedGames")
        if not os.path.exists(saveFolder):
            os.mkdir(saveFolder)
        fleetList:UnitManagerBase.UnitList = []
        for team in self.getUnitManager().Teams.values():
            fleetList += team
        with open(os.path.join(saveFolder,name),"w") as file:
            file.write(AGeToPy.formatObject(fleetList))
        NC(3,f"Save successful! Saved at {os.path.join(saveFolder,name)}")
    
    def load(self):
        self.clearAll()
        from SavedGames import LastSave
    
    def clearAll(self):
        fleetList:UnitManagerBase.UnitList = []
        for team in self.getUnitManager().Teams.values():
            fleetList += team
        for i in fleetList:
            i.completelyDestroy()

class AppClass(ape.APEApp):
    pass
