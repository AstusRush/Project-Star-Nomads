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
from BaseClasses import HexBase, FleetBase, ShipBase, ModelBase, BaseModules, UnitManagerBase, get
from Economy import Resources, BaseEconomicModules
from GUI import BaseInfoWidgets, Windows
from Environment import Environment

class EngineClass(ape.APE):
    REINFORCEMENT_RANGE =  4
    REINFORCEMENT_TIME  = 15
    CurrentBattleTurn = 0
    CurrentBattleAggressorHex:'HexBase._Hex' = None
    CurrentBattleDefenderHex:'HexBase._Hex' = None
    _HexToLookAtAfterBattle:'HexBase._Hex' = None
    DebugPrintsEnabled:bool = False
    
    def start(self):
        self._NumHexGridsCampaign, self._NumHexGridsBattle = 0, 0
        self.Scene:'Scene.CampaignScene' = None
        self.BattleScene:'Scene.BattleScene' = None
        self.UnitManager:'UnitManagerBase.CampaignUnitManager' = None
        self.BattleUnitManager:'UnitManagerBase.CombatUnitManager' = None
        self.FleetsInBattle:typing.List[FleetBase.Fleet] = []
        self.base.start()
        self.startCampaignScene()
        self.CurrentlyInBattle = False
        
        self.newGame()
        QtCore.QTimer.singleShot(1000, lambda: self.autoadjustGraphicSettings())
        get.app().S_NewTurnStarted.connect(lambda: self._handleNewTurn())
    
    def interactionsDisabled(self, influenceCameraMovement:bool=False) -> 'InteractionDisabler':
        return InteractionDisabler(influenceCameraMovement)
    
    def endTurn(self):
        if not self.CurrentlyInBattle:
            self.autoSave()
        App().processEvents()
        get.app().S_TurnEnded.emit()
        get.unitManager().endTurn()
    
    def _handleNewTurn(self):
        for fleet in get.unitManager():
            fleet.arrangeShips()
        if self.CurrentlyInBattle:
            self.CurrentBattleTurn += 1
            self.handleReinforcement()
    
    def startCampaignScene(self):
        self.UnitManager = UnitManagerBase.CampaignUnitManager()
        self.Scene = Scene.CampaignScene()
        self.Scene.start((70,70))
    
    def generateCampaignSector(self):
        environmentCreator = Environment.EnvironmentCreator_Sector()
        environmentCreator.generate(self.Scene.HexGrid, combat=False)
    
    def transitionToNewCampaignSector(self):
        self.clearAll(exceptPlayer=True)
        self.generateCampaignSector()
        
        #TODO: The following code is ugly but at least it handles all reasonable edge-cases
        freeHex = None
        dummyFleet = FleetBase.Fleet(0)
        for i in get.hexGrid().Hexes:
            if freeHex: break
            for h in i:
                if dummyFleet._navigable(h):
                    freeHex = h
                    break
        dummyFleet.destroy()
        c = 2
        hexes = self.Scene.HexGrid.getCentreHexes(c)
        while len(hexes) < len(self.UnitManager.Teams[1])+1:
            c += 1
            hexes = self.Scene.HexGrid.getCentreHexes(c)
        hexes = self.Scene.HexGrid.getCentreHexes(c+3)
        random.shuffle(hexes)
        for fleet in self.UnitManager.Teams[1]:
            for h in hexes:
                if not HexBase.findPath(h,freeHex)[0]: continue
                if not h.fleet and fleet._navigable(h):
                    fleet.moveToHex(h, animate=False)
                    break
                elif h.fleet and h.fleet() is fleet:
                    break
            else:
                NC(2,"Could not place Fleet!!! Trying to place it just about anywhere now")
                for _ in range(500): #TODO: What happens if we can't place a flotilla? We need an abort condition and a way to handle it...
                    hex_ = random.choice(random.choice(get.hexGrid().Hexes))
                    if fleet._navigable(hex_) and HexBase.findPath(hex_,freeHex)[0]:
                        fleet.moveToHex(hex_, animate=False)
                        break
        
        self.resetCameraAndSetUnitTab()
    
    def startBattleScene(self, fleets:'list[FleetBase.Fleet]', aggressorHex:'HexBase._Hex', defenderHex:'HexBase._Hex', battleType=0):
        if self.CurrentlyInBattle: raise Exception("A battle is already happening")
        #TODO: What happens when no player fleet is involved?!
        #self._CameraPositionBeforeBattle = self.Scene.Camera.CameraCenter.getPos()
        size = self.queryPlayerForBattleMapSize()
        self.CurrentBattleTurn = 1
        self._HexToLookAtAfterBattle = defenderHex
        self.setHexInteractionFunctions()
        self.CurrentlyInBattle = True
        self.BattleType = battleType
        self.UnitManager.unselectAll()
        self.Scene.HexGrid.clearAllSelections()
        self.FleetsInBattle = fleets
        self.CurrentBattleAggressorHex = aggressorHex
        self.CurrentBattleDefenderHex = defenderHex
        self.Scene.pause()
        self.BattleUnitManager = UnitManagerBase.CombatUnitManager()
        self.BattleScene = Scene.BattleScene()
        self.BattleScene.start(size=size)
        environmentCreator = Environment.EnvironmentCreator_Battle()
        environmentCreator.generate(self.BattleScene.HexGrid, combat=True)
        self.transferFleetsToBattle(fleets, battleType)
        #self.BattleScene.Camera.moveToHex(random.choice(self.BattleUnitManager.Teams[1]).hex())
        #self.BattleScene.Camera.focusRandomFleet(team=1)
        self.resetCameraAndSetUnitTab()
    
    def queryPlayerForBattleMapSize(self) -> 'typing.Tuple[float,float]':
        msgBox = QtWidgets.QMessageBox(get.window())
        msgBox.setText(f"Select Battle Size")
        msgBox.setInformativeText(f"How large should the battle map be??")
        T_Button,T_BN = msgBox.addButton("Tiny",msgBox.ButtonRole.ActionRole)   , 0
        S_Button,S_BN = msgBox.addButton("Small",msgBox.ButtonRole.ActionRole)  , 1
        M_Button,M_BN = msgBox.addButton("Medium",msgBox.ButtonRole.ActionRole) , 2
        L_Button,L_BN = msgBox.addButton("Large",msgBox.ButtonRole.ActionRole)  , 3
        H_Button,H_BN = msgBox.addButton("Huge",msgBox.ButtonRole.ActionRole)   , 4
        msgBox.setDefaultButton(M_Button)
        selected = msgBox.exec()
        size = 50
        if   selected == T_BN:
            size = 25
        elif selected == S_BN:
            size = 35
        elif selected == M_BN:
            size = 50
        elif selected == L_BN:
            size = 60
        elif selected == H_BN:
            size = 75
        return (size, size)
    
    def transferFleetsToBattle(self, fleets:'list[FleetBase.Fleet]', battleType, reinforcements=False):
        freeHex = None
        dummyFlotilla = FleetBase.Flotilla(0)
        for i in get.hexGrid().Hexes:
            if freeHex: break
            for h in i:
                if dummyFlotilla._navigable(h):
                    freeHex = h
                    break
        dummyFlotilla.destroy()
        for fleet in fleets:
            fleet_parts = self.splitFleetIntoFlotillas(fleet)
            for num, ships in enumerate(fleet_parts):
                flotilla = FleetBase.Flotilla(fleet.Team)
                flotilla.Name = f"Flotilla {num} of {fleet.Name}"
                for ship in ships:
                    flotilla.addShip(ship)
                self.placeFlotillaInBattle(flotilla, fleet, battleType, reinforcements, freeHex)
    
    def placeFlotillaInBattle(self, flotilla:FleetBase.Flotilla, fleet:FleetBase.Fleet, battleType, reinforcements, freeHex):
        #TODO: Implement battle types and have special positioning rules for things like ambushes or imprecise jump drives
        #MAYBE: It would be cool to have an FTL precision system without which ships jump to random positions
        #           and higher levels allow the player to pick initial positions and then maybe inhibitors that disallow the placement of ships right next to enemies...
        #           Well we are most certainly not at a point to make decisions about implementing that just yet.
        if 1 <= flotilla.Team <= 4:
            hexes = self.BattleScene.HexGrid.getCornerHexes(flotilla.Team-1,int(min(self.BattleScene.HexGrid.Size)/5))
            random.shuffle(hexes)
            for hex_ in hexes: #TODO: What happens if we can't place a flotilla? We need an abort condition and a way to handle it...
                #TODO: This should be derived from the fleet positions
                if flotilla._navigable(hex_) and HexBase.findPath(hex_,freeHex)[0]:
                    break
            else:
                NC(2,"Could not place Flotilla!!! Trying to place it just about anywhere now")
                for _ in range(500): #TODO: What happens if we can't place a flotilla? We need an abort condition and a way to handle it...
                    hex_ = random.choice(random.choice(self.BattleScene.HexGrid.Hexes))
                    if flotilla._navigable(hex_) and HexBase.findPath(hex_,freeHex)[0]:
                        break
                else:
                    NC(1,"Could not place Flotilla anywhere!!!")
        else:
            for _ in range(500): #TODO: What happens if we can't place a flotilla? We need an abort condition and a way to handle it...
                hex_ = random.choice(random.choice(self.BattleScene.HexGrid.Hexes))
                if flotilla._navigable(hex_) and HexBase.findPath(hex_,freeHex)[0]:
                    break
            else:
                NC(1,"Could not place Flotilla anywhere!!!")
        flotilla.moveToHex(hex_,animate=False)
    
    def handleReinforcement(self):
        if not self.CurrentlyInBattle: raise Exception("No battle is happening already happening")
        if self.CurrentBattleTurn % self.REINFORCEMENT_TIME == 0 and (self.CurrentBattleTurn // self.REINFORCEMENT_TIME) + 2 <= self.REINFORCEMENT_RANGE:
            if not self.CurrentBattleDefenderHex:
                NC(2,"Can not handle reinforcements due to unspecified CurrentBattleDefenderHex")
                return
            currentRange = (self.CurrentBattleTurn // self.REINFORCEMENT_TIME)
            hexes = set(self.CurrentBattleDefenderHex.getRing(currentRange))
            #hexes.update(self.CurrentBattleAggressorHex.getRing(currentRange))
            fleets = [h.fleet() for h in hexes if h.fleet]
            fleetsToAdd:'list[FleetBase.Fleet]' = []
            for fleet in fleets:
                if fleet.team() < 1: continue
                if fleet not in self.FleetsInBattle:
                    self.FleetsInBattle.append(fleet)
                    fleetsToAdd.append(fleet)
            if fleetsToAdd:
                self.transferFleetsToBattle(fleetsToAdd, self.BattleType, reinforcements=True)
                textList = [f"{f.Name} of {f.TeamName}" for f in fleetsToAdd]
                get.app().processEvents()
                NC(3,"Sensors have detected reinforcements entering the battle!\n"+"\n".join(textList),DplStr="Reinforcements Detected!")
    
    def endBattleScene(self):
        if not self.CurrentlyInBattle:
            NC(3,"It was requested to end the current battle but the is no battle.",tb=True)
            return
        self.BattleUnitManager.unselectAll()
        fleetLogs:'list[dict]' = []
        for fleet in self.FleetsInBattle:
            fleetLogs.append(fleet.battleEnded())
        self.BattleUnitManager.destroy()
        self.BattleUnitManager = None
        self.BattleScene.end()
        self.BattleScene = None
        self.Scene.continue_()
        self.CurrentlyInBattle = False
        #self.Scene.Camera.CameraCenter.setPos(self._CameraPositionBeforeBattle)
        if self._HexToLookAtAfterBattle: self.Scene.Camera.moveToHex(self._HexToLookAtAfterBattle)
        else: NC(2,"Can not recentre camera due to unspecified _HexToLookAtAfterBattle")
        NC(3, self.makeBattleLog(fleetLogs), DplStr="Battle Ended") #TODO: Give more information about the battle
        self.UnitManager.unselectAll()
        if self.UnitManager.CurrentlyHandlingTurn:
            base().taskMgr.add(self.UnitManager._endTurn_handleAICombat())
    
    def makeBattleLog(self, fleetLogs:'list[dict]') -> str:
        return "The battle has ended!" #TODO: Better log
    
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
    
    def getScene(self, campaign:bool = None) -> 'Scene.BaseScene':
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
                ships_speed_groups = list(flotillasDict.values())
                
                print("Flotilla split for", fleet.Name)
                print(f"{len(fleet.Ships)}")
                print(f"{len(ships_speed_groups)}")
                print(f"{sum([len(i) for i in ships_speed_groups])}")
                
                # Ensure that flotillas do not have more than 5 ships and separate them is necessary
                flotilla_groups:'typing.List[typing.List[ShipBase.ShipBase]]' = []
                for group in ships_speed_groups:
                    if len(group) >= 6:
                        sNum = len(group) // 3
                        sRem = len(group) % 3
                        for i in range(sNum):
                            flotilla_groups.append(group[i::sNum])
                    else:
                        flotilla_groups.append(group)
            except:
                NC(2,"Could not split fleet into flotillas in the usual way. Splitting the ships by number instead.", exc=True)
                if fleet.Team != 1 and len(fleet.Ships) >= 6:
                    sNum = len(fleet.Ships) // 3
                    sRem = len(fleet.Ships) % 3
                    flotilla_groups:'typing.List[typing.List[ShipBase.ShipBase]]' = []
                    for i in range(sNum):
                        flotilla_groups.append(fleet.Ships[i::sNum])
                else:
                    return [fleet.Ships.copy()]
            
            # Checks if all ships are in exactly one flotilla
            for i in flotilla_groups: #TODO: This check seems somewhat superfluous
                for j in i:
                    if j not in fleet.Ships:
                        NC(2,"At least one ship would not be in the fleet.Ships! Putting all ships into one flotilla instead!", input=f"{fleet = }\n{fleet.Ships = }\n{flotilla_groups = }")
                        return [fleet.Ships]
            for ship in fleet.Ships:
                for flotilla in flotilla_groups:
                    if ship in flotilla:
                        break
                else:
                    NC(2,"At least one ship would not be in a flotilla! Putting all ships into one flotilla instead!", input=f"{fleet = }\n{fleet.Ships = }\n{flotilla_groups = }")
                    return [fleet.Ships]
            if sum([len(i) for i in flotilla_groups]) != len(fleet.Ships): #TODO: the method for this check is questionable
                NC(2,"At least one ship would be in two flotillas! Putting all ships into one flotilla instead!", input=f"{fleet = }\n{fleet.Ships = }\n{flotilla_groups = }")
                return [fleet.Ships.copy()]
            
            return flotilla_groups
        except:
            NC(2,"Could not split fleet into flotillas! Putting all ships into the same flotilla instead.", input=f"{fleet = }", exc=True)
            return [fleet.Ships.copy()]
    
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
    
    def autoSave(self):
        self.save("AutoSave", notify=False)
    
    def save(self, name="", notify=True):
        if self.CurrentlyInBattle:
            NC(2,"Currently, saving is only possible on the campaign map", DplStr="Could NOT Save!")
            return
        
        wd = os.path.dirname(__file__).rsplit(os.path.sep,1)[0]
        saveFolder = os.path.join(wd,"SavedGames")
        if not os.path.exists(saveFolder):
            os.mkdir(saveFolder)
        
        if not name:
            name = QtWidgets.QFileDialog.getSaveFileName(get.window(), "Save the game", saveFolder, "Save Files(*.save);;Python Files(*.py);;Any Files(*.*)", "Save Files(*.save)")[0]
            if not name: return
        if not name.endswith(".save"):
            name += ".save"
        
        #TODO: This is not compressed enough and I don't know how to compress it more.
        #       (It certainly is far more compressible. I just haven't learned a better way to save this data than the wacky way I invented.
        #           Other game devs have way better ways to store that data. Don't judge me! This is my first game!)
        #       Therefore we need to save each fleet into its own file.
        #       This means that each saved game creates a folder filled with multiple files that all need to be executed (by loading the text and calling `exec` on it).
        #       Then we can also have other files that store other data like the tech tree.
        
        fleetList:UnitManagerBase.UnitList = []
        for team in self.getUnitManager().Teams.values():
            fleetList += team
        with open(os.path.join(saveFolder,name),"w") as file:
            file.write(AGeToPy.formatObject(fleetList))
        if notify: NC(3,f"Save successful! Saved at {os.path.join(saveFolder,name)}", DplStr="Game Saved!")
        print(f"Save successful! Saved at {os.path.join(saveFolder,name)}")
    
    def load(self):
        #if self._confirmNewOrLoad("loading"): # Option to abort already covered by the file selector
        
        wd = os.path.dirname(__file__).rsplit(os.path.sep,1)[0]
        saveFolder = os.path.join(wd,"SavedGames")
        savePath = QtWidgets.QFileDialog.getOpenFileName(get.window(), "Select File to Load", saveFolder, "Save Files(*.save);;Python Files(*.py);;Any Files(*.*)", "Save Files(*.save)")[0]
        
        if not savePath: return
        
        with get.engine().interactionsDisabled(True):
            App().processEvents()
            if self.CurrentlyInBattle:
                self.endBattleScene()
            
            self.clearAll()
            #from SavedGames import LastSave
            d = {}
            with open(savePath) as f:
                exec(f.read(), d, d)
            
            self.resetCameraAndSetUnitTab()
    
    def clearAll(self,exceptPlayer=False):
        if self.CurrentlyInBattle:
            self.endBattleScene()
        fleetList:UnitManagerBase.UnitList = []
        for team in self.getUnitManager().Teams.values():
            if exceptPlayer and team.ID == 1: continue
            else: fleetList += team
        for i in fleetList:
            i.completelyDestroy()
        for i in self.Scene.HexGrid.Hexes:
            for j in i:
                j.ResourcesFree.clear()
                j.ResourcesHarvestable.clear()
    
    def newGame(self):
        if self._confirmNewOrLoad("starting a new game"):
            self.clearAll()
            import Ships
            Fleet1 = FleetBase.Fleet(1)
            Fleet1.Name = "Nomad Fleet"
            ship = Ships.TestShips.NomadOne()
            Fleet1.addShip(ship)
            #Fleet1.moveToHex(self.getHex((24,25)))
            Fleet1.moveToHex(self.Scene.HexGrid.getCentreHexes(1)[0])
            self.generateCampaignSector()
            self.resetCameraAndSetUnitTab()
            #TODO: Ensure that the fleet can actually move (I once spawned inside an steroid cluster which blocked all movement)
    
    def _confirmNewOrLoad(self, action:str=""):
        confirm = True
        if self.UnitManager.Teams[1]:
            msgBox = QtWidgets.QMessageBox(get.window())
            msgBox.setText(f"Are you sure?")
            msgBox.setInformativeText(f"It seems like you are already in a game. Are you sure you want to proceed {action}?")
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Cancel)
            confirm = msgBox.exec() == QtWidgets.QMessageBox.Yes
        return confirm
    
    def resetCameraAndSetUnitTab(self):
        get.hexGrid().clearAllSelections()
        get.window().TabWidget.setCurrentWidget(get.window().HexInfoDisplay)
        get.scene().Camera.resetCameraPosition()
        fleet = get.camera().focusRandomFleet(team=1)
        if fleet and fleet.hex:
            fleet.hex().select()
    
    def autoadjustGraphicSettings(self):
        try:
            fps = ape.globalClock().getAverageFrameRate()
            if fps < 30 and not get.menu().SkyboxOptionsWidget.SkyboxStatic():
                get.menu().SkyboxOptionsWidget.Nebulae.set(False)
                get.menu().SkyboxOptionsWidget.newSkybox(True)
                NC(3,"Low framerate detected. Nebulae in the skybox were automatically turned off to improve framerate.")
        except:
            NC(3,"Error while trying to auto-adjust graphic settings", exc=True)

class AppClass(ape.APEApp):
    S_NewTurnStarted = pyqtSignal()
    S_TurnEnded = pyqtSignal()
    S_HexSelectionChanged = pyqtSignal()
    def __init__(self, args, useExcepthook=True):
        super().__init__(args, useExcepthook)
        #StarNomadsColourPalette.SNDark.update(self.Themes["Dark"])
        StarNomadsDark = "[Star Nomads] Dark"
        self.addTheme(StarNomadsDark, StarNomadsColourPalette.SNDark)
        self.setTheme(StarNomadsDark)
        self.optionWindow.Input_Field.LoadCurrentPalette() #TODO: Doing this should be the task of AGeLib! It's Stupid that I need to do this manually here!
    
    #def r_setTheme(self):
    #    pass #TODO

class InteractionDisabler():
    def __init__(self, influenceCameraMovement:bool=False) -> None:
        self.InfluenceCameraMovement = influenceCameraMovement
    
    def __enter__(self):
        get.window().setDisabled(True)
        get.scene().setDisabled(True, self.InfluenceCameraMovement)
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        get.window().setDisabled(False)
        get.scene().setDisabled(False, self.InfluenceCameraMovement)
        return False # False to not suppress further error handling
