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
if TYPE_CHECKING:
    from BaseClasses import FleetBase
    from BaseClasses import BaseModules
    from Economy import EconomyManager
from BaseClasses import ListLoader
from BaseClasses import HexBase
from BaseClasses import ModelBase
from GUI import BaseInfoWidgets
from Economy import Resources

#TODO: There maybe should be a loop to assign elements from the dictionary to make it less error prone to add new attributes
IMP_SHIPBASE = [("PSN get","from BaseClasses import get"),("PSN ShipBase","from BaseClasses import ShipBase"),("PSN ShipBaseConstructor","""
def createShip(d:dict):
    if "INTERNAL_NAME" in d:
        ship = get.shipClasses()[d["INTERNAL_NAME"]]()
    else:
        ship = ShipBase.ShipBase()
    
    ship.Name = d["Name"]
    ship.ClassName = d["ClassName"]
    ship.WasHitLastTurn = d["WasHitLastTurn"]
    ship.ShieldsWereOffline = d["ShieldsWereOffline"]
    ship.setModules(d["Modules"])
    ship.setModel(d["Model"])
    ship.IsBlockingTilePartially = d["IsBlockingTilePartially"]
    ship.IsBlockingTileCompletely = d["IsBlockingTileCompletely"]
    ship.IsBackgroundObject = d["IsBackgroundObject"]
    
    ship.ExplosionSoundEffectPath = d["ExplosionSoundEffectPath"]
    ship.init_effects()
    return ship
""")]

class ShipsStats():
    def __init__(self, ship:'ShipBase') -> None:
        self.ship = weakref.ref(ship)
    
    @property
    def HP_Hull(self) -> float:
        if self.ship().hull:
            return self.ship().hull().HP_Hull
        else:
            return float("inf")
    
    @HP_Hull.setter
    def HP_Hull(self, value:float):
        if self.ship().hull:
            self.ship().hull().HP_Hull = value
    
    @property
    def HP_Hull_max(self) -> float:
        if self.ship().hull:
            return self.ship().hull().HP_Hull_max
        else:
            return float("inf")
    
    @property
    def NoticeableDamage(self) -> float:
        if self.ship().hull:
            return self.ship().hull().NoticeableDamage
        else:
            return 0
    
    @property
    def HP_Shields(self) -> float:
        return sum([i.HP_Shields for i in self.ship().Shields])
    
    @HP_Shields.setter
    def HP_Shields(self, value:float):
        for i in self.ship().Shields:
            i.HP_Shields = value * i.HP_Shields_max/self.HP_Shields_max
    
    @property
    def HP_Shields_max(self) -> float:
        return sum([i.HP_Shields_max for i in self.ship().Shields])
    
    @property
    def HP_Shields_Regeneration(self) -> float:
        return sum([i.HP_Shields_Regeneration for i in self.ship().Shields])
    
    @property
    def Mass(self) -> float:
        return sum([i.Mass for i in self.ship().Modules])
    
    @property
    def SensorRanges(self) -> typing.Tuple[float,float,float,float,float]:
        """
        Sensor ranges: no resolution, low resolution, medium resolution, high resolution, perfect resolution
        Note: no resolution is always infinite and only exist so that the indices match with the information levels 0='Not visible' to 4='Fully visible'
        """
        if self.ship().sensor:
            return float("inf"), self.ship().sensor().LowRange, self.ship().sensor().MediumRange, self.ship().sensor().HighRange, self.ship().sensor().PerfectRange
        else:
            return float("inf"), 0, 0, 0, 0
    
    def _getMaxMovement(self, maxThrust:float):
        #OLD: return round(maxThrust/self.Mass,2)
        # maybe : log(x^1.6+1)^1.41   with x = maxThrust/self.Mass
        return np.log(maxThrust/self.Mass**1.6+1)**1.41
    
    def _getRemainingMovement(self, maxThrust:float, remainingThrust:float):
        #OLD: return round(remainingThrust/self.Mass,2)
        return self._getMaxMovement(maxThrust) * remainingThrust/maxThrust
    
    def _getSpendThrust(self, maxThrust:float, remainingThrust:float, value:float):
        #OLD: return value*self.Mass
        return value/self._getMaxMovement(maxThrust) * maxThrust
    
    @property
    def Movement_Sublight(self) -> typing.Tuple[float,float]:
        "Remaining and maximum movement on the combat map."
        if self.ship().thruster:
            mass = self.Mass
            return self._getRemainingMovement(self.ship().thruster().Thrust, self.ship().thruster().RemainingThrust) , self._getMaxMovement(self.ship().thruster().Thrust)
        else:
            return 0, 0
    
    def spendMovePoints_Sublight(self, value:float):
        if self.ship().thruster:
            self.ship().thruster().RemainingThrust -= self._getSpendThrust(self.ship().thruster().Thrust, self.ship().thruster().RemainingThrust, value)
    
    @property
    def Movement_FTL(self) -> typing.Tuple[float,float]:
        "Remaining and maximum movement on the campaign map."
        if self.ship().engine:
            mass = self.Mass
            return self._getRemainingMovement(self.ship().engine().Thrust, self.ship().engine().RemainingThrust) , self._getMaxMovement(self.ship().engine().Thrust)
        else:
            return 0, 0
    
    def spendMovePoints_FTL(self, value:float):
        if self.ship().engine:
            self.ship().engine().RemainingThrust -= self._getSpendThrust(self.ship().engine().Thrust, self.ship().engine().RemainingThrust, value)
    
    @property
    def Movement(self) -> typing.Tuple[float,float]:
        "Remaining and maximum movement on the current map."
        if get.engine().CurrentlyInBattle: return self.Movement_Sublight
        else: return self.Movement_FTL
    
    @property
    def MovementStr(self) -> str:
        "'Remaining/Maximum' movement on the current map."
        if get.engine().CurrentlyInBattle: m = self.Movement_Sublight
        else: m = self.Movement_FTL
        return f"{round(m[0],3)}/{round(m[1],3)}"
    
    def spendMovePoints(self, value:float):
        if get.engine().CurrentlyInBattle: self.spendMovePoints_Sublight(value)
        else: self.spendMovePoints_FTL(value)
    
    @property
    def Evasion(self) -> float:
        """
        This is the evasion chance of the ship. It is influenced by the hull, the maximum movement range, and the remaining movement range\n
        You get the most evasion bonus if a ship has used half of its movement points with diminishing returns for more or less\n
            If a ship has moved less it is relatively stationary and therefore easier to hit\n
            If a ship has moved more it is too focused on reaching its destination to evade and is instead going in a predictable straight line\n
        This evasion chance is also influenced by the maximum speed\n
        If you have used exactly halve of your movement points you will get an evasion bonus of you maximum movement points in percent. The chance is distributed by using a cosine function.\n
            i.e. if you have 10 maximum movement points and have 5 remaining movement points you will get an additional 10% evasion chance on top of your hull evasion chance\n
            if you have used none or all of your movement points you will get no evasion bonus at all.\n
            and if you have used a 1/4 or 3/4 of your movement points you will get about 0.7 of the evasion chance bonus.\n
        The following code can be used to generate plots for all reasonable scenarios.\n
        (The code uses standard AGeLib plotter commands but `plot` and `draw` are equivalent to the matplotlib functions and `dpl` is equivalent to `print` (and the first two lines can be ignored))\n
        ```
        display()
        clear()
        for m in range(20):
            m += 1
            pl = []
            for c in range(m+1):
                #v = m/50*(1/2**(1+abs(c-m/2))) # an earlier attempt that produces undesirable results
                v = m/100*np.cos( abs(c-m/2)/m *np.pi )
                dpl(m,c,0.1+v )#,1/2**(1+abs(c-m/2)) )
                pl.append(v)
            plot(range(m+1),pl,label=str(m))
            dpl()
        draw()
        ```
        """
        #MAYBE: This formula can probably be rewritten without the abs and maybe even using a sine which should allow to simplify the formula
        #REMINDER: Make a manual folder and put a well formatted and labelled plot of the evasion bonus into it
        if self.ship().hull:
            movementBonus = 0
            c,m = self.Movement_Sublight
            if c > 0 and m > 0:
                movementBonus = m/100*np.cos( abs(c-m/2)/m *np.pi )
            return self.ship().hull().Evasion + movementBonus
        else:
            return 0
    
    @property
    def Value(self) -> float:
        return sum([i.Value for i in self.ship().Modules])
    
    @property
    def Threat(self) -> float:
        return sum([i.Threat for i in self.ship().Modules])
    
    @property
    def Defensiveness(self) -> float:
        return ((self.HP_Shields+self.HP_Shields_max)/2 /400 + (self.HP_Hull+self.HP_Hull_max)/2 /400)*(1+self.Evasion)

class ShipBase():
    Name = "Unnamed Entity (ShipBase)"
    ClassName = "Unnamed Entity Class (ShipBase)"
    ExplosionSoundEffectPath = "tempModels/SFX/arfexpld.wav"
    
    Model: ModelBase.ModelBase = None
    campaignFleet:typing.Union['weakref.ref[FleetBase.Fleet]',None] = None
    battleFleet:typing.Union['weakref.ref[FleetBase.Flotilla]',None] = None
  #region init and destroy
    def __init__(self) -> None:
        self.Interface = BaseInfoWidgets.ShipInterface(self)
        self.Stats = ShipsStats(self)
        self.fleet = None # type: 'weakref.ref[FleetBase.FleetBase]'
        self.hull: 'weakref.ref[BaseModules.Hull]' = None
        self.thruster: 'weakref.ref[BaseModules.Thruster]' = None
        self.sensor: 'weakref.ref[BaseModules.Sensor]' = None
        self.engine: 'weakref.ref[BaseModules.Engine]' = None
        self.Shields: 'typing.List[BaseModules.Shield]' = []
        self.Weapons: 'typing.List[BaseModules.Weapon]' = []
        self.Node = p3dc.NodePath(p3dc.PandaNode(f"Central node of ship {id(self)}"))
        self.Node.reparentTo(render())
        self.Modules:'typing.List[BaseModules.Module]' = []
        
        self.IsBlockingTilePartially  = True  #MAYBE: these could be attributes of the ship hull
        self.IsBlockingTileCompletely = False #MAYBE: these could be attributes of the ship hull
        self.IsBackgroundObject       = False #MAYBE: these could be attributes of the ship hull
        
        from Economy import EconomyManager
        self.EconomyManager = EconomyManager.ShipEconomyManager(self)
        
        self.init_combat()
        self.init_effects()
    
    def init_combat(self):#TODO:TEMPORARY
        self.init_HP()
    
    def init_HP(self):#TODO:TEMPORARY
        self.Destroyed = False
        # self.Evasion = 0.1
        # self.HP_Hull_max = 100
        # self.HP_Hull = self.HP_Hull_max
        # self.HP_Hull_Regeneration = self.HP_Hull_max / 20
        # self.NoticeableDamage = self.HP_Hull_max / 10
        # self.HP_Shields_max = 400
        # self.HP_Shields = self.HP_Shields_max
        # self.HP_Shields_Regeneration = self.HP_Shields_max / 8
        self.WasHitLastTurn = False
        self.ShieldsWereOffline = False
    
    def destroy(self, task=None):
        if self.Interface.QuickView:
            try:
                self.Interface.QuickView.ship = None
            except: pass
        self.Destroyed = True
        try:
            self.Interface.destroy() #TODO: Check if this is doing everything correctly
        except:
            ExceptionOutput()
        #try:
        #    get.unitManager().Teams[self.fleet().Team].remove(self)
        #except:
        #    if self in get.unitManager().Teams[self.fleet().Team]:
        #        raise
        if self.fleet:
            self.fleet().removeShip(self)
        self.__del__()
        #if task:
        #    return Task.cont
    
    def __del__(self):
        self.Destroyed = True
        if self.ExplosionEffect:
            self.ExplosionEffect.removeNode()
        if self.ExplosionEffect2:
            self.ExplosionEffect2.removeNode()
        #if self.fleet().isSelected():
        #    get.unitManager().selectUnit(None)
        #if self.hex:
        #    if self.hex().unit:
        #        if self.hex().unit() is self:
        #            self.hex().unit = None
        #CRITICAL: Ensure that all Nodes get cleaned up!
        if self.Model:
            self.Model.Model.removeNode()
        self.Node.removeNode()
    
    @property
    def ResourceManager(self) -> 'EconomyManager.ShipResourceManager':
        return self.EconomyManager.ResourceManager
  #endregion init and destroy
  #region Management
    def resourceCost(self) -> 'Resources._ResourceDict':
        d = Resources._ResourceDict()
        for module in self.Modules:
            d += module.resourceCost()
        return d
    
    def handleNewCombatTurn(self):
        for i in self.Modules:
            i.handleNewCombatTurn()
        self.WasHitLastTurn = False
        if self.ShieldsWereOffline:
            self.ShieldsWereOffline = False
    
    def handleNewCampaignTurn(self):
        self.WasHitLastTurn = False
        if self.ShieldsWereOffline:
            self.ShieldsWereOffline = False
        #TODO: What do we do about healing?
        for i in self.Modules:
            i.handleNewCampaignTurn()
    
    def addModule(self, module:'BaseModules.Module'):
        from BaseClasses import BaseModules
        if module in self.Modules:
            NC(1,f"The module {module.Name} is already in the modules list! It can not be added again! That this was even possible is a bug! Adding this module again will be skipped to keep the game stable.", tb=True)
            return
        module.setShip(self)
        self.Modules.append(module)
        if isinstance(module, BaseModules.Hull):
            if self.hull: self.removeModule(self.hull(),warn=True)
            self.hull = weakref.ref(module)
        if isinstance(module, BaseModules.Thruster):
            if self.thruster: self.removeModule(self.thruster(),warn=True)
            self.thruster = weakref.ref(module)
        if isinstance(module, BaseModules.Engine):
            if self.engine: self.removeModule(self.engine(),warn=True)
            self.engine = weakref.ref(module)
        if isinstance(module, BaseModules.Sensor):
            if self.sensor: self.removeModule(self.sensor(),warn=True)
            self.sensor = weakref.ref(module)
        if hasattr(module, "HP_Shields"):
            self.Shields.append(module)
        if isinstance(module, BaseModules.Weapon):
            self.Weapons.append(module)
    
    def removeModule(self, module:'BaseModules.Module', warn=False):
        from BaseClasses import BaseModules
        if warn: NC(2,f"Removing module {module.Name} from modules!")
        #TODO: clean up the module (eg get rid of all gui elements)
        if self.hull and module is self.hull():
            self.hull = None
        if self.thruster and module is self.thruster():
            self.thruster = None
        if self.engine and module is self.engine():
            self.engine = None
        if self.sensor and module is self.sensor():
            self.sensor = None
        if module in self.Shields:
            self.Shields.remove(module)
        if module in self.Weapons:
            self.Weapons.remove(module)
        self.Modules.remove(module)
    
    def canModuleBeAdded(self, module:'typing.Union[BaseModules.Module,type[BaseModules.Module]]'):
        """
        Returns whether the module Can be added without any problems.\n
        Especially returns false if the module would occupy an already occupied unique module slot like the hull.
        """
        from BaseClasses import BaseModules
        if AGeAux.isInstanceOrSubclass(module, BaseModules.Hull) and self.hull:
            return False
        if AGeAux.isInstanceOrSubclass(module, BaseModules.Thruster) and self.thruster:
            return False
        if AGeAux.isInstanceOrSubclass(module, BaseModules.Engine) and self.engine:
            return False
        if AGeAux.isInstanceOrSubclass(module, BaseModules.Sensor) and self.sensor:
            return False
        return True
    
    def removeAllModules(self):
        if get.engine().DebugPrintsEnabled:
            print("RM ======= START")
            print("Removing all modules of ship", self.Name)
        modules = self.Modules.copy()
        for module in modules:
            if get.engine().DebugPrintsEnabled: print("removing", module.Name)
            self.removeModule(module)
        if get.engine().DebugPrintsEnabled:
            print("RM ======= END")
    
    def addModules(self, modules:typing.List['BaseModules.Module']):
        for module in modules:
            self.addModule(module)
    
    def setModules(self, modules:typing.List['BaseModules.Module']):
        self.removeAllModules()
        self.addModules(modules)
    
    def getModuleOfType(self, module:'typing.Union[BaseModules.Module,type[BaseModules.Module]]') -> 'typing.Union[BaseModules.Module,bool]':
        if isinstance(module,type):
            t = module
        else:
            t = type(module)
        for i in self.Modules:
            if AGeAux.isInstanceOrSubclass(i,t):
                return i
        return False
    
    def getAllModulesOfType(self, module:'typing.Union[BaseModules.Module,type[BaseModules.Module]]') -> 'list[BaseModules.Module]':
        if isinstance(module,type):
            t = module
        else:
            t = type(module)
        ret = []
        for i in self.Modules:
            if AGeAux.isInstanceOrSubclass(i,t):
                ret.append(i)
        return ret
    
    def isActiveTurn(self):
        if self.fleet:
            return self.fleet().isActiveTurn()
        else: return False
    
    def team(self):
        if self.fleet:
            return self.fleet().Team
        else: return None
    
    def isPlayer(self):
        return self.team() == 1
  #endregion Management
  #region Save/Load/Copy
    def tocode_AGeLib(self, name="", indent=0, indentstr="    ", ignoreNotImplemented = False) -> typing.Tuple[str,dict]:
        ret, imp = "", {}
        # ret is the ship data that calls a function which is stored as an entry in imp which constructs the ship
        # Thus, ret, when executed, will be this ship. This can then be nested in a list so that we can reproduce entire fleets.
        imp.update(IMP_SHIPBASE)
        ret = indentstr*indent
        if name:
            ret += name + " = "
        ret += f"createShip(\n"
        r,i = AGeToPy._topy(self.tocode_AGeLib_GetDict(), indent=indent+2, indentstr=indentstr, ignoreNotImplemented=ignoreNotImplemented)
        ret += f"{r}\n{indentstr*(indent+1)})"
        imp.update(i)
        return ret, imp
    
    def tocode_AGeLib_GetDict(self) -> dict:
        d = {
            "Name" : self.Name ,
            "ClassName" : self.ClassName ,
            "Model" : self.Model ,
            "Modules" : self.Modules ,
            "ExplosionSoundEffectPath" : self.ExplosionSoundEffectPath ,
            "WasHitLastTurn" : self.WasHitLastTurn ,
            "ShieldsWereOffline" : self.ShieldsWereOffline ,
            "IsBlockingTilePartially" : self.IsBlockingTilePartially,
            "IsBlockingTileCompletely" : self.IsBlockingTileCompletely,
            "IsBackgroundObject" : self.IsBackgroundObject,
        }
        get.shipClasses() # This is called to ensure that all custom ship have the INTERNAL_NAME set
        if hasattr(self, "INTERNAL_NAME"):
            d["INTERNAL_NAME"] = self.INTERNAL_NAME
        return d
    
    def copy(self, resetCondition=False, removeModel=False) -> 'ShipBase': #VALIDATE: Does this work as intended?
        l = {}
        #print(AGeToPy.formatObject(self,"shipCopy"))
        exec(AGeToPy.formatObject(self,"shipCopy"),l,l)
        ship:'ShipBase' = l["shipCopy"]
        if resetCondition:
            for module in ship.Modules:
                module.resetCondition()
        if removeModel:
            self.clearModel()
        return ship
  #endregion Save/Load
  #region Interface
    def getQuickView(self):
        return self.Interface.getQuickView()
    
    def getInterface(self) -> QtWidgets.QWidget:
        if not get.engine().CurrentlyInBattle:
            return self.Interface.getInterface()
        else:
            return self.Interface.getCombatInterface()
    
    def updateInterface(self):
        if not get.engine().CurrentlyInBattle:
            self.Interface.updateInterface()
        else:
            self.Interface.updateCombatInterface()
        self.Interface.updateInfoWindow()
    
    def openInfoWindow(self):
        self.Interface.openInfoWindow()
    
  #endregion Interface
  #region Interaction
    def interactWith(self, hex:'HexBase._Hex', mustBePlayer:bool=True):
        "This method is only for player interactions!"
        if not self.isActiveTurn() or (mustBePlayer and not self.isPlayer()): return False, True
        if hex.fleet:
            if get.engine().CurrentlyInBattle and get.unitManager().isHostile(self.fleet().Team, hex.fleet().Team):
                #TODO: The fleet should look at that hex before this attack is executed
                self.attack(hex)
                return False, True
            elif hex.distance(self.fleet().hex()) == 1 and self.fleet().Team == hex.fleet().Team and self.Stats.Movement[0] >= 1:
                self.fleet().removeShip(self)
                hex.fleet().addShip(self)
                self.Stats.spendMovePoints(1)
                return True, True
        elif hex.distance(self.fleet().hex()) == 1 and self.fleet()._navigable(hex) and self.Stats.Movement[0] >= 1:
            from BaseClasses import FleetBase
            if get.engine().CurrentlyInBattle: f = FleetBase.Flotilla(self.fleet().Team)
            else: f = FleetBase.Fleet(self.fleet().Team)
            f.moveToHex(hex,False)
            self.fleet().removeShip(self)
            hex.fleet().addShip(self)
            self.Stats.spendMovePoints(1)
            return True, True
        return False, True
    
    def attack(self, hex:'HexBase._Hex', forceAttack:bool=False):
        "Fire with all weapons on the target hex. If forceAttack is True the attack will happen even if the ship is destroyed or it's currently not the ship's turn"
        if (self.Destroyed or not self.isActiveTurn()) and not forceAttack:
            return False
        for i in self.Weapons:
            i.attack(hex)
        self.updateInterface()
  #endregion Interaction
  #region model
    def reparentTo(self, fleet):
        # type: (FleetBase.FleetBase) -> None
        if fleet._IsFleet:
            if self.campaignFleet and self.campaignFleet() and self.campaignFleet() is not fleet:
                try: self.campaignFleet().removeShip(self, notifyIfNotContained=False)
                except: NC(1,exc=True) # This should mean that the fleet no longer exists and the weakref therefore no longer points to anything... #VALIDATE: is this correct? Can we intercept that exception specifically? What other exceptions could be thrown when removing the ship? Are any of these important?
            self.fleet = self.campaignFleet = weakref.ref(fleet)
        elif fleet._IsFlotilla:
            if self.battleFleet and self.battleFleet() and self.battleFleet() is not fleet:
                try: self.battleFleet().removeShip(self, notifyIfNotContained=False)
                except: NC(1,exc=True) # This should mean that the fleet no longer exists and the weakref therefore no longer points to anything... #VALIDATE: is this correct? Can we intercept that exception specifically? What other exceptions could be thrown when removing the ship? Are any of these important?
            self.fleet = self.battleFleet = weakref.ref(fleet)
        else:
            self.destroy()
            raise Exception(f"Fleet '{fleet.Name}' is neither a fleet nor a flotilla! This should not be possible! This ship will self-destruct as a response to this!")
        self.Node.reparentTo(fleet.Node)
        self.Node.setPos(0,0,0)
        try:
            self.Model.applyTeamColour()
        except:
            NC(2,"Could not apply team colour",exc=True,input=f"{self.Model = }")
    
    def makeModel(self, modelPath):
        if not modelPath:
            return self.generateProceduralModel()
        else:
            model = ModelBase.ModelBase(modelPath)
            return self.setModel(model)
    
    def generateProceduralModel(self):
        from ProceduralGeneration import ProceduralShips
        model = ProceduralShips.ProceduralShip(ship=self)
        return self.setModel(model)
    
    def setModel(self, model: 'typing.Union[ModelBase.ModelBase,None]'):
        if model is None: return self.generateProceduralModel()
        if self.Model:
            self.clearModel()
        self.Model = model
        self.Model.ship = weakref.ref(self)
        self.Model.Node.reparentTo(self.Node)
        self.Model.Node.setPos(0,0,0)
    
    def clearModel(self):
        if self.Model:
            self.Model.destroy()
            self.Model = None
    
    def setPos(self, *args):
        self.Node.setPos(*args)
  #endregion model
  #region Effects
    def init_effects(self):
        self.ExplosionEffect:p3dc.NodePath = None
        self.ExplosionEffect2:p3dc.NodePath = None
        self.ExplosionSoundEffect = base().loader.loadSfx(self.ExplosionSoundEffectPath)
        self.ExplosionSoundEffect.setVolume(0.12)
    
    def removeNode(self, node:p3dc.NodePath, time = 1):
        base().taskMgr.doMethodLater(time, lambda task: self._removeNode(node), str(id(node)))
    
    def _removeNode(self, node:p3dc.NodePath):
        #try:
        node.removeNode()
    
    def explode(self):
        #CRITICAL: The ship should already count as destroyed at this point (thus before the animation is played)
        #           Otherwise it is still possible to accidentally attack "the explosion" when giving orders hastily
        #           Maybe the destroy method should take a time in seconds. Then all the removal of game logic is handled before the nodes are destroyed.
        #               The timer should then be started at the start of the function so that the removal of the game logic does not desync the timer.
        #               I like it that the Unit is deselected only after the explosion so that the UI stays up during the explosion (this way one can see the overkill damage). This effect should be kept.
        #           Reminder: Removing the game logic also includes to make it impossible to give orders to the ship. (At the time of writing this you can move the explosion around... which looks kinda funny...)
        self.Destroyed = True
        explosionDuration = 1.0
        self.Model.Model.setColor((0.1,0.1,0.1,1))
        
        self.ExplosionSoundEffect.setVolume(get.menu().SoundOptionsWidget.WeaponSoundVolume())
        self.ExplosionSoundEffect.play()
        
        self.ExplosionEffect:p3dc.NodePath = ape.loadModel("Models/Simple Geometry/sphere.ply")
        if typing.TYPE_CHECKING: self.ExplosionEffect = p3dc.NodePath()
        colour = App().PenColours["Orange"].color()
        colour.setAlphaF(0.6)
        self.ExplosionEffect.setColor(ape.colour(colour))
        self.ExplosionEffect.setTransparency(p3dc.TransparencyAttrib.MAlpha)
        #self.ExplosionEffect.setSize(0.1)
        self.ExplosionEffect.reparentTo(self.Node)
        self.ExplosionEffect.scaleInterval(explosionDuration, 1.5, 0.1).start()
        
        self.ExplosionEffect2:p3dc.NodePath = ape.loadModel("Models/Simple Geometry/sphere.ply")
        if typing.TYPE_CHECKING: self.ExplosionEffect2 = p3dc.NodePath()
        colour = App().PenColours["Red"].color()
        #colour.setAlphaF(0.5)
        self.ExplosionEffect2.setColor(ape.colour(colour))
        #self.ExplosionEffect2.setTransparency(p3dc.TransparencyAttrib.MAlpha)
        #self.ExplosionEffect2.setSize(0.1)
        self.ExplosionEffect2.reparentTo(self.Node)
        self.ExplosionEffect2.scaleInterval(explosionDuration, 1.1, 0.05).start()
        
        if get.engine().DebugPrintsEnabled:
            print(f"{self.Name} was destroyed!")
        
        base().taskMgr.doMethodLater(explosionDuration, self.destroy, str(id(self)))
    
    def showShield(self, time = 1):
        
        shieldEffect:p3dc.NodePath = ape.loadModel("Models/Simple Geometry/sphere.ply")
        try:
            if self.Stats.HP_Shields >= self.Stats.HP_Shields_max / 2:
                c = "Shield 100"
            elif self.Stats.HP_Shields >= self.Stats.HP_Shields_max / 4:
                c = "Shield 50"
            else:
                c = "Shield 25"
            colour = App().Theme["Star Nomads"][c].color()
            colour.setAlphaF(0.3)
            shieldEffect.setColor(ape.colour(colour))
            shieldEffect.setTransparency(p3dc.TransparencyAttrib.MAlpha)
            #shieldEffect.setSize(0.1)
            shieldEffect.reparentTo(self.Node)
            
            bounds = self.Model.Model.getTightBounds()
            bounds = (bounds[1]-bounds[0])
            shieldEffect.setScale(bounds)
            #shieldEffect.setSx()
            #shieldEffect.setSy()
            #shieldEffect.setSz()
            
            shieldEffect.show()
        finally:
            self.removeNode(shieldEffect, time)
    
    
  #endregion Effects
  #region Combat Defensive
    def takeDamage(self, damage:float, accuracy:float = 1 ,shieldFactor:float = 1, normalHullFactor:float = 1, shieldPiercing:bool = False) -> typing.Tuple[bool,bool,float]:
        """
        This method handles sustaining damage. \n
        TODO: describe parameters \n
        returns bool[shot hit the target], bool[destroyed the target], float[the amount of inflicted damage]
        """
        #FEATURE:HULLTYPES
        #FEATURE:WEAPONSTRUCTURES: instead of handing over a bazillion parameters there should be a class for weapons which can handle everything. That class should probably replace this takeDamage method all together
        hit = np.random.random_sample() < min(0.95 , max(0.05 , accuracy-self.Stats.Evasion))
        finalDamage = 0
        destroyed = False
        if hit:
            if shieldPiercing or self.Stats.HP_Shields <= 0:
                finalDamage = damage*normalHullFactor
                self.Stats.HP_Hull -= finalDamage
                if self.Stats.HP_Hull <= 0:
                    destroyed = True
            else:
                finalDamage = damage*shieldFactor
                self.Stats.HP_Shields -= finalDamage
                if self.Stats.HP_Shields <= 0:
                    self.Stats.HP_Shields = 0
                    self.ShieldsWereOffline = True
                self.showShield()
            self.WasHitLastTurn = finalDamage >= self.Stats.NoticeableDamage
        #if self.fleet().isSelected():
        #    self.displayStats(True)
        self.updateInterface()
        if destroyed and not self.Destroyed: self.explode()
        return hit, destroyed, finalDamage
    
  #endregion Combat Defensive
  #region ...
    #def ___(self,):
  #endregion ...
  #region ...
    #def ___(self,):
  #endregion ...

class Ship(ShipBase):
    pass
