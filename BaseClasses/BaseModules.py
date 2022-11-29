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
if TYPE_CHECKING:
    from BaseClasses import FleetBase
    from BaseClasses import ShipBase
    from BaseClasses import ModelBase
    from ProceduralGeneration import ProceduralShips
from BaseClasses import get
from Economy import tech
from BaseClasses import HexBase
from GUI import ModuleWidgets

IMP_BASEMODULES = [("PSN get","from BaseClasses import get"),("PSN BaseModules","from BaseClasses import BaseModules"),("PSN ModuleConstructor","""
def createModule(d:dict):
    module = get.modules()[d["INTERNAL_NAME"]]()
    for k,v in d.items():
        setattr(module, k, v)
    return module
""")]

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
    Buildable = False
    Mass = 0
    Value = 0.1
    Threat = 0
    def __init__(self) -> None:
        self.ship:'weakref.ref[ShipBase.ShipBase]' = None
        self.moduleModel:'typing.Union[weakref.ref[ProceduralShips.ShipModule],None]' = None
        self.automaticallyDetermineValues()
    
    def automaticallyDetermineValues(self):
        """
        This method is used to automatically determine values that are derived from those that the player can edit.\n
        These are the threat, value, and mass of the module.\n
        If your module has other derived values you can reimplement this method to calculate them (though this should rarely be necessary).
        """
        if hasattr(self, "calculateThreat"):
            self.Threat = self.calculateThreat()
        if hasattr(self, "calculateValue"):
            self.Value = self.calculateValue()
        if hasattr(self, "calculateMass"):
            self.Mass = self.calculateMass()
    
    def setShip(self, ship:'ShipBase.ShipBase') -> None:
        self.ship = weakref.ref(ship)
    
    def isActiveTurn(self):
        if self.ship:
            return self.ship().isActiveTurn()
        else: return False
    
    def team(self):
        if self.ship:
            return self.ship().team()
        else: return None
    
    def isPlayer(self):
        return self.team() == 1
    
    def handleNewCombatTurn(self):
        """
        This method is called at the start of each combat turn to perform all required actions like resetting the movement-points and healing hull and shields as well as rearming the weapons.
        """
        pass
    
    def handleNewCampaignTurn(self):
        """
        This method is called at the start of each campaign turn to perform all required actions like resetting the movement-points and healing hull and shields as well as rearming the weapons.\n
        This method should also reset everything regarding combat to ensure that the ship is ready for the next combat (i.e. restore shields, sublight movement-points, and weapons)
        """
        pass
    
    def tocode_AGeLib(self, name="", indent=0, indentstr="    ", ignoreNotImplemented = False) -> typing.Tuple[str,dict]:
        ret, imp = "", {}
        imp.update(IMP_BASEMODULES)
        ret = indentstr*indent
        if name:
            ret += name + " = "
        ret += f"createModule(\n"
        r,i = AGeToPy._topy(self.tocode_AGeLib_GetDict(), indent=indent+2, indentstr=indentstr, ignoreNotImplemented=ignoreNotImplemented)
        ret += f"{r}\n{indentstr*(indent+1)})"
        imp.update(i)
        return ret, imp
    
    def tocode_AGeLib_GetDict(self) -> dict:
        get.modules()
        d = {
            "INTERNAL_NAME" : self.INTERNAL_NAME,
            "Name" : self.Name ,
            "Mass" : self.Mass ,
            "Value" : self.Value ,
            "Threat" : self.Threat ,
        }
        d.update(self.save())
        return d
    
    def save(self) -> dict:
        """
        Returns a dictionary with all values (and their names) that need to be saved to fully recreate this module.\n
        This method is called automatically when this module is saved.\n
        Reimplement this method if you create custom values. But don't forget to call `d.update(super().save())` before returning the dict!
        """
        return {}
    
    def getCustomisableStats(self) -> 'dict[str,typing.Callable[[],AGeInput._TypeWidget]]':
        """
        This method returns a dictionary with the names (must be the actual member name of the object) of all values that the player can customize in the ship creator as keys
        and functions (lambda functions) which return widgets with which these values can be edited.\n
        (These widgets must be widgets from AGeInput or at least behave in the same way in regards to value retrieval and layout behaviour!)\n
        Don't forget to call `d.update(super().getCustomisableStats())` before returning the dict to ensure that all basic stats like the module name are also customizable!\n
        You might also want to remove certain entries after calling `d.update(super().getCustomisableStats())` like removing the `Mass` entry if your module derives the mass from the other stats.
        """
        d = {
            "Name": lambda: AGeInput.Str(None,"Name",self.Name) ,
        }
        if tech.statCustomisationUnlocked(self,"Mass"): d["Mass"] = lambda: AGeInput.Float(None,"Mass",self.Mass,tech.moduleStatMin(self,"Mass"),tech.moduleStatMax(self,"Mass"))
        return d
    
    def copy(self) -> "Module": #VALIDATE: Does this work as intended?
        l = {}
        exec(AGeToPy.formatObject(self,"moduleCopy"),globals(),l)
        module:"Module" = l["moduleCopy"]
        module.resetCondition()
        return module
    
    def resetCondition(self):
        """
        This method should restore the condition of this module.\n
        It should, for example, set normal weapons to ready, set weapons that need to be charged before usage to not ready,
        restore the hull integrity, set the remaining movement-points to the maximum movement-points,
        empty all storage, and restore the shields.\n
        This method is used when a new module is created via the copy method or when it is edited in the ship creator
        (to ensure that i.e. an increase in the shield capacity is immediately reflected in the current strength of the shield)
        """
        pass
    
    def makeValuesValid(self) -> 'str':
        """
        This method ensures that all values are valid and should return a string that describes all modification
        or an empty string in case no modifications were required.\n
        This method is used, for example, when the user modifies the module values in the ship creator.\n
        An example for such a modification would be to ensure that the maximum weapon range is larger than the minimum weapon range.\n
        This method should only enforce rules that arise from the interaction between values.
        To limit the valid range for each value modify the getCustomisableStats method to limit the users input range as well as the tech tree where these limits are determined.
        """
        return ""
    
    def getModuleModelBuilder(self) -> 'typing.Union[type[ProceduralShips.ShipModule],None]':
        """
        This method can return a custom class that inherits from ProceduralShips.ShipModule which is then used to create the model for this module.\n
        This allows modders to add custom appearances for their modules.
        """
        return None

class Hull(Module):
    # The hull of a ship (can be tied to a ship model)
    # Determines the size of the ship (and maybe available slots for module types)
    # Also influences the HP of the ship and the required engine size
    Name = "Unnamed Hull Module"
    Buildable = True
    Evasion = 0.1
    Mass = 1
    HP_Hull_max = 100
    HP_Hull = HP_Hull_max
    HP_Hull_Regeneration = HP_Hull_max / 20
    NoticeableDamage = HP_Hull_max / 10
    
    def calculateValue(self): #TODO: Come up with a better formula for this that takes evasion, mass, etc. into account
        return self.HP_Hull_max / 100
    
    def handleNewCampaignTurn(self):
        self.HP_Hull = self.HP_Hull_max
    
    def resetCondition(self):
        super().resetCondition()
        self.HP_Hull = self.HP_Hull_max
    
    def handleNewCombatTurn(self):
        self.healAtTurnStart()
    
    def healAtTurnStart(self):
        #TODO: This should be 2 methods: One that calculates the healing and one that the first one and then actually updates the values. This way the first method can be used to display a prediction to the user
        regenFactor = 1 if not self.ship().WasHitLastTurn else 0.5
        self.HP_Hull = min(self.HP_Hull + self.HP_Hull_Regeneration*regenFactor , self.HP_Hull_max)
    
    def save(self) -> dict:
        """
        Returns a dictionary with all values (and their names) that need to be saved to fully recreate this module.\n
        This method is called automatically when this module is saved.\n
        Reimplement this method if you create custom values. But don't forget to call `d.update(super().save())` before returning the dict!
        """
        return {
            "Evasion" : self.Evasion ,
            "Mass" : self.Mass ,
            "HP_Hull_max" : self.HP_Hull_max ,
            "HP_Hull" : self.HP_Hull ,
            "HP_Hull_Regeneration" : self.HP_Hull_Regeneration ,
            "NoticeableDamage" : self.NoticeableDamage ,
        }

class Asteroid_Hull(Hull):
    Name = "Asteroid"
    Buildable = False
    Evasion = 0
    Mass = 10
    HP_Hull_max = 1000
    HP_Hull = HP_Hull_max
    HP_Hull_Regeneration = 0
    NoticeableDamage = HP_Hull_max / 10

class HullPlating(Module):
    Name = "Unnamed HullPlating Module"
    Buildable = True
    pass

#class PowerGenerator(Module): #MAYBE: I don't see how a power system would help
#    Buildable = True
#    pass

class Engine(Module): # FTL Engine
    Name = "Unnamed Engine Module"
    Buildable = True
    Thrust = 6
    RemainingThrust = 6
    
    def __init__(self) -> None:
        super().__init__()
        self.Widget:ModuleWidgets.EngineWidget = None
    
    def calculateValue(self): #TODO: Come up with a better formula for this
        return self.Thrust / 10
    
    def handleNewCampaignTurn(self):
        self.RemainingThrust = self.Thrust
    
    def resetCondition(self):
        super().resetCondition()
        self.RemainingThrust = self.Thrust
    
    def getInterface(self) -> QtWidgets.QWidget:
        self.Widget = ModuleWidgets.EngineWidget(self)
        return self.Widget
    
    def updateInterface(self):
        if self.Widget:
            try:
                self.Widget.updateInterface()
            except RuntimeError:
                self.Widget = None # This usually means that the widget is destroyed but I don't know of a better way to test for it...
    
    def save(self) -> dict:
        """
        Returns a dictionary with all values (and their names) that need to be saved to fully recreate this module.\n
        This method is called automatically when this module is saved.\n
        Reimplement this method if you create custom values. But don't forget to call `d.update(super().save())` before returning the dict!
        """
        return {
            "Thrust" : self.Thrust ,
            "RemainingThrust" : self.RemainingThrust ,
        }
    
    def getCustomisableStats(self) -> 'dict[str,typing.Callable[[],AGeInput._TypeWidget]]':
        d = super().getCustomisableStats()
        if tech.statCustomisationUnlocked(self,"Thrust"): d["Thrust"] = lambda: AGeInput.Float(None,"Thrust",self.Thrust,tech.moduleStatMin(self,"Thrust"),tech.moduleStatMax(self,"Thrust"))
        return d

class Thruster(Module): # Sublight Thruster
    Name = "Unnamed Thruster Module"
    Buildable = True
    Thrust = 6
    RemainingThrust = 6
    
    def __init__(self) -> None:
        super().__init__()
        self.Widget:ModuleWidgets.ThrusterWidget = None
    
    def calculateValue(self): #TODO: Come up with a better formula for this
        return self.Thrust / 10
    
    def handleNewCampaignTurn(self):
        self.RemainingThrust = self.Thrust
    
    def handleNewCombatTurn(self):
        self.RemainingThrust = self.Thrust
    
    def resetCondition(self):
        super().resetCondition()
        self.RemainingThrust = self.Thrust
    
    def getCombatInterface(self) -> QtWidgets.QWidget:
        self.Widget = ModuleWidgets.ThrusterWidget(self)
        return self.Widget
    
    def updateCombatInterface(self):
        if self.Widget:
            try:
                self.Widget.updateInterface()
            except RuntimeError:
                self.Widget = None # This usually means that the widget is destroyed but I don't know of a better way to test for it...
    
    def save(self) -> dict:
        """
        Returns a dictionary with all values (and their names) that need to be saved to fully recreate this module.\n
        This method is called automatically when this module is saved.\n
        Reimplement this method if you create custom values. But don't forget to call `d.update(super().save())` before returning the dict!
        """
        return {
            "Thrust" : self.Thrust ,
            "RemainingThrust" : self.RemainingThrust ,
        }
    
    def getCustomisableStats(self) -> 'dict[str,typing.Callable[[],AGeInput._TypeWidget]]':
        d = super().getCustomisableStats()
        if tech.statCustomisationUnlocked(self,"Thrust"): d["Thrust"] = lambda: AGeInput.Float(None,"Thrust",self.Thrust,tech.moduleStatMin(self,"Thrust"),tech.moduleStatMax(self,"Thrust"))
        return d

class Shield(Module):
    Name = "Unnamed Shield Module"
    Buildable = True
    HP_Shields_max = 400
    HP_Shields = HP_Shields_max
    HP_Shields_Regeneration = HP_Shields_max / 8
    
    def __init__(self) -> None:
        super().__init__()
        self.Widget:ModuleWidgets.ShieldWidget = None
    
    def calculateValue(self): #TODO: Come up with a better formula for this that takes HP_Shields_Regeneration into account
        return self.HP_Shields_max / 400 + self.HP_Shields_Regeneration / 400
    
    def handleNewCampaignTurn(self):
        self.HP_Shields = self.HP_Shields_max
    
    def handleNewCombatTurn(self):
        self.healAtTurnStart()
    
    def resetCondition(self):
        super().resetCondition()
        self.HP_Shields = self.HP_Shields_max
    
    def healAtTurnStart(self):
        #TODO: This should be 2 methods: One that calculates the healing and one that the first one and then actually updates the values. This way the first method can be used to display a prediction to the user
        if not self.ship().ShieldsWereOffline:
            regenFactor = 1 if not self.ship().WasHitLastTurn else 0.5
            self.HP_Shields = min(self.HP_Shields + self.HP_Shields_Regeneration*regenFactor , self.HP_Shields_max)
    
    def getCombatInterface(self) -> QtWidgets.QWidget:
        self.Widget = ModuleWidgets.ShieldWidget(self)
        return self.Widget
    
    def updateCombatInterface(self):
        if self.Widget:
            try:
                self.Widget.updateInterface()
            except RuntimeError:
                self.Widget = None # This usually means that the widget is destroyed but I don't know of a better way to test for it...
    
    def save(self) -> dict:
        """
        Returns a dictionary with all values (and their names) that need to be saved to fully recreate this module.\n
        This method is called automatically when this module is saved.\n
        Reimplement this method if you create custom values. But don't forget to call `d.update(super().save())` before returning the dict!
        """
        return {
            "HP_Shields_max" : self.HP_Shields_max ,
            "HP_Shields" : self.HP_Shields ,
            "HP_Shields_Regeneration" : self.HP_Shields_Regeneration ,
        }
    
    def getCustomisableStats(self) -> 'dict[str,typing.Callable[[],AGeInput._TypeWidget]]':
        d = super().getCustomisableStats()
        if tech.statCustomisationUnlocked(self,"HP_Shields_max"): d["HP_Shields_max"] = lambda: AGeInput.Float(None,"Shield Capacity",self.HP_Shields_max,tech.moduleStatMin(self,"HP_Shields_max"),tech.moduleStatMax(self,"HP_Shields_max"))
        if tech.statCustomisationUnlocked(self,"HP_Shields_Regeneration"): d["HP_Shields_Regeneration"] = lambda: AGeInput.Float(None,"Shield Regeneration",self.HP_Shields_Regeneration,tech.moduleStatMin(self,"HP_Shields_Regeneration"),tech.moduleStatMax(self,"HP_Shields_Regeneration"))
        return d

class Quarters(Module):
    # Houses crew and civilians
    # Crew is used to staff other modules and repair things. Crew is also used to pilot fighters and board enemies
    # Crew is recruited from the civilian population of the fleet.
    #MAYBE: Make variants to separate crew and civilians. I currently see no advantage of making a distinction. After all the crew is part of the population and shares all needs...
    #       It would only make sense to make a distinction between people who can operate a specific module and those that can not and in that case there would need to be a complex education system...
    #       Therefore a distinction is (at least until version 1.0 of the game) not useful
    Name = "Unnamed Quarters Module"
    Buildable = False
    pass

class Cargo(Module):
    # Used to store resources
    Name = "Unnamed Cargo Module"
    Buildable = False
    pass

class Hangar(Module):
    Name = "Unnamed Hangar Module"
    Buildable = False
    pass

class ConstructionModule(Module):
    # Modules to construct new ships.
    #TODO: Make 2 variants: Enclosed (can move while constructing) and open (can not move while constructing)
    Name = "Unnamed ConstructionModule Module"
    Buildable = True
    ConstructionResourcesGeneratedPerTurn = 0.2 #NOTE: This is only a temporary system
    Mass = 1
    
    def __init__(self) -> None:
        super().__init__()
        self.Widget:ModuleWidgets.ConstructionModuleWidget = None
        self.ConstructionResourcesStored = 0 #NOTE: This is only a temporary system
    
    def calculateValue(self):
        return 10 + 50*self.ConstructionResourcesGeneratedPerTurn #NOTE: This is only a temporary system
    
    def handleNewCampaignTurn(self):
        self.ConstructionResourcesStored += self.ConstructionResourcesGeneratedPerTurn #NOTE: This is only a temporary system
    
    def getInterface(self) -> QtWidgets.QWidget:
        self.Widget = ModuleWidgets.ConstructionModuleWidget(self)
        return self.Widget
    
    def updateInterface(self):
        if self.Widget:
            try:
                self.Widget.updateInterface()
            except RuntimeError:
                self.Widget = None # This usually means that the widget is destroyed but I don't know of a better way to test for it...
    
    def buildShip(self, ship:'ShipBase.Ship', model:'typing.Union[type[ModelBase.ShipModel],None]') -> bool:
        if get.engine().CurrentlyInBattle:
            NC(2,"Could not construct ship: There is a battle taking place.\nThe engineers are too busy fighting to start the construction of a ship!")
            return False
        elif ship.Stats.Value > self.ConstructionResourcesStored:
            NC(2, f"Could not construct ship: insufficient resources {self.ConstructionResourcesStored} out of {ship.Stats.Value}")
            return False
        else:
            self.ConstructionResourcesStored -= ship.Stats.Value
            if model is None: ship.generateProceduralModel()
            else: ship.setModel(model())
            self.ship().fleet().addShip(ship)
            self.updateInterface()
            #TODO: update the fleet Quick View to show the new ship!
            NC(3, "Ship constructed") #TODO: Better text
            return True
    
    def save(self) -> dict:
        """
        Returns a dictionary with all values (and their names) that need to be saved to fully recreate this module.\n
        This method is called automatically when this module is saved.\n
        Reimplement this method if you create custom values. But don't forget to call `d.update(super().save())` before returning the dict!
        """
        return {
            "Value" : self.Value ,
            "ConstructionResourcesGeneratedPerTurn" : self.ConstructionResourcesGeneratedPerTurn ,
            "ConstructionResourcesStored" : self.ConstructionResourcesStored ,
        }
    
    def copy(self) -> "ConstructionModule":
        module = super().copy()
        module.ConstructionResourcesStored = 0 #NOTE: This is only a temporary system
        return module

class Sensor(Module):
    # Includes sensors that increase weapon accuracy
    Name = "Unnamed Sensor Module"
    Buildable = True
    LowRange = 20
    MediumRange = 12
    HighRange = 4
    PerfectRange = 1
    
    def save(self) -> dict:
        """
        Returns a dictionary with all values (and their names) that need to be saved to fully recreate this module.\n
        This method is called automatically when this module is saved.\n
        Reimplement this method if you create custom values. But don't forget to call `d.update(super().save())` before returning the dict!
        """
        return {
            "LowRange" : self.LowRange ,
            "MediumRange" : self.MediumRange ,
            "HighRange" : self.HighRange ,
            "PerfectRange" : self.PerfectRange ,
        }

class Economic(Module):
    Buildable = False
    # Modules for economic purposes like educating and entertaining people (civilians and crew), harvesting or processing resources, growing food, and researching stuff.
    #MAYBE: Researching could be tied to other modules like sensors to scan stuff or special experimental weapons to test stuff or experimental shields to test stuff or... you get the idea
    Name = "Unnamed Economic Module"
    pass

class Augment(Module):
    # All augmentations that enhance/modify the statistics of other modules like +dmg% , +movementpoints , or +shieldRegeneration
    Name = "Unnamed Augment Module"
    Buildable = False
    pass

class Support(Module): #MAYBE: inherit from Augment
    # like Augment but with an area of effect to buff allies or debuff enemies
    Name = "Unnamed Support Module"
    Buildable = False
    pass

class Special(Module):
    # Modules that add new special functions to ships that can be used via buttons in the gui like:
    #   hacking the enemy, cloaking, extending shields around allies, repairing allies, sensor pings, boarding
    Name = "Unnamed Special Module"
    Buildable = False
    pass

class Weapon(Module):
    Name = "Unnamed Weapon Module"
    Buildable = False
    SoundEffectPath = "tempModels/SFX/phaser.wav"
    Damage = 50
    Accuracy = 1
    ShieldFactor = 1
    HullFactor = 1
    Range = 3
    MinimalRange = 0
    ShieldPiercing = False
    
    def __init__(self) -> None:
        super().__init__()
        self.Widget:ModuleWidgets.WeaponWidget = None
        self.Ready = True
        self.SFX = base().loader.loadSfx(self.SoundEffectPath)
        self.SFX.setVolume(0.07)
        print(f"{self.Name = }\n{self.Threat = }\n{self.Value = }\n{self.Mass = }\n")
    
    def calculateThreat(self):
        return self.Damage/100 * self.Accuracy * ((20 if self.ShieldPiercing else self.ShieldFactor) + self.HullFactor)/2 * ((1+self.Range-self.MinimalRange/2)/4.5)**2
    
    def calculateValue(self):
        return self.calculateThreat()/3
    
    def calculateMass(self):
        return max(0.01 , self.calculateThreat()/3 + ((1+self.Range-self.MinimalRange/3)/4.5)**2 - 1)/2 * self.Accuracy
    
    def makeValuesValid(self) -> 'str':
        adjustments = super().makeValuesValid()
        if self.Range < self.MinimalRange:
            adjustments += "The maximal range was smaller than the minimal range and was therefore increased to match. The outcome may be undesirable.\n"
            self.Range = self.MinimalRange
        return adjustments
    
    def handleNewCampaignTurn(self):
        self.Ready = True
    
    def resetCondition(self):
        super().resetCondition()
        self.Ready = True
    
    def handleNewCombatTurn(self):
        self.Ready = True
        #self.updateCombatInterface()
    
    def getCombatInterface(self) -> QtWidgets.QWidget:
        self.Widget = ModuleWidgets.WeaponWidget(self)
        return self.Widget
    
    def updateCombatInterface(self):
        if self.Widget:
            try:
                self.Widget.updateInterface()
            except RuntimeError:
                self.Widget = None # This usually means that the widget is destroyed but I don't know of a better way to test for it...
    
    def attack(self, target:'HexBase._Hex'):
        if not target.fleet or target.fleet().isDestroyed():
            #TODO: Do we want a notification?
            #NC(2, "A weapon was fired on a hex with no fleet or an already destroyed fleet." ,input=f"Fleet: {self.ship().fleet().Name}\nShip: {self.ship().Name}\nModule: {self.Name}\nTarget coordinates: {target.Coordinates}")
            return
        if self.Ready and self.MinimalRange <= self.ship().fleet().hex().distance(target) <= self.Range:
            for _ in range(6):
                targetShip = random.choice(target.fleet().Ships)
                if not targetShip.Destroyed:
                    self.SFX.setVolume(get.menu().SoundOptionsWidget.WeaponSoundVolume())
                    self.SFX.play() #TODO: do not play a sound effect too many times at the same time
                    hit , targetDestroyed, damageDealt = targetShip.takeDamage(self.Damage,self.Accuracy,self.ShieldFactor,self.HullFactor,self.ShieldPiercing)
                    self.fireEffectAt(targetShip, hit) #TODO: loading too many effects at the same time is too slow...
                    self.Ready = False
                    #self.updateCombatInterface()
                    break
    
    def fireEffectAt(self, target:'ShipBase.ShipBase', hit:bool=True):
        raise NotImplementedError(f"fireEffectAt is not implemented for this weapon named {self.Name}")
    
    def save(self) -> dict:
        """
        Returns a dictionary with all values (and their names) that need to be saved to fully recreate this module.\n
        This method is called automatically when this module is saved.\n
        Reimplement this method if you create custom values. But don't forget to call `d.update(super().save())` before returning the dict!
        """
        return {
            "SoundEffectPath" : self.SoundEffectPath ,
            "Damage" : self.Damage ,
            "Accuracy" : self.Accuracy ,
            "ShieldFactor" : self.ShieldFactor ,
            "HullFactor" : self.HullFactor ,
            "Range" : self.Range ,
            "MinimalRange" : self.MinimalRange ,
            "ShieldPiercing" : self.ShieldPiercing ,
            "Ready" : self.Ready ,
        }
    
    def getCustomisableStats(self) -> 'dict[str,typing.Callable[[],AGeInput._TypeWidget]]':
        d = super().getCustomisableStats()
        del d["Mass"]
        if tech.statCustomisationUnlocked(self,"Damage"): d["Damage"] = lambda: AGeInput.Float(None,"Damage",self.Damage,tech.moduleStatMin(self,"Damage"),tech.moduleStatMax(self,"Damage"))
        if tech.statCustomisationUnlocked(self,"Accuracy"): d["Accuracy"] = lambda: AGeInput.Float(None,"Accuracy",self.Accuracy,tech.moduleStatMin(self,"Accuracy"),tech.moduleStatMax(self,"Accuracy"))
        if tech.statCustomisationUnlocked(self,"ShieldFactor"): d["ShieldFactor"] = lambda: AGeInput.Float(None,"ShieldFactor",self.ShieldFactor,tech.moduleStatMin(self,"ShieldFactor"),tech.moduleStatMax(self,"ShieldFactor"))
        if tech.statCustomisationUnlocked(self,"HullFactor"): d["HullFactor"] = lambda: AGeInput.Float(None,"HullFactor",self.HullFactor,tech.moduleStatMin(self,"HullFactor"),tech.moduleStatMax(self,"HullFactor"))
        if tech.statCustomisationUnlocked(self,"Range"): d["Range"] = lambda: AGeInput.Int(None,"Range",self.Range,tech.moduleStatMin(self,"Range"),tech.moduleStatMax(self,"Range"))
        if tech.statCustomisationUnlocked(self,"MinimalRange"): d["MinimalRange"] = lambda: AGeInput.Int(None,"MinimalRange",self.MinimalRange,tech.moduleStatMin(self,"MinimalRange"),tech.moduleStatMax(self,"MinimalRange"))
        if tech.statCustomisationUnlocked(self,"ShieldPiercing"): d["ShieldPiercing"] = lambda: AGeInput.Bool(None,"ShieldPiercing",self.ShieldPiercing)
        return d

class Weapon_Beam(Weapon): #TODO: SFX (for now we can reuse the assets from Star Trek Armada 2 for prototyping)
    Name = "Unnamed Weapon_Beam Module"
    Buildable = True
    SoundEffectPath = "tempModels/SFX/phaser.wav"
    ModelPath = "Models/Simple Geometry/rod.ply"
    PenColourName = "Orange"
    
    def fireEffectAt(self, target:'ShipBase.ShipBase', hit:bool=True):
        laserEffect:p3dc.NodePath = loader().loadModel(self.ModelPath)
        try:
            laserEffect.reparentTo(self.ship().Node)
            if self.moduleModel:
                laserEffect.setPos(self.ship().Node.getRelativePoint(self.moduleModel().Node,self.moduleModel().Node.get_pos()))
            #else:
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
    
    def save(self) -> dict:
        """
        Returns a dictionary with all values (and their names) that need to be saved to fully recreate this module.\n
        This method is called automatically when this module is saved.\n
        Reimplement this method if you create custom values. But don't forget to call `d.update(super().save())` before returning the dict!
        """
        d = super().save()
        d["ModelPath"] = self.ModelPath
        d["PenColourName"] = self.PenColourName
        return d
