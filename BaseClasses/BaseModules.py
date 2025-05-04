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
from BaseClasses import HexBase
from GUI import ModuleWidgets
from Tech import tech
from Economy import Resources

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
    Name = "Generic Module"
    Buildable = False
    Mass = 0
    Value = 0.1
    Threat = 0
    def __init__(self) -> None:
        self.ship:'weakref.ref[ShipBase.ShipBase]' = None
        self.moduleModel:'typing.Union[weakref.ref[ProceduralShips.ShipModule],None]' = None
        self.Widget:'ModuleWidgets.ModuleWidget' = None
        self.FullWidget:'ModuleWidgets.ModuleWidget' = None
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
    
    def resourceCost(self) -> 'Resources._ResourceDict':
        raise NotImplementedError(f"{type(self)} does not implement resourceCost yet!")
    
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
    
    def getFullInterface(self):
        self.FullWidget = ModuleWidgets.ModuleWidget(self)
        return self.FullWidget
    
    def getQuickFullInterfaceString(self):
        s = (
            f"{self.Name}"
            f"\n\tMass: {round(self.Mass,3)}"
            f"\n\tValue: {round(self.Value,3)}"
            f"\n\tThreat: {round(self.Threat,3)}"
        )
        return s
    
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
        tech.addStatCustomizer(d,self,"Mass",AGeInput.Float)
        return d
    
    def copy(self) -> "Module": #VALIDATE: Does this work as intended?
        l = {}
        exec(AGeToPy.formatObject(self,"moduleCopy"),l,l)
        module:"Module" = l["moduleCopy"]
        module.resetCondition()
        return module
    
    def resetCondition(self):
        """
        This method should restore the condition of this module to a state as if it were just constructed.\n
        It should, for example, set normal weapons to ready, set weapons that need to be charged before usage to not ready,
        restore the hull integrity, set the remaining movement-points 0, and empty all storage.\n
        This method is used when a new module is created via the copy method or when it is edited in the ship creator.\n
        This also ensures that one can not cheat by constantly editing models to get more movement points or other advantages.
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
    Name = "Hull"
    Buildable = True
    Evasion = 0.1
    Mass = 1
    HP_Hull_max = 100
    HP_Hull = HP_Hull_max
    HP_Hull_Regeneration = HP_Hull_max / 20
    NoticeableDamage = HP_Hull_max / 10
    
    def __init__(self) -> None:
        super().__init__()
        self.Widget:'ModuleWidgets.HullWidget' = None
        self.FullWidget:'ModuleWidgets.HullWidget' = None
    
    def resourceCost(self) -> 'Resources._ResourceDict':
        return Resources._ResourceDict.new(
            Resources.Metals(self.Value),
            Resources.Crystals(self.Value/4),
        )
    
    def calculateValue(self): #TODO: Come up with a better formula for this that takes evasion, mass, etc. into account
        return self.HP_Hull_max / 100 * (1+self.Evasion)**7 * (1+(self.HP_Hull_Regeneration - self.HP_Hull_max / 20)/200)**(1.4) / (self.Mass)**(0.6)
    
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
    
    def getFullInterface(self):
        self.FullWidget = ModuleWidgets.HullWidget(self)
        return self.FullWidget
    
    def save(self) -> dict:
        """
        Returns a dictionary with all values (and their names) that need to be saved to fully recreate this module.\n
        This method is called automatically when this module is saved.\n
        Reimplement this method if you create custom values. But don't forget to call `d.update(super().save())` before returning the dict!
        """
        d = super().save()
        d.update({
            "Evasion" : self.Evasion ,
            "Mass" : self.Mass ,
            "HP_Hull_max" : self.HP_Hull_max ,
            "HP_Hull" : self.HP_Hull ,
            "HP_Hull_Regeneration" : self.HP_Hull_Regeneration ,
            "NoticeableDamage" : self.NoticeableDamage ,
        })
        return d
    
    def getCustomisableStats(self) -> 'dict[str,typing.Callable[[],AGeInput._TypeWidget]]':
        d = super().getCustomisableStats()
        tech.addStatCustomizer(d,self,"Evasion",AGeInput.Float)
        tech.addStatCustomizer(d,self,"HP_Hull_max",AGeInput.Float,"Hull Integrity")
        tech.addStatCustomizer(d,self,"HP_Hull_Regeneration",AGeInput.Float,"Hull Regeneration")
        #if tech.statCustomisationUnlocked(self,"Thrust"): d["Thrust"] = lambda: AGeInput.Float(None,"Thrust",self.Thrust,tech.moduleStatMin(self,"Thrust"),tech.moduleStatMax(self,"Thrust"))
        return d

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
    Name = "Hull Plating"
    Buildable = True
    
    def __init__(self) -> None:
        super().__init__()
        self.Widget:'ModuleWidgets.HullPlatingWidget' = None
        self.FullWidget:'ModuleWidgets.HullPlatingWidget' = None
    
    def getFullInterface(self):
        self.FullWidget = ModuleWidgets.HullPlatingWidget(self)
        return self.FullWidget

#class PowerGenerator(Module): #MAYBE: I don't see how a power system would help
#    Buildable = True
#    pass

class Engine(Module): # FTL Engine
    Name = "Engine"
    Buildable = True
    Thrust = 6
    RemainingThrust = 6
    
    def __init__(self) -> None:
        super().__init__()
        self.Widget:ModuleWidgets.EngineWidget = None
        self.FullWidget:ModuleWidgets.EngineWidget = None
    
    def resourceCost(self) -> 'Resources._ResourceDict':
        return Resources._ResourceDict.new(
            Resources.Metals(self.Value/2),
            Resources.RareMetals(self.Value/5),
            Resources.Crystals(self.Value*3/4),
        )
    
    def calculateValue(self): #TODO: Come up with a better formula for this
        return self.Thrust / 10
    
    def handleNewCampaignTurn(self):
        self.RemainingThrust = self.Thrust
    
    def resetCondition(self):
        super().resetCondition()
        self.RemainingThrust = 0#self.Thrust
    
    def getInterface(self) -> QtWidgets.QWidget:
        self.Widget = ModuleWidgets.EngineWidget(self)
        return self.Widget
    
    def updateInterface(self):
        if self.Widget:
            try:
                self.Widget.updateInterface()
            except RuntimeError:
                self.Widget = None # This usually means that the widget is destroyed but I don't know of a better way to test for it...
        if self.FullWidget:
            try:
                self.FullWidget.updateFullInterface()
            except RuntimeError:
                self.FullWidget = None # This usually means that the widget is destroyed but I don't know of a better way to test for it...
    
    def getFullInterface(self):
        self.FullWidget = ModuleWidgets.EngineWidget(self)
        return self.FullWidget
    
    def save(self) -> dict:
        """
        Returns a dictionary with all values (and their names) that need to be saved to fully recreate this module.\n
        This method is called automatically when this module is saved.\n
        Reimplement this method if you create custom values. But don't forget to call `d.update(super().save())` before returning the dict!
        """
        d = super().save()
        d.update({
            "Thrust" : self.Thrust ,
            "RemainingThrust" : self.RemainingThrust ,
        })
        return d
    
    def getCustomisableStats(self) -> 'dict[str,typing.Callable[[],AGeInput._TypeWidget]]':
        d = super().getCustomisableStats()
        del d["Mass"] #TEMPORARY
        tech.addStatCustomizer(d,self,"Thrust",AGeInput.Float)
        return d

class Thruster(Module): # Sublight Thruster
    Name = "Thruster"
    Buildable = True
    Thrust = 6
    RemainingThrust = 6
    
    def __init__(self) -> None:
        super().__init__()
        self.Widget:ModuleWidgets.ThrusterWidget = None
        self.FullWidget:ModuleWidgets.ThrusterWidget = None
    
    def resourceCost(self) -> 'Resources._ResourceDict':
        return Resources._ResourceDict.new(
            Resources.Metals(self.Value*3/4),
            Resources.Crystals(self.Value/3),
        )
    
    def calculateValue(self): #TODO: Come up with a better formula for this
        return self.Thrust / 10
    
    def handleNewCampaignTurn(self):
        self.RemainingThrust = self.Thrust
    
    def handleNewCombatTurn(self):
        self.RemainingThrust = self.Thrust
    
    def resetCondition(self):
        super().resetCondition()
        self.RemainingThrust = 0#self.Thrust
    
    def getCombatInterface(self) -> QtWidgets.QWidget:
        self.Widget = ModuleWidgets.ThrusterWidget(self)
        return self.Widget
    
    def updateCombatInterface(self):
        if self.Widget:
            try:
                self.Widget.updateInterface()
            except RuntimeError:
                self.Widget = None # This usually means that the widget is destroyed but I don't know of a better way to test for it...
        if self.FullWidget:
            try:
                self.FullWidget.updateFullInterface()
            except RuntimeError:
                self.FullWidget = None # This usually means that the widget is destroyed but I don't know of a better way to test for it...
    
    def getFullInterface(self):
        self.FullWidget = ModuleWidgets.ThrusterWidget(self)
        return self.FullWidget
    
    def save(self) -> dict:
        """
        Returns a dictionary with all values (and their names) that need to be saved to fully recreate this module.\n
        This method is called automatically when this module is saved.\n
        Reimplement this method if you create custom values. But don't forget to call `d.update(super().save())` before returning the dict!
        """
        d = super().save()
        d.update({
            "Thrust" : self.Thrust ,
            "RemainingThrust" : self.RemainingThrust ,
        })
        return d
    
    def getCustomisableStats(self) -> 'dict[str,typing.Callable[[],AGeInput._TypeWidget]]':
        d = super().getCustomisableStats()
        del d["Mass"] #TEMPORARY
        tech.addStatCustomizer(d,self,"Thrust",AGeInput.Float)
        return d

class Shield(Module):
    Name = "Shield Module"
    Buildable = True
    HP_Shields_max = 400
    HP_Shields = HP_Shields_max
    HP_Shields_Regeneration = HP_Shields_max / 8
    
    def __init__(self) -> None:
        super().__init__()
        self.Widget:ModuleWidgets.ShieldWidget = None
        self.FullWidget:ModuleWidgets.ShieldWidget = None
    
    def resourceCost(self) -> 'Resources._ResourceDict':
        return Resources._ResourceDict.new(
            Resources.Metals(self.Value/4),
            Resources.RareMetals(self.Value/6),
            Resources.Crystals(self.Value),
        )
    
    def calculateValue(self): #TODO: Come up with a better formula for this that takes HP_Shields_Regeneration into account
        return self.HP_Shields_max / 400 + self.HP_Shields_Regeneration / 400
    
    def handleNewCampaignTurn(self):
        self.HP_Shields = self.HP_Shields_max
    
    def handleNewCombatTurn(self):
        self.healAtTurnStart()
    
    def resetCondition(self):
        super().resetCondition()
        self.HP_Shields = 0#self.HP_Shields_max
    
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
        if self.FullWidget:
            try:
                self.FullWidget.updateFullInterface()
            except RuntimeError:
                self.FullWidget = None # This usually means that the widget is destroyed but I don't know of a better way to test for it...
    
    def getFullInterface(self):
        self.FullWidget = ModuleWidgets.ShieldWidget(self)
        return self.FullWidget
    
    def save(self) -> dict:
        """
        Returns a dictionary with all values (and their names) that need to be saved to fully recreate this module.\n
        This method is called automatically when this module is saved.\n
        Reimplement this method if you create custom values. But don't forget to call `d.update(super().save())` before returning the dict!
        """
        d = super().save()
        d.update({
            "HP_Shields_max" : self.HP_Shields_max ,
            "HP_Shields" : self.HP_Shields ,
            "HP_Shields_Regeneration" : self.HP_Shields_Regeneration ,
        })
        return d
    
    def getCustomisableStats(self) -> 'dict[str,typing.Callable[[],AGeInput._TypeWidget]]':
        d = super().getCustomisableStats()
        tech.addStatCustomizer(d,self,"HP_Shields_max",AGeInput.Float,"Shield Capacity")
        tech.addStatCustomizer(d,self,"HP_Shields_Regeneration",AGeInput.Float,"Shield Regeneration")
        return d

class Quarters(Module):
    # Houses crew and civilians
    # Crew is used to staff other modules and repair things. Crew is also used to pilot fighters and board enemies
    # Crew is recruited from the civilian population of the fleet.
    #MAYBE: Make variants to separate crew and civilians. I currently see no advantage of making a distinction. After all the crew is part of the population and shares all needs...
    #       It would only make sense to make a distinction between people who can operate a specific module and those that can not and in that case there would need to be a complex education system...
    #       Therefore a distinction is (at least until version 1.0 of the game) not useful
    Name = "Quarters Module"
    Buildable = False
    
    def __init__(self) -> None:
        super().__init__()
        self.Widget:'ModuleWidgets.QuartersWidget' = None
        self.FullWidget:'ModuleWidgets.QuartersWidget' = None
    
    def getFullInterface(self):
        self.FullWidget = ModuleWidgets.QuartersWidget(self)
        return self.FullWidget

class Hangar(Module):
    Name = "Hangar"
    Buildable = False
    
    def __init__(self) -> None:
        super().__init__()
        self.Widget:'ModuleWidgets.HangarWidget' = None
        self.FullWidget:'ModuleWidgets.HangarWidget' = None
    
    def getFullInterface(self):
        self.FullWidget = ModuleWidgets.HangarWidget(self)
        return self.FullWidget

class Sensor(Module):
    # Includes sensors that increase weapon accuracy
    Name = "Sensors"
    Buildable = True
    LowRange = 20
    MediumRange = 12
    HighRange = 4
    PerfectRange = 1
    
    def __init__(self) -> None:
        super().__init__()
        self.Widget:'ModuleWidgets.SensorWidget' = None
        self.FullWidget:'ModuleWidgets.SensorWidget' = None
    
    def resourceCost(self) -> 'Resources._ResourceDict':
        return Resources._ResourceDict.new(
            Resources.Metals(self.Value/4),
            Resources.RareMetals(self.Value/4),
            Resources.Crystals(self.Value),
        )
    
    def getFullInterface(self):
        self.FullWidget = ModuleWidgets.SensorWidget(self)
        return self.FullWidget
    
    def save(self) -> dict:
        """
        Returns a dictionary with all values (and their names) that need to be saved to fully recreate this module.\n
        This method is called automatically when this module is saved.\n
        Reimplement this method if you create custom values. But don't forget to call `d.update(super().save())` before returning the dict!
        """
        d = super().save()
        d.update({
            "LowRange" : self.LowRange ,
            "MediumRange" : self.MediumRange ,
            "HighRange" : self.HighRange ,
            "PerfectRange" : self.PerfectRange ,
        })
        return d

class _Economic(Module):
    """
    Implemented in `Economy.BaseEconomicModules.py`\n
    This class only exists for basic type checking purposes.\n
    Do not inherit form this class! Inherit from `Economy.BaseEconomicModules.Economic` instead!
    """
    pass

class Augment(Module):
    # All augmentations that enhance/modify the statistics of other modules like +dmg% , +movementpoints , or +shieldRegeneration
    #   but also modules that have a localised effect on the tile like effects from nebulae.
    #   In general pretty much everything that has some kind of passive effect that is restricted to the ship, the fleet, or the tile.
    Name = "Augment Module"
    Buildable = False
    
    def __init__(self) -> None:
        super().__init__()
        self.Widget:'ModuleWidgets.AugmentWidget' = None
        self.FullWidget:'ModuleWidgets.AugmentWidget' = None
    
    def getFullInterface(self):
        self.FullWidget = ModuleWidgets.AugmentWidget(self)
        return self.FullWidget

class TileCostModifier(Augment):
    Name = "Tile Cost Modifier Module"
    Buildable = False
    
    def __init__(self) -> None:
        super().__init__()
        #FEATURE:MOVECOST: Implement tile cost

class Support(Module): #MAYBE: inherit from Augment
    # Like Augment but with an area of effect that impacts nearby tiles to, for example, buff allies or debuff enemies.
    Name = "Support Module"
    Buildable = False
    
    def __init__(self) -> None:
        super().__init__()
        self.Widget:'ModuleWidgets.SupportWidget' = None
        self.FullWidget:'ModuleWidgets.SupportWidget' = None
    
    def getFullInterface(self):
        self.FullWidget = ModuleWidgets.SupportWidget(self)
        return self.FullWidget

class Special(Module):
    # Modules that add new special functions to ships that can be used via buttons in the gui like:
    #   hacking the enemy, cloaking, extending shields around allies, repairing allies, sensor pings, boarding
    Name = "Special Module"
    Buildable = False
    
    def __init__(self) -> None:
        super().__init__()
        self.Widget:'ModuleWidgets.SpecialWidget' = None
        self.FullWidget:'ModuleWidgets.SpecialWidget' = None
    
    def getFullInterface(self):
        self.FullWidget = ModuleWidgets.SpecialWidget(self)
        return self.FullWidget

class MicroJumpDrive(Special):
    Name = "Micro Jump Drive"
    Buildable = True
    #Value = 5
    Threat = 2
    MaxCharges = 1
    Cooldown = 8 #REMINDER: Cooldown = float("inf") means that the ability can only be used once per campaign turn
    Range = 10
    #MAYBE: Increase the MaxCharges and make longer jumps use up more charges. Something maybe one charge per hex travelled and a recharge rate of one charge per turn and MaxCharges = 10
    def __init__(self) -> None:
        super().__init__()
        self.Widget:'ModuleWidgets.MicroJumpDriveWidget' = None
        self.FullWidget:'ModuleWidgets.MicroJumpDriveWidget' = None
        self.Charge = self.MaxCharges
    
    def resourceCost(self) -> 'Resources._ResourceDict':
        return Resources._ResourceDict.new(
            Resources.Metals(self.Value/2),
            Resources.RareMetals(self.Value/4),
            Resources.Crystals(self.Value*3/4),
        )
    
    #def calculateThreat(self):
    #    return self.Damage/100 * self.Accuracy * ((20 if self.ShieldPiercing else self.ShieldFactor) + self.HullFactor)/2 * ((1+self.Range-self.MinimalRange/2)/4.5)**2
    
    def calculateValue(self): #TODO: Tinkers with this formula some more
        return 3*(self.Range/2)**(1.6)/(self.Cooldown)**(0.7)*(self.MaxCharges*5/9)**(1.2)
    
    #def calculateMass(self):
    #    return max(0.01 , self.calculateThreat()/3 + ((1+self.Range-self.MinimalRange/3)/4.5)**2 - 1)/2 * self.Accuracy
    
    #def makeValuesValid(self) -> 'str':
    #    adjustments = super().makeValuesValid()
    #    if self.Range < self.MinimalRange:
    #        adjustments += "The maximal range was smaller than the minimal range and was therefore increased to match. The outcome may be undesirable.\n"
    #        self.Range = self.MinimalRange
    #    return adjustments
    
    def handleNewCampaignTurn(self):
        self.Charge = self.MaxCharges
    
    def resetCondition(self):
        super().resetCondition()
        self.Charge = 0#self.MaxCharges
    
    def handleNewCombatTurn(self):
        self.Charge = min(self.Charge+1/self.Cooldown , self.MaxCharges)
        #self.updateCombatInterface()
    
    def getCombatInterface(self) -> QtWidgets.QWidget:
        self.Widget = ModuleWidgets.MicroJumpDriveWidget(self)
        return self.Widget
    
    def updateCombatInterface(self):
        if self.Widget:
            try:
                self.Widget.updateInterface()
            except RuntimeError:
                self.Widget = None # This usually means that the widget is destroyed but I don't know of a better way to test for it...
        if self.FullWidget:
            try:
                self.FullWidget.updateFullInterface()
            except RuntimeError:
                self.FullWidget = None # This usually means that the widget is destroyed but I don't know of a better way to test for it...
    
    def getFullInterface(self):
        self.FullWidget = ModuleWidgets.MicroJumpDriveWidget(self)
        return self.FullWidget
    
    def jump(self):
        if not get.engine().CurrentlyInBattle: raise Exception("The Micro Jump Drive can only be used in battle!")
        if self.Charge < 1: raise Exception("Not enough charge to jump!")
        #TODO: onHover should give a tooltip that informs the user about the interaction
        #TODO: The select button should be marked to signal that the jump action is selected, clicking the button again should cancel the selection,
        #       and onClear should remove the marking of the button (if it still exists since the selection could have changed and thus removed the button!)
        get.engine().setHexInteractionFunctions(self.jumpTo, lambda _:(False,True), None, self.clearInteraction)
        self.highlightRange(True)
    
    def highlightRange(self, highlight=True):
        get.hexGrid().clearAllHexHighlighting(True)
        if highlight:
            get.hexGrid().highlightHexes(self.ship().fleet().hex().getDisk(self.Range), HexBase._Hex.COLOUR_REACHABLE, HexBase._Hex.COLOUR_REACHABLE, False, clearFirst=True)
    
    def jumpTo(self, hex:'HexBase._Hex') -> 'tuple[bool,bool]':
        if not get.engine().CurrentlyInBattle:
            NC(1, "The Micro Jump Drive can only be used in battle!")
            return False,True
        if not isinstance(hex, HexBase._Hex):
            NC(1, f"hex must be an instance of HexBase._Hex, not {type(hex)}", input=hex)
            return False,True
        
        if ( self.Charge < 1
            or hex.distance(self.ship().fleet().hex()) > self.Range
            or not self.isActiveTurn()
            ): return False,True
        
        if hex.fleet:
            if self.team() == hex.fleet().Team:
                self.ship().fleet().removeShip(self.ship())
                hex.fleet().addShip(self.ship())
                self.Charge -= 1
                self.playEffect()
                return True, True
            else:
                return False,True
        elif self.ship().fleet()._navigable(hex):
            from BaseClasses import FleetBase
            if get.engine().CurrentlyInBattle: f = FleetBase.Flotilla(self.team())
            else: f = FleetBase.Fleet(self.team())
            self.ship().fleet().removeShip(self.ship())
            f.addShip(self.ship())
            f.moveToHex(hex,False)
            self.Charge -= 1
            self.playEffect()
            return True, True
        
        return False, True
    
    def playEffect(self):
        pass #TODO: micro jump effect
    
    def clearInteraction(self):
        self.highlightRange(False)
        if self.ship().fleet().isSelected():
            self.ship().fleet().highlightRanges(True)
    
    def save(self) -> dict:
        """
        Returns a dictionary with all values (and their names) that need to be saved to fully recreate this module.\n
        This method is called automatically when this module is saved.\n
        Reimplement this method if you create custom values. But don't forget to call `d.update(super().save())` before returning the dict!
        """
        d = super().save()
        d.update({
            "MaxCharges" : self.MaxCharges ,
            "Cooldown" : self.Cooldown ,
            "Range" : self.Range ,
            "Charge" : self.Charge ,
        })
        return d
    
    def getCustomisableStats(self) -> 'dict[str,typing.Callable[[],AGeInput._TypeWidget]]':
        d = super().getCustomisableStats()
        #del d["Mass"]
        tech.addStatCustomizer(d,self,"MaxCharges",AGeInput.Float,"Max Charges")
        tech.addStatCustomizer(d,self,"Cooldown",AGeInput.Float,"Cooldown")
        tech.addStatCustomizer(d,self,"Range",AGeInput.Int,"Range")
        return d

class TeamJumpDrive(Special):
    Name = "Team Jump Drive"
    Buildable = True
    Value = 1
    Threat = 0
    Cooldown = 100
    MaxCharges = 1
    def __init__(self) -> None:
        super().__init__()
        self.Widget:'ModuleWidgets.TeamJumpDriveWidget' = None
        self.FullWidget:'ModuleWidgets.TeamJumpDriveWidget' = None
        self.Charge = self.MaxCharges
    
    def resourceCost(self) -> 'Resources._ResourceDict':
        return Resources._ResourceDict.new(
            Resources.Metals(self.Value/2),
            Resources.RareMetals(self.Value/4),
            Resources.Crystals(self.Value*3/4),
        )
    
    #def calculateThreat(self):
    #    return self.Damage/100 * self.Accuracy * ((20 if self.ShieldPiercing else self.ShieldFactor) + self.HullFactor)/2 * ((1+self.Range-self.MinimalRange/2)/4.5)**2
    
    #def calculateValue(self): #TODO: Tinkers with this formula some more
    #    return 3*(self.Range/2)**(1.6)/(self.Cooldown)**(0.7)*(self.MaxCharges*5/9)**(1.2)
    
    #def calculateMass(self):
    #    return max(0.01 , self.calculateThreat()/3 + ((1+self.Range-self.MinimalRange/3)/4.5)**2 - 1)/2 * self.Accuracy
    
    #def makeValuesValid(self) -> 'str':
    #    adjustments = super().makeValuesValid()
    #    if self.Range < self.MinimalRange:
    #        adjustments += "The maximal range was smaller than the minimal range and was therefore increased to match. The outcome may be undesirable.\n"
    #        self.Range = self.MinimalRange
    #    return adjustments
    
    def handleNewCampaignTurn(self):
        self.Charge = min(self.Charge+1/self.Cooldown , self.MaxCharges)
    
    def resetCondition(self):
        super().resetCondition()
        self.Charge = 0#self.MaxCharges
    
    def getInterface(self) -> QtWidgets.QWidget:
        self.Widget = ModuleWidgets.TeamJumpDriveWidget(self)
        return self.Widget
    
    def updateInterface(self):
        if self.Widget:
            try:
                self.Widget.updateInterface()
            except RuntimeError:
                self.Widget = None # This usually means that the widget is destroyed but I don't know of a better way to test for it...
        if self.FullWidget:
            try:
                self.FullWidget.updateFullInterface()
            except RuntimeError:
                self.FullWidget = None # This usually means that the widget is destroyed but I don't know of a better way to test for it...
    
    def getFullInterface(self):
        self.FullWidget = ModuleWidgets.TeamJumpDriveWidget(self)
        return self.FullWidget
    
    def jump(self):
        if get.engine().CurrentlyInBattle: raise Exception("The Team Jump Drive can not be used in battle!")
        if self.Charge < 1: raise Exception("Not enough charge to jump!")
        get.engine().transitionToNewCampaignSector()
        self.Charge -= 1
    
    def playEffect(self):
        pass #TODO: team jump effect
    
    def save(self) -> dict:
        """
        Returns a dictionary with all values (and their names) that need to be saved to fully recreate this module.\n
        This method is called automatically when this module is saved.\n
        Reimplement this method if you create custom values. But don't forget to call `d.update(super().save())` before returning the dict!
        """
        d = super().save()
        d.update({
            "MaxCharges" : self.MaxCharges ,
            "Cooldown" : self.Cooldown ,
            "Charge" : self.Charge ,
        })
        return d

class Weapon(Module):
    Name = "Weapon Module"
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
        self.FullWidget:ModuleWidgets.WeaponWidget = None
        self.Ready = True
        self.SFX = base().loader.loadSfx(self.SoundEffectPath)
        self.SFX.setVolume(0.07)
        #print(f"{self.Name = }\n{self.Threat = }\n{self.Value = }\n{self.Mass = }\n")
    
    def resourceCost(self) -> 'Resources._ResourceDict':
        return Resources._ResourceDict.new(
            Resources.Metals(self.Value*3/4),
            Resources.RareMetals(max(self.Value/4*(self.Range-3),0)),
            Resources.Crystals(self.Value),
        )
    
    def calculateThreat(self):
        return self.Damage/100 * self.Accuracy * ((20 if self.ShieldPiercing else self.ShieldFactor) + self.HullFactor)/2 * ((1+self.Range-self.MinimalRange/2)/4.5)**2
    
    def calculateValue(self):
        return self.calculateThreat()
    
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
        self.Ready = False#True
    
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
        if self.FullWidget:
            try:
                self.FullWidget.updateFullInterface()
            except RuntimeError:
                self.FullWidget = None # This usually means that the widget is destroyed but I don't know of a better way to test for it...
    
    def getFullInterface(self):
        self.FullWidget = ModuleWidgets.WeaponWidget(self)
        return self.FullWidget
    
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
                    hit, targetDestroyed, damageDealt = targetShip.takeDamage(self.Damage,self.Accuracy,self.ShieldFactor,self.HullFactor,self.ShieldPiercing)
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
        d = super().save()
        d.update({
            "SoundEffectPath" : self.SoundEffectPath ,
            "Damage" : self.Damage ,
            "Accuracy" : self.Accuracy ,
            "ShieldFactor" : self.ShieldFactor ,
            "HullFactor" : self.HullFactor ,
            "Range" : self.Range ,
            "MinimalRange" : self.MinimalRange ,
            "ShieldPiercing" : self.ShieldPiercing ,
            "Ready" : self.Ready ,
        })
        return d
    
    def getCustomisableStats(self) -> 'dict[str,typing.Callable[[],AGeInput._TypeWidget]]':
        d = super().getCustomisableStats()
        if "Mass" in d: del d["Mass"]
        tech.addStatCustomizer(d,self,"Damage",AGeInput.Float)
        tech.addStatCustomizer(d,self,"Accuracy",AGeInput.Float)
        tech.addStatCustomizer(d,self,"ShieldFactor",AGeInput.Float,"Shield Damage Factor")
        tech.addStatCustomizer(d,self,"HullFactor",AGeInput.Float,"Hull Damage Factor")
        tech.addStatCustomizer(d,self,"Range",AGeInput.Int)
        tech.addStatCustomizer(d,self,"MinimalRange",AGeInput.Int,"Minimal Range")
        tech.addStatCustomizer(d,self,"ShieldPiercing",AGeInput.Bool,"Shield Piercing")
        return d

class Weapon_Beam(Weapon):
    Name = "Beam Weapon Module"
    Buildable = True
    SoundEffectPath = "tempModels/SFX/phaser.wav"
    ModelPath = "Models/Simple Geometry/rod.ply"
    PenColourName = "Orange"
    
    def fireEffectAt(self, target:'ShipBase.ShipBase', hit:bool=True):
        laserEffect:p3dc.NodePath = ape.loadModel(self.ModelPath)
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
        d.update({
            "ModelPath" : self.ModelPath ,
            "PenColourName" : self.PenColourName ,
        })
        return d
