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
from GUI import BaseInfoWidgets, ShipSelectDialogue

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
        self.StandardSize = (1200,650)
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
        self.LifeEdit = False
        
        self.ShipStats = ShipStats(self)
        self.addWidget(self.ShipStats)
        self.ModuleList = ModuleListWidget(self)
        self.addWidget(self.ModuleList)
        self.ModuleEditor = ModuleEditor(self)
        self.addWidget(self.ModuleEditor)
        
        self._ShipInitialized = False
    
    def setConstructionModule(self, module:BaseModules.ConstructionModule):
        self.constructionModule:'weakref.ref[BaseModules.ConstructionModule]' = weakref.ref(module)
        if not self._ShipInitialized: self._initFirstShip()
    
    def lifeEditing(self) -> bool:
        return self.LifeEdit
    
    def canEdit(self) -> bool:
        return not (self.LifeEdit and get.engine().CurrentlyInBattle)
    
    def _initFirstShip(self):
        self._ShipInitialized = True
        self.addModule(BaseModules.Hull)
        self.addModule(BaseModules.Thruster)
        self.addModule(BaseModules.Engine)
        self.addModule(BaseModules.Sensor)
        self.ShipStats.getInterface()
    
    def buildShip(self):
        #self.Ship.Name = self.ShipStats.NameInput()
        #self.Ship.ClassName = self.ShipStats.ClassInput()
        if not self.Ship:
            NC(2, "You are currently not editing a ship, therefore you can not build a ship.")
            return
        if self.lifeEditing():
            return self.applyNewModel()
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
    
    def applyNewModel(self):
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setText(f"Apply Model?")
        msgBox.setInformativeText(  "You are modifying an already existing ship. It is, therefore, already build.\n"
                                    "What this button does instead is applying a new model.\n"
                                    "Do you want to apply the currently selected model to the ship?"
                                    f"The currently selected model is {self.ShipStats.ModelSelectBox.currentText()}")
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Cancel)
        if not self.lifeEditing():
            NC(2,"The currently active ship is not being life edited but it was requested to change the model. This is an invalid operation. Please report this incident to the developer.",
                input=f"Ship:\n{self.Ship}\n\nModel:\n{self.Ship.Model}\n\nfleet:\n{self.Ship.fleet}\n\nlifeEditing:\n{self.lifeEditing()}", tb=True)
        elif msgBox.exec():
            model = get.shipModels()[self.ShipStats.ModelSelectBox.currentText()]
            self.Ship.clearModel()
            if model is None: self.Ship.generateProceduralModel()
            else: self.Ship.setModel(model())
            self.Ship.Model.centreModel()
            if self.Ship.fleet:
                self.Ship.fleet().arrangeShips()
            else:
                NC(2,"The ship has no fleet. How was it possible for this request to even happen?",input=f"Ship:\n{self.Ship}\n\nFleet:\n{self.Ship.fleet}\n\nlifeEditing:\n{self.lifeEditing()}",tb=True)
    
    def canModuleBeAdded(self, module:'typing.Union[BaseModules.Module,type[BaseModules.Module]]'):
        return self.Ship.canModuleBeAdded(module)
    
    def _addModuleToShip(self, module:'BaseModules.Module'):
        self.Ship.addModule(module)
        self.ShipStats.updateShipInterface()
        if self.lifeEditing():
            self.regenerateShipModel()
    
    def addModule(self, module:'typing.Union[BaseModules.Module,type[BaseModules.Module]]'):
        self.ModuleList.addModule(module)
    
    def removeModule(self, module:'BaseModules.Module'):
        self.Ship.removeModule(module)
        self.ShipStats.updateShipInterface()
        if self.lifeEditing():
            self.regenerateShipModel()
    
    def _clearCurrentShip(self):
        self._ShipInitialized = False
        self.ModuleEditor.clear()
        self.ModuleList.clear()
        self.ShipStats.clear()
        if not self.LifeEdit: self.Ship.destroy()
        self.Ship = None
    
    def setShip(self, ship:'typing.Union[ShipBase.Ship,None]'=None, lifeEdit:bool=False):
        self._clearCurrentShip()
        self.LifeEdit = lifeEdit
        if ship is None:
            self.Ship = ShipBase.Ship()
            self._initFirstShip()
        else:
            self.Ship = ship
        self.ShipStats.getInterface()
        self.ShipStats.updateShipInterface()
        self.ModuleList.populate()
        if self.Ship.Model and not self.Ship.fleet:
            if self.lifeEditing():
                NC(2,"The currently active ship is being life edited but it seems to not be part of a fleet... Something has apparently gone wrong...\n"
                    "The reason this was detected is because the model should be removed of ships that are being edited but do not belong to a fleet.\n"
                    "The model will not be removed now in case the detection of the fleet was faulty but this incident should be reported to the developer.\n",
                    input=f"Ship:\n{self.Ship}\n\nModel:\n{self.Ship.Model}\n\nfleet:\n{self.Ship.fleet}\n\nlifeEditing:\n{self.lifeEditing()}", tb=True)
            else:
                self.Ship.clearModel()
    
    def loadShip(self, ship:'ShipBase.Ship'):
        self.setShip(ship, lifeEdit=True)
        #TODO: We should ensure that critical modules like a hull are always present on all loaded ships
    
    def copyShip(self, ship:'ShipBase.Ship'):
        ship = ship.copy(resetCondition=False, removeModel=False)
        self.setShip(ship)
    
    def regenerateShipModel(self):
        if self.Ship.Model:
            #TODO: This should be easier...
            self.Ship.Model._init_model()
            self.Ship.Model.Node.reparentTo(self.Ship.Node)
            self.Ship.Model.centreModel()
            if self.Ship.fleet:
                self.Ship.fleet().arrangeShips()
            else:
                NC(2,"The ship has no fleet. How was it possible for this request to even happen?",input=f"Ship:\n{self.Ship}\n\nFleet:\n{self.Ship.fleet}\n\nlifeEditing:\n{self.lifeEditing()}",tb=True)
        else:
            if self.Ship.fleet:
                fleet = self.Ship.fleet()
            else:
                fleet = self.Ship.fleet
            NC(2,"The ship has no model that could get reloaded. How was it possible for this request to even happen?",input=f"Ship:\n{self.Ship}\n\nFleet:\n{fleet}\n\nlifeEditing:\n{self.lifeEditing()}",tb=True)

class ShipStats(AGeWidgets.TightGridFrame):
    def __init__(self, parent:'ConstructionWidget') -> None:
        super().__init__(parent,makeCompact=False)
        self.ShipStats = None
        self.EditShipButton = self.addWidget(AGeWidgets.Button(self,"Edit existing ship",lambda: self.editShip()))
        self.CopyShipButton = self.addWidget(AGeWidgets.Button(self,"Copy existing ship",lambda: self.copyShip()))
        self.NewShipButton = self.addWidget(AGeWidgets.Button(self,"New ship",lambda: self.newShip()))
        self.ModelExplanationLabel = self.addWidget(QtWidgets.QLabel("Select the ship model:", self))
        #TODO: Handle editing an active ship (and also handle loading a ship (or ship copy) into the editor by setting this accordingly)
        #TODO: When lifeEditing the build button might be used to apply a selected model?
        self.ModelSelectBox = self.addWidget(QtWidgets.QComboBox(self))
        #self.NameInput = self.addWidget(AGeInput.Str(None,"Name",self.ship().Name)) # Handled by the BaseInfoWidgets.FullInfoWidget and should not be interfered with
        #self.ClassInput = self.addWidget(AGeInput.Str(None,"Class",self.ship().ClassName)) # Handled by the BaseInfoWidgets.FullInfoWidget and should not be interfered with
        self.Label = self.addWidget(QtWidgets.QLabel("Ship stats\nAll of the ship stats", self))
        self.BuildButton = self.addWidget(AGeWidgets.Button(self,"Build ship",lambda: self.parent().buildShip()))
        self.InterfaceButton = self.addWidget(AGeWidgets.Button(self,"Get stats",lambda: self.getInterface()))
        #TODO: It would be neat to select a construction module out of a list of all construction modules.
        #TODO: Display the resources the construction module has access to.
        
        #MAYBE: Use BaseInfoWidgets.FullInfoWidget instead
        
        self.populateAddModuleSelectBox()
    
    def parent(self) -> 'ConstructionWidget':
        return super().parent()
    
    def clear(self):
        self.Label.setText("Ship Stats\nAll of the Ship Stats")
        if self.ShipStats:
            self.layout().removeWidget(self.ShipStats)
            self.ShipStats.deleteLater()
            self.ShipStats = None
    
    def newShip(self):
        confirm = self.parent().lifeEditing()
        if not confirm:
            msgBox = QtWidgets.QMessageBox(self)
            msgBox.setText(f"Are you sure?")
            msgBox.setInformativeText(f"Do you really want to remove your current blueprint and start over?")
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Cancel)
            confirm = msgBox.exec() == QtWidgets.QMessageBox.Yes
        if confirm:
            self.parent().setShip()
    
    def editShip(self):
        shipSelector = ShipSelectDialogue.ShipSelectDialogue(self, queryString="Select a ship to edit", fleet=self.parent().constructionModule().ship().fleet())
        shipSelector.exec()
        ship = shipSelector.SelectedShip
        NC(3,ship)
        if ship:
            self.parent().loadShip(ship)
    
    def copyShip(self):
        shipSelector = ShipSelectDialogue.ShipSelectDialogue(self, queryString="Select a ship to use as a template for a new ship")
        shipSelector.exec()
        ship = shipSelector.SelectedShip
        NC(3,ship)
        if ship:
            self.parent().copyShip(ship)
    
    def populateAddModuleSelectBox(self):
        for k,v in get.shipModels().items():
            self.ModelSelectBox.addItem(k)
        self.ModelSelectBox.setCurrentText("Procedural")
    
    def ship(self) -> ShipBase.Ship:
        return self.parent().Ship
    
    def getInterface(self): #TODO: We need a better interface
        if self.ShipStats:
            self.layout().removeWidget(self.ShipStats)
            self.ShipStats.deleteLater()
            self.ShipStats = None
        try:
            self.ShipStats = self.addWidget(self.parent().Ship.getInterface())
        except:
            NC(exc=True)
            self.ShipStats = None
    
    def updateShipInterface(self):
        if self.ShipStats:
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
        self.ModuleTypeSelectionWidget = self.addWidget(ModuleTypeSelectionWidget(self),0,0)
        self.ModuleList = self.addWidget(InstalledModuleListWidget(self),0,1)
        self.ModuleTypeSelectionWidget.populate()
    
    def parent(self) -> 'ConstructionWidget':
        return super().parent()
    
    def addModule(self, module:'typing.Union[BaseModules.Module,type[BaseModules.Module]]'):
        self.ModuleList.addModule(module)
    
    def clear(self):
        self.ModuleList.clear()
        self.ModuleTypeSelectionWidget.clear()
    
    def populate(self):
        self.ModuleList.populate()
        self.ModuleTypeSelectionWidget.populate()

class ModuleTypeSelectionWidget(AGeWidgets.TightGridWidget):
    def __init__(self, parent:'ModuleListWidget') -> None:
        super().__init__(parent, makeCompact=False)
        self.Label = self.addWidget(QtWidgets.QLabel("Module Types",self))
        self.OnlyCoreCB = self.addWidget(QtWidgets.QCheckBox("Show only base modules",self))
        self.OnlyCoreCB.stateChanged.connect(lambda: self.populate())
        #MAYBE: only hide fulfilled unique mandatory modules
        self.HideUniqueMandatoryCB = self.addWidget(QtWidgets.QCheckBox("Hide mandatory basics",self))
        self.HideUniqueMandatoryCB.setToolTip("Hide basic modules that are mandatory and can only exist once per ship.\nThese are hull, thrusters, engines, and sensors.")
        self.HideUniqueMandatoryCB.setChecked(True)
        self.HideUniqueMandatoryCB.stateChanged.connect(lambda: self.populate())
        self.ModuleTypeList = self.addWidget(ModuleTypeList(self))
    
    def parent(self) -> 'ModuleListWidget':
        return super().parent()
    
    def addModule(self, module:'typing.Union[BaseModules.Module,type[BaseModules.Module]]'):
        self.parent().addModule(module)
    
    def populate(self, startsWith:'typing.Union[str,tuple[str],None]'=None, type_:'typing.Union[type[BaseModules.Module],tuple[type[BaseModules.Module]],None]'=None):
        if startsWith is None and self.OnlyCoreCB.isChecked():
            startsWith = "BaseModules"
        self.ModuleTypeList.populate(startsWith=startsWith, type_=type_, hideUniqueMandatory=self.HideUniqueMandatoryCB.isChecked())
    
    def clear(self):
        self.ModuleTypeList.clear()

class ModuleTypeList(QtWidgets.QListWidget):
    def __init__(self, parent:'ModuleListWidget') -> None:
        super().__init__(parent)
        self.itemDoubleClicked.connect(lambda item: self.addModule(item))
        self.installEventFilter(self)
    
    def parent(self) -> 'ModuleTypeSelectionWidget':
        return super().parent()
    
    def populate(self, startsWith:'typing.Union[str,tuple[str],None]'=None, type_:'typing.Union[type[BaseModules.Module],tuple[type[BaseModules.Module]],None]'=None, hideUniqueMandatory:bool=False):
        self.clear()
        for moduleName,moduleType in get.modules().items():
            if (moduleType.Buildable
                and (startsWith is None or moduleName.startswith(startsWith))
                and (type_ is None or issubclass(moduleType,type_))
                and (
                    not hideUniqueMandatory or not issubclass(moduleType,(BaseModules.Hull, BaseModules.Engine, BaseModules.Thruster, BaseModules.Sensor))
                    )
                ):
                item = ModuleTypeItem()
                item.setText(moduleName)
                item.setData(100, moduleType)
                self.addItem(item)
    
    def addModule(self, item:'ModuleTypeItem'):
        self.parent().addModule(item.data(100)) # get.modules()[self.AddModuleSelectBox.currentText()])

class InstalledModuleListWidget(AGeWidgets.TightGridWidget):
    def __init__(self, parent:'ModuleListWidget') -> None:
        super().__init__(parent, makeCompact=False)
        self.Label = self.addWidget(QtWidgets.QLabel("Installed Modules",self))
        self.ModuleList = self.addWidget(ModuleList(self))
    
    def parent(self) -> 'ModuleListWidget':
        return super().parent()
    
    def addModule(self, module:'typing.Union[BaseModules.Module,type[BaseModules.Module]]'):
        self.ModuleList.addModule(module)
    
    def clear(self):
        self.ModuleList.clear()
    
    def populate(self):
        self.ModuleList.populate()

class ModuleList(QtWidgets.QListWidget):
    def __init__(self, parent:'InstalledModuleListWidget') -> None:
        super().__init__(parent)
        self.itemDoubleClicked.connect(lambda item: self.selectModuleForEditor(item))
        self.installEventFilter(self)
    
    def lifeEditing(self):
        return self.constructionWidget().lifeEditing()
    
    def parent(self) -> 'InstalledModuleListWidget':
        return super().parent()
    
    def constructionWidget(self) -> 'ConstructionWidget':
        return self.parent().parent().parent()
    
    def getShipModuleOfType(self, module:'typing.Union[BaseModules.Module,type[BaseModules.Module]]', types:'list[type[BaseModules.Module]]'=None):
        if isinstance(module,type):
            t = module
        else:
            t = type(module)
        if types:
            for i in types:
                if AGeAux.isInstanceOrSubclass(module,i):
                    t = i
                    break
        print("looking for",t)
        return self.constructionWidget().Ship.getModuleOfType(t)
    
    def populate(self):
        self.clear()
        self.constructionWidget().ModuleEditor.clear()
        for module in self.constructionWidget().Ship.Modules:
            self.listModule(module)
    
    def addModule(self, module:'typing.Union[BaseModules.Module,type[BaseModules.Module]]'):
        moduleToReplace = None
        if not self.constructionWidget().canEdit(): return
        if (AGeAux.isInstanceOrSubclass(module,(BaseModules.Hull, BaseModules.Engine, BaseModules.Thruster, BaseModules.Sensor))
            and (moduleToReplace:=self.getShipModuleOfType(module, types=(BaseModules.Hull, BaseModules.Engine, BaseModules.Thruster, BaseModules.Sensor)))
            ):
            msgBox = QtWidgets.QMessageBox(self)
            msgBox.setText(f"Are you sure?")
            msgBox.setInformativeText(f"You already have a module of this type. In order to install the selected module you must replace the existing one. Do you want to replace {moduleToReplace.Name}?")
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Cancel)
            confirm = msgBox.exec() == QtWidgets.QMessageBox.Yes
            if confirm:
                self.removeModuleByReference(moduleToReplace, force=True)
            else:
                return
        elif not self.constructionWidget().canModuleBeAdded(module):
            NC(2,"Module can not be added.")
            return
        if isinstance(module,type):
            module = module()
        if self.lifeEditing():
            if module.Value > self.constructionWidget().constructionModule().ConstructionResourcesStored:
                NC(2, f"Not enough resources to add this module (Cost/Stored: {module.Value}/{self.constructionWidget().constructionModule().ConstructionResourcesStored})")
                if moduleToReplace:
                    self.constructionWidget().constructionModule().ConstructionResourcesStored += moduleToReplace.Value*2 # Ensure that there can be no rounding error that could stop readding it
                    self.addModule(moduleToReplace)
                    self.constructionWidget().constructionModule().ConstructionResourcesStored -= moduleToReplace.Value*2
                return
            else:
                self.constructionWidget().constructionModule().ConstructionResourcesStored -= module.Value
        module.resetCondition()
        item = self.listModule(module)
        self.constructionWidget()._addModuleToShip(item.data(100))
        self.constructionWidget().ModuleEditor.setModule(item)
    
    def listModule(self, module:'BaseModules.Module') -> 'ModuleItem':
        item = ModuleItem()
        item.setText(module.Name)
        item.setData(100, module)
        self.addItem(item)
        return item
    
    def selectModuleForEditor(self, item:'ModuleItem') -> None:
        self.constructionWidget().ModuleEditor.setModule(item)
    
    def removeModule(self, item:'ModuleItem', force=False):
        if not self.constructionWidget().canEdit(): return
        if not force and isinstance(item.data(100),(BaseModules.Hull, BaseModules.Engine, BaseModules.Thruster, BaseModules.Sensor)):
            NC(2, f"You can not remove essential modules. You can, however, replace them.")
            return
        if item.data(100) is self.constructionWidget().constructionModule():
            NC(2, f"Can not remove active construction module")
            return
        if self.lifeEditing():
            self.constructionWidget().constructionModule().ConstructionResourcesStored += item.data(100).Value
        self.constructionWidget().ModuleEditor.unsetModule(item)
        self.constructionWidget().removeModule(item.data(100))
        self.takeItem(self.row(item))
    
    def removeModuleByReference(self, module:'BaseModules.Module', force=False):
        for i in range(self.count()):
            item = self.item(i)
            if item.data(100) is module:
                self.removeModule(item=item, force=force)
                return
        NC(2,f"Could not find {module} in the list", tb=True)
    
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

class ModuleTypeItem(QtWidgets.QListWidgetItem):
    pass

class ModuleEditor(AGeWidgets.TightGridFrame):
    def __init__(self, parent:'ConstructionWidget') -> None:
        super().__init__(parent,makeCompact=False)
        self.NameLabel = self.addWidget(QtWidgets.QLabel("Module Editor", self))
        self.ValueLabel = self.addWidget(QtWidgets.QLabel("", self))
        self.Apply = self.addWidget(AGeWidgets.Button(self, "Apply", lambda: self.applyStats()))
        self.ModuleStatContainer = self.addWidget(AGeWidgets.TightGridFrame(self,makeCompact=False))
        #self.StatDict:'dict[str,typing.Callable[[],typing.Any]]' = {}
        self.StatDict:'dict[str,AGeInput._TypeWidget]' = {}
    
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
            self.ModuleStatContainer.deleteLater()
            self.ModuleStatContainer = None
    
    def loadModuleStats(self):
        if self.ModuleStatContainer:
            self.layout().removeWidget(self.ModuleStatContainer)
            self.ModuleStatContainer.deleteLater()
            self.ModuleStatContainer = None
        self.ModuleStatContainer = self.addWidget(AGeWidgets.TightGridFrame(self,makeCompact=False))
        self.StatDict = {statName:self.ModuleStatContainer.addWidget(widget()) for statName, widget in self.ActiveModule.getCustomisableStats().items()}
        for v in self.StatDict.values():
            v.S_ValueChanged.connect(lambda: self.previewCost())
    
    def applyStats(self):
        if self.ModuleStatContainer and self.ActiveModule and self.StatDict:
            if not self.parent().canEdit(): return
            if self.ActiveModule is self.parent().constructionModule().ConstructionResourcesStored:
                NC(2, f"Can not edit active construction module")
                return
            valueBefore:'float' = self.ActiveModule.Value
            statsBefore = self.ActiveModule.tocode_AGeLib_GetDict()
            for k,v in self.StatDict.items():
                setattr(self.ActiveModule,k,v())
            self._applyStats()
            if self.parent().lifeEditing():
                if self.ActiveModule.Value - valueBefore > self.parent().constructionModule().ConstructionResourcesStored:
                    NC(2, f"Not enough resources to modify this module (Cost/Stored: {self.ActiveModule.Value}/{self.parent().constructionModule().ConstructionResourcesStored+valueBefore})")
                    for k,v in statsBefore.items():
                        setattr(self.ActiveModule,k,v)
                    self._applyStats()
                # Not strictly required if the player could not afford the changes but in case makeValuesValid changes something we want to be fair
                #print(f"{self.parent().constructionModule().ConstructionResourcesStored=} += {valueBefore=} - {self.ActiveModule.Value=}")
                self.parent().constructionModule().ConstructionResourcesStored += valueBefore - self.ActiveModule.Value
                self.parent().ShipStats.updateShipInterface()
                self.parent().regenerateShipModel()
    
    def predictCost(self):
        module = self.ActiveModule.copy()
        for k,v in self.StatDict.items():
            setattr(module,k,v())
        module.resetCondition()
        module.automaticallyDetermineValues()
        cost = module.Value-self.ActiveModule.Value
        return cost
    
    def previewCost(self):
        self.updateValueLabel(costToChange=self.predictCost())
    
    def checkValidity(self):
        pass #TODO: Use this to check if applying the stats is valid (check)
    
    def _applyStats(self):
        adjustments = self.ActiveModule.makeValuesValid()
        if adjustments: NC(2, "Not all values were valid. The following adjustments were made:\n"+adjustments)
        self.ActiveModule.resetCondition()
        self.ActiveModule.automaticallyDetermineValues()
        self.parent().ShipStats.updateShipInterface()
        self.updateValueLabel()
        self.ActiveModuleItem.setText(self.ActiveModule.Name)
        self.loadModuleStats()
        self.NameLabel.setText(self.ActiveModule.Name)
    
    def updateValueLabel(self, costToChange:'int'=0):
        #text = f"Value: {self.ActiveModule.Value}\nThreat {self.ActiveModule.Threat}\nMass {self.ActiveModule.Mass}"
        #if costToChange: text += f"\nExpected cost to change: {costToChange}"
        #self.ValueLabel.setText(text)
        self.ValueLabel.setText(f"Value: {self.ActiveModule.Value}\nThreat {self.ActiveModule.Threat}\nMass {self.ActiveModule.Mass}\n{f'Expected cost to change: {round(costToChange,5)}' if round(costToChange,5) else ''}")
