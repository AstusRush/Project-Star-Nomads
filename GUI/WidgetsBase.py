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
    from BaseClasses import ShipBase, FleetBase, BaseModules, HexBase
else:
    # These imports make Python happy
    #sys.path.append('../AstusPandaEngine')
    from AGeLib import *
    import AstusPandaEngine as ape
    from AstusPandaEngine import engine, base, render, loader
    from AstusPandaEngine import window as _window

from BaseClasses import get

class PandaWidget(ape.PandaWidget):
    pass

class FleetStats(QtWidgets.QSplitter):
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget']) -> None:
        super().__init__(parent=parent)
        self.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.FleetScrollWidget = QtWidgets.QScrollArea(self)
        self.FleetScrollWidget.setWidgetResizable(True)
        super().addWidget(self.FleetScrollWidget)
        self.FleetOverview = AGeWidgets.TightGridWidget(self)
        self.FleetScrollWidget.setWidget(self.FleetOverview)
        
        self.DetailScrollWidget = QtWidgets.QScrollArea(self)
        self.DetailScrollWidget.setWidgetResizable(True)
        super().addWidget(self.DetailScrollWidget)
        self.DetailView = AGeWidgets.TightGridWidget(self)
        self.DetailScrollWidget.setWidget(self.DetailView)
        
        self.LastDetailsWidget:QtWidgets.QWidget = None
    
    def addWidget(self, widget):
        #TODO: This should instead handle ShipQuickView widgets
        #REMINDER: If only on ShipQuickView is displayed it should directly open the full ShipInterface. This however must be managed at the point where addWidget is called...
        self.FleetOverview.layout().addWidget(widget)
    
    def removeWidget(self, widget):
        self.FleetOverview.layout().removeWidget(widget)
        self.DetailView = AGeWidgets.TightGridWidget(self)
        self.DetailScrollWidget.setWidget(self.DetailView)
        #if self.LastDetailsWidget:
        #    self.DetailView.layout().removeWidget(self.FleetOverview)
        #    self.LastDetailsWidget.destroy()
    
    def showDetails(self, widget): #TODO: if the ship gets destroyed this should get cleared and the clearing mechanism is currently bad in general
        self.DetailView = AGeWidgets.TightGridWidget(self)
        self.DetailScrollWidget.setWidget(self.DetailView)
        #if self.LastDetailsWidget:
        #    self.DetailView.layout().removeWidget(self.LastDetailsWidget)
        #    self.LastDetailsWidget.destroy()
        self.DetailView.layout().addWidget(widget)
        self.LastDetailsWidget = widget

class ShipQuickView(AGeWidgets.TightGridFrame): #TODO: Should This be part of the ShipInterface class?
    def __init__(self, ship: 'ShipBase.ShipBase') -> None:
        super().__init__(parent=None)
        self.ship = weakref.ref(ship)
        #TODO: This should be a button with an Icon of the ship as well as an HP and Shield bar and the name
        #       and information about the weapons that are ready (so that it is easy to see which weapons can still be used this turn)
        #       When pressing the button the full ship interface of the ship should be shown in FleetStats.DetailView
        #       There should also be a way to select ships to only perform actions on these like separating a fleet of flotilla)
        #TODO: When the ship gets destroyed this needs to remove itself and also needs to potentially remove the full interface
        #self.Button = self.addWidget(AGeWidgets.Button(self,"",lambda: self.showFullInterface()),0,0)
        self.Button = self.addWidget(AGeWidgets.ToolButton(self),0,0)
        self.Button.clicked.connect(lambda: self.showFullInterface())
        self.Button.setIcon(QtGui.QIcon(self.ship().Model.IconPath))
        self.Button.setIconSize(60,60)
        self.Label_Hull = self.addWidget(QtWidgets.QLabel(self),0,1)
        self.Label_HP = self.addWidget(QtWidgets.QLabel(self),0,2)
        if not get.engine().CurrentlyInBattle:
            self.updateInterface()
        else:
            self.Label_Weapons = self.addWidget(QtWidgets.QLabel(self),0,3)
            self.updateCombatInterface()
    
    def updateCombatInterface(self):
        self.Label_Hull.setText(f"Name: {self.ship().Name}\nClass: {self.ship().ClassName}")
        self.Label_HP.setText(f"Hull: {self.ship().Stats.HP_Hull}/{self.ship().Stats.HP_Hull_max}\nShields: {self.ship().Stats.HP_Shields}/{self.ship().Stats.HP_Shields_max}")
        w = [i for i in self.ship().Modules if hasattr(i,"Ready")]
        wa = [i for i in w if i.Ready]
        self.Label_Weapons.setText(f"Weapons: {len(wa)}/{len(w)}")
    
    def updateInterface(self):
        self.Label_Hull.setText(f"Name: {self.ship().Name}\nClass: {self.ship().ClassName}")
        self.Label_HP.setText(f"Hull: {self.ship().Stats.HP_Hull}/{self.ship().Stats.HP_Hull_max}\nShields: {self.ship().Stats.HP_Shields}/{self.ship().Stats.HP_Shields_max}")
        #w = [i for i in self.ship().Modules if hasattr(i,"Ready")]
        #wa = [i for i in w if i.Ready]
    
    def showFullInterface(self):
        if not get.engine().CurrentlyInBattle:
            get.window().UnitStatDisplay.showDetails(self.ship().Interface.getInterface())
        else:
            get.window().UnitStatDisplay.showDetails(self.ship().Interface.getCombatInterface())

class ShipInterface:
    def __init__(self, ship: 'ShipBase.ShipBase') -> None:
        self.ship = weakref.ref(ship)
        self.Label:QtWidgets.QLabel = None
        self.QuickView:'ShipQuickView' = None
    
    def getQuickView(self) -> QtWidgets.QWidget:
        self.QuickView = ShipQuickView(self.ship())
        return self.QuickView
    
    def getInterface(self) -> QtWidgets.QWidget:
        self.Frame = AGeWidgets.TightGridFrame()
        # Movement Points: {self.fleet().MovePoints}/{self.fleet().MovePoints_max}
        self.Label = self.Frame.addWidget(QtWidgets.QLabel(self.Frame))
        for i in self.ship().Modules:
            if hasattr(i,"getInterface"):
                self.Frame.addWidget(i.getInterface())
        self.updateInterface()
        return self.Frame
    
    def updateInterface(self):
        text = textwrap.dedent(f"""
        Class: {self.ship().ClassName}
        Name: {self.ship().Name}
        Hull: {self.ship().Stats.HP_Hull}/{self.ship().Stats.HP_Hull_max}
        Shields: {self.ship().Stats.HP_Shields}/{self.ship().Stats.HP_Shields_max}
        """)
        try:
            if self.Label:
                self.Label.setText(text)
                for i in self.ship().Modules:
                    if hasattr(i,"updateInterface"):
                        i.updateInterface()
        except RuntimeError:
            pass # This usually means that the widget is destroyed but I don't know of a better way to test for it...
        try:
            if self.QuickView:
                self.QuickView.updateInterface()
        except RuntimeError:
            pass # This usually means that the widget is destroyed but I don't know of a better way to test for it...
    
    def getCombatInterface(self) -> QtWidgets.QWidget:
        self.Frame = AGeWidgets.TightGridFrame()
        # Movement Points: {self.fleet().MovePoints}/{self.fleet().MovePoints_max}
        self.Label = self.Frame.addWidget(QtWidgets.QLabel(self.Frame))
        for i in self.ship().Modules:
            if hasattr(i,"getCombatInterface"):
                self.Frame.addWidget(i.getCombatInterface())
        self.updateCombatInterface()
        return self.Frame
    
    def updateCombatInterface(self):
        text = textwrap.dedent(f"""
        Class: {self.ship().ClassName}
        Name: {self.ship().Name}
        Hull: {self.ship().Stats.HP_Hull}/{self.ship().Stats.HP_Hull_max}
        Shields: {self.ship().Stats.HP_Shields}/{self.ship().Stats.HP_Shields_max}
        """)
        try:
            if self.Label:
                self.Label.setText(text)
                for i in self.ship().Modules:
                    if hasattr(i,"updateCombatInterface"):
                        i.updateCombatInterface()
        except RuntimeError:
            pass # This usually means that the widget is destroyed but I don't know of a better way to test for it...
        try:
            if self.QuickView:
                self.QuickView.updateCombatInterface()
        except RuntimeError:
            pass # This usually means that the widget is destroyed but I don't know of a better way to test for it...
