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
    from BaseClasses import ShipBase
    from BaseClasses import ModelBase
from BaseClasses import HexBase

class Module():
    # Should at least implement:
    #   size (hull and some augments have negative values)
    #   resource costs
    #   module hp (if <=0 the module is inoperable until repaired) (some modules may have infinite HP but only if they are not targetable)
    #   exposure of the module (which means "how likely is the module to be hit" (a construction module is big and can be easily hit but weapons are much smaller))
    #       (Some modules like the hull should not be attackable since the ships hull-HP takes that role)
    #       (This is used to determine random module damage. Targeted attacks by fighters on for example weapon systems are effected by this but far more likely to hit)
    #   required staff (#MAYBE: make a distinction between staff on the strategic map and staff on the tactical map since the crew that usually operates refineries can operate guns during combat)
    #   (Slot type is basically the type of the subclass but maybe it would be helpful to implement it here)
    Name = "Unnamed Generic Module"
    Mass = 0
    def __init__(self, ship:'ShipBase.ShipBase') -> None:
        self.ship = weakref.ref(ship)
    
    def handleNewCombatTurn(self):
        pass

class Hull(Module):
    # The hull of a ship (can be tied to a ship model)
    # Determins the size of the ship (and maybe available slots for module types)
    # Also influences the HP of the ship and the required engine size
    Name = "Unnamed Hull Module"
    Evasion = 0.1
    Mass = 1
    HP_Hull_max = 100
    HP_Hull = HP_Hull_max
    HP_Hull_Regeneration = HP_Hull_max / 20
    NoticeableDamage = HP_Hull_max / 10
    
    def handleNewCombatTurn(self):
        self.healAtTurnStart()
    
    def healAtTurnStart(self):
        #TODO: This should be 2 methods: One that calculates the healing and one that the first one and then actually updates the values. This way the first method can be used to display a prediction to the user
        regenFactor = 1 if not self.ship().WasHitLastTurn else 0.5
        self.HP_Hull = min(self.HP_Hull + self.HP_Hull_Regeneration*regenFactor , self.HP_Hull_max)

class HullPlating(Module):
    Name = "Unnamed HullPlating Module"
    pass

#class PowerGenerator(Module): #MAYBE: I don't see how a power system would help
#    pass

class Engine(Module): # FTL Engine
    Name = "Unnamed Engine Module"
    Thrust = 6
    RemainingThrust = 6

class Thruster(Module): # Sublight Thruster
    Name = "Unnamed Thruster Module"
    Thrust = 6
    RemainingThrust = 6
    
    def __init__(self, ship:'ShipBase.ShipBase') -> None:
        super().__init__(ship)
        self.Widget = None
    
    def handleNewCombatTurn(self):
        self.RemainingThrust = self.Thrust
    
    def getCombatInterface(self) -> QtWidgets.QWidget:
        self.Widget = QtWidgets.QLabel()
        return self.Widget
    
    def updateCombatInterface(self):
        if self.Widget:
            try:
                c,m = self.ship().Stats.Movement_Sublight
                self.Widget.setText(f"{self.Name} (Sublight Thruster):\n\tMovement: {c}/{m}\n\tThrust: {self.RemainingThrust}/{self.Thrust}\n\tShip Mass: {self.ship().Stats.Mass}")
            except RuntimeError:
                pass # This usually means that the widget is destroyed but I don't know of a better way to test for it...

class Shield(Module):
    Name = "Unnamed Shield Module"
    HP_Shields_max = 400
    HP_Shields = HP_Shields_max
    HP_Shields_Regeneration = HP_Shields_max / 8
    
    def __init__(self, ship:'ShipBase.ShipBase') -> None:
        super().__init__(ship)
        self.Widget = None
    
    def handleNewCombatTurn(self):
        self.healAtTurnStart()
    
    def healAtTurnStart(self):
        #TODO: This should be 2 methods: One that calculates the healing and one that the first one and then actually updates the values. This way the first method can be used to display a prediction to the user
        if not self.ship().ShieldsWereOffline:
            regenFactor = 1 if not self.ship().WasHitLastTurn else 0.5
            self.HP_Shields = min(self.HP_Shields + self.HP_Shields_Regeneration*regenFactor , self.HP_Shields_max)
    
    def getCombatInterface(self) -> QtWidgets.QWidget:
        self.Widget = QtWidgets.QLabel()
        return self.Widget
    
    def updateCombatInterface(self):
        if self.Widget:
            try:
                self.Widget.setText(f"{self.Name} (Shield):\n\tHP: {self.HP_Shields}/{self.HP_Shields_max}\n\tRegeneration per turn: {self.HP_Shields_Regeneration} (Halved if damaged last turn)\n\t(It takes one turn to reactivate the shields if their HP reaches 0)")
            except RuntimeError:
                pass # This usually means that the widget is destroyed but I don't know of a better way to test for it...

class Quarters(Module):
    # Houses crew and civilians
    # Crew is used to staff other modules and repair things. Crew is also used to pilot fighters and board enemies
    # Crew is recruited from the civilian population of the fleet.
    #MAYBE: Make variants to separate crew and civilians. I currently see no advantage of making a distinction. After all the crew is part of the population and shares all needs...
    #       It would only make sense to make a distinction between people who can operate a specific module and those that can not and in that case there would need to be a complex education system...
    #       Therefore a distinction is (at least until version 1.0 of the game) not useful
    Name = "Unnamed Quarters Module"
    pass

class Cargo(Module):
    # Used to store resources
    Name = "Unnamed Cargo Module"
    pass

class Hangar(Module):
    Name = "Unnamed Hangar Module"
    pass

class ConstructionModule(Module):
    # Modules to construct new ships.
    #TODO: Make 2 variants: Enclosed (can move while constructing) and open (can not move while constructing)
    Name = "Unnamed ConstructionModule Module"
    pass

class Sensor(Module):
    # Includes sensors that increase weapon accuracy
    Name = "Unnamed Sensor Module"
    pass

class Economic(Module):
    # Modules for economic purposes like educating and entertaining people (civilians and crew), harvesting or processing resources, growing food, and researching stuff.
    #MAYBE: Researching could be tied to other modules like sensors to scan stuff or special experimental weapons to test stuff or experimental shields to test stuff or... you get the idea
    Name = "Unnamed Economic Module"
    pass

class Augment(Module):
    # All augmentations that enhance/modify the statistics of other modules like +dmg% , +movementpoints , or +shieldRegeneration
    Name = "Unnamed Augment Module"
    pass

class Support(Module): #MAYBE: inherit from Augment
    # like Augment but with an area of effect to buff allies or debuff enemies
    Name = "Unnamed Support Module"
    pass

class Special(Module):
    # Modules that add new special functions to ships that can be used via buttons in the gui like:
    #   hacking the enemy, cloaking, extending shields around allies, repairing allies, sensor pings, boarding
    Name = "Unnamed Special Module"
    pass

class Weapon(Module):
    Name = "Unnamed Weapon Module"
    SoundEffectPath = "tempModels/SFX/phaser.wav"
    Damage = 50
    Accuracy = 1
    ShieldFactor = 1
    HullFactor = 1
    Range = 3 #TODO: Implement weapon Range
    def __init__(self, ship:'ShipBase.ShipBase') -> None:
        super().__init__(ship)
        self.Widget = None
        self.ShieldPiercing = False
        self.Ready = True
        self.SFX = base().loader.loadSfx(self.SoundEffectPath)
    
    def handleNewCombatTurn(self):
        self.Ready = True
        #self.updateCombatInterface()
    
    def getCombatInterface(self) -> QtWidgets.QWidget:
        self.Widget = QtWidgets.QLabel()
        return self.Widget
    
    def updateCombatInterface(self):
        if self.Widget:
            try:
                self.Widget.setText(f"{self.Name} is {'Ready' if self.Ready else 'Used'}\n\tRange: {self.Range}\n\tDamage: {self.Damage}\n\tAccuracy: {self.Accuracy}\n\tHullFactor: {self.HullFactor}\n\tShieldFactor: {self.ShieldFactor}")
            except RuntimeError:
                pass # This usually means that the widget is destroyed but I don't know of a better way to test for it...
    
    def attack(self, target:'HexBase._Hex'):
        if self.Ready:
            targetShip = random.choice(target.fleet().Ships)
            if not targetShip.Destroyed:
                self.SFX.play()
                hit , targetDestroyed, damageDealt = targetShip.takeDamage(self.Damage,self.Accuracy,self.ShieldFactor,self.HullFactor,self.ShieldPiercing)
                self.fireEffectAt(targetShip, hit)
                self.Ready = False
                #self.updateCombatInterface()
    
    def fireEffectAt(self, target:'ShipBase.ShipBase', hit:bool=True):
        raise NotImplementedError(f"fireEffectAt is not implemented for this weapon named {self.Name}")

class Weapon_Beam(Weapon): #TODO: SFX (for now we can reuse the assets from Star Trek Armada 2 for prototyping)
    Name = "Unnamed Weapon_Beam Module"
    SoundEffectPath = "tempModels/SFX/phaser.wav"
    def __init__(self, ship:'ShipBase.ShipBase') -> None:
        super().__init__(ship)
        self.ModelPath = "Models/Simple Geometry/rod.ply"
        self.PenColourName = "Orange"
    
    def fireEffectAt(self, target:'ShipBase.ShipBase', hit:bool=True):
        laserEffect:p3dc.NodePath = loader().loadModel(self.ModelPath)
        try:
            laserEffect.reparentTo(self.ship().Node)
            laserEffect.look_at(target.Node)
            #laserEffect.setZ(1.5)
            # This prevents lights from affecting this particular node
            laserEffect.setLightOff()
            
            hitPos = target.Node.getPos(render())
            beamLength = (hitPos - self.ship().Model.Model.getPos(render())).length()
            if not hit:
                beamLength += 1
            #laserEffect.setZ(beamLength/2)
            laserEffect.setScale(0.02,beamLength,0.02)
            colour = App().PenColours[self.PenColourName].color()
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
            self.ship().removeNode(laserEffect, 1)
