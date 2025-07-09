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
        self.Name = name
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
    
    def resources(self) -> 'Resources._ResourceDict':
        raise NotImplementedError()
    
    def __iter__(self) -> 'typing.Generator[_StorageDisplayBase]':
        for i in self.ParticipantWidgets:
            yield i
            for j in i:
                yield j
    
    def __contains__(self, w:'typing.Union[_StorageDisplayBase,None]') -> bool:
        if not w: return False
        for i in self:
            if i is w:
                return True
        return False
    
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
    
    def addResources(self, r:'Resources._ResourceDict') -> 'Resources._ResourceDict':
        """
        Try to put as many resources from a _ResourceDict into a container and returns everything that did not fit as a new _ResourceDict\n
        the given _ResourceDict is not altered!
        """
        raise NotImplementedError(f"addResources is not implemented for {type(self)}")
    
    def subtractResources(self, r:'Resources._ResourceDict') -> 'Resources._ResourceDict':
        return self.addResources(-r)

class TransferWidget(_StorageDisplayBase):
    S_SelectionChanged = pyqtSignal()
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget']=None, participants=None) -> None:
        super().__init__(parent, participants)
        self.Selected1:'typing.Union[_StorageDisplayBase,None]' = None
        self.Selected2:'typing.Union[_StorageDisplayBase,None]' = None
        self.TransferSlider = self.addOuterWidget(TransferSlider(self)) #TODO: This being inside the scroll area of the window is very ugly and unintuitive... This needs to change
        
        App().S_ColourChanged.connect(self._setPalette)
        
        #self.addParticipant(participants)
    
    def _setPalette(self):
        try:
            self.colourAsSelected(self.Selected1)
            self.colourAsSelected(self.Selected2)
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
        if self.Selected1 and (w in self.Selected1 or self.Selected1 in w):
            self.colourAsUnselected(self.Selected1)
            self.Selected1 = None
        if self.Selected2 and (w in self.Selected2 or self.Selected2 in w):
            self.colourAsUnselected(self.Selected2)
            self.Selected2 = None
        if self.Selected1 and self.Selected2:
            self.colourAsUnselected(self.Selected2)
        if self.Selected1:
            self.Selected2 = self.Selected1
        self.Selected1 = w
        self.colourAsSelected(self.Selected1)
        self.S_SelectionChanged.emit()
    
    def childRightClicked(self, w:'_StorageDisplayBase'):
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
        if self.Selected1 and (w in self.Selected1 or self.Selected1 in w):
            self.colourAsUnselected(self.Selected1)
            self.Selected1 = None
        if self.Selected2 and (w in self.Selected2 or self.Selected2 in w):
            self.colourAsUnselected(self.Selected2)
            self.Selected2 = None
        self.colourAsUnselected(self.Selected2)
        self.Selected2 = w
        self.colourAsSelected(self.Selected2)
        self.S_SelectionChanged.emit()
    
    def connectChildren(self):
        for i in self:
            i.S_ClickedL.connect(self.childLeftClicked)
            i.S_ClickedR.connect(self.childRightClicked)

class TransferSlider(AGeWidgets.TightGridWidget):
    def __init__(self, parent:'TransferWidget') -> None:
        self.transferWidget = weakref.ref(parent)
        super().__init__(parent)
        self.Mutex = QtCore.QMutex()
        self.Items:'list[SliderItem]' = []
        self.HeaderLabel1:'typing.Union[QtWidgets.QLabel,None]' = None
        self.HeaderLabel2:'typing.Union[QtWidgets.QLabel,None]' = None
        self.transferWidget().S_SelectionChanged.connect(self.setUpSliders)
    
    def setUpSliders(self):
        self.clear()
        c1 = self.transferWidget().Selected2
        c2 = self.transferWidget().Selected1
        if c1: self.HeaderLabel1 = self.addWidget(QtWidgets.QLabel(c1.Name),0,1)
        if c2: self.HeaderLabel2 = self.addWidget(QtWidgets.QLabel(c2.Name),0,3)
        if not (c1 and c2): return
        r = abs(c1.resources()) + abs(c2.resources())
        for c,i in enumerate(r):
            if bool(r[i]):
                self.Items.append(SliderItem(self, c+1, i, c1, c2))
    
    def clear(self):
        for i in self.Items:
            i.deleteLater()
        self.Items.clear()
        if self.HeaderLabel1:
            self.layout().removeWidget(self.HeaderLabel1)
            self.HeaderLabel1.deleteLater()
            self.HeaderLabel1 = None
        if self.HeaderLabel2:
            self.layout().removeWidget(self.HeaderLabel2)
            self.HeaderLabel2.deleteLater()
            self.HeaderLabel2 = None

class SliderItem():
    def __init__(self, parent:'TransferSlider',c:int,resource:'Resources.Resource_',c1:'_StorageDisplayBase',c2:'_StorageDisplayBase') -> None:
        self.transferSlider = weakref.ref(parent)
        self.Resource = resource
        self.container1 = weakref.ref(c1)
        self.container2 = weakref.ref(c2)
        self.OriginalValue1 = c1.resources()[resource].Quantity
        self.OriginalValue2 = c2.resources()[resource].Quantity
        self.LabelName = self.transferSlider().addWidget(QtWidgets.QLabel(str(resource)),c,0)
        self.Label1 = self.transferSlider().addWidget(QtWidgets.QLabel(str(round(c1.resources()[resource].Quantity,5))),c,1)
        self.Slider = self.transferSlider().addWidget(AGeInput.FloatSlider(self.transferSlider(),"",0,
                                                                        min_=-min(c1.resources().FreeCapacity,c2.resources()[resource].Quantity),
                                                                        max_=+min(c2.resources().FreeCapacity,c1.resources()[resource].Quantity)),c,2)
        self.Label2 = self.transferSlider().addWidget(QtWidgets.QLabel(str(round(c2.resources()[resource].Quantity,5))),c,3)
        self.Slider.S_ValueChanged.connect(self.apply)
    
    def apply(self):
        with QtCore.QMutexLocker(self.transferSlider().Mutex):
            r = self.Resource.new(self.OriginalValue1 - self.container1().resources()[self.Resource] - self.Slider())
            d = Resources._ResourceDict()
            d.add(r)
            a = self.container1().addResources(d)
            b = self.container2().addResources(-d)
        if bool(a+b):
            NC(1,"Error while transferring resource",input=f"To be transferred:\n{d=}\n\nCould not fit in a:\n{a=}\n\nCould not fit in b:\n{b=}",tb=True)
            #CRITICAL: Handle resource transfer errors!
            #NOTE: This bool-check allows for resource duplication/deletion due to floating-point noise since I had to give it a tolerance of 1e-14.
            #       Loosing 1e-15 of a resource due to this and then not being able to build something could be frustrating...
            #       Though, this is actually a problem everywhere where resources are transferred/spend/gained/processed and hard to avoid...
        self.update()
    
    def update(self):
        self.transferSlider().transferWidget().update()
        self.Label1.setText(str(round(self.container1().resources()[self.Resource].Quantity,5)))
        self.Label2.setText(str(round(self.container2().resources()[self.Resource].Quantity,5)))
    
    def deleteLater(self):
        self.transferSlider().layout().removeWidget(self.LabelName)
        self.transferSlider().layout().removeWidget(self.Label1)
        self.transferSlider().layout().removeWidget(self.Slider)
        self.transferSlider().layout().removeWidget(self.Label2)
        self.LabelName.deleteLater()
        self.Label1.deleteLater()
        self.Slider.deleteLater()
        self.Label2.deleteLater()

class HexStorageDisplay(_StorageDisplayBase):
    def __init__(self, parent: '_StorageDisplayBase', content: 'HexBase._Hex') -> None:
        super().__init__(parent, name=content.Name)
        self.content = weakref.ref(content)
        for i in content:
            self.addParticipant(i)
        #TODO: free and harvestabel resources should have name labels. (Though I want to get rid of those things anyway since they don't get saved and are incompatible with the general architecture and design of the program.)
        self.addParticipant(content.ResourcesFree)
        self.addParticipant(content.ResourcesHarvestable)
    
    def resources(self) -> 'Resources._ResourceDict':
        r = Resources._ResourceDict()
        for i in self.content():
            r += i.ResourceManager.storedResources()
        return r
    
    def addResources(self, r:'Resources._ResourceDict') -> 'Resources._ResourceDict':
        """
        Try to put as many resources from a _ResourceDict into a container and returns everything that did not fit as a new _ResourceDict\n
        the given _ResourceDict is not altered!
        """
        #TODO: If adding resources and space is insufficient dump resources into free floating container
        #TODO: If subtracting resources consider free floating containers first
        for i in self.content():
            if i.Team == 1: #TODO: Also consider free floating containers
                r = i.ResourceManager.add(r)
        return r

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
    
    def update(self):
        self.Label.setText(self.content().ResourceManager.storedResources().text())
        super().update()
    
    def resources(self) -> 'Resources._ResourceDict':
        return self.content().ResourceManager.storedResources()
    
    def addWidget(self, widget:'QtWidgets.QWidget', *args, **kwargs):
        if self._ContentCounter is None:
            self.Frame.addWidget(widget, *args, **kwargs)
        else:
            self.Frame.addWidget(widget, 1, self._ContentCounter)
            self._ContentCounter += 1
        return widget
    
    def addResources(self, r:'Resources._ResourceDict') -> 'Resources._ResourceDict':
        """
        Try to put as many resources from a _ResourceDict into a container and returns everything that did not fit as a new _ResourceDict\n
        the given _ResourceDict is not altered!
        """
        return self.content().ResourceManager.add(r)

class ShipStorageDisplay(_StorageDisplayBase):
    def __init__(self, parent: '_StorageDisplayBase', content: 'ShipBase.ShipBase') -> None:
        super().__init__(parent, name=content.Name)
        self.content = weakref.ref(content)
        for i in content.Modules:
            if isinstance(i, BaseEconomicModules.Cargo):
                self.addParticipant(i)
    
    def resources(self) -> 'Resources._ResourceDict':
        return self.content().ResourceManager.storedResources()
    
    def addResources(self, r:'Resources._ResourceDict') -> 'Resources._ResourceDict':
        """
        Try to put as many resources from a _ResourceDict into a container and returns everything that did not fit as a new _ResourceDict\n
        the given _ResourceDict is not altered!
        """
        return self.content().ResourceManager.add(r)

class ResourceDictionaryStorageDisplay(_StorageDisplayBase):
    def __init__(self, parent: '_StorageDisplayBase', content: 'Resources._ResourceDict', name="") -> None:
        super().__init__(parent, name=name)
        self.content = weakref.ref(content)
        #TODO: This does work in principle but could break due to things overwriting the original resource dictionaries.
        #       These dictionaries are not meant to be used in the way they are used in this context.
        #       Maybe this widget should just be deleted...
        
        self.Label:'QtWidgets.QLabel' = self.addWidget(QtWidgets.QLabel(content.text()))
    
    def update(self):
        self.Label.setText(self.content().text())
    
    def resources(self) -> 'Resources._ResourceDict':
        return self.content()
    
    def addResources(self, r:'Resources._ResourceDict') -> 'Resources._ResourceDict':
        """
        Try to put as many resources from a _ResourceDict into a container and returns everything that did not fit as a new _ResourceDict\n
        the given _ResourceDict is not altered!
        """
        return self.content().fillFrom(r)

class ModuleStorageDisplay(ResourceDictionaryStorageDisplay):
    def __init__(self, parent: '_StorageDisplayBase', content: 'BaseEconomicModules.Cargo') -> None:
        self.content_CargoModule = weakref.ref(content)
        super().__init__(parent, content.storedResources(), name=content.Name)
    
    def update(self):
        self.Label.setText(self.content_CargoModule().storedResources().text())
        super().update()
    
    def resources(self) -> 'Resources._ResourceDict':
        return self.content_CargoModule().storedResources()
    
    def addResources(self, r:'Resources._ResourceDict') -> 'Resources._ResourceDict':
        """
        Try to put as many resources from a _ResourceDict into a container and returns everything that did not fit as a new _ResourceDict\n
        the given _ResourceDict is not altered!
        """
        return self.content_CargoModule().storedResources().fillFrom(r)
