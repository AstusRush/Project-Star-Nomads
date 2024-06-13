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
from GUI import BaseInfoWidgets
from GUI import EconomyInfoWidgets
from GUI import Menu
from GUI import Debug

class MainWindowClass(AWWF):#APEWindow):
    S_PandaKeystroke  = pyqtSignal(str)
    S_PandaButtonDown = pyqtSignal(str)
    S_PandaButtonUp   = pyqtSignal(str)
    def __init__(self, widget):
        super(MainWindowClass, self).__init__(IncludeErrorButton=True, FullscreenHidesBars=True)
        App().setMainWindow(self)
        self.LastOpenState = self.showMaximized
        self.CentralSplitter = QtWidgets.QSplitter(self)
        self.setCentralWidget(self.CentralSplitter)
        
        self.TabWidget = QtWidgets.QTabWidget(self.CentralSplitter)
        #
        self.cw = QtWidgets.QWidget(self.CentralSplitter)
        self.PandaContainer = widget(self.cw)
        self.PandaContainer.installEventFilter(self)
        
        self.setupUI()
    
    def setupUI(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.PandaContainer)
        
        self.genWidget = QtWidgets.QWidget(self)
        genLayout = QtWidgets.QHBoxLayout()
        genLayout.setContentsMargins(0,0,0,0)
        
        #self.genCB = QtWidgets.QCheckBox(self)
        #self.genCB.setText("Use seed 6")
        #genLayout.addWidget(self.genCB)
        self.EndTurnButton = AGeWidgets.Button(self,"End Turn",lambda: get.engine().endTurn())
        base().accept("control-enter",lambda: get.engine().endTurn()) # ctrl + Enter
        base().accept("control-space",lambda: get.engine().endTurn()) # ctrl + Space
        genLayout.addWidget(self.EndTurnButton)
        
        self.genWidget.setLayout(genLayout)
        layout.addWidget(self.genWidget)
        
        self.cw.setLayout(layout)
        
        self.DebugMenu = Debug.DebugMenu(self)
        self.TabWidget.addTab(self.DebugMenu, "Debug Menu")
        
        self.UnitStatDisplay = BaseInfoWidgets.FleetStats(self)
        self.TabWidget.addTab(self.UnitStatDisplay, "Unit Stats")
        
        self.EconomyDisplay = EconomyInfoWidgets.EconomyDisplay(self)
        self.TabWidget.addTab(self.EconomyDisplay, "Economy")
        
        self.Menu = Menu.Menu(self)
        self.TabWidget.addTab(self.Menu, "Menu")
        
        self.TabWidget.setCurrentWidget(self.Menu) # Overwritten by the engine starting a new game but sensible nonetheless
        
        self.CentralSplitter.setSizes([510,App().screenAt(QtGui.QCursor().pos()).size().width()-510])
    
    def showDevToolTabs(self):
        self.Console1 = AGeIDE.ConsoleWidget(self)
        self.Console1.setGlobals(self.globals())
        #self.Console1.setText("self.genPlayer()\nself.HexGrid = AGE.HexGrid(self.AGE)\n")
        self.TabWidget.insertTab(0, self.Console1, "Con1")
        self.Console2 = AGeIDE.ConsoleWidget(self)
        self.Console2.setGlobals(self.globals())
        #self.Console2.setText("self.genFloorAndPlayer()\n")
        self.TabWidget.insertTab(1, self.Console2, "Con2")
        #self.GeneratorEditor = AGeIDE.OverloadWidget(self, self.gen, "gen")
        #self.TabWidget.addTab(self.GeneratorEditor, "Gen")
        self.Overload1 = AGeIDE.OverloadWidget(self)
        self.Overload1.setGlobals(self.globals())
        self.TabWidget.insertTab(2, self.Overload1, "Overload 1")
        self.Overload2 = AGeIDE.OverloadWidget(self)
        self.Overload2.setGlobals(self.globals())
        self.TabWidget.insertTab(3, self.Overload2, "Overload 2")
        self.Inspect = AGeIDE.InspectWidget(self)
        self.Inspect.setGlobals(self.globals())
        self.TabWidget.insertTab(4, self.Inspect, "Inspect")
        
        #self.Console1.setText("self.Pawn = Unit((25,25),App().MiscColours[\"Self\"])\n")
        
        self.Console1.setText(TEMP_CODE)
        #self.Console1.setText(TEMP_CODE_PROC_TEST)
        #self.Console1.setText(TEMP_CODE_PROC_TEST_ASTEROID)
        
        self.Console2.setText("engine().endBattleScene()\n#get.hex((24,24)).ResourcesHarvestable.add(Resources.Salvage(12))\n")
    
    def eventFilter(self, source, event):
        #if event.type() == 6: # QtCore.QEvent.KeyPress
        #if hasattr(self,"AGE"):
        #    self.AGE.eventFilter(source, event)
        return super().eventFilter(source, event) # let the normal eventFilter handle the event
    
    def globals(self):
        return vars(sys.modules['__main__'])
    
    def getHex(self, i:typing.Tuple[int,int]) -> 'Hex._Hex':
        return get.engine().getHex(i)


ENTERPRISE_IMPORT ="""
self.Pawn = Unit((25,24),name="USS Enterprise",model="/Users/Robin/Desktop/Projects/AstusGameEngine_dev/3DModels/NCC-1701-D.gltf")
self.Pawn2 = Unit((25,26),name="USS Galaxy",model="/Users/Robin/Desktop/Projects/AstusGameEngine_dev/3DModels/NCC-1701-D.gltf")
"""
TEMP_CODE = """

if True:
    self.P1_Fleet1 = self.getHex((25,25)).fleet()
    ship1 = Ships.TestShips.MiningTest()
    self.P1_Fleet1.addShip(ship1)
    ship2 = Ships.TestShips.RefineryTest()
    self.P1_Fleet1.addShip(ship2)

else:
    get.engine().clearAll()
    self.P1_Fleet1 = FleetBase.Fleet(1)
    self.P1_Fleet1.Name = "Fleet 1"
    if True:
        ship = Ships.TestShips.NomadOne()
        self.P1_Fleet1.addShip(ship)
    
    if False:
        ship = Ships.AI_faction_ships.AI_PatrolCraft_1()
        #ship = Ships.TestShips.ProcTestShip()
        #ship = Ships.TestShips.TestShip()
        ship.Name = f"Test 1"
        self.P1_Fleet1.addShip(ship)
    
    self.P1_Fleet1.moveToHex(self.getHex((25,25)))
    
    if True:
        #ship = Ships.TestShips.SpaceDock()
        #ship.Name = f"Home One"
        #self.P1_Fleet1.addShip(ship)
        for i in range(3):
            ship = Ships.TestShips.Prometheus()
            ship.Name = f"Prometheus 1-{i}"
            self.P1_Fleet1.addShip(ship)
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

TEMP_CODE_PROC_TEST_ASTEROID = """
if not hasattr(self, "ship"):
    from ProceduralGeneration import GeomBuilder
    self.GeomBuilder = GeomBuilder
    
    self.P1_Fleet1 = FleetBase.Fleet(1)
    self.P1_Fleet1.Name = "Fleet 1"
    
    self.ship = Ships.TestShips.ProcTest_Asteroid()
    self.ship.Name = f"Test 1"
    self.P1_Fleet1.addShip(self.ship)
    
    self.P1_Fleet1.moveToHex(self.getHex((25,25)))
else:
    self.ship.Model._init_model()
    self.ship.Model.centreModel()
    self.ship.Model.Node.reparentTo(self.ship.Node)
    self.ship.Model.Node.setPos(0,0,0)
# self.ship.Model.generateModel
# self.ship.Model.applyTexture
# self.ship.Model.generateTexture
# self.GeomBuilder.GeomBuilder.add_asteroid
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
