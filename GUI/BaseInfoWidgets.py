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

class HexInfoDisplay(QtWidgets.QSplitter):
    #MAYBE: Currently all of this is operated by the fleet in displayStats, getInterface, and updateInterface.
    #       Maybe hte code populating the UI should be moved here instead and the fleet simply calls the appropriate methods when appropriate.
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget']=None) -> None:
        super().__init__(parent=parent)
        self.setOrientation(QtCore.Qt.Orientation.Vertical)
        self.FleetScrollWidget = QtWidgets.QScrollArea(self)
        self.FleetScrollWidget.setWidgetResizable(True)
        self.HexText = QtWidgets.QLabel()
        super().addWidget(self.FleetScrollWidget)
        self.FleetOverview = AGeWidgets.TightGridWidget(self)
        self.FleetScrollWidget.setWidget(self.FleetOverview)
        
        self.DetailScrollWidget = QtWidgets.QScrollArea(self)
        self.DetailScrollWidget.setWidgetResizable(True)
        super().addWidget(self.DetailScrollWidget)
        self.DetailView = AGeWidgets.TightGridWidget(self)
        self.DetailScrollWidget.setWidget(self.DetailView)
        
        self.LastDetailsWidget:QtWidgets.QWidget = None
        get.app().S_HexSelectionChanged.connect(lambda: self.updateInfo())
        self.HexText = QtWidgets.QLabel()
        self.addWidget(self.HexText)
    
    def updateInfo(self):
        #MAYBE: Instead of updating immediately, this could trigger a 0.05 second timer which triggers the update to avoid repeated update calls in loops or similar situations
        #           Each new update call would then be ignored if the timer is already running or reset the time of the timer.
        if get.hexGrid().SelectedHex: self.HexText.setText(get.hexGrid().SelectedHex.Name)
        else: self.HexText.setText("")
        
        self._clearOld()
        self._addNew()
        self._updateAll()
    
    def _clearOld(self):
        hex_ = get.hexGrid().SelectedHex
        if not hex_: return self.clearAll()
        l = []
        if hex_.fleet and hex_.fleet().widget and not hex_.fleet().Hidden: l.append(hex_.fleet().widget())
        for backgroundFleet in hex_.content:
            if backgroundFleet().widget and not backgroundFleet().Hidden: l.append(backgroundFleet().widget())
        
        for widget in self.FleetOverview:
            if widget not in l and isinstance(widget, FleetStats):
                if TYPE_CHECKING: widget:'FleetStats' = widget
                if widget.fleet().IsMovingFrom:
                    if get.hexGrid().SelectedHex:
                        if widget.fleet().IsMovingFrom != get.hexGrid().SelectedHex.Coordinates:
                            self.removeWidget(widget)
                else:
                    self.removeWidget(widget)
        
        # Clear details view if no fleets are being displayed
        if not [widget for widget in self.FleetOverview if isinstance(widget, FleetStats)]:
            self.DetailView = AGeWidgets.TightGridWidget(self)
            self.DetailScrollWidget.setWidget(self.DetailView)
    
    def clearAll(self):
        for widget in self.FleetOverview:
            if isinstance(widget, FleetStats):
                if TYPE_CHECKING: widget:'FleetStats' = widget
                if widget.fleet().IsMovingFrom:
                    if get.hexGrid().SelectedHex:
                        if widget.fleet().IsMovingFrom != get.hexGrid().SelectedHex.Coordinates:
                            self.removeWidget(widget)
                else:
                    self.removeWidget(widget)
        
        # Clear details view if no fleets are being displayed
        if not [widget for widget in self.FleetOverview if isinstance(widget, FleetStats)]:
            self.DetailView = AGeWidgets.TightGridWidget(self)
            self.DetailScrollWidget.setWidget(self.DetailView)
    
    def _addNew(self):
        hex_ = get.hexGrid().SelectedHex
        if not hex_: return
        l = []
        if hex_.fleet and not hex_.fleet().widget: self._displayStats(hex_.fleet())
        for backgroundFleet in hex_.content:
            if not backgroundFleet().widget: self._displayStats(backgroundFleet())
        
        # Clear IsMoving flag. This is the main clearing point fo that flag. All others are merely backups for special situations
        if hex_.fleet: hex_.fleet().clearIsMovingFlag()
        for backgroundFleet in hex_.content:
            backgroundFleet().clearIsMovingFlag()
    
    def _updateAll(self):
        for widget in self.FleetOverview:
            if isinstance(widget, FleetStats):
                if TYPE_CHECKING: widget:'FleetStats' = widget
                widget.updateInterface()
    
    def _displayStats(self, fleet:typing.Union['FleetBase.Fleet','FleetBase.Flotilla'], display=True, forceRebuild=False):
        if display and not fleet.Hidden:
            if forceRebuild or not fleet.widget:
                w = FleetStats(self, fleet)
                fleet.widget = weakref.ref(w)
                self.addWidget(w)
            fleet.widget().updateInterface()
        else:
            #get.window().UnitStatDisplay.Text.setText("No unit selected")
            if fleet.widget:
                self.removeWidget(fleet.widget())
                #fleet.widget().deleteLater()
            fleet.widget = None
    
    def addWidget(self, widget:'QtWidgets.QWidget'):
        #TODO: This should instead handle ShipQuickView widgets
        self.FleetOverview.layout().addWidget(widget)
    
    def removeWidget(self, widget:'QtWidgets.QWidget'):
        if widget:
            if isinstance(widget, FleetStats) and widget.fleet:
                if TYPE_CHECKING: widget:'FleetStats' = widget
                self.clearDetailView(widget.fleet())
                widget.fleet().widget = None
            self.FleetOverview.layout().removeWidget(widget)
            widget.deleteLater()
        
        #if self.LastDetailsWidget:
        #    self.DetailView.layout().removeWidget(self.FleetOverview)
        #    self.FleetOverview.deleteLater()
        #    self.LastDetailsWidget.deleteLater()
    
    def clearDetailView(self, fleet:typing.Union['FleetBase.Fleet','FleetBase.Flotilla']):
        clear = False
        for widget in self.DetailView:
            if isinstance(widget, ShipQuickView) and widget.ship:
                if TYPE_CHECKING: widget:'ShipQuickView' = widget
                if widget.ship() in fleet.Ships:
                    clear = True
        if clear:
            self.DetailView = AGeWidgets.TightGridWidget(self)
            self.DetailScrollWidget.setWidget(self.DetailView)
    
    def showDetails(self, widget:'QtWidgets.QWidget'): #TODO: if the ship gets destroyed this should get cleared and the clearing mechanism is currently bad in general
        self.DetailView = AGeWidgets.TightGridWidget(self)
        self.DetailScrollWidget.setWidget(self.DetailView)
        #if self.LastDetailsWidget:
        #    self.DetailView.layout().removeWidget(self.LastDetailsWidget)
        #    self.FleetOverview.deleteLater()
        #    self.LastDetailsWidget.deleteLater()
        self.DetailView.layout().addWidget(widget)
        self.LastDetailsWidget = widget

class FleetStats(AGeWidgets.TightGridFrame):
    def __init__(self, parent: 'HexInfoDisplay', fleet: typing.Union['FleetBase.Fleet','FleetBase.Flotilla']) -> None:
        self.parentInfoDisplay = weakref.ref(parent)
        self.fleet = weakref.ref(fleet)
        super().__init__(parent=parent)
        fleet.widget = weakref.ref(self)
        self.makeInterface()
    
    #def displayStats(self, display=True, forceRebuild=False): #TODO: Overhaul this! The displayed information should not be the combat interface but the campaign interface!
    #    if display and not self.fleet().Hidden:
    #        if forceRebuild or not self.Widget:
    #            get.window().HexInfoDisplay.addWidget(self.getInterface())
    #        self.updateInterface()
    #    else:
    #        #get.window().UnitStatDisplay.Text.setText("No unit selected")
    #        if self.Widget:
    #            get.window().HexInfoDisplay.removeWidget(self.Widget)
    #            self.Widget.deleteLater()
    #        self.Widget = None
    
    def makeInterface(self): #TODO: Overhaul this! The displayed information should not be the combat interface but the campaign interface!
        self.NameInput = self.addWidget(AGeInput.Name(self,"Name",self.fleet(),"Name"))
        self.Label = self.addWidget(QtWidgets.QLabel(self))
        for ship in self.fleet().Ships:
            self.addWidget(ship.getQuickView())
    
    def updateInterface(self):
        for ship in self.fleet().Ships:
            ship.updateInterface()
        for widget in self:
            if isinstance(widget, ShipQuickView):
                if TYPE_CHECKING: widget:'ShipQuickView' = widget
                if (not widget.ship) or (widget.ship() not in self.fleet().Ships):
                    self.layout().removeWidget(widget)
        for ship in self.fleet().Ships:
            found = False
            for widget in self:
                if isinstance(widget, ShipQuickView):
                    if TYPE_CHECKING: widget:'ShipQuickView' = widget
                    if widget.ship and widget.ship() == ship:
                        found = True
                        break
            if not found: self.addWidget(ship.getQuickView())
        if self.fleet()._IsFleet:
            text = textwrap.dedent(f"""
            Team: {self.fleet().TeamName}
            Positions: {self.fleet().hex().Coordinates}
            Movement Points: {round(self.fleet().MovePoints,3)}/{round(self.fleet().MovePoints_max,3)}
            """).strip()
            # Hull HP: {[f"{i.Stats.HP_Hull}/{i.Stats.HP_Hull_max}" for i in self.Ships]}
            # Shield HP: {[f"{i.Stats.HP_Shields}/{i.Stats.HP_Shields_max}" for i in self.Ships]}
            #Hull: {self.HP_Hull}/{self.HP_Hull_max} (+{self.HP_Hull_Regeneration} per turn (halved if the ship took a single hit that dealt at least {self.NoticeableDamage} damage last turn))
            #Shields: {self.HP_Shields}/{self.HP_Shields_max} (+{self.HP_Shields_Regeneration} per turn (halved if the ship took a single hit that dealt at least {self.NoticeableDamage} damage last turn))
            #get.window().UnitStatDisplay.Text.setText(text)
            self.Label.setText(text)
        elif self.fleet()._IsFlotilla:
            text = textwrap.dedent(f"""
            Team: {self.fleet().Team}
            Positions: {self.fleet().hex().Coordinates}
            Movement Points: {round(self.fleet().MovePoints,3)}/{round(self.fleet().MovePoints_max,3)}
            """).strip()
            # Hull HP: {[f"{i.Stats.HP_Hull}/{i.Stats.HP_Hull_max}" for i in self.Ships]}
            # Shield HP: {[f"{i.Stats.HP_Shields}/{i.Stats.HP_Shields_max}" for i in self.Ships]}
            #Hull: {self.HP_Hull}/{self.HP_Hull_max} (+{self.HP_Hull_Regeneration} per turn (halved if the ship took a single hit that dealt at least {self.NoticeableDamage} damage last turn))
            #Shields: {self.HP_Shields}/{self.HP_Shields_max} (+{self.HP_Shields_Regeneration} per turn (halved if the ship took a single hit that dealt at least {self.NoticeableDamage} damage last turn))
            #get.window().UnitStatDisplay.Text.setText(text)
            self.Label.setText(text)
        
        if len(self.fleet().Ships) == 1 and not self.fleet().isBackgroundObject():
            get.window().HexInfoDisplay.showDetails(self.fleet().Ships[0].getInterface())

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
            get.window().HexInfoDisplay.showDetails(self.ship().Interface.getInterface())
        else:
            get.window().HexInfoDisplay.showDetails(self.ship().Interface.getCombatInterface())

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
    
    def getQuickView(self) -> 'ShipQuickView':
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
        try: #FIXME: When ending a battle while having open the InfoWindow self.Frame.addWidget() in the for-loop sometimes reports that the TightGridFrame no longer exists, despite self.Frame having been created just a couple lines earlier... Though I have not figured out how to reproduce it reliably...
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
        except:
            NC(2,"Could not set up Full Info Widget",exc=True)
    
    def updateInfo(self):
        self._init_UI()
        try:
            if self.Label:
                text = \
                f"Hull: {round(self.ship().Stats.HP_Hull,3)}/{round(self.ship().Stats.HP_Hull_max,3)}\n"\
                f"Shields: {round(self.ship().Stats.HP_Shields,3)}/{round(self.ship().Stats.HP_Shields_max,3)}\n"\
                f"Movement Sublight: {round(self.ship().Stats.Movement_Sublight[0],3)}/{round(self.ship().Stats.Movement_Sublight[1],3)}\n"\
                f"Movement FTL: {round(self.ship().Stats.Movement_FTL[0],3)}/{round(self.ship().Stats.Movement_FTL[1],3)}\n"\
                f"Evasion: {round(self.ship().Stats.Evasion,3)}\n"\
                f"Mass: {round(self.ship().Stats.Mass,3)}\n"\
                f"Value: {round(self.ship().Stats.Value,3)}\n"\
                f"Threat: {round(self.ship().Stats.Threat,3)}\n"\
                f"Defensiveness: {round(self.ship().Stats.Defensiveness,3)}\n"\
                f"{self.ship().resourceCost().text('Resource Value:')}\n"
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
