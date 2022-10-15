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
from BaseClasses import HexBase
from BaseClasses import ModelBase
from GUI import WidgetsBase

class ShipsStats():
    def __init__(self, ship:'ShipBase') -> None:
        self.ship = weakref.ref(ship)
    
    @property
    def HP_Hull(self) -> float:
        return self.ship().hull().HP_Hull
    
    @HP_Hull.setter
    def HP_Hull(self, value:float):
        self.ship().hull().HP_Hull = value
    
    @property
    def HP_Hull_max(self) -> float:
        return self.ship().hull().HP_Hull_max
    
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
        return float("inf"), self.ship().sensor().LowRange, self.ship().sensor().MediumRange, self.ship().sensor().HighRange, self.ship().sensor().PerfectRange
    
    @property
    def Movement_Sublight(self) -> typing.Tuple[float,float]:
        "Remaining and maximum movement on the combat map."
        mass = self.Mass
        return round(self.ship().thruster().RemainingThrust/mass,2) , round(self.ship().thruster().Thrust/mass,2)
    
    def spendMovePoints_Sublight(self, value:float):
        self.ship().thruster().RemainingThrust -= value*self.Mass
    
    @property
    def Movement_FTL(self) -> typing.Tuple[float,float]:
        "Remaining and maximum movement on the campaign map."
        mass = self.Mass
        return round(self.ship().engine().RemainingThrust/mass,2) , round(self.ship().engine().Thrust/mass,2)
    
    @property
    def Movement(self) -> typing.Tuple[float,float]:
        "Remaining and maximum movement on the current map."
        if get.engine().CurrentlyInBattle: return self.Movement_Sublight
        else: return self.Movement_FTL
    
    def spendMovePoints_FTL(self, value:float):
        self.ship().engine().RemainingThrust -= value*self.Mass
    
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
        c,m = self.Movement_Sublight
        return self.ship().hull().Evasion + m/100*np.cos( abs(c-m/2)/m *np.pi )
    
    @property
    def Value(self) -> float:
        return sum([i.Value for i in self.ship().Modules])
    
    @property
    def Threat(self) -> float:
        return sum([i.Threat for i in self.ship().Modules])
    
    @property
    def Defensiveness(self) -> float:
        return ((self.HP_Shields+self.HP_Shields_max)/2 + (self.HP_Hull+self.HP_Hull_max)/2)*(1/self.Evasion)

class ShipBase():
    Name = "Unnamed Entity (ShipBase)"
    ClassName = "Unnamed Entity Class (ShipBase)"
    ExplosionSoundEffectPath = "tempModels/SFX/arfexpld.wav"
    
    Model: ModelBase.ModelBase = None
    campaignFleet:typing.Union[weakref.ref['FleetBase.Fleet'],None] = None
    battleFleet:typing.Union[weakref.ref['FleetBase.Flotilla'],None] = None
  #region init and destroy
    def __init__(self) -> None:
        self.Interface = WidgetsBase.ShipInterface(self)
        self.Stats = ShipsStats(self)
        self.fleet = None # type: weakref.ref['FleetBase.FleetBase']
        self.hull: 'weakref.ref[BaseModules.Hull]' = None
        self.thruster: 'weakref.ref[BaseModules.Thruster]' = None
        self.sensor: 'weakref.ref[BaseModules.Sensor]' = None
        self.engine: 'weakref.ref[BaseModules.Engine]' = None
        self.Shields: 'typing.List[BaseModules.Shield]' = []
        self.Weapons: 'typing.List[BaseModules.Weapon]' = []
        self.Node = p3dc.NodePath(p3dc.PandaNode(f"Central node of ship {id(self)}"))
        self.Node.reparentTo(render())
        self.Modules:'typing.List[BaseModules.Module]' = []
        self.ExplosionSoundEffect = base().loader.loadSfx(self.ExplosionSoundEffectPath)
        self.ExplosionSoundEffect.setVolume(0.35)
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
  #endregion init and destroy
  #region Management
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
        self.Modules.append(module)
        if isinstance(module, BaseModules.Hull):
            if self.hull: self.Modules.remove(self.hull(),warn=True)
            self.hull = weakref.ref(module)
        if isinstance(module, BaseModules.Thruster):
            if self.thruster: self.Modules.remove(self.thruster(),warn=True)
            self.thruster = weakref.ref(module)
        if isinstance(module, BaseModules.Engine):
            if self.engine: self.Modules.remove(self.engine(),warn=True)
            self.engine = weakref.ref(module)
        if isinstance(module, BaseModules.Sensor):
            if self.sensor: self.Modules.remove(self.sensor(),warn=True)
            self.sensor = weakref.ref(module)
        if hasattr(module, "HP_Shields"):
            self.Shields.append(module)
        if isinstance(module, BaseModules.Weapon):
            self.Weapons.append(module)
    
    def removeModule(self, module:'BaseModules.Module', warn=False):
        from BaseClasses import BaseModules
        if warn: NC(2,f"Removing module {module.Name} from modules!")
        self.Modules.remove(module)
        if module is self.hull():
            self.hull = None
        if module is self.thruster():
            self.thruster = None
        if module is self.engine():
            self.engine = None
        if module is self.sensor():
            self.sensor = None
        if hasattr(module, "HP_Shields"):
            self.Shields.remove(module)
        if isinstance(module, BaseModules.Weapon):
            self.Weapons.remove(module)
  #endregion Management
  #region Interface
    def getQuickView(self) -> QtWidgets.QWidget:
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
  #endregion Interface
  #region Interaction
    def interactWith(self, hex:'HexBase._Hex'):
        if hex.fleet:
            if get.engine().CurrentlyInBattle and not get.unitManager().isAllied(self.fleet().Team, hex.fleet().Team):
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
    
    def attack(self, hex:'HexBase._Hex'):
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
    
    def makeModel(self, modelPath):
        model = ModelBase.ModelBase(modelPath)
        self.setModel(model)
    
    def setModel(self, model: ModelBase.ModelBase):
        self.Model = model
        self.Model.Node.reparentTo(self.Node)
        self.Model.Node.setPos(0,0,0)
    
    def setPos(self, *args):
        self.Node.setPos(*args)
  #endregion model
  #region Effects
    def init_effects(self): #TODO:OVERHAUL --- DOES NOT WORK CURRENTLY!
        self.ExplosionEffect:p3dc.NodePath = None
        self.ExplosionEffect2:p3dc.NodePath = None
    
    def removeNode(self, node:p3dc.NodePath, time = 1):
        base().taskMgr.doMethodLater(time, lambda task: self._removeNode(node), str(id(node)))
    
    def _removeNode(self, node:p3dc.NodePath):
        #try:
        node.removeNode()
    
    def explode(self): #TODO:OVERHAUL --- DOES NOT WORK CURRENTLY!
        #CRITICAL: The ship should already count as destroyed at this point (thus before the animation is played)
        #           Otherwise it is still possible to accidentally attack "the explosion" when giving orders hastily
        #           Maybe the destroy method should take a time in seconds. Then all the removal of game logic is handled before the nodes are destroyed.
        #               The timer should then be started at the start of the function so that the removal of the game logic does not desync the timer.
        #               I like it that the Unit is deselected only after the explosion so that the UI stays up during the explosion (this way one can see the overkill damage). This effect should be kept.
        #           Reminder: Removing the game logic also includes to make it impossible to give orders to the ship. (At the time of writing this you can move the explosion around... which looks kinda funny...)
        self.Destroyed = True
        explosionDuration = 1.0
        self.Model.Model.setColor((0.1,0.1,0.1,1))
        
        self.ExplosionSoundEffect.play()
        
        self.ExplosionEffect:p3dc.NodePath = loader().loadModel("Models/Simple Geometry/sphere.ply")
        if typing.TYPE_CHECKING: self.ExplosionEffect = p3dc.NodePath()
        colour = App().PenColours["Orange"].color()
        colour.setAlphaF(0.6)
        self.ExplosionEffect.setColor(ape.colour(colour))
        self.ExplosionEffect.setTransparency(p3dc.TransparencyAttrib.MAlpha)
        #self.ExplosionEffect.setSize(0.1)
        self.ExplosionEffect.reparentTo(self.Node)
        self.ExplosionEffect.scaleInterval(explosionDuration, 1.5, 0.1).start()
        
        self.ExplosionEffect2:p3dc.NodePath = loader().loadModel("Models/Simple Geometry/sphere.ply")
        if typing.TYPE_CHECKING: self.ExplosionEffect2 = p3dc.NodePath()
        colour = App().PenColours["Red"].color()
        #colour.setAlphaF(0.5)
        self.ExplosionEffect2.setColor(ape.colour(colour))
        #self.ExplosionEffect2.setTransparency(p3dc.TransparencyAttrib.MAlpha)
        #self.ExplosionEffect2.setSize(0.1)
        self.ExplosionEffect2.reparentTo(self.Node)
        self.ExplosionEffect2.scaleInterval(explosionDuration, 1.1, 0.05).start()
        
        base().taskMgr.doMethodLater(explosionDuration, self.destroy, str(id(self)))
    
    def showShield(self, time = 1): #TODO:OVERHAUL --- DOES NOT WORK CURRENTLY!
        
        shieldEffect:p3dc.NodePath = loader().loadModel("Models/Simple Geometry/sphere.ply")
        try:
            if self.Stats.HP_Shields >= self.Stats.HP_Shields_max / 2:
                c = "Green"
            elif self.Stats.HP_Shields >= self.Stats.HP_Shields_max / 4:
                c = "Orange"
            else:
                c = "Red"
            colour = App().PenColours[c].color()
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
        hit = np.random.random_sample() < accuracy-self.Stats.Evasion
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
            self.WasHitLastTurn = finalDamage >= self.hull().NoticeableDamage
        #if self.fleet().isSelected():
        #    self.displayStats(True)
        self.updateInterface()
        if destroyed and not self.Destroyed: self.explode()
        return hit, destroyed, finalDamage
    
    def destroy(self, task=None):
        self.Destroyed = True
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
    
  #endregion Combat Defensive
  #region ...
    #def ___(self,):
  #endregion ...
  #region ...
    #def ___(self,):
  #endregion ...

class Ship(ShipBase):
    pass
