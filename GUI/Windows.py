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
from heapq import heappush, heappop

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
else:
    # These imports make Python happy
    #sys.path.append('../AstusPandaEngine')
    from AGeLib import *
    import AstusPandaEngine as ape
    from AstusPandaEngine import engine, base, render, loader
    from AstusPandaEngine import window as _window

# Game Imports
from BaseClasses import HexBase as Hex
from BaseClasses.Unit import Unit
from BaseClasses.get import unitManager, window
from GUI import WidgetsBase

class MainWindowClass(ape.APELabWindow):#APEWindow):
    def setupUI(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.pandaContainer)
        
        self.genWidget = QtWidgets.QWidget(self)
        genLayout = QtWidgets.QHBoxLayout()
        genLayout.setContentsMargins(0,0,0,0)
        
        #self.genCB = QtWidgets.QCheckBox(self)
        #self.genCB.setText("Use seed 6")
        #genLayout.addWidget(self.genCB)
        self.EndTurnButton = AGeWidgets.Button(self,"End Turn",lambda: unitManager().endTurn())
        genLayout.addWidget(self.EndTurnButton)
        
        self.genWidget.setLayout(genLayout)
        layout.addWidget(self.genWidget)
        
        self.cw.setLayout(layout)
        
        #self.Console1.setText("self.Pawn = Unit((25,25),App().MiscColours[\"Self\"])\n")
        self.Console1.setText(TEMP_CODE)
        self.Console2.setText("self.Pawn.takeDamage(400)\n\n#for i in unitManager().Teams[1]:\n#\ti.takeDamage(400,2)\n#\ti.takeDamage(400,2)\n")
        
        self.UnitStatDisplay = WidgetsBase.ShipStats(self)
        self.TabWidget.addTab(self.UnitStatDisplay, "Unit Stats")
    
    def gen(self):
        self.HexGrid.generateHex()
            
    def start(self):
        self.HexGrid = Hex.HexGrid()
        #Unit((25,25),name="self"  ,model="Models/Simple Geometry/cube.ply", colour=App().MiscColours["Self"]   )
        #Unit((27,22),name="a pawn",model="Models/Simple Geometry/cube.ply", colour=App().MiscColours["Neutral"])
        #Unit((26,23),name="a pawn",model="Models/Simple Geometry/cube.ply", colour=App().MiscColours["Neutral"])
        #Unit((25,23),name="a pawn",model="Models/Simple Geometry/cube.ply", colour=App().MiscColours["Neutral"])
        #Unit((24,23),name="a pawn",model="Models/Simple Geometry/cube.ply", colour=App().MiscColours["Neutral"])
        #Unit((23,22),name="a pawn",model="Models/Simple Geometry/cube.ply", colour=App().MiscColours["Neutral"])
        
    def getHex(self, i:typing.Tuple[int,int]) -> 'Hex._Hex':
        return self.HexGrid.getHex(i)


ENTERPRISE_IMPORT ="""
self.Pawn = Unit((25,24),name="USS Enterprise",model="/Users/Robin/Desktop/Projects/AstusGameEngine_dev/3DModels/NCC-1701-D.gltf")
self.Pawn2 = Unit((25,26),name="USS Galaxy",model="/Users/Robin/Desktop/Projects/AstusGameEngine_dev/3DModels/NCC-1701-D.gltf")
"""
TEMP_CODE = """
self.Fleet = FleetBase.Flotilla()

self.Ship = Ships.TestShips.Enterprise()
self.Fleet.addShip(self.Ship)

self.Ship = Ships.TestShips.Enterprise()
self.Fleet.addShip(self.Ship)

self.Ship = Ships.TestShips.Enterprise()
self.Fleet.addShip(self.Ship)

self.Fleet.moveToHex(self.getHex((25,25)))
"""


TEMP_CODE_OLD = """
self.Fleet = FleetBase.Flotilla()

self.Ship = ShipBase.Ship()
self.Model = ModelBase.EnterpriseModel()
self.Ship.setModel(self.Model)
self.Fleet.addShip(self.Ship)

self.Ship = ShipBase.Ship()
self.Model = ModelBase.EnterpriseModel()
self.Ship.setModel(self.Model)
self.Fleet.addShip(self.Ship)

self.Ship = ShipBase.Ship()
self.Model = ModelBase.EnterpriseModel()
self.Ship.setModel(self.Model)
self.Fleet.addShip(self.Ship)

self.Fleet.moveToHex(self.getHex((25,25)))
"""
