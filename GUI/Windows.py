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
        #self.Console1.setText(TEMP_CODE_PROC_TEST)
        
        self.Console2.setText("engine().endBattleScene()\n")
        
        self.UnitStatDisplay = WidgetsBase.FleetStats(self)
        self.TabWidget.addTab(self.UnitStatDisplay, "Unit Stats")
        
        self.Menu = WidgetsBase.Menu(self)
        self.TabWidget.addTab(self.Menu, "Menu")
    
    def getHex(self, i:typing.Tuple[int,int]) -> 'Hex._Hex':
        return get.engine().getHex(i)


ENTERPRISE_IMPORT ="""
self.Pawn = Unit((25,24),name="USS Enterprise",model="/Users/Robin/Desktop/Projects/AstusGameEngine_dev/3DModels/NCC-1701-D.gltf")
self.Pawn2 = Unit((25,26),name="USS Galaxy",model="/Users/Robin/Desktop/Projects/AstusGameEngine_dev/3DModels/NCC-1701-D.gltf")
"""
TEMP_CODE = """
self.P1_Fleet1 = FleetBase.Fleet(1)
self.P1_Fleet1.Name = "Fleet 1"
for i in range(3):
    ship = Ships.TestShips.Prometheus()
    ship.Name = f"Prometheus 1-{i}"
    self.P1_Fleet1.addShip(ship)

ship = Ships.TestShips.SpaceDock()
ship.Name = f"Home One"
self.P1_Fleet1.addShip(ship)

if False:
    ship = Ships.TestShips.TestShip()
    ship.Name = f"Test 1"
    self.P1_Fleet1.addShip(ship)

self.P1_Fleet1.moveToHex(self.getHex((25,25)))

if False:
    ###########################################
    self.P1_Fleet2 = FleetBase.Fleet(1)
    self.P1_Fleet2.Name = "Fleet 2"
    for i in range(3):
        ship = Ships.TestShips.Enterprise()
        ship.Name = f"Enterprise 1-{i}"
        self.P1_Fleet2.addShip(ship)
    self.P1_Fleet2.moveToHex(self.getHex((25,26)))
    ###########################################
    self.P2_Fleet1 = FleetBase.Fleet(2)
    self.P2_Fleet1.Name = "P2 Fleet 1"
    for i in range(3):
        ship = Ships.TestShips.Prometheus()
        ship.Name = f"Prometheus 1-{i}"
        self.P2_Fleet1.addShip(ship)
    self.P2_Fleet1.moveToHex(self.getHex((25,24)))
    ###########################################
    self.P2_Fleet2 = FleetBase.Fleet(2)
    self.P2_Fleet2.Name = "P2 Fleet 2"
    for i in range(3):
        ship = Ships.TestShips.Enterprise()
        ship.Name = f"Enterprise 2-{i}"
        self.P2_Fleet2.addShip(ship)
    self.P2_Fleet2.moveToHex(self.getHex((26,24)))
    ###########################################
    self.P2_Fleet3 = FleetBase.Fleet(2)
    self.P2_Fleet3.Name = "P2 Fleet 3"
    for i in range(3):
        ship = Ships.TestShips.Enterprise()
        ship.Name = f"Enterprise 3-{i}"
        self.P2_Fleet3.addShip(ship)
    self.P2_Fleet3.moveToHex(self.getHex((24,24)))
    ###########################################
    self.P3_Fleet1 = FleetBase.Fleet(3)
    self.P3_Fleet1.Name = "P3 Fleet 1"
    for i in range(3):
        ship = Ships.TestShips.Enterprise()
        ship.Name = f"Enterprise 1-{i}"
        self.P3_Fleet1.addShip(ship)
    self.P3_Fleet1.moveToHex(self.getHex((26,25)))
    ###########################################
    self.P3_Fleet2 = FleetBase.Fleet(3)
    self.P3_Fleet2.Name = "P3 Fleet 2"
    for i in range(3):
        ship = Ships.TestShips.Enterprise()
        ship.Name = f"Enterprise 2-{i}"
        self.P3_Fleet2.addShip(ship)
    self.P3_Fleet2.moveToHex(self.getHex((24,25)))
    ###########################################
"""

TEMP_CODE_PROC_TEST = """
if not hasattr(self, "ship"):
    from ProceduralGeneration import GeomBuilder
    self.GeomBuilder = GeomBuilder
    
    self.P1_Fleet1 = FleetBase.Fleet(1)
    self.P1_Fleet1.Name = "Fleet 1"
    
    self.ship = Ships.TestShips.ProcTestShip()
    self.ship.Name = f"Test 1"
    self.P1_Fleet1.addShip(self.ship)
    
    self.P1_Fleet1.moveToHex(self.getHex((25,25)))
else:
    self.ship.Model._init_model()
    self.ship.Model.centreModel()
    self.ship.Model.Node.reparentTo(self.ship.Node)
    self.ship.Model.Node.setPos(0,0,0)
# self.ship.Model.generateModel
# self.GeomBuilder.GeomBuilder.add_sphere
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
