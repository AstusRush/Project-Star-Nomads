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
    from GUI import ModuleWidgets

from BaseClasses import get

#TODO: All widgets for ships and modules etc should be of a special class that resets the reference of the parent to itself to None when it gets destroyed
#       (and can do other cleanup work like clearing the Hex interaction functions)

class FleetStats(QtWidgets.QSplitter):
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget']) -> None:
        super().__init__(parent=parent)
        self.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.FleetScrollWidget = QtWidgets.QScrollArea(self)
        self.FleetScrollWidget.setWidgetResizable(True)
        super().addWidget(self.FleetScrollWidget)
        #TODO: Rename Fleets (All Fleets including enemies. After all it is up to the player how they call the enemy fleets. The enemy crew will still call their fleet however they want.)
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
        self.handleIcon()
        self.Label_Info = self.addWidget(QtWidgets.QLabel(self),0,1)
        self.Label_Def = self.addWidget(QtWidgets.QLabel(self),0,2)
        if not get.engine().CurrentlyInBattle:
            self.updateInterface()
        else:
            self.Label_Weapons = self.addWidget(QtWidgets.QLabel(self),0,3)
            self.updateCombatInterface()
    
    def handleIcon(self):
        if self.ship().Model.IconPath:
            self.Button.setIcon(QtGui.QIcon(self.ship().Model.IconPath))
            self.Button.setIconSize(60,60)
        else:
            self.Button.setText(self.ship().ClassName[0:3])
            self.Button.setMinimumSize(60,60)
    
    def updateCombatInterface(self):
        self.Label_Info.setText(f"Name: {self.ship().Name}\nClass: {self.ship().ClassName}\nMovement: {self.ship().Stats.MovementStr}")
        self.Label_Def.setText(f"Hull: {round(self.ship().Stats.HP_Hull,3)}/{round(self.ship().Stats.HP_Hull_max,3)}\nShields: {round(self.ship().Stats.HP_Shields,3)}/{round(self.ship().Stats.HP_Shields_max,3)}\nEvasion: {round(self.ship().Stats.Evasion,3)}")
        w = [i for i in self.ship().Modules if hasattr(i,"Ready")]
        wa = [i for i in w if i.Ready]
        self.Label_Weapons.setText(f"Weapons: {len(wa)}/{len(w)}")
    
    def updateInterface(self):
        self.Label_Info.setText(f"Name: {self.ship().Name}\nClass: {self.ship().ClassName}\nMovement: {self.ship().Stats.MovementStr}")
        self.Label_Def.setText(f"Hull: {round(self.ship().Stats.HP_Hull,3)}/{round(self.ship().Stats.HP_Hull_max,3)}\nShields: {round(self.ship().Stats.HP_Shields,3)}/{round(self.ship().Stats.HP_Shields_max,3)}")
        #w = [i for i in self.ship().Modules if hasattr(i,"Ready")]
        #wa = [i for i in w if i.Ready]
    
    def showFullInterface(self):
        if not get.engine().CurrentlyInBattle:
            get.window().UnitStatDisplay.showDetails(self.ship().Interface.getInterface())
        else:
            get.window().UnitStatDisplay.showDetails(self.ship().Interface.getCombatInterface())

class ShipInterface:
    #TODO: There should be a way to show the FULL interface for all modules so that one can see the combat stats while on the Campaign map and vice versa.
    #       But this should be an extra view so that the standard view only shows the relevant information for the current situation to not clutter the UI.
    #       This also means that all actions for the UI must be inoperable while in this special view to not allow a ship to fire its weapons on the campaign map...
    def __init__(self, ship: 'ShipBase.ShipBase') -> None:
        self.ship = weakref.ref(ship)
        self.InfoWindow:'InfoWindow' = None
        self.Frame:AGeWidgets.TightGridFrame = None
        self.FullInfoButton:AGeWidgets.Button = None
        self.Label:QtWidgets.QLabel = None
        self.QuickView:'ShipQuickView' = None
    
    def destroy(self):
        pass
    
    def getQuickView(self) -> QtWidgets.QWidget:
        self.QuickView = ShipQuickView(self.ship())
        return self.QuickView
    
    def select(self):
        if self.ship().fleet:
            #TODO: onHover should give a tooltip that informs the user about the interaction
            #TODO: The select button should be marked to signal that the ship is selected, clicking the button again should cancel the selection,
            #       and onClear should remove the marking of the button (if it still exists since the selection could have changed and thus removed the button!)
            get.engine().setHexInteractionFunctions(lambda h: (True,True), self.ship().interactWith, None, None)
        else:
            self.SelectButton.setText("Can not select:\nThe ship is not in a fleet")
    
    def getInterface(self) -> QtWidgets.QWidget:
        self.Frame = AGeWidgets.TightGridFrame()
        self.FullInfoButton = self.Frame.addWidget(AGeWidgets.Button(self.Frame, "Open Info Window", self.openInfoWindow))
        self.Label = self.Frame.addWidget(QtWidgets.QLabel(self.Frame))
        self.SelectButton = self.Frame.addWidget(AGeWidgets.Button(self.Frame, "Select", lambda: self.select()))
        for i in self.ship().Modules:
            if hasattr(i,"getInterface"):
                self.Frame.addWidget(i.getInterface())
        self.updateInterface()
        return self.Frame
    
    def updateInterface(self):
        self.updateInfoWindow()
        try:
            if self.Label:
                text = textwrap.dedent(f"""
                Name: {self.ship().Name}
                Class: {self.ship().ClassName}
                Hull: {round(self.ship().Stats.HP_Hull,3)}/{round(self.ship().Stats.HP_Hull_max,3)}
                Shields: {round(self.ship().Stats.HP_Shields,3)}/{round(self.ship().Stats.HP_Shields_max,3)}
                Movement: {round(self.ship().Stats.Movement_FTL[0],3)}/{round(self.ship().Stats.Movement_FTL[1],3)}
                Value: {round(self.ship().Stats.Value,3)}
                Threat: {round(self.ship().Stats.Threat,3)}
                Defensiveness: {round(self.ship().Stats.Defensiveness,3)}
                """).strip()
                self.Label.setText(text)
                for i in self.ship().Modules:
                    if hasattr(i,"updateInterface"):
                        i.updateInterface()
        except RuntimeError:
            self.Label = None # This usually means that the widget is destroyed but I don't know of a better way to test for it...
        try:
            if self.QuickView:
                self.QuickView.updateInterface()
        except RuntimeError:
            self.QuickView = None # This usually means that the widget is destroyed but I don't know of a better way to test for it...
    
    def getCombatInterface(self) -> QtWidgets.QWidget:
        self.Frame = AGeWidgets.TightGridFrame()
        self.FullInfoButton = self.Frame.addWidget(AGeWidgets.Button(self.Frame, "Open Info Window", self.openInfoWindow))
        self.Label = self.Frame.addWidget(QtWidgets.QLabel(self.Frame))
        self.SelectButton = self.Frame.addWidget(AGeWidgets.Button(self.Frame, "Select", lambda: self.select()))
        for i in self.ship().Modules:
            if hasattr(i,"getCombatInterface"):
                self.Frame.addWidget(i.getCombatInterface())
        self.updateCombatInterface()
        return self.Frame
    
    def updateCombatInterface(self):
        self.updateInfoWindow()
        try:
            if self.Label:
                text = textwrap.dedent(f"""
                Name: {self.ship().Name}
                Class: {self.ship().ClassName}
                Hull: {round(self.ship().Stats.HP_Hull,3)}/{round(self.ship().Stats.HP_Hull_max,3)}
                Shields: {round(self.ship().Stats.HP_Shields,3)}/{round(self.ship().Stats.HP_Shields_max,3)}
                Movement: {round(self.ship().Stats.Movement_Sublight[0],3)}/{round(self.ship().Stats.Movement_Sublight[1],3)}
                Evasion: {round(self.ship().Stats.Evasion,3)}
                Value: {round(self.ship().Stats.Value,3)}
                Threat: {round(self.ship().Stats.Threat,3)}
                Defensiveness: {round(self.ship().Stats.Defensiveness,3)}
                """).strip()
                self.Label.setText(text)
                for i in self.ship().Modules:
                    if hasattr(i,"updateCombatInterface"):
                        i.updateCombatInterface()
        except RuntimeError:
            self.Label = None # This usually means that the widget is destroyed but I don't know of a better way to test for it...
        try:
            if self.QuickView:
                self.QuickView.updateCombatInterface()
        except RuntimeError:
            self.QuickView = None # This usually means that the widget is destroyed but I don't know of a better way to test for it...
    
    def openInfoWindow(self):
        if self.InfoWindow is None:
            self.InfoWindow = InfoWindow(self.ship())
        else:
            self.InfoWindow.updateInfo()
        self.InfoWindow.show()
    
    def updateInfoWindow(self):
        if self.InfoWindow is not None:
            self.InfoWindow.updateInfo()


class InfoWindow(AWWF):
    def __init__(self, ship:'ShipBase.ShipBase'):
        super().__init__(parent=None, IncludeTopBar=True, initTopBar=True, IncludeStatusBar=True, IncludeErrorButton=True, FullscreenHidesBars=False)
        self.ship:'weakref.ref[ShipBase.ShipBase]' = weakref.ref(ship)
        self.FullInfoWidget = FullInfoWidget(self, ship)
        self.setCentralWidget(self.FullInfoWidget)
        self.setWindowTitle(f"Ship Info: {self.ship().Name}")
        self.StandardSize = (500, 700)
        self.positionReset()
    
    def updateInfo(self):
        self.FullInfoWidget.updateInfo()

class FullInfoWidget(QtWidgets.QScrollArea):
    def __init__(self, parent: "typing.Union[QtWidgets.QWidget,None]", ship:'ShipBase.ShipBase') -> None:
        super().__init__(parent)
        self.ship:'weakref.ref[ShipBase.ShipBase]' = weakref.ref(ship)
        self.updateInfo()
    
    def _init_UI(self):
        if isinstance(self.window(),InfoWindow):
            self.window().setWindowTitle(f"Ship Info: {self.ship().Name}")
        self.setWidgetResizable(True)
        self.Frame = AGeWidgets.TightGridFrame()
        self.setWidget(self.Frame)
        self.RefreshButton = self.Frame.addWidget(AGeWidgets.Button(self.Frame, "Refresh", lambda: self.updateInfo()))
        self.NameField = self.Frame.addWidget(AGeInput.Name(self.Frame, "Name: ", self.ship(), "Name"))
        self.ClassField = self.Frame.addWidget(AGeInput.Name(self.Frame, "Class: ", self.ship(), "ClassName"))
        self.Label = self.Frame.addWidget(QtWidgets.QLabel(self.Frame))
        self.ModuleWidgets:'list[ModuleWidgets.ModuleWidget]' = []
        for i in self.ship().Modules:
            self.ModuleWidgets.append(self.Frame.addWidget(i.getFullInterface()))
    
    def updateInfo(self):
        self._init_UI()
        try:
            if self.Label:
                text = textwrap.dedent(f"""
                Hull: {round(self.ship().Stats.HP_Hull,3)}/{round(self.ship().Stats.HP_Hull_max,3)}
                Shields: {round(self.ship().Stats.HP_Shields,3)}/{round(self.ship().Stats.HP_Shields_max,3)}
                Movement: {round(self.ship().Stats.Movement_Sublight[0],3)}/{round(self.ship().Stats.Movement_Sublight[1],3)}
                Evasion: {round(self.ship().Stats.Evasion,3)}
                Value: {round(self.ship().Stats.Value,3)}
                Threat: {round(self.ship().Stats.Threat,3)}
                Defensiveness: {round(self.ship().Stats.Defensiveness,3)}
                """).strip()
                self.Label.setText(text)
                for widget in self.ModuleWidgets:
                    widget.updateFullInterface()
        except RuntimeError:
            self.Label = None # This usually means that the widget is destroyed but I don't know of a better way to test for it...
        #try:
        #    if self.QuickView:
        #        self.QuickView.updateCombatInterface()
        #except RuntimeError:
        #    self.QuickView = None # This usually means that the widget is destroyed but I don't know of a better way to test for it...
