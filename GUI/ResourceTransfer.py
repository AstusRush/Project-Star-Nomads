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

from BaseClasses import ShipBase, FleetBase, BaseModules, HexBase
from Economy import BaseEconomicModules, Resources

if TYPE_CHECKING:
    from GUI import ModuleWidgets

from BaseClasses import get

class TransferWindow(AWWF):
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget']=None) -> None:
        super().__init__(parent)
        self.StandardSize = (1200,650)
        self.ScrollArea = QtWidgets.QScrollArea(self)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(5)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ScrollArea.sizePolicy().hasHeightForWidth())
        self.ScrollArea.setSizePolicy(sizePolicy)
        self.ScrollArea.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        self.ScrollArea.setWidgetResizable(True)
        self.ScrollArea.setObjectName("ScrollArea")
        #self.ScrollArea.set
        self.TransferWidget = TransferWidget(self.ScrollArea)
        self.setCentralWidget(self.ScrollArea)
        self.ScrollArea.setWidget(self.TransferWidget)
    
    def show(self):
        super().show()
        App().processEvents()
        self.positionReset()
        App().processEvents()
        self.activateWindow()
    
    def addParticipants(self, participants):
        #TODO: Enforce that this can only be called once since the child connection would break otherwise
        self.TransferWidget.addParticipants(participants)
        self.TransferWidget.connectChildren()
    
    def addParticipant(self, participant):
        #TODO: Enforce that this can only be called once since the child connection would break otherwise
        self.TransferWidget.addParticipant(participant)
        self.TransferWidget.connectChildren()

class _StorageDisplayBase(AGeWidgets.TightGridWidget):
    S_ClickedL = pyqtSignal(QtWidgets.QWidget)
    S_ClickedR = pyqtSignal(QtWidgets.QWidget)
    def __init__(self, parent: typing.Optional['_StorageDisplayBase']=None,
                        participants
                                :'list[typing.Union[HexBase._Hex,FleetBase.FleetBase,ShipBase.ShipBase,BaseEconomicModules.Cargo,Resources._ResourceDict]]'
                                =None,
                        name="") -> None:
        self.ParticipantWidgets:'set[_StorageDisplayBase]' = set()
        super().__init__(parent)
        self.Frame:'AGeWidgets.TightGridFrame' = self.addOuterWidget(AGeWidgets.TightGridFrame(self))
        if name:
            self.NameLabel = self.addWidget(QtWidgets.QLabel(name))
        self.addParticipants(participants)
        self.setAutoFillBackground(True)
        self.installEventFilter(self)
    
    def eventFilter(self, source, event):
        # type: (QtWidgets.QWidget, QtCore.QEvent|QtGui.QKeyEvent|QtGui.QMouseEvent) -> bool
        try:
            if event.type() == QtCore.QEvent.Type.MouseButtonPress:
                if   event.button() == QtCore.Qt.MouseButton.LeftButton:
                    self.S_ClickedL.emit(self)
                    return True
                elif event.button() == QtCore.Qt.MouseButton.RightButton:
                    self.S_ClickedR.emit(self)
                    return True
                #NC(10,source)
                #if TYPE_CHECKING: event:QtGui.QMouseEvent = event
                #self.childAt(event.pos())
        except:
            NC(1,exc=True)
        return super().eventFilter(source, event)
    
    def __iter__(self) -> 'typing.Generator[_StorageDisplayBase]':
        for i in self.ParticipantWidgets:
            yield i
            for j in i:
                yield j
    
    def addWidget(self, widget:'QtWidgets.QWidget', *args, **kwargs):
        self.Frame.addWidget(widget, *args, **kwargs)
        return widget
    
    def addOuterWidget(self, widget:'QtWidgets.QWidget', *args, **kwargs):
        super().addWidget(widget, *args, **kwargs)
        return widget
    
    def addParticipants(self, participants):
        if not participants: return
        for i in participants:
            self.addParticipant(i)
    
    def addParticipant(self, participant):
        if   isinstance(participant, HexBase._Hex):
            w = self.addWidget(HexStorageDisplay(self, participant))
        elif isinstance(participant, FleetBase.FleetBase):
            w = self.addWidget(FleetStorageDisplay(self, participant))
        elif isinstance(participant, ShipBase.ShipBase):
            w = self.addWidget(ShipStorageDisplay(self, participant))
        elif isinstance(participant, BaseEconomicModules.Cargo):
            w = self.addWidget(ModuleStorageDisplay(self, participant))
        elif isinstance(participant, Resources._ResourceDict):
            w = self.addWidget(ResourceDictionaryStorageDisplay(self, participant))
        elif participant is None:
            return
        else:
            NC(2,f"_StorageDisplayBase can not handle objects of type {type(participant)}",tb=True)
            return
        self.ParticipantWidgets.add(w)
    
    def update(self):
        try:
            for i in self.ParticipantWidgets:
                i.update()
        except:
            NC(2,"Could not update resource display", exc=True)

class TransferWidget(_StorageDisplayBase):
    S_SelectionChanged = pyqtSignal()
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget']=None, participants=None) -> None:
        super().__init__(parent, participants)
        self.Selected1:'typing.Union[_StorageDisplayBase,None]' = None
        self.Selected2:'typing.Union[_StorageDisplayBase,None]' = None
        self.TransferSlider = self.addOuterWidget(TransferSlider(self))
        #TODO: Basic UI Setup
        
        App().S_ColourChanged.connect(self._setPalette)
        
        #self.addParticipant(participants)
    
    def _setPalette(self):#, palette:'QtGui.QPalette'):
        #NOTE: Changing the palette closes the transfer window in 90% of cases but it has nothing to do with any of the setPalette or eventFilter code...
        try:
            palette = App().Palette
            ret = super().setPalette(palette)
            for i in self:
                try:
                    i.setPalette(palette)
                except:
                    NC(2,exc=True)
            self.colourAsSelected(self.Selected1)
            self.colourAsSelected(self.Selected2)
            return ret
        except:
            NC(2,exc=True)
    
    def colourAsSelected(self, w:'typing.Union[_StorageDisplayBase,None]'):
        if w:
            pal = self.palette()
            pal.setBrush(pal.ColorGroup.All, pal.ColorRole.Window, self.palette().brush(pal.ColorGroup.Active, pal.ColorRole.AlternateBase))
            w.setPalette(pal)
    
    def colourAsUnselected(self, w:'typing.Union[_StorageDisplayBase,None]'):
        if w:
            w.setPalette(self.palette())
    
    def childLeftClicked(self, w:'_StorageDisplayBase'):
        #TODO: Handle selection where one is the child of the other since transfer would not work correctly and neither does highlighting
        if not w: return
        if self.Selected1 is w:
            self.colourAsUnselected(self.Selected1)
            self.Selected1 = self.Selected2
            self.Selected2 = None
            self.S_SelectionChanged.emit()
            return
        if self.Selected2 is w:
            self.colourAsUnselected(self.Selected2)
            self.Selected2 = None
            self.S_SelectionChanged.emit()
            return
        if self.Selected1 and self.Selected2:
            self.colourAsUnselected(self.Selected2)
        if self.Selected1:
            self.Selected2 = self.Selected1
        self.Selected1 = w
        self.colourAsSelected(self.Selected1)
        self.S_SelectionChanged.emit()
    
    def childRightClicked(self, w:'_StorageDisplayBase'):
        if self.Selected2 is w:
            self.colourAsUnselected(self.Selected2)
            self.Selected2 = None
            self.S_SelectionChanged.emit()
            return
        self.colourAsUnselected(self.Selected2)
        self.Selected2 = w
        self.colourAsSelected(self.Selected2)
        self.S_SelectionChanged.emit()
    
    def connectChildren(self):
        for i in self:
            i.S_ClickedL.connect(self.childLeftClicked)
            i.S_ClickedR.connect(self.childRightClicked)

class TransferSlider(QtWidgets.QWidget):
    def __init__(self, parent:'TransferWidget') -> None:
        self.TransferWidget = parent
        super().__init__(parent)

class HexStorageDisplay(_StorageDisplayBase):
    def __init__(self, parent: '_StorageDisplayBase', content: 'HexBase._Hex') -> None:
        super().__init__(parent, name=content.Name)
        self.content = weakref.ref(content)
        for i in content:
            self.addParticipant(i)
        #TODO: free and harvestabel resources should have name labels
        #TODO: Validate that updating these resource dictionaries actually works
        #       (Are those references or copies? I think that this would probably break due to reassignments of those members somewhere.
        #       These dictionaries are not meant to be used in the way we use them here)
        self.addParticipant(content.ResourcesFree)
        self.addParticipant(content.ResourcesHarvestable)
        pass #TODO

class FleetStorageDisplay(_StorageDisplayBase):
    def __init__(self, parent: '_StorageDisplayBase', content: 'FleetBase.FleetBase') -> None:
        self._ContentCounter = None
        super().__init__(parent, name=content.Name)
        self._ContentCounter = 0
        self.content = weakref.ref(content)
        self.Label:'QtWidgets.QLabel' = self.addWidget(QtWidgets.QLabel(content.ResourceManager.storedResources().text()))
        for i in content.Ships:
            if any(isinstance(j, BaseEconomicModules.Cargo) for j in i.Modules):
                self.addParticipant(i)
        pass #TODO
    
    def update(self):
        self.Label.setText(self.content().ResourceManager.storedResources().text())
        super().update()
    
    def addWidget(self, widget:'QtWidgets.QWidget', *args, **kwargs):
        if self._ContentCounter is None:
            self.Frame.addWidget(widget, *args, **kwargs)
        else:
            self.Frame.addWidget(widget, 1, self._ContentCounter)
            self._ContentCounter += 1
        return widget

class ShipStorageDisplay(_StorageDisplayBase):
    def __init__(self, parent: '_StorageDisplayBase', content: 'ShipBase.ShipBase') -> None:
        super().__init__(parent, name=content.Name)
        self.content = weakref.ref(content)
        for i in content.Modules:
            if isinstance(i, BaseEconomicModules.Cargo):
                self.addParticipant(i)
        pass #TODO

class ResourceDictionaryStorageDisplay(_StorageDisplayBase):
    def __init__(self, parent: '_StorageDisplayBase', content: 'Resources._ResourceDict', name="") -> None:
        super().__init__(parent, name=name)
        self.content = weakref.ref(content)
        #TODO: Are those references or copies? I think that this would probably break due to reassignments of those members somewhere.
        #       These dictionaries are not meant to be used in the way we use them here!
        #       Maybe this widget should just be deleted
        
        self.Label:'QtWidgets.QLabel' = self.addWidget(QtWidgets.QLabel(content.text()))
        
        pass #TODO
    
    def update(self):
        self.Label.setText(self.content().text())

class ModuleStorageDisplay(ResourceDictionaryStorageDisplay):
    def __init__(self, parent: '_StorageDisplayBase', content: 'BaseEconomicModules.Cargo') -> None:
        self.content_CargoModule = weakref.ref(content)
        super().__init__(parent, content.storedResources(), name=content.Name)
    
    def update(self):
        self.Label.setText(self.content_CargoModule().storedResources().text())
        super().update()
