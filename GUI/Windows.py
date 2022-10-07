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
from BaseClasses import get
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
        self.EndTurnButton = AGeWidgets.Button(self,"End Turn",lambda: get.unitManager().endTurn())
        base().accept("control-enter",lambda: get.unitManager().endTurn()) # ctrl + Enter
        genLayout.addWidget(self.EndTurnButton)
        
        self.genWidget.setLayout(genLayout)
        layout.addWidget(self.genWidget)
        
        self.cw.setLayout(layout)
        
        #self.Console1.setText("self.Pawn = Unit((25,25),App().MiscColours[\"Self\"])\n")
        self.Console1.setText(TEMP_CODE)
        self.Console2.setText("engine().endBattleScene()\n")
        
        self.UnitStatDisplay = WidgetsBase.FleetStats(self)
        self.TabWidget.addTab(self.UnitStatDisplay, "Unit Stats")
    
    def getHex(self, i:typing.Tuple[int,int]) -> 'Hex._Hex':
        return get.engine().getHex(i)


ENTERPRISE_IMPORT ="""
self.Pawn = Unit((25,24),name="USS Enterprise",model="/Users/Robin/Desktop/Projects/AstusGameEngine_dev/3DModels/NCC-1701-D.gltf")
self.Pawn2 = Unit((25,26),name="USS Galaxy",model="/Users/Robin/Desktop/Projects/AstusGameEngine_dev/3DModels/NCC-1701-D.gltf")
"""
TEMP_CODE = """
self.Fleet1 = FleetBase.Fleet(1)
self.Fleet1.Name = "Fleet 1"

self.Ship11 = Ships.TestShips.Enterprise()
self.Ship11.Name = "Enterprise 11"
self.Fleet1.addShip(self.Ship11)

self.Ship12 = Ships.TestShips.Enterprise()
self.Ship12.Name = "Enterprise 12"
self.Fleet1.addShip(self.Ship12)

self.Ship13 = Ships.TestShips.Enterprise()
self.Ship13.Name = "Enterprise 13"
self.Fleet1.addShip(self.Ship13)

self.Fleet1.moveToHex(self.getHex((25,25)))

###########################################

self.Fleet2 = FleetBase.Fleet(2)
self.Fleet2.Name = "Fleet 2"

self.Ship21 = Ships.TestShips.Enterprise()
self.Ship21.Name = "Enterprise 21"
self.Fleet2.addShip(self.Ship21)

self.Ship22 = Ships.TestShips.Enterprise()
self.Ship22.Name = "Enterprise 22"
self.Fleet2.addShip(self.Ship22)

self.Ship23 = Ships.TestShips.Enterprise()
self.Ship23.Name = "Enterprise 23"
self.Fleet2.addShip(self.Ship23)

self.Fleet2.moveToHex(self.getHex((25,24)))

###########################################

self.Fleet3 = FleetBase.Fleet(3)
self.Fleet3.Name = "Fleet 3"

self.Ship31 = Ships.TestShips.Enterprise()
self.Ship31.Name = "Enterprise 31"
self.Fleet3.addShip(self.Ship31)

self.Ship32 = Ships.TestShips.Enterprise()
self.Ship32.Name = "Enterprise 32"
self.Fleet3.addShip(self.Ship32)

self.Ship33 = Ships.TestShips.Enterprise()
self.Ship33.Name = "Enterprise 33"
self.Fleet3.addShip(self.Ship33)

self.Fleet3.moveToHex(self.getHex((24,24)))

###########################################

self.Fleet4 = FleetBase.Fleet(3)
self.Fleet4.Name = "Fleet 4"

self.Ship41 = Ships.TestShips.Enterprise()
self.Ship41.Name = "Enterprise 41"
self.Fleet4.addShip(self.Ship41)

self.Ship42 = Ships.TestShips.Enterprise()
self.Ship42.Name = "Enterprise 42"
self.Fleet4.addShip(self.Ship42)

self.Ship43 = Ships.TestShips.Enterprise()
self.Ship43.Name = "Enterprise 43"
self.Fleet4.addShip(self.Ship43)

self.Fleet4.moveToHex(self.getHex((26,24)))
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
