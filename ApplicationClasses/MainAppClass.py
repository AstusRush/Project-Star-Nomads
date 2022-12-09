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
import math
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

from ApplicationClasses import Scene, StarNomadsColourPalette
from BaseClasses import HexBase, FleetBase, ShipBase, ModelBase, BaseModules, UnitManagerBase, Environment, get
from GUI import BaseInfoWidgets, Windows

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
        
        self.newGame()
    
    def startCampaignScene(self):
        self.UnitManager = UnitManagerBase.CampaignUnitManager()
        self.Scene = Scene.CampaignScene()
        self.Scene.start()
    
    def startBattleScene(self, fleets:'list[FleetBase.Fleet]', battleType=0):
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
        self.transferFleetsToBattle(fleets, battleType)
        environmentCreator = Environment.EnvironmentCreator()
        environmentCreator.generate(self.BattleScene.HexGrid, combat=True)
        #self.BattleScene.Camera.moveToHex(random.choice(self.BattleUnitManager.Teams[1]).hex())
        self.BattleScene.Camera.focusRandomFleet(team=1)
    
    def transferFleetsToBattle(self, fleets:'list[FleetBase.Fleet]', battleType):
        for fleet in fleets:
            fleet_parts = self.splitFleetIntoFlotillas(fleet)
            for num, ships in enumerate(fleet_parts):
                flotilla = FleetBase.Flotilla(fleet.Team)
                flotilla.Name = f"Flotilla {num} of {fleet.Name}"
                for ship in ships:
                    flotilla.addShip(ship)
                self.placeFlotillaInBattle(flotilla, fleet, battleType)
    
    def placeFlotillaInBattle(self, flotilla:FleetBase.Flotilla, fleet:FleetBase.Fleet, battleType):
        #TODO: Implement battle types and have special positioning rules for things like ambushes or imprecise jump drives
        #MAYBE: It would be cool to have an FTL precision system without which ships jump to random positions
        #           and higher levels allow the player to pick initial positions and then maybe inhibitors that disallow the placement of ships right next to enemies...
        #           Well we are most certainly not at a point to make decisions about implementing that just yet.
        if 1 <= flotilla.Team <= 4:
            hexes = self.BattleScene.HexGrid.getCornerHexes(flotilla.Team-1,int(min(self.BattleScene.HexGrid.Size)/5))
            while True: #TODO: What happens if we can't place a flotilla? We need an abort condition and a way to handle it...
                #TODO: This should be derived from the fleet positions
                hex_ = random.choice(hexes)
                if flotilla._navigable(hex_):
                    break
        else:
            while True: #TODO: What happens if we can't place a flotilla? We need an abort condition and a way to handle it...
                hex_ = random.choice(random.choice(self.BattleScene.HexGrid.Hexes))
                if flotilla._navigable(hex_):
                    break
        flotilla.moveToHex(hex_,animate=False)
    
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
        NC(3, f"The battle has ended!\n{salvageMessage}", DplStr="Battle Ended") #TODO: Give more information about the battle
        if self.UnitManager.CurrentlyHandlingTurn:
            base().taskMgr.add(self.UnitManager._endTurn_handleAICombat())
    
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
    
    def getScene(self, campaign = None) -> 'Scene.BaseScene':
        if campaign is None:
            campaign = not bool(self.BattleScene)
        if campaign:
            return self.Scene
        else:
            return self.BattleScene
    
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
        #TODO: It would be great if we were to group the ships according to their types and movement ###DONE (at least the movement part) but would benefit from more fine-tuning
        try:
            #speedGroups = []
            #for ship in fleet.Ships:
            #    speed = math.floor(ship.Stats.Movement_Sublight[1])
            #    if speed not in speedGroups: speedGroups.append(speed)
            flotillasDict:'dict[int,list[ShipBase.ShipBase]]' = {}
            for ship in fleet.Ships:
                speed = math.floor(ship.Stats.Movement_Sublight[1])
                if speed not in flotillasDict: flotillasDict[speed] = [ship]
                else: flotillasDict[speed].append(ship)
            ships = list(flotillasDict.values())
            #TODO: Ensure that flotillas do not have more than 4 ships and separate them is necessary
        except:
            NC(2,"Could not split fleet into flotillas in the usual way. Splitting the ships by number instead.", exc=True)
            if fleet.Team != 1 and len(fleet.Ships) >= 6:
                sNum = len(fleet.Ships) // 3
                sRem = len(fleet.Ships) % 3
                ships = []
                for i in range(sNum):
                    ships.append(fleet.Ships[i::sNum])
            else:
                return [fleet.Ships.copy()]
        for i in ships:
            for j in i:
                if j not in fleet.Ships:
                    NC(2,"One ship would not be in the fleet.Ships! Putting all ships into one flotilla instead!", input=f"{fleet = }\n{fleet.Ships = }\n{ships = }")
                    return [fleet.Ships]
        if sum([len(i) for i in ships]) != len(fleet.Ships):
            NC(2,"One ship would be in two flotillas! Putting all ships into one flotilla instead!", input=f"{fleet = }\n{fleet.Ships = }\n{ships = }")
            return [fleet.Ships]
        return ships
    
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
            NC(2,"Currently, saving is only possible on the campaign map", DplStr="Could NOT Save!")
            return
        name += ".py"
        self._save(name)
    
    def _save(self, name="LastSave.py"):
        #TODO: This is not compressed enough and I don't know how to compress it more.
        #       (It certainly is far more compressible. I just haven't learned a better way to save this data than the wacky way I invented.
        #           Other game devs have way better ways to store that data. Don't judge me! This is my first game!)
        #       Therefore we need to save each fleet into its own file.
        #       This means that each saved game creates a folder filled with multiple files that all need to be executed (by loading the text and calling `exec` on it).
        #       Then we can also have other files that store other data like the tech tree.
        #TODO: Select a name for the save file
        wd = os.path.dirname(__file__).rsplit(os.path.sep,1)[0]
        saveFolder = os.path.join(wd,"SavedGames")
        if not os.path.exists(saveFolder):
            os.mkdir(saveFolder)
        fleetList:UnitManagerBase.UnitList = []
        for team in self.getUnitManager().Teams.values():
            fleetList += team
        with open(os.path.join(saveFolder,name),"w") as file:
            file.write(AGeToPy.formatObject(fleetList))
        NC(3,f"Save successful! Saved at {os.path.join(saveFolder,name)}", DplStr="Game Saved!")
    
    def load(self):
        if self._confirmNewOrLoad("loading"):
            #TODO: See _save
            #TODO: It would be neat to not have to restart the game every time one wants to load
            #TODO: Select a save file
            #TODO: It would be nice if the camera would zoom to an owned fleet or would even remember its position when the save was made
            if self.CurrentlyInBattle:
                NC(2,"Currently, loading is only possible on the campaign map")
                return
            self.clearAll()
            from SavedGames import LastSave
    
    def clearAll(self): #TODO: also clear any battle that is currently active and return to the campaign map
        fleetList:UnitManagerBase.UnitList = []
        for team in self.getUnitManager().Teams.values():
            fleetList += team
        for i in fleetList:
            i.completelyDestroy()
    
    def newGame(self):
        if self._confirmNewOrLoad("starting a new game"):
            self.clearAll()
            import Ships
            Fleet1 = FleetBase.Fleet(1)
            Fleet1.Name = "Nomad Fleet"
            ship = Ships.TestShips.NomadOne()
            Fleet1.addShip(ship)
            Fleet1.moveToHex(self.getHex((24,25)))
            get.window().TabWidget.setCurrentWidget(get.window().UnitStatDisplay)
            get.scene().Camera.resetCameraPosition()
            get.camera().focusRandomFleet(team=1)
    
    def _confirmNewOrLoad(self, verb:str=""):
        confirm = True
        if self.UnitManager.Teams[1]:
            msgBox = QtWidgets.QMessageBox(get.window())
            msgBox.setText(f"Are you sure?")
            msgBox.setInformativeText(f"It seems like you are already in a game. Are you sure you want to proceed {verb}?")
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Cancel)
            confirm = msgBox.exec() == QtWidgets.QMessageBox.Yes
        return confirm

class AppClass(ape.APEApp):
    def __init__(self, args, useExcepthook=True):
        super().__init__(args, useExcepthook)
        #StarNomadsColourPalette.SNDark.update(self.Themes["Dark"])
        StarNomadsDark = "[Star Nomads] Dark"
        self.addTheme(StarNomadsDark, StarNomadsColourPalette.SNDark)
        self.setTheme(StarNomadsDark)
        self.optionWindow.Input_Field.LoadCurrentPalette() #TODO: Doing this should be the task of AGeLib! It's Stupid that I need to do this manually here!
    
    #def r_setTheme(self):
    #    pass #TODO
