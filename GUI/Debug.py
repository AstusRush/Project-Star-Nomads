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


class DebugMenu(QtWidgets.QScrollArea):
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget'] = None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.MainWidget = AGeWidgets.TightGridWidget(self)
        self.setWidget(self.MainWidget)
        
        self.DebugWidget = self.MainWidget.addWidget(DebugWidget(self.MainWidget))

class DebugWidget(AGeWidgets.TightGridFrame):
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget'] = None) -> None:
        super().__init__(parent)
        self.Label = self.addWidget(QtWidgets.QLabel("Debug",self))
        self.HeadlineLine = self.addWidget(QtWidgets.QFrame(self))
        self.HeadlineLine.setFrameShape(QtWidgets.QFrame.HLine)
        self.HeadlineLine.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.ShowDevToolTabsButton = self.addWidget(AGeWidgets.Button(self,"Show Dev Tool Tabs", lambda: self.showDevToolTabs()))
        self.SpawnAsteroidButton = self.addWidget(AGeWidgets.Button(self,"Spawn Asteroid at selected hex", lambda: spawnAsteroidAtSelectedHex()))
        self.SpawnSalvageButton = self.addWidget(AGeWidgets.Button(self,"Spawn 1 unit of salvage at selected hex", lambda: spawnSalvageAtSelectedHex(1.0)))
        self.RegenerateProceduralShipModelsButton = self.addWidget(AGeWidgets.Button(self,"Regenerate procedural ship models", lambda: regenerateProceduralShipModels()))
        self.RegenerateAllProceduralModelsButton = self.addWidget(AGeWidgets.Button(self,"Regenerate all procedural models", lambda: regenerateAllProceduralModels()))
        self.EndBattleButton = self.addWidget(AGeWidgets.Button(self,"End Battle",lambda: get.engine().endBattleScene()))
        self.EnableDebugOutputButton = self.addWidget(AGeWidgets.Button(self,"Enable print Debug Output",lambda: self.toggleDebugOutput()))
        self.GetTeamValuesButton = self.addWidget(AGeWidgets.Button(self,"Get combined value of each team",lambda: getTeamValues()))
    
    def showDevToolTabs(self):
        get.window().showDevToolTabs()
        self.layout().removeWidget(self.ShowDevToolTabsButton)
    
    def toggleDebugOutput(self):
        get.engine().DebugPrintsEnabled = not get.engine().DebugPrintsEnabled
        if get.engine().DebugPrintsEnabled:
            self.EnableDebugOutputButton.setText("Disable print Debug Output")
        else:
            self.EnableDebugOutputButton.setText("Enable print Debug Output")

def spawnAsteroidAtSelectedHex():
    from Environment import Environment, EnvironmentalObjects, EnvironmentalObjectGroups
    currentHex = get.hexGrid().SelectedHex
    if not currentHex:
        NC(2,"No Hex is selected")
    if currentHex.fleet:
        NC(2, "The Hex is already occupied", input=currentHex.fleet())
        return
    combat = get.engine().CurrentlyInBattle
    object = EnvironmentalObjects.Asteroid()
    if not combat: objectGroup = EnvironmentalObjectGroups.EnvironmentalObjectGroup_Campaign()
    else: objectGroup = EnvironmentalObjectGroups.EnvironmentalObjectGroup_Battle()
    objectGroup.Name = object.Name
    objectGroup.addShip(object)
    objectGroup.moveToHex(currentHex, False)

def spawnSalvageAtSelectedHex(amount=1.0):
    from Economy import Resources
    if get.hexGrid().SelectedHex:
        get.hexGrid().SelectedHex.ResourcesHarvestable.add(Resources.Salvage(amount))
    else:
        NC(2,"No Hex is selected")

def getTeamValues():
    s = "Values of each Team:"
    for i in get.unitManager().Teams.values():
        s += f"\n{i.name()}: {i.value()}"
    NC(3,s,DplStr="Team Values")

def regenerateProceduralShipModels():
    #TODO: This currently removes all non-procedural models, too, and replaces them with procedural ones
    for i,t in get.unitManager().Teams.items():
        if i <=0: continue
        for f in t:
            for s in f.Ships:
                s.setModel(None)
            f.arrangeShips()

def regenerateAllProceduralModels():
    #TODO: This currently removes all non-procedural models, too, and replaces them with procedural ones
    for i,t in get.unitManager().Teams.items():
        for f in t:
            for s in f.Ships:
                s.setModel(None)
            f.arrangeShips()
