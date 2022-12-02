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
    from ...AstusPandaEngine.AstusPandaEngine import window as _window
else:
    # These imports make Python happy
    #sys.path.append('../AstusPandaEngine')
    from AGeLib import *
    import AstusPandaEngine as ape
    from AstusPandaEngine import engine, base, render, loader
    from AstusPandaEngine import window as _window

#from ApplicationClasses import Scene, StarNomadsColourPalette
#from GUI import Windows, WidgetsBase
from BaseClasses import HexBase, FleetBase, ShipBase, ModelBase, BaseModules, UnitManagerBase, get
from GUI import BaseInfoWidgets

#TODO: The construction Window should be opened from a construction module
#       The window should stay open and not block anything
#       When eventually pressing the Build button the game must check whether this action is still possible
#           This means checking whether the game is currently in combat, whether the construction module still exists,
#               whether there are still enough resources,
#               if a ship is edited whether that ship still exists and whether it is still in the same fleet as the ship with the construction module, etc
#       The window probably has a list widget to which one can add new modules from a list
#           and clicking on a list entry opens a widget in which one can edit the modules stats.
#       Then there is a stat display for the entire ship and a resource cost and construction time display
#       And of course a widget where one can select a model for the ship. This model can at first only be initialized when the build button is clicked
#           but it would be cool to eventually have a model preview.
#           But since a model swap should not cost any resources or time one can change the model to your hearts content so a preview is not critically important.
#       Eventually there should be a way to save ship and module blueprints and the ability to load these but this is also not all to important for now.
#       What is however important is a check to ensure that unique module types only exist once on the ship.
#       To display all the stats correctly we actually have to initialize the ship and the modules and add the modules to the ship.
#           Therefore there must be a strong link between them.

class ConstructionWindow(AWWF):
    def __init__(self, parent=None, IncludeTopBar=True, initTopBar=True, IncludeStatusBar=True, IncludeErrorButton=True, FullscreenHidesBars=False):
        super().__init__(parent, IncludeTopBar, initTopBar, IncludeStatusBar, IncludeErrorButton, FullscreenHidesBars)
        # Maybe a triple splitter for ( Ship Stats | Module List | Module Editor )
        self.StandardSize = (900,500)
        self.ConstructionWidget = self.CW = ConstructionWidget(self)
        self.setCentralWidget(self.ConstructionWidget)
    
    def setConstructionModule(self, module:BaseModules.ConstructionModule):
        self.ConstructionWidget.setConstructionModule(module)

class ConstructionWidget(QtWidgets.QSplitter):
    constructionModule: 'weakref.ref[BaseModules.ConstructionModule]' = None
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget'] = None) -> None:
        super().__init__(parent)
        #self.Splitter = self.addWidget(QtWidgets.QSplitter(self))
        self.Ship = ShipBase.Ship()
        
        self.ShipStats = ShipStats(self)
        self.addWidget(self.ShipStats)
        self.ModuleList = ModuleListWidget(self)
        self.addWidget(self.ModuleList)
        self.ModuleEditor = ModuleEditor(self)
        self.addWidget(self.ModuleEditor)
        
        self.__Initialized = False
    
    def setConstructionModule(self, module:BaseModules.ConstructionModule):
        self.constructionModule:'weakref.ref[BaseModules.ConstructionModule]' = weakref.ref(module)
        if not self.__Initialized: self._initFirstShip()
    
    def _initFirstShip(self):
        self.__Initialized = True
        self.ModuleList.ModuleList.addModule(BaseModules.Hull)
        self.ModuleList.ModuleList.addModule(BaseModules.Thruster)
        self.ModuleList.ModuleList.addModule(BaseModules.Engine)
        self.ModuleList.ModuleList.addModule(BaseModules.Sensor)
        self.ShipStats.getInterface()
    
    def buildShip(self):
        #self.Ship.Name = self.ShipStats.NameInput()
        #self.Ship.ClassName = self.ShipStats.ClassInput()
        if not self.Ship.hull:
            NC(2, "Could not build ship as critical component is missing: hull")
            return
        if not self.Ship.engine:
            NC(2, "Could not build ship as critical component is missing: engine")
            return
        if not self.Ship.thruster:
            NC(2, "Could not build ship as critical component is missing: thruster")
            return
        if not self.Ship.sensor:
            NC(2, "Could not build ship as critical component is missing: sensor")
            return
        if self.constructionModule and not self.constructionModule().ship().Destroyed:
            model = get.shipModels()[self.ShipStats.ModelSelectBox.currentText()]
            if self.constructionModule().buildShip(self.Ship, model):
                self.window().close() #TODO: This is currently necessary since the constructed ship is still the ship which is being edited and would therefore allow modification but would also eat up resources if the build button is spammed
        else:
            NC(2, f"Could not construct ship: The construction module no longer exists")
    
    def canModuleBeAdded(self, module:'typing.Union[BaseModules.Module,type[BaseModules.Module]]'):
        return self.Ship.canModuleBeAdded(module)
    
    def addModule(self, module:'BaseModules.Module'):
        #TODO: There are some modules that can only exist once on a ship. We should either clean up removed modules from the interface or simply not allow a module to be added in those cases...
        self.Ship.addModule(module)
        self.ShipStats.updateShipInterface()
    
    def removeModule(self, module:'BaseModules.Module'):
        self.Ship.removeModule(module)
        self.ShipStats.updateShipInterface()

class ShipStats(AGeWidgets.TightGridFrame):
    def __init__(self, parent:'ConstructionWidget') -> None:
        super().__init__(parent,makeCompact=False)
        self.ShipStats = None
        self.ModelSelectBox = self.addWidget(QtWidgets.QComboBox(self))
        #self.NameInput = self.addWidget(AGeInput.Str(None,"Name",self.ship().Name)) # Handled by the BaseInfoWidgets.FullInfoWidget and should not be interfered with
        #self.ClassInput = self.addWidget(AGeInput.Str(None,"Class",self.ship().ClassName)) # Handled by the BaseInfoWidgets.FullInfoWidget and should not be interfered with
        self.Label = self.addWidget(QtWidgets.QLabel("Ship Stats\nAll of the Ship Stats", self))
        self.BuildButton = self.addWidget(AGeWidgets.Button(self,"Build Ship",lambda: self.parent().buildShip()))
        self.InterfaceButton = self.addWidget(AGeWidgets.Button(self,"Get Stats",lambda: self.getInterface()))
        #TODO: It would be neat to select a construction module out of a list of all construction modules.
        #TODO: Display the resources the construction module has access to.
        
        #MAYBE: Use BaseInfoWidgets.FullInfoWidget instead
        
        self.populateAddModuleSelectBox()
    
    def parent(self) -> 'ConstructionWidget':
        return super().parent()
    
    def populateAddModuleSelectBox(self):
        for k,v in get.shipModels().items():
            self.ModelSelectBox.addItem(k)
        self.ModelSelectBox.setCurrentText("Procedural")
    
    def ship(self) -> ShipBase.Ship:
        return self.parent().Ship
    
    def getInterface(self): #TODO: We need a better interface
        if self.ShipStats:
            self.layout().removeWidget(self.ShipStats)
            self.ShipStats = None
        try:
            self.ShipStats = self.addWidget(self.parent().Ship.getInterface())
        except:
            NC(exc=True)
            self.ShipStats = None
    
    def updateShipInterface(self):
        text = f"Value: {self.ship().Stats.Value}"
        try:
            text += f"\nAvailable Resources: {self.parent().constructionModule().ConstructionResourcesStored}"
        except:
            text += f"\nAvailable Resources: ???"
            NC(2, "The construction module for this window might no longer exist...", exc=True)
        try:
            self.ship().updateInterface()
        except:
            text += f"\nCould not refresh interface"
            NC(4,"Could not refresh ship interface", exc=True)
        self.Label.setText(text)

class ModuleListWidget(AGeWidgets.TightGridFrame):
    def __init__(self, parent:'ConstructionWidget') -> None:
        super().__init__(parent,makeCompact=False)
        self.AddModuleSelectBox = self.addWidget(QtWidgets.QComboBox(self))
        self.AddModuleButton = self.addWidget(AGeWidgets.Button(self,"Add Module",lambda: self.addModule()))
        self.ModuleList = self.addWidget(ModuleList(self))
        self.populateAddModuleSelectBox()
    
    def parent(self) -> 'ConstructionWidget':
        return super().parent()
    
    def populateAddModuleSelectBox(self):
        for k,v in get.modules().items():
            if v.Buildable:
                self.AddModuleSelectBox.addItem(k)
    
    def addModule(self):
        self.ModuleList.addModule(get.modules()[self.AddModuleSelectBox.currentText()])

class ModuleList(QtWidgets.QListWidget):
    def __init__(self, parent:'ModuleListWidget') -> None:
        super().__init__(parent)
        self.itemDoubleClicked.connect(lambda item: self.selectModuleForEditor(item))
        self.installEventFilter(self)
    
    def parent(self) -> 'ModuleListWidget':
        return super().parent()
    
    def addModule(self, module:'typing.Union[BaseModules.Module,type[BaseModules.Module]]'):
        if not self.parent().parent().canModuleBeAdded(module):
            NC(2,"Module can not be added.")
        else:
            if isinstance(module,type):
                module = module()
            item = ModuleItem()
            item.setText(module.Name)
            item.setData(100, module)
            self.addItem(item)
            self.parent().parent().addModule(item.data(100))
            self.parent().parent().ModuleEditor.setModule(item)
    
    def selectModuleForEditor(self, item: QtWidgets.QListWidgetItem) -> None:
        self.parent().parent().ModuleEditor.setModule(item)
    
    def removeModule(self, item:"ModuleItem"):
        self.parent().parent().ModuleEditor.unsetModule(item)
        self.parent().parent().removeModule(item.data(100))
        self.takeItem(self.row(item))
    
    def duplicateModule(self, item:"ModuleItem"):
        self.addModule(item.data(100).copy())
    
    def eventFilter(self, source, event):
        #TODO: Add Tooltips for the Actions! These should also specify whether the action will be executed on all selected items or only the right-clicked-one! "Delete" should also mention "Del" as the hotkey!
        #FEATURE: When multiple items are selected the context menu should be different: instead of the usual options there should be options to format the selected items in a specific way and copy the result to the clipboard
        #FEATURE: The comma separation every 3 digits is cool! There should be a way to copy the solution or the equation including this separation
        try:
            if event.type() == 82: # QtCore.QEvent.ContextMenu
            # ---------------------------------- History Context Menu ----------------------------------
                item = source.itemAt(event.pos())
                if item:
                    menu = QtWidgets.QMenu()
                    action = menu.addAction('Select [DoubleClick]')
                    action.triggered.connect(lambda: self.selectModuleForEditor(item))
                    action = menu.addAction('Duplicate')
                    action.triggered.connect(lambda: self.duplicateModule(item))
                    action = menu.addAction('Remove [Del]')
                    action.triggered.connect(lambda: self.removeModule(item))
                    menu.setPalette(self.palette())
                    menu.setFont(self.font())
                    menu.exec_(event.globalPos())
                    return True
            elif event.type() == 6: # QtCore.QEvent.KeyPress
                if event.key() == QtCore.Qt.Key_Delete:
                    if self.selectedItems():
                        self.removeModule(self.selectedItems()[0])
            return super().eventFilter(source, event)
        except:
            NC(lvl=1,exc=True,win=self.window().windowTitle(),input=str(event))
            return super().eventFilter(source, event)

class ModuleItem(QtWidgets.QListWidgetItem):
    pass

class ModuleEditor(AGeWidgets.TightGridFrame):
    def __init__(self, parent:'ConstructionWidget') -> None:
        super().__init__(parent,makeCompact=False)
        self.NameLabel = self.addWidget(QtWidgets.QLabel("Module Editor", self))
        self.ValueLabel = self.addWidget(QtWidgets.QLabel("", self))
        self.Apply = self.addWidget(AGeWidgets.Button(self, "Apply", lambda: self.applyStats()))
        self.ModuleStatContainer = self.addWidget(AGeWidgets.TightGridFrame(self,makeCompact=False))
        self.StatDict:'dict[str,typing.Callable[[],typing.Any]]' = {}
    
    def parent(self) -> 'ConstructionWidget':
        return super().parent()
    
    def setModule(self, item:'ModuleItem'):
        self.clear()
        module:'BaseModules.Module' = item.data(100)
        self.ActiveModule = module
        self.ActiveModuleItem = item
        self.NameLabel.setText(module.Name)
        self.updateValueLabel()
        self.loadModuleStats()
    
    def unsetModule(self, item:'ModuleItem'):
        if self.ActiveModule is item.data(100):
            self.clear()
    
    def clear(self):
        self.ActiveModule = None
        self.ActiveModuleItem = None
        self.StatDict = {}
        self.NameLabel.setText("No module is selected")
        self.ValueLabel.setText("")
        if self.ModuleStatContainer:
            self.layout().removeWidget(self.ModuleStatContainer)
            self.ModuleStatContainer = None
    
    def loadModuleStats(self):
        if self.ModuleStatContainer:
            self.layout().removeWidget(self.ModuleStatContainer)
            self.ModuleStatContainer = None
        self.ModuleStatContainer = self.addWidget(AGeWidgets.TightGridFrame(self,makeCompact=False))
        self.StatDict = {statName:self.ModuleStatContainer.addWidget(widget()) for statName, widget in self.ActiveModule.getCustomisableStats().items()}
    
    def applyStats(self):
        if self.ModuleStatContainer and self.ActiveModule and self.StatDict:
            for k,v in self.StatDict.items():
                setattr(self.ActiveModule,k,v())
            adjustments = self.ActiveModule.makeValuesValid()
            if adjustments: NC(2, "Not all values were valid. The following adjustments were made:\n"+adjustments)
            self.ActiveModule.resetCondition()
            self.ActiveModule.automaticallyDetermineValues()
            self.parent().ShipStats.updateShipInterface()
            self.updateValueLabel()
            self.ActiveModuleItem.setText(self.ActiveModule.Name)
            self.loadModuleStats()
            self.NameLabel.setText(self.ActiveModule.Name)
    
    def updateValueLabel(self):
        self.ValueLabel.setText(f"Value: {self.ActiveModule.Value}\nThreat {self.ActiveModule.Threat}\nMass {self.ActiveModule.Mass}")
