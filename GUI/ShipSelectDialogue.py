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

class ShipSelectDialogue(QtWidgets.QDialog):
    def __init__(self, parent:QtWidgets.QWidget=None, queryString:str="Select a ship", team:'typing.Union[None,int]'=None, fleet:'typing.Union[None,FleetBase.FleetBase]'=None) -> None:
        super().__init__(parent)
        self.SelectedShip = None
        self.setLayout(QtWidgets.QGridLayout(self))
        self.SelectorWidget = _SelectorWidget(self, queryString=queryString, team=team, fleet=fleet)
        self.layout().addWidget(self.SelectorWidget)
        self.setWindowTitle(queryString)

class _SelectorWidget(AGeWidgets.TightGridWidget):
    def __init__(self,
                    parent: ShipSelectDialogue,
                    queryString:str="Select a ship",
                    team:'typing.Union[None,int]'=None,
                    fleet:'typing.Union[None,FleetBase.FleetBase]'=None
                    ) -> None:
        super().__init__(parent, makeCompact=False)
        self.ShipSelectDialogue = parent
        self.Label = self.addWidget(QtWidgets.QLabel(queryString, self))
        self.ShipList = self.addWidget(ShipListWidget(self, team, fleet))
        self.SelectedLabel = self.addWidget(QtWidgets.QLabel("No Ship Selected", self))
        self.AbortButton = self.addWidget(AGeWidgets.Button(self, "Abort", lambda: self.ShipSelectDialogue.done(int(bool(None)))))
        self.ConfirmButton = self.addWidget(AGeWidgets.Button(self, "Confirm", lambda: self.ShipSelectDialogue.done(int(bool(self.parent().SelectedShip)))))
        self.ShipList.ShipList.itemDoubleClicked.connect(lambda item: self.selectShip(item))
        self.ShipList.ShipList.itemClicked.connect(lambda item: self.selectShip(item))
    
    def selectShip(self, item:'ShipItem'):
        self.parent().SelectedShip = item.data(100)
        self.SelectedLabel.setText(item.text())

class ShipListWidget(AGeWidgets.TightGridWidget):
    def __init__(self,
                    parent: ShipSelectDialogue,
                    team:'typing.Union[None,int]'=None,
                    fleet:'typing.Union[None,FleetBase.FleetBase]'=None
                    ) -> None:
        super().__init__(parent, makeCompact=False)
        self.ConfinedToTeam = team
        self.ConfinedToFleet = fleet
        #TODO: Add Name Filter
        if self.ConfinedToFleet is None and self.ConfinedToTeam is None:
            self.TeamFilter = self.addWidget(QtWidgets.QComboBox(self))
            self.TeamFilter.addItem("All", None)
            for teamID,team in get.unitManager().Teams.items():
                self.TeamFilter.addItem(team.name(), teamID)
            self.TeamFilter.setCurrentText("All")
            self.TeamFilter.currentIndexChanged.connect(lambda: self.populate())
        self.ShipList = self.addWidget(QtWidgets.QListWidget(self))
        self.populate()
    
    def populate(self):
        self.ShipList.clear()
        if self.ConfinedToFleet is not None:
            fleets = [self.ConfinedToFleet]
        elif self.ConfinedToTeam is not None:
            fleets = get.unitManager().Teams[self.ConfinedToTeam]
        elif self.TeamFilter.currentText() != "All":
            fleets = get.unitManager().Teams[self.TeamFilter.currentData()]
        else:
            fleets = []
            for team in get.unitManager().Teams.values():
                fleets.extend(team)
        
        for fleet in fleets:
            for ship in fleet.Ships:
                self.listShip(ship)
    
    def listShip(self, ship:'ShipBase.Ship') -> 'ShipItem':
        item = ShipItem()
        item.setText(f"Name: {ship.Name}\nClass: {ship.ClassName}\nFleet: {ship.fleet().Name}")
        item.setData(100, ship)
        self.ShipList.addItem(item)
        return item

class ShipItem(QtWidgets.QListWidgetItem):
    pass
