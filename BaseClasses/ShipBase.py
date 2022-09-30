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
from BaseClasses import get
if TYPE_CHECKING:
    from BaseClasses import FleetBase
    from BaseClasses import BaseModules
from BaseClasses import HexBase
from BaseClasses import ModelBase

class ShipBase():
  #region init and destroy
    def __init__(self) -> None:
        self.fleet = None # type: weakref.ref['FleetBase.FleetBase']
        self.Model: ModelBase.ModelBase = None
        self.hull: 'weakref.ref[BaseModules.Hull]' = None
        self.Node = p3dc.NodePath(p3dc.PandaNode(f"Central node of ship {id(self)}"))
        self.Node.reparentTo(render())
        self.Modules:'typing.List[BaseModules.Module]' = []
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
        self.HP_Shields_max = 400
        self.HP_Shields = self.HP_Shields_max
        self.HP_Shields_Regeneration = self.HP_Shields_max / 8
        self.WasHitLastTurn = False
        self.ShieldsWereOffline = False
  #endregion init and destroy
  #region Properties
    @property
    def HP(self):
        return self.hull().HP_Hull
    
    @HP.setter
    def HP(self, value):
        self.hull().HP_Hull = value
    
  #endregion Properties
  #region Management
    def handleNewTurn(self):
        for i in self.Modules:
            i.handleNewTurn()
    
    def addModule(self, module:'BaseModules.Module'):
        from BaseClasses import BaseModules
        self.Modules.append(module)
        if isinstance(module, BaseModules.Hull):
            if self.hull: self.Modules.remove(self.hull())
            self.hull = weakref.ref(module)
        #match module:
        #    case BaseModules.Hull():
        #        if self.hull: self.Modules.remove(self.hull())
        #        self.hull = weakref.ref(module)
  #endregion Management
  #region model
    def reparentTo(self, fleet):
        # type: (FleetBase.FleetBase) -> None
        self.fleet = weakref.ref(fleet)
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
    
    def fireLaserEffectAt(self, unit:'ShipBase', hit:bool=True): #TODO:OVERHAUL --- DOES NOT WORK CURRENTLY!
        #TODO: Align the laser towards the target ship so that multiship flotillas look better
        laserEffect:p3dc.NodePath = loader().loadModel("Models/Simple Geometry/rod.ply")
        try:
            laserEffect.reparentTo(self.Node)
            #laserEffect.setZ(1.5)
            # This prevents lights from affecting this particular node
            laserEffect.setLightOff()
            
            hitPos = unit.Node.getPos(render())
            beamLength = (hitPos - self.Model.Model.getPos(render())).length()
            if not hit:
                beamLength += 1
            #laserEffect.setZ(beamLength/2)
            laserEffect.setScale(0.02,beamLength,0.02)
            colour = App().PenColours["Orange"].color()
            laserEffect.setColor(ape.colour(colour))
            if not hit:
                miss = np.random.random_sample()
                miss1s = 1 if np.random.random_sample() > 0.5 else -1
                miss2s = 1 if np.random.random_sample() > 0.5 else -1
                miss1o = np.random.random_sample()*0.3-0.15
                miss2o = np.random.random_sample()*0.3-0.15
                laserEffect.setH(20*miss1s*(miss+miss1o))
                laserEffect.setP(20*miss2s*(1-miss+miss2o))
        finally:
            #base().taskMgr.doMethodLater(1, lambda task: self._removeNode(laserEffect), str(id(laserEffect)))
            self.removeNode(laserEffect, 1)
    
    def showShield(self, time = 1): #TODO:OVERHAUL --- DOES NOT WORK CURRENTLY!
        
        shieldEffect:p3dc.NodePath = loader().loadModel("Models/Simple Geometry/sphere.ply")
        try:
            if self.HP_Shields >= self.HP_Shields_max / 2:
                c = "Green"
            elif self.HP_Shields >= self.HP_Shields_max / 4:
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
    
    def healAtTurnStart(self):
        #TODO: This should be 2 methods: One that calculates the healing and one that the first one and then actually updates the values. This way the first method can be used to display a prediction to the user
        #REMINDER: When displaying this to the user there should also be a short text explaining that taking noticeable damage halves the regeneration for one turn and that shields need one turn to restart after being taken down.
        regenFactor = 1 if not self.WasHitLastTurn else 0.5
        # self.HP_Hull = min(self.HP_Hull + self.HP_Hull_Regeneration*regenFactor , self.HP_Hull_max)
        if self.ShieldsWereOffline:
            self.ShieldsWereOffline = False
        else:
            self.HP_Shields = min(self.HP_Shields + self.HP_Shields_Regeneration*regenFactor , self.HP_Shields_max)
        self.WasHitLastTurn = False
    
    def takeDamage(self, damage:float, accuracy:float = 1 ,shieldFactor:float = 1, normalHullFactor:float = 1, shieldPiercing:bool = False) -> typing.Tuple[bool,bool,float]:
        """
        This method handles sustaining damage. \n
        TODO: describe parameters \n
        returns bool[shot hit the target], bool[destroyed the target], float[the amount of inflicted damage]
        """
        #FEATURE:HULLTYPES
        #FEATURE:WEAPONSTRUCTURES: instead of handing over a bazillion parameters there should be a class for weapons which can handle everything. That class should probably replace this takeDamage method all together
        hit = np.random.random_sample() < accuracy-self.hull().Evasion
        finalDamage = 0
        destroyed = False
        if hit:
            if shieldPiercing or self.HP_Shields <= 0:
                finalDamage = damage*normalHullFactor
                self.HP -= finalDamage
                if self.HP <= 0:
                    destroyed = True
            else:
                finalDamage = damage*shieldFactor
                self.HP_Shields -= finalDamage
                if self.HP_Shields <= 0:
                    self.HP_Shields = 0
                    self.ShieldsWereOffline = True
                self.showShield()
            self.WasHitLastTurn = finalDamage >= self.hull().NoticeableDamage
        if self.fleet().isSelected():
            self.diplayStats(True)
        if destroyed and not self.Destroyed: self.explode()
        return hit, destroyed, finalDamage
    
    def destroy(self, task=None):
        self.Destroyed = True
        #try:
        #    get.unitManager().Teams[self.fleet().Team].remove(self)
        #except:
        #    if self in get.unitManager().Teams[self.fleet().Team]:
        #        raise
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
        self.Model.Model.removeNode()
        self.Node.removeNode()
    
  #endregion Combat Defensive
  #region Display Information
    def diplayStats(self, display=True): #TODO:OVERHAUL --- DOES NOT WORK CURRENTLY!
        if display:
            text = textwrap.dedent(f"""
            Name: {self.fleet().Name}
            Team: {self.fleet().Team}
            Positions: {self.fleet().hex().Coordinates}
            
            Movement Points: {self.fleet().MovePoints}/{self.fleet().MovePoints_max}
            """)
            
            #Hull: {self.HP_Hull}/{self.HP_Hull_max} (+{self.HP_Hull_Regeneration} per turn (halfed if the ship took a single hit that dealt at least {self.NoticeableDamage} damage last turn))
            #Shields: {self.HP_Shields}/{self.HP_Shields_max} (+{self.HP_Shields_Regeneration} per turn (halfed if the ship took a single hit that dealt at least {self.NoticeableDamage} damage last turn))
            get.window().UnitStatDisplay.Text.setText(text)
        else:
            get.window().UnitStatDisplay.Text.setText("No unit selected")
  #endregion Display Information
  #region ...
    #def ___(self,):
  #endregion ...
  #region ...
    #def ___(self,):
  #endregion ...

class Ship(ShipBase):
    pass
