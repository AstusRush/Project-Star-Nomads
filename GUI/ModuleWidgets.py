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

from BaseClasses import get
from GUI import WidgetsBase

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

class HullWidget(WidgetsBase.ModuleWidget):
    module: 'weakref.ref[BaseModules.Hull]' = None
    def __init__(self, module:typing.Optional['BaseModules.Hull'] = None) -> None:
        super().__init__(parent=None, module=module)

class HullPlatingWidget(WidgetsBase.ModuleWidget):
    module: 'weakref.ref[BaseModules.HullPlating]' = None
    def __init__(self, module:typing.Optional['BaseModules.HullPlating'] = None) -> None:
        super().__init__(parent=None, module=module)

class EngineWidget(WidgetsBase.ModuleWidget):
    module: 'weakref.ref[BaseModules.Engine]' = None
    def __init__(self, module:typing.Optional['BaseModules.Engine'] = None) -> None:
        super().__init__(parent=None, module=module)
        self.Label = self.addWidget(QtWidgets.QLabel(self))
    
    def updateInterface(self):
        c,m = self.module().ship().Stats.Movement_FTL
        c,m = round(c,3),round(m,3)
        self.Label.setText(f"{self.module().Name} (FLT Engine):\n\tMovement: {c}/{m}\n\tThrust: {round(self.module().RemainingThrust,3)}/{round(self.module().Thrust,3)}\n\tShip Mass: {round(self.module().ship().Stats.Mass,3)}")

class ThrusterWidget(WidgetsBase.ModuleWidget):
    module: 'weakref.ref[BaseModules.Thruster]' = None
    def __init__(self, module:typing.Optional['BaseModules.Thruster'] = None) -> None:
        super().__init__(parent=None, module=module)
        self.Label = self.addWidget(QtWidgets.QLabel(self))
    
    def updateInterface(self):
        c,m = self.module().ship().Stats.Movement_Sublight
        c,m = round(c,3),round(m,3)
        self.Label.setText(f"{self.module().Name} (Sublight Thruster):\n\tMovement: {c}/{m}\n\tThrust: {round(self.module().RemainingThrust,3)}/{round(self.module().Thrust,3)}\n\tShip Mass: {round(self.module().ship().Stats.Mass,3)}")

class ShieldWidget(WidgetsBase.ModuleWidget):
    module: 'weakref.ref[BaseModules.Shield]' = None
    def __init__(self, module:typing.Optional['BaseModules.Shield'] = None) -> None:
        super().__init__(parent=None, module=module)
        self.Label = self.addWidget(QtWidgets.QLabel(self))
    
    def updateInterface(self):
        self.Label.setText(f"{self.module().Name} (Shield):\n\tHP: {round(self.module().HP_Shields,3)}/{round(self.module().HP_Shields_max,3)}\n\tRegeneration per turn: {round(self.module().HP_Shields_Regeneration,3)} (Halved if damaged last turn)\n\t(It takes one turn to reactivate the shields if their HP reaches 0)")

class QuartersWidget(WidgetsBase.ModuleWidget):
    module: 'weakref.ref[BaseModules.Quarters]' = None
    def __init__(self, module:typing.Optional['BaseModules.Quarters'] = None) -> None:
        super().__init__(parent=None, module=module)

class CargoWidget(WidgetsBase.ModuleWidget):
    module: 'weakref.ref[BaseModules.Cargo]' = None
    def __init__(self, module:typing.Optional['BaseModules.Cargo'] = None) -> None:
        super().__init__(parent=None, module=module)

class HangarWidget(WidgetsBase.ModuleWidget):
    module: 'weakref.ref[BaseModules.Hangar]' = None
    def __init__(self, module:typing.Optional['BaseModules.Hangar'] = None) -> None:
        super().__init__(parent=None, module=module)

class ConstructionModuleWidget(WidgetsBase.ModuleWidget):
    module: 'weakref.ref[BaseModules.ConstructionModule]' = None
    def __init__(self, module:typing.Optional['BaseModules.ConstructionModule'] = None) -> None:
        super().__init__(parent=None, module=module)
        self.Label = self.addWidget(QtWidgets.QLabel(self))
        if self.module().isPlayer(): self.ConstructionWindowButton = self.addWidget(AGeWidgets.Button(self, "Open construction window", lambda: self.openConstructionWindow()))
        self.ShipComboBox = self.addWidget(QtWidgets.QComboBox(self))
        self.populateBuildList()
        if self.module().isPlayer(): self.BuildButton = self.addWidget(AGeWidgets.Button(self, "Build", lambda: self.build()))
        if advancedMode(): self.DEBUG_AddResourceButton = self.addWidget(AGeWidgets.Button(self, "DEBUG: Add resources", lambda: self.debug_addResources()))
        self.MessageLabel = self.addWidget(QtWidgets.QLabel(self))
    
    def debug_addResources(self):
        self.module().ConstructionResourcesStored += 100
        self.updateInterface()
    
    def updateInterface(self):
        self.Label.setText(f"{self.module().Name} (Construction Module):\n\tConstruction resources stored: {self.module().ConstructionResourcesStored}\n\tConstruction resources generated per turn: {self.module().ConstructionResourcesGeneratedPerTurn}")
    
    def populateBuildList(self):
        l = []
        for name, ship in get.shipClasses().items():
            s = ship(False)
            l.append(f"{s.Stats.Value} - {name}")
            s.destroy()
        self.ShipComboBox.addItems(l)
    
    def build(self):
        if not self.module().isPlayer():
            self.MessageLabel.setText("You can not build ships for the enemy")
            return False
        ship = get.shipClasses()[self.ShipComboBox.currentText().split(" - ",1)[1]]()
        if ship.Stats.Value > self.module().ConstructionResourcesStored:
            message = f"Not enough resources to build that ship! The ship costs {ship.Stats.Value} but you only have {self.module().ConstructionResourcesStored}"
            self.MessageLabel.setText(message)
            ship.destroy()
        else:
            self.module().ConstructionResourcesStored -= ship.Stats.Value
            self.module().ship().fleet().addShip(ship)
            self.updateInterface()
            #TODO: update the fleet Quick View to show the new ship!
    
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

class SensorWidget(WidgetsBase.ModuleWidget):
    module: 'weakref.ref[BaseModules.Sensor]' = None
    def __init__(self, module:typing.Optional['BaseModules.Sensor'] = None) -> None:
        super().__init__(parent=None, module=module)

class EconomicWidget(WidgetsBase.ModuleWidget):
    module: 'weakref.ref[BaseModules.Economic]' = None
    def __init__(self, module:typing.Optional['BaseModules.Economic'] = None) -> None:
        super().__init__(parent=None, module=module)

class AugmentWidget(WidgetsBase.ModuleWidget):
    module: 'weakref.ref[BaseModules.Augment]' = None
    def __init__(self, module:typing.Optional['BaseModules.Augment'] = None) -> None:
        super().__init__(parent=None, module=module)

class SupportWidget(WidgetsBase.ModuleWidget):
    module: 'weakref.ref[BaseModules.Support]' = None
    def __init__(self, module:typing.Optional['BaseModules.Support'] = None) -> None:
        super().__init__(parent=None, module=module)

class SpecialWidget(WidgetsBase.ModuleWidget):
    module: 'weakref.ref[BaseModules.Special]' = None
    def __init__(self, module:typing.Optional['BaseModules.Special'] = None) -> None:
        super().__init__(parent=None, module=module)

class MicroJumpDriveWidget(SpecialWidget):
    module: 'weakref.ref[BaseModules.MicroJumpDrive]' = None
    def __init__(self, module:typing.Optional['BaseModules.MicroJumpDrive'] = None) -> None:
        super().__init__(module=module)
        self.Label = self.addWidget(QtWidgets.QLabel(self))
        if self.module().isPlayer(): self.Button = self.addWidget(AGeWidgets.Button(self,"Jump",lambda: self.jump()))
    
    def updateInterface(self):
        self.Label.setText( f"{self.module().Name} is {'Ready' if self.module().Charge >= 1 else 'Charging'}"
                            f"\n\tCharge: {round(self.module().Charge,3)}/{round(self.module().MaxCharges,3)} (+{1/round(self.module().Cooldown,3)} per Turn)"
                            f"\n\tRange: {round(self.module().Range,3)}"
                            )
    
    def jump(self):
        if self.module().Charge >= 1:
            self.module().jump()
        else:
            self.Button.setText("Not enough charge!")

class WeaponWidget(WidgetsBase.ModuleWidget):
    module: 'weakref.ref[BaseModules.Weapon]' = None
    def __init__(self, module:typing.Optional['BaseModules.Weapon'] = None) -> None:
        super().__init__(parent=None, module=module)
        self.Label = self.addWidget(QtWidgets.QLabel(self))
    
    def updateInterface(self):
        self.Label.setText( f"{self.module().Name} is {'Ready' if self.module().Ready else 'Used'}"
                            f"\n\tRange: {round(self.module().Range,3)}"
                            f"\n\tDamage: {round(self.module().Damage,3)}"
                            f"\n\tAccuracy: {round(self.module().Accuracy,3)}"
                            f"\n\tHullFactor: {round(self.module().HullFactor,3)}"
                            f"\n\tShieldFactor: {round(self.module().ShieldFactor,3)}"
                            )
