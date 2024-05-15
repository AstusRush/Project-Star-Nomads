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
from BaseClasses import HexBase
from BaseClasses import ShipBase
from BaseClasses import ModelBase
from BaseClasses import BaseModules
from BaseClasses import FleetBase
from GUI import ModuleWidgets
from Economy import Resources
from Tech import tech

if TYPE_CHECKING:
    from Economy import EconomyManager

class Economic(BaseModules._Economic):
    Buildable = False
    # Modules for economic purposes like educating and entertaining people (civilians and crew), harvesting or processing resources, growing food, and researching stuff.
    #MAYBE: Researching could be tied to other modules like sensors to scan stuff or special experimental weapons to test stuff or experimental shields to test stuff or... you get the idea
    Name = "Economic Module"
    
    def __init__(self) -> None:
        super().__init__()
        self.Widget:'ModuleWidgets.EconomicWidget' = None
        self.FullWidget:'ModuleWidgets.EconomicWidget' = None
    
    def getFullInterface(self):
        self.FullWidget = ModuleWidgets.EconomicWidget(self)
        return self.FullWidget

class Cargo(Economic):
    # Used to store resources
    Name = "Cargo Module"
    Buildable = True
    _Capacity = 20
    
    def __init__(self) -> None:
        super().__init__()
        self.Widget:'ModuleWidgets.CargoWidget' = None
        self.FullWidget:'ModuleWidgets.CargoWidget' = None
        self._StoredResources = Resources._ResourceDict()
        self._StoredResources.setCapacity(self.Capacity)
    
    @property
    def Capacity(self) -> float:
        return self._Capacity
    
    @Capacity.setter
    def Capacity(self, cap:float):
        #TODO: The way this should work is that we first create a copy of self._StoredResources
        #       then we change its capacity to the new value
        #       then we check if this new capacity is valid
        #       and then apply the new capacity to the self._StoredResources and change self._Capacity
        #       and if any of that fails we raise an appropriate exception and have not actually broken anything
        #   (maybe don't actually create the copy but instead just check the numbers... that would probably be cleaner... But this at least gets the idea across)
        self._Capacity = cap
        self._StoredResources.setCapacity(self._Capacity)
    
    def freeCapacity(self) -> float:
        return self._StoredResources.FreeCapacity
    
    def resourceCost(self) -> 'Resources._ResourceDict':
        return Resources._ResourceDict.new(
            Resources.Metals(self.Value/4),
            Resources.Crystals(self.Value/8),
        )
    
    def calculateValue(self):
        return self.Capacity /50
    
    def calculateMass(self):
        return self.Capacity /50
    
    def getFullInterface(self):
        self.FullWidget = ModuleWidgets.CargoWidget(self)
        return self.FullWidget
    
    def storedResources(self) -> Resources._ResourceDict:
        return self._StoredResources
    
    def getCustomisableStats(self) -> 'dict[str,typing.Callable[[],AGeInput._TypeWidget]]':
        d = super().getCustomisableStats()
        if "Mass" in d: del d["Mass"]
        tech.addStatCustomizer(d,self,"Capacity",AGeInput.Float) #CRITICAL: Does this work?
        return d
    
    def save(self) -> dict:
        """
        Returns a dictionary with all values (and their names) that need to be saved to fully recreate this module.\n
        This method is called automatically when this module is saved.\n
        Reimplement this method if you create custom values. But don't forget to call `d.update(super().save())` before returning the dict!
        """
        d = super().save()
        d.update({
            "_Capacity" : self._Capacity ,
            "_StoredResources" : self._StoredResources ,
        })
        return d
    
    #TODO: Write an interface for the content

class ConstructionModule(Economic):
    # Modules to construct new ships.
    #TODO: Make 2 variants: Enclosed (can move while constructing) and open (can not move while constructing)
    Name = "Construction Module"
    Buildable = True
    # ConstructionResourcesGeneratedPerTurn = 0.2 #NOTE: This is only a temporary system
    Mass = 1
    
    def __init__(self) -> None:
        super().__init__()
        self.Widget:ModuleWidgets.ConstructionModuleWidget = None
        self.FullWidget:ModuleWidgets.ConstructionModuleWidget = None
        # self.ConstructionResourcesStored = 0 #NOTE: This is only a temporary system
    
    def resourceCost(self) -> 'Resources._ResourceDict':
        return Resources._ResourceDict.new(
            Resources.Metals(self.Value*3/4),
            Resources.RareMetals(self.Value/8),
            Resources.Crystals(self.Value/4),
        )
    
    def calculateValue(self):
        return 10
    
    def handleNewCampaignTurn(self):
        pass # self.ConstructionResourcesStored += self.ConstructionResourcesGeneratedPerTurn #NOTE: This is only a temporary system
    
    def getInterface(self) -> QtWidgets.QWidget:
        self.Widget = ModuleWidgets.ConstructionModuleWidget(self)
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
        self.FullWidget = ModuleWidgets.ConstructionModuleWidget(self)
        return self.FullWidget
    
    def buildShip(self, ship:'ShipBase.Ship', model:'typing.Union[type[ModelBase.ShipModel],None]') -> bool:
        cost = ship.resourceCost()
        resourceDelta = self.availableResources() - cost
        if get.engine().CurrentlyInBattle:
            NC(2,"Could not construct ship: There is a battle taking place.\nThe engineers are too busy fighting to start the construction of a ship!")
            return False
        elif resourceDelta.anyNegative():
            NC(2, resourceDelta.text("Could not construct ship: insufficient resources\nResource shortages are negative, surplus is positive"))
            return False
        else:
            self.spend(cost)
            if model is None: ship.generateProceduralModel()
            else: ship.setModel(model())
            self.ship().fleet().addShip(ship)
            self.updateInterface()
            #TODO: update the fleet Quick View to show the new ship! Just calling self.ship().fleet().select does not work when the fleet is already selected
            #                                                             (though it should be part of the solution since the player probably wants to select the fleet that contains the newly constructed ship)
            NC(3, f"The ship \"{ship.Name}\" of the {ship.ClassName} Class has been constructed and is now part of {self.ship().fleet().Name}\n{cost.text('The construction costs:')}")
            return True
    
    def canSpend(self, r:'Resources._ResourceDict') -> bool:
        resourceDelta = self.availableResources() - r
        return (not resourceDelta.anyNegative()) and resourceDelta.UsedCapacity < self.ship().fleet().ResourceManager.capacity()
    
    def spend(self, r:'Resources._ResourceDict'):
        if not self.canSpend(r): raise Resources._InsufficientResourcesException()
        d = self.ship().fleet().ResourceManager.subtract(r)
        if d: NC(2, "Something went wrong while spending resources!", input=f"{self.canSpend() = }\n\n{r.text('Resources that should be spend:')}\n\n{d.text('Resources that have not been spend:')}")
    
    def save(self) -> dict:
        """
        Returns a dictionary with all values (and their names) that need to be saved to fully recreate this module.\n
        This method is called automatically when this module is saved.\n
        Reimplement this method if you create custom values. But don't forget to call `d.update(super().save())` before returning the dict!
        """
        d = super().save()
        d.update({
            "Value" : self.Value ,
            # "ConstructionResourcesGeneratedPerTurn" : self.ConstructionResourcesGeneratedPerTurn ,
            # "ConstructionResourcesStored" : self.ConstructionResourcesStored ,
        })
        return d
    
    def copy(self) -> "ConstructionModule":
        module = super().copy()
        # module.ConstructionResourcesStored = 0 #NOTE: This is only a temporary system
        return module
    
    def availableResources(self) -> Resources._ResourceDict:
        return self.ship().fleet().ResourceManager.storedResources()

class Refinery(Economic):
    # Modules to convert resources into other resources
    Name = "Undefined Refinery Module"
    Buildable = False
    Input:'list[Resources.Resource_]' = None
    Output:'list[Resources.Resource_]' = None
    
    def __init__(self) -> None:
        super().__init__()
        self.Widget:'ModuleWidgets.RefineryWidget' = None
        self.FullWidget:'ModuleWidgets.RefineryWidget' = None
        #CRITICAL: REFINERY MODULE
    
    def calculateValue(self):
        #CRITICAL: REFINERY MODULE
        return 1
    
    def calculateMass(self):
        #CRITICAL: REFINERY MODULE
        return 0.5
    
    def resourceCost(self) -> 'Resources._ResourceDict':
        #CRITICAL: REFINERY MODULE
        return Resources._ResourceDict.new(
            Resources.Metals(self.Value*3/4),
            Resources.RareMetals(self.Value/8),
            Resources.Crystals(self.Value/4),
        )
    
    def handleNewCampaignTurn(self):
        self.convertResources()
    
    def convertResources(self):
        available = self.ship().fleet().ResourceManager.storedResources()
        mul = 1
        for r in self.Input:
            mul = min(mul, available[r]/r)
        self.ship().fleet().ResourceManager.subtract(Resources._ResourceDict.fromList([mul*r for r in self.Input]))
        tooMuch = self.ship().fleet().ResourceManager.add(Resources._ResourceDict.fromList([mul*r for r in self.Output]))
        if tooMuch:
            #CRITICAL: prevent that this can even happen
            NC(1,tooMuch.text("Could not store all produced resources. The following resources were spaced:"),func="Refinery.convertResources",input=f"{self.Name = }\n{self.ship().Name = }\n{self.ship().fleet().Name = }")
            self.ship().fleet().hex().ResourcesFree += tooMuch
    
    def getInterface(self):
        self.Widget = ModuleWidgets.RefineryWidget(self)
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
        self.FullWidget = ModuleWidgets.RefineryWidget(self)
        return self.FullWidget
    
    def save(self) -> dict:
        """
        Returns a dictionary with all values (and their names) that need to be saved to fully recreate this module.\n
        This method is called automatically when this module is saved.\n
        Reimplement this method if you create custom values. But don't forget to call `d.update(super().save())` before returning the dict!
        """
        d = super().save()
        d.update({
            "Input" : self.Input ,
            "Output" : self.Output ,
        })
        return d
    
    def getCustomisableStats(self) -> 'dict[str,typing.Callable[[],AGeInput._TypeWidget]]':
        d = super().getCustomisableStats()
        if "Mass" in d: del d["Mass"]
        #tech.addStatCustomizer(d,self,"Capacity",AGeInput.Float)
        return d

class RecyclingModule(Refinery):
    # Module to convert salvage into other resources
    Name = "Recycling Module"
    Buildable = True
    Input:'list[Resources.Resource_]' = [Resources.Salvage(1)]
    Output:'list[Resources.Resource_]' = [Resources.Metals(0.5),Resources.Crystals(0.4),Resources.RareMetals(0.1)]

class OreRefineryModule(Refinery):
    # Module to convert ore into metals
    Name = "Ore Refinery Module"
    Buildable = True
    Input:'list[Resources.Resource_]' = [Resources.Ore(1)]
    Output:'list[Resources.Resource_]' = [Resources.Metals(1)]

class RareOreRefineryModule(Refinery):
    # Module to convert rare ore into rare metals
    Name = "Rare Ore Refinery Module"
    Buildable = True
    Input:'list[Resources.Resource_]' = [Resources.RareOre(1)]
    Output:'list[Resources.Resource_]' = [Resources.RareMetals(1)]

class HarvestModule(Economic):
    # Modules to harvest resources
    Name = "Undefined Harvest Module"
    Buildable = False
    HarvestRange = 0
    Input:'list[Resources.Resource_]' = None # What is collected from the hex
    Output:'list[Resources.Resource_]' = None # What is stored in the fleet (should be the same as `Input` in most cases but could be used for )
    
    def __init__(self) -> None:
        super().__init__()
        self.Widget:'ModuleWidgets.HarvestWidget' = None
        self.FullWidget:'ModuleWidgets.HarvestWidget' = None
        #CRITICAL: HARVEST MODULE
    
    def calculateValue(self):
        #CRITICAL: HARVEST MODULE
        return 1 * ((self.HarvestRange+1)**2)
    
    def calculateMass(self):
        #CRITICAL: HARVEST MODULE
        return 0.5
    
    def resourceCost(self) -> 'Resources._ResourceDict':
        #CRITICAL: HARVEST MODULE
        return Resources._ResourceDict.new(
            Resources.Metals(self.Value*3/4),
            Resources.RareMetals(self.Value/8),
            Resources.Crystals(self.Value/4),
        )
    
    def handleNewCampaignTurn(self):
        self.harvestResources()
    
    def harvestResources(self):
        #TODO: should not harvest the amount from each tile but in total!
        for h in self.ship().fleet().hex().getDisk(self.HarvestRange):
            self.harvestResourcesFromHex(h)
            self.harvestResourcesFromHexObjects(h)
    
    def harvestResourcesFromHex(self, hex_:"HexBase._Hex"):
        available = hex_.ResourcesHarvestable
        if not available: return
        mul = 1
        for r in self.Input:
            mul = min(mul, available[r]/r)
        mul = min(mul, self.ship().fleet().ResourceManager.freeCapacity() / Resources._ResourceDict.fromList([r for r in self.Input]).UsedCapacity)
        hex_.ResourcesHarvestable -= Resources._ResourceDict.fromList([mul*r for r in self.Input])
        tooMuch = self.ship().fleet().ResourceManager.add(Resources._ResourceDict.fromList([mul*r for r in self.Output]))
        if tooMuch:
            #VALIDATE: This case should be impossible but this is exactly why this message is helpful for debugging: If this case occurs something is broken
            text = tooMuch.text("Could not store all harvested resources. This should not happen. Please report this incident. The following resources were spaced:"),
            NC(1,text,input=f"{self.Name = }\n{self.ship().Name = }\n{self.ship().fleet().Name = }")
            hex_.ResourcesFree += tooMuch
    
    def harvestResourcesFromHexObjects(self, hex_:"HexBase._Hex"):
        try:
            if not hex_.fleet: return
            if hex_.fleet().team() != -1: return
            available = hex_.fleet().ResourceManager.storedResources()
            if not available: return
            mul = 1
            for r in self.Input:
                mul = min(mul, available[r]/r)
            mul = min(mul, self.ship().fleet().ResourceManager.freeCapacity() / Resources._ResourceDict.fromList([r for r in self.Input]).UsedCapacity)
            hex_.fleet().ResourceManager.subtract(Resources._ResourceDict.fromList([mul*r for r in self.Input]))
            tooMuch = self.ship().fleet().ResourceManager.add(Resources._ResourceDict.fromList([mul*r for r in self.Output]))
            if tooMuch:
                #VALIDATE: This case should be impossible but this is exactly why this message is helpful for debugging: If this case occurs something is broken
                text = tooMuch.text("Could not store all harvested resources. This should not happen. Please report this incident. The following resources were spaced:"),
                NC(1,text,input=f"{self.Name = }\n{self.ship().Name = }\n{self.ship().fleet().Name = }\nHarvested from {hex_.fleet().Name = }")
                hex_.ResourcesFree += tooMuch
            if not hex_.fleet().ResourceManager.storedResources():
                hex_.fleet().TeamRing.hide()
        except:
            NC(4,"Could not harvest resources due to exception",exc=True)
            return
    
    def getInterface(self):
        self.Widget = ModuleWidgets.HarvestWidget(self)
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
        self.FullWidget = ModuleWidgets.HarvestWidget(self)
        return self.FullWidget
    
    def save(self) -> dict:
        """
        Returns a dictionary with all values (and their names) that need to be saved to fully recreate this module.\n
        This method is called automatically when this module is saved.\n
        Reimplement this method if you create custom values. But don't forget to call `d.update(super().save())` before returning the dict!
        """
        d = super().save()
        d.update({
            "HarvestRange" : self.HarvestRange ,
            "Input" : self.Input ,
            "Output" : self.Output ,
        })
        return d
    
    def getCustomisableStats(self) -> 'dict[str,typing.Callable[[],AGeInput._TypeWidget]]':
        d = super().getCustomisableStats()
        if "Mass" in d: del d["Mass"]
        tech.addStatCustomizer(d,self,"HarvestRange",AGeInput.Int)
        return d

class SalvageModule(HarvestModule):
    Name = "Salvage Module"
    Buildable = True
    HarvestRange = 0
    Input:'list[Resources.Resource_]' = [Resources.Salvage(2)]
    Output:'list[Resources.Resource_]' = [Resources.Salvage(2)]

class OreMiningModule(HarvestModule):
    Name = "Ore Mining Module"
    Buildable = True
    HarvestRange = 1
    Input:'list[Resources.Resource_]' = [Resources.Ore(2)]
    Output:'list[Resources.Resource_]' = [Resources.Ore(2)]

class RareOreMiningModule(HarvestModule):
    Name = "Rare Ore Mining Module"
    Buildable = True
    HarvestRange = 1
    Input:'list[Resources.Resource_]' = [Resources.RareOre(0.5)]
    Output:'list[Resources.Resource_]' = [Resources.RareOre(0.5)]

class CrystalMiningModule(HarvestModule):
    Name = "Crystal Mining Module"
    Buildable = True
    HarvestRange = 1
    Input:'list[Resources.Resource_]' = [Resources.Crystals(1.5)]
    Output:'list[Resources.Resource_]' = [Resources.Crystals(1.5)]

class Asteroid_Resources(Cargo):
    Name = "Resource Rich Asteroid"
    Buildable = False
    _Capacity = 200
