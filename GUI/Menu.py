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


class Menu(QtWidgets.QScrollArea):
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget'] = None) -> None:
        super().__init__(parent)
        #TODO: This should probably become part of the options window with individual tabs for different option categories so that scrolling is not necessary
        #                                                                                        as scrolling can result in accidental changes for spin boxes
        self.setWidgetResizable(True)
        self.MainWidget = AGeWidgets.TightGridWidget(self)
        self.setWidget(self.MainWidget)
        
        self.SaveLoadWidget = self.MainWidget.addWidget(SaveLoadWidget(self.MainWidget))
        self.DifficultyOptionsWidget = self.MainWidget.addWidget(DifficultyOptionsWidget(self.MainWidget))
        self.HighlightOptionsWidget = self.MainWidget.addWidget(HighlightOptionsWidget(self.MainWidget))
        self.GraphicsOptionsWidget = self.MainWidget.addWidget(GraphicsOptionsWidget(self.MainWidget))
        self.SoundOptionsWidget = self.MainWidget.addWidget(SoundOptionsWidget(self.MainWidget))

class SaveLoadWidget(AGeWidgets.TightGridFrame):
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget'] = None) -> None:
        super().__init__(parent)
        self.Label = self.addWidget(QtWidgets.QLabel("Save/Load/New",self))
        self.HeadlineLine = self.addWidget(QtWidgets.QFrame(self))
        self.HeadlineLine.setFrameShape(QtWidgets.QFrame.HLine)
        self.HeadlineLine.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.NewButton  = self.addWidget(AGeWidgets.Button(self,"New" ,lambda: get.engine().newGame()))
        self.SaveButton = self.addWidget(AGeWidgets.Button(self,"Save",lambda: get.engine().save()))
        self.LoadButton = self.addWidget(AGeWidgets.Button(self,"Load",lambda: get.engine().load()))

class DifficultyOptionsWidget(AGeWidgets.TightGridFrame):
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget'] = None) -> None:
        super().__init__(parent)
        self.Label = self.addWidget(QtWidgets.QLabel("Difficulty",self))
        self.HeadlineLine = self.addWidget(QtWidgets.QFrame(self))
        self.HeadlineLine.setFrameShape(QtWidgets.QFrame.HLine)
        self.HeadlineLine.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.EnemyTotalStrength = self.addWidget(AGeInput.Float(self,"Enemy Total Strength",2.0,0.6,20.0))
        self.EnemyStrengthPerFleet = self.addWidget(AGeInput.Float(self,"Enemy Strength per Fleet",0.7,0.2,10.0))

class HighlightOptionsWidget(AGeWidgets.TightGridFrame):
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget'] = None) -> None:
        super().__init__(parent)
        self.Label = self.addWidget(QtWidgets.QLabel("Highlighting",self))
        self.HeadlineLine = self.addWidget(QtWidgets.QFrame(self))
        self.HeadlineLine.setFrameShape(QtWidgets.QFrame.HLine)
        self.HeadlineLine.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.HighlightWeaponRange = self.addWidget(AGeInput.Bool(self,"Highlight weapon range",True))
        self.HideGrid = self.addWidget(AGeInput.Bool(self,"Hide Grid",False))

class GraphicsOptionsWidget(AGeWidgets.TightGridFrame):
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget'] = None) -> None:
        super().__init__(parent)
        self.Label = self.addWidget(QtWidgets.QLabel("Graphics",self))
        self.HeadlineLine = self.addWidget(QtWidgets.QFrame(self))
        self.HeadlineLine.setFrameShape(QtWidgets.QFrame.HLine)
        self.HeadlineLine.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.ChangeSkyboxButton = self.addWidget(AGeWidgets.Button(self,"Generate new Skybox", self.newSkybox))
        self.SkyboxStatic = self.addWidget(AGeInput.Bool(self,"Use static Skybox\nUnchecked: Use pure shader Skybox (lower performance)\nChecked: Use static skybox (takes long to generate)", False))
        self.SkyboxResolution = self.addWidget(AGeInput.Int(self,"Static Skybox Resolution (512·2ˣ)", 2, 0, 4))
        self.AsteroidResolution = self.addWidget(AGeInput.Int(self,"Asteroid Resolution\n(lower=faster battle loading)",10,5,50,"²"))
        self.AsteroidNoisePasses = self.addWidget(AGeInput.Int(self,"Asteroid Noise Passes\n(higher=more diverse asteroids\n but higher likelihood of 'negative volume')",3,0,5))
        self.AsteroidTexture = self.addWidget(AGeInput.Bool(self,"Use a randomly generated texture for asteroids\nIf disabled the individual faces are\n coloured which results in a retro look",False))
        self.AsteroidTextureResolution = self.addWidget(AGeInput.Int(self,"Asteroid Texture Resolution\n(lower=faster battle loading)",256,64,1024,"²"))
        self.ShipTexture = self.addWidget(AGeInput.Bool(self,"Use a randomly generated texture for ships\nThis makes it look more interesting.",True))
        self.RedrawEntireGridWhenHighlighting = self.addWidget(AGeInput.Bool(self,"Redraw entire grid when highlighting\n(Useful when changing hex colours)\n(Disable if selecting a unit is slow)",True))
    
    def newSkybox(self):
        get.scene().loadSkybox()

class SoundOptionsWidget(AGeWidgets.TightGridFrame):
    def __init__(self, parent: typing.Optional['QtWidgets.QWidget'] = None) -> None:
        super().__init__(parent)
        self.Label = self.addWidget(QtWidgets.QLabel("Sound",self))
        self.HeadlineLine = self.addWidget(QtWidgets.QFrame(self))
        self.HeadlineLine.setFrameShape(QtWidgets.QFrame.HLine)
        self.HeadlineLine.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.WeaponSoundVolume = self.addWidget(AGeInput.Float(self,"Weapon Sound Volume",0.07,0.001,1.0))
        self.ExplosionSoundVolume = self.addWidget(AGeInput.Float(self,"Explosion Sound Volume",0.12,0.001,1.0))
