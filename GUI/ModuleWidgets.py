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

if TYPE_CHECKING:
    from BaseClasses import ShipBase, FleetBase, BaseModules, HexBase
    from Economy import BaseEconomicModules

from BaseClasses import get
from GUI import BaseInfoWidgets
from Economy import Resources

""" Template for constructor: (replace # with the module name)
class #Widget(WidgetsBase.ModuleWidget):
    module: weakref.ref[BaseModules.#] = None
    def __init__(self, module:typing.Optional['BaseModules.#'] = None) -> None:
        super().__init__(parent=None, module=module)

List of all the module names:

l = [
    'Hull',
    'HullPlating',
    'Engine',
    'Thruster',
    'Shield',
    'Quarters',
    'Cargo',
    'Hangar',
    'ConstructionModule',
    'Sensor',
    'Economic',
    'Augment',
    'Support',
    'Special',
    'Weapon',
]
"""

class ModuleWidget(AGeWidgets.TightGridWidget):
    module: 'weakref.ref[BaseModules.Module]' = None
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget'] = None, module:typing.Optional['BaseModules.Module'] = None) -> None:
        from BaseClasses import BaseModules
        if isinstance(parent,BaseModules.Module):
            parent, module = module, parent
        super().__init__(parent=parent)
        self.module = weakref.ref(module)
    
    def updateFullInterface(self):
        if not hasattr(self,"Label"):
            self.Label = self.addWidget(QtWidgets.QLabel(self))
        m:'BaseModules.Module' = self.module()
        self.Label.setText(f"{m.Name}"
                            f"\n\tMass: {round(m.Mass,3)}"
                            f"\n\tValue: {round(m.Value,3)}"
                            f"\n\tThreat: {round(m.Threat,3)}"
                            )

class HullWidget(ModuleWidget):
    module: 'weakref.ref[BaseModules.Hull]' = None
    def __init__(self, module:typing.Optional['BaseModules.Hull'] = None) -> None:
        super().__init__(parent=None, module=module)
    
    def updateFullInterface(self):
        if not hasattr(self,"Label"):
            self.Label = self.addWidget(QtWidgets.QLabel(self))
        m = self.module()
        self.Label.setText( f"{m.Name}"
                            f"\n\tMass: {round(m.Mass,3)}"
                            f"\n\tValue: {round(m.Value,3)}"
                            f"\n\tThreat: {round(m.Threat,3)}"
                            f"\n\tHull HP: {round(m.HP_Hull,3)}/{round(m.HP_Hull_max,3)}"
                            f"\n\tRegeneration: {round(m.HP_Hull_Regeneration,3)} per turn"
                            f"\n\tEvasion: {round(m.Evasion,3)}"
                            )

class HullPlatingWidget(ModuleWidget):
    module: 'weakref.ref[BaseModules.HullPlating]' = None
    def __init__(self, module:typing.Optional['BaseModules.HullPlating'] = None) -> None:
        super().__init__(parent=None, module=module)

class EngineWidget(ModuleWidget):
    module: 'weakref.ref[BaseModules.Engine]' = None
    def __init__(self, module:typing.Optional['BaseModules.Engine'] = None) -> None:
        super().__init__(parent=None, module=module)
        self.Label = self.addWidget(QtWidgets.QLabel(self))
    
    def updateFullInterface(self):
        self.updateInterface()
    
    def updateInterface(self):
        c,m = self.module().ship().Stats.Movement_FTL
        c,m = round(c,3),round(m,3)
        self.Label.setText( f"{self.module().Name} (FLT Engine):"
                            f"\n\tMovement: {c}/{m}"
                            f"\n\tThrust: {round(self.module().RemainingThrust,3)}/{round(self.module().Thrust,3)}"
                            f"\n\tShip Mass: {round(self.module().ship().Stats.Mass,3)}"
                            )

class ThrusterWidget(ModuleWidget):
    module: 'weakref.ref[BaseModules.Thruster]' = None
    def __init__(self, module:typing.Optional['BaseModules.Thruster'] = None) -> None:
        super().__init__(parent=None, module=module)
        self.Label = self.addWidget(QtWidgets.QLabel(self))
    
    def updateFullInterface(self):
        self.updateInterface()
    
    def updateInterface(self):
        c,m = self.module().ship().Stats.Movement_Sublight
        c,m = round(c,3),round(m,3)
        self.Label.setText( f"{self.module().Name} (Sublight Thruster):"
                            f"\n\tMovement: {c}/{m}"
                            f"\n\tThrust: {round(self.module().RemainingThrust,3)}/{round(self.module().Thrust,3)}"
                            f"\n\tShip Mass: {round(self.module().ship().Stats.Mass,3)}"
                            )

class ShieldWidget(ModuleWidget):
    module: 'weakref.ref[BaseModules.Shield]' = None
    def __init__(self, module:typing.Optional['BaseModules.Shield'] = None) -> None:
        super().__init__(parent=None, module=module)
        self.Label = self.addWidget(QtWidgets.QLabel(self))
    
    def updateFullInterface(self):
        self.updateInterface()
    
    def updateInterface(self):
        self.Label.setText( f"{self.module().Name} (Shield):"
                            f"\n\tHP: {round(self.module().HP_Shields,3)}/{round(self.module().HP_Shields_max,3)}"
                            f"\n\tRegeneration per turn: {round(self.module().HP_Shields_Regeneration,3)} (Halved if damaged last turn)\n\t(It takes one turn to reactivate the shields if their HP reaches 0)"
                            )

class QuartersWidget(ModuleWidget):
    module: 'weakref.ref[BaseModules.Quarters]' = None
    def __init__(self, module:typing.Optional['BaseModules.Quarters'] = None) -> None:
        super().__init__(parent=None, module=module)

class HangarWidget(ModuleWidget):
    module: 'weakref.ref[BaseModules.Hangar]' = None
    def __init__(self, module:typing.Optional['BaseModules.Hangar'] = None) -> None:
        super().__init__(parent=None, module=module)

class ConstructionModuleWidget(ModuleWidget):
    module: 'weakref.ref[BaseEconomicModules.ConstructionModule]' = None
    def __init__(self, module:typing.Optional['BaseEconomicModules.ConstructionModule'] = None) -> None:
        super().__init__(parent=None, module=module)
        self.Label = self.addWidget(QtWidgets.QLabel(self))
        if self.module().isPlayer(): self.ConstructionWindowButton = self.addWidget(AGeWidgets.Button(self, "Open construction window", lambda: self.openConstructionWindow()))
        #TODO: implement this build mechanic in the construction window to load all of the ship designs
        #self.ShipComboBox = self.addWidget(QtWidgets.QComboBox(self))
        #self.populateBuildList()
        #if self.module().isPlayer(): self.BuildButton = self.addWidget(AGeWidgets.Button(self, "Build", lambda: self.build()))
        self.MessageLabel = self.addWidget(QtWidgets.QLabel(self))
    
    def updateFullInterface(self):
        self.updateInterface()
    
    def updateInterface(self):
        self.Label.setText( f"{self.module().Name} (Construction Module):"
                            #f"\n\tConstruction resources stored: {self.module().ConstructionResourcesStored}"
                            #f"\n\tConstruction resources generated per turn: {self.module().ConstructionResourcesGeneratedPerTurn}"
                            )
    
    #def populateBuildList(self):
    #    l = []
    #    for name, ship in get.shipClasses().items():
    #        s = ship(False)
    #        l.append(f"{s.Stats.Value} - {name}")
    #        s.destroy()
    #    self.ShipComboBox.addItems(l)
    
    #def build(self):
    #    if not self.module().isPlayer():
    #        self.MessageLabel.setText("You can not build ships for the enemy")
    #        return False
    #    ship = get.shipClasses()[self.ShipComboBox.currentText().split(" - ",1)[1]]()
    #    if ship.Stats.Value > self.module().ConstructionResourcesStored:
    #        message = f"Not enough resources to build that ship! The ship costs {ship.Stats.Value} but you only have {self.module().ConstructionResourcesStored}"
    #        self.MessageLabel.setText(message)
    #        ship.destroy()
    #    else:
    #        self.module().ConstructionResourcesStored -= ship.Stats.Value
    #        self.module().ship().fleet().addShip(ship)
    #        self.updateInterface()
    
    def openConstructionWindow(self):
        if not self.module().isPlayer(): return False
        from GUI import ConstructionWindow
        ###### TEMP:
        try:
            get.engine().constructionWindow.close()
            get.engine().constructionWindow.deleteLater()
        except: pass
        import importlib
        importlib.reload(ConstructionWindow)
        ###### Also remove the self. as this should not be a member
        get.engine().constructionWindow = ConstructionWindow.ConstructionWindow()
        get.engine().constructionWindow.setConstructionModule(self.module())
        get.engine().constructionWindow.show()
        App().processEvents()
        get.engine().constructionWindow.positionReset()
        App().processEvents()
        get.engine().constructionWindow.activateWindow()
        #NC(2,"The construction window is very much a work in progress.\nThere are barely any checks to prevent that something goes wrong!\nYou have been warned!",DplStr="Attention! WIP!",unique=True)

class SensorWidget(ModuleWidget):
    module: 'weakref.ref[BaseModules.Sensor]' = None
    def __init__(self, module:typing.Optional['BaseModules.Sensor'] = None) -> None:
        super().__init__(parent=None, module=module)
        self.Label = self.addWidget(QtWidgets.QLabel(self))
    
    def updateFullInterface(self):
        self.updateInterface()
    
    def updateInterface(self):
        self.Label.setText( f"{self.module().Name} (Sensors):"
                            f"\n\tLow Resolution: {round(self.module().LowRange,3)}"
                            f"\n\tMedium Resolution: {round(self.module().MediumRange,3)}"
                            f"\n\tHigh Resolution: {round(self.module().HighRange,3)}"
                            f"\n\tPerfect Resolution: {round(self.module().PerfectRange,3)}"
                            )

class EconomicWidget(ModuleWidget):
    module: 'weakref.ref[BaseEconomicModules.Economic]' = None
    def __init__(self, module:typing.Optional['BaseEconomicModules.Economic'] = None) -> None:
        super().__init__(parent=None, module=module)

class CargoWidget(ModuleWidget):
    module: 'weakref.ref[BaseEconomicModules.Cargo]' = None
    def __init__(self, module:typing.Optional['BaseEconomicModules.Cargo'] = None) -> None:
        super().__init__(parent=None, module=module)
        self.Label = self.addWidget(QtWidgets.QLabel(self))
        if advancedMode(): self.DEBUG_AddResourceButton = self.addWidget(AGeWidgets.Button(self, "DEBUG: Fill resources", lambda: self.debug_addResources()))
    
    def debug_addResources(self):
        self.module().StoredResources.set(Resources.Metals(self.module().Capacity/3))
        self.module().StoredResources.set(Resources.Crystals(self.module().Capacity/3))
        self.module().StoredResources.set(Resources.RareMetals(self.module().Capacity/6))
        self.module().StoredResources.set(Resources.AdvancedComponents(self.module().Capacity/6.001))
        self.updateInterface()
    
    def updateFullInterface(self):
        self.updateInterface()
    
    def updateInterface(self):
        self.Label.setText( self.module().StoredResources.text(f"{self.module().Name} (Capacity {round(self.module().StoredResources.UsedCapacity,5)} / {round(self.module().Capacity,5)})") )

class AugmentWidget(ModuleWidget):
    module: 'weakref.ref[BaseModules.Augment]' = None
    def __init__(self, module:typing.Optional['BaseModules.Augment'] = None) -> None:
        super().__init__(parent=None, module=module)

class SupportWidget(ModuleWidget):
    module: 'weakref.ref[BaseModules.Support]' = None
    def __init__(self, module:typing.Optional['BaseModules.Support'] = None) -> None:
        super().__init__(parent=None, module=module)

class SpecialWidget(ModuleWidget):
    module: 'weakref.ref[BaseModules.Special]' = None
    def __init__(self, module:typing.Optional['BaseModules.Special'] = None) -> None:
        super().__init__(parent=None, module=module)

class MicroJumpDriveWidget(SpecialWidget):
    module: 'weakref.ref[BaseModules.MicroJumpDrive]' = None
    def __init__(self, module:typing.Optional['BaseModules.MicroJumpDrive'] = None) -> None:
        super().__init__(module=module)
        self.Label = self.addWidget(QtWidgets.QLabel(self))
        if self.module().isPlayer(): self.Button = self.addWidget(AGeWidgets.Button(self,"Jump",lambda: self.jump()))
    
    def updateFullInterface(self):
        self.updateInterface()
    
    def updateInterface(self):
        self.Label.setText( f"{self.module().Name} is {'Ready' if self.module().Charge >= 1 else 'Charging'}"
                            f"\n\tCharge: {round(self.module().Charge,3)}/{round(self.module().MaxCharges,3)} (+{1/round(self.module().Cooldown,3)} per Turn)"
                            f"\n\tRange: {round(self.module().Range,3)}"
                            )
    
    def jump(self):
        if self.module().Charge >= 1:
            try:
                self.module().jump()
            except:
                NC(2,"Can not Jump!", exc=True)
        else:
            self.Button.setText("Not enough charge!")

class WeaponWidget(ModuleWidget):
    module: 'weakref.ref[BaseModules.Weapon]' = None
    def __init__(self, module:typing.Optional['BaseModules.Weapon'] = None) -> None:
        super().__init__(parent=None, module=module)
        self.Label = self.addWidget(QtWidgets.QLabel(self))
    
    def updateFullInterface(self):
        self.updateInterface()
    
    def updateInterface(self):
        self.Label.setText( f"{self.module().Name} is {'Ready' if self.module().Ready else 'Used'}"
                            f"\n\tRange: {round(self.module().Range,3)}"
                            f"\n\tDamage: {round(self.module().Damage,3)}"
                            f"\n\tAccuracy: {round(self.module().Accuracy,3)}"
                            f"\n\tHullFactor: {round(self.module().HullFactor,3)}"
                            f"\n\tShieldFactor: {round(self.module().ShieldFactor,3)}"
                            )
