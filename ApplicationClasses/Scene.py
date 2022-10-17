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

from ApplicationClasses import Camera
from BaseClasses import HexBase, FleetBase, ShipBase, ModelBase, UnitManagerBase, get
from GUI import Windows, WidgetsBase

def getSkyboxPathList(sector=True, sun=True):
    l = []
    #SKYBOX_PATH_LIST_SECTOR = [ #TODO: automatically scan the folders and populate this list
    #    "Models/Skyboxes/Sector/GreenSpace1/GreenSpace1.egg",
    #    "Models/Skyboxes/Sector/BlackOrangeSpace1/BlackOrangeSpace1.egg",
    #]
    #SKYBOX_PATH_LIST_SUN = [ #TODO: automatically scan the folders and populate this list
    #    "Models/Skyboxes/Sun/BlackOrangeSpace1/BlackOrangeSpace1.egg",
    #]
    if sector:
        specFolder = os.path.join("Models","Skyboxes","Sector")
        for folder in os.listdir(specFolder):
            for file in os.listdir(os.path.join(specFolder,folder)):
                if file.endswith(".egg"):
                    l.append(os.path.join(specFolder,folder,file))
        #l += SKYBOX_PATH_LIST_SECTOR
    if sun:
        specFolder = os.path.join("Models","Skyboxes","Sun")
        for folder in os.listdir(specFolder):
            for file in os.listdir(os.path.join(specFolder,folder)):
                if file.endswith(".egg"):
                    l.append(os.path.join(specFolder,folder,file))
        #l += SKYBOX_PATH_LIST_SUN
    return l

def getRandomSkyboxPath(sector=True, sun=True):
    l = getSkyboxPathList(sector=sector, sun=sun)
    return random.choice(l)

class BaseClass(ape.APEPandaBase):
    def start(self):
        if self.render_pipeline:
            # Set time of day
            self.render_pipeline.daytime_mgr.time = "5:20"
            
            # Use a special effect for rendering the scene, this is because the
            # roaming ralph model has no normals or valid materials
            self.render_pipeline.set_effect(ape.render(), "_pipeline_effect-texture.yaml", {}, sort=250)
        
        self.disableMouse()  # Disable mouse camera control
        self.camera.setPosHpr(0, -12, 8, 0, -35, 0)  # Set the camera
        
        # Since we are using collision detection to do picking, we set it up like
        # any other collision detection system with a traverser and a handler
        self.picker = p3dc.CollisionTraverser()  # Make a traverser
        self.pq = p3dc.CollisionHandlerQueue()  # Make a handler
        # Make a collision node for our picker ray
        self.pickerNode = p3dc.CollisionNode('mouseRay')
        # Attach that node to the camera since the ray will need to be positioned relative to it
        self.pickerNP = self.camera.attachNewNode(self.pickerNode)
        # Everything to be picked will use bit 1. This way if we were doing other collision we could separate it
        self.pickerNode.setFromCollideMask(p3dc.BitMask32.bit(1))
        self.pickerRay = p3dc.CollisionRay()  # Make our ray
        # Add it to the collision node
        self.pickerNode.addSolid(self.pickerRay)
        # Register the ray as something that can cause collisions
        self.picker.addCollider(self.pickerNP, self.pq)
        # self.picker.showCollisions(render)


class BaseScene(ape.APEScene):
    _SCENE_TYPE_STR = "Unknown"
    def start(self):
        self.Camera = Camera.StrategyCamera()
        ape.base().win.setClearColor(p3dc.Vec4(0,0,0,1))
        self.loadSkybox()
        
        # Per-pixel lighting and shadows are initially on
        self.perPixelEnabled = True
        self.shadowsEnabled = True
        
        self.HexGrid = HexBase.HexGrid(name=f"{self._SCENE_TYPE_STR} Hex Grid number {get.engine()._increaseAndGetNumOfGridsOfType(self._SCENE_TYPE_STR)}")
        self.HexGrid.generateHex()
        
        #CRITICAL: use self.Camera.setLimits
        
        #base().accept("l", self.togglePerPixelLighting)
        #base().accept("e", self.toggleShadows
    
    def loadSkybox(self):
        self.Camera.loadSkybox(getRandomSkyboxPath())
    
    def pause(self):
        self.HexGrid.Root.hide()
        self.HexGrid.Active = False
        self.Camera.pause()
    
    def continue_(self):
        self.HexGrid.Root.show()
        self.HexGrid.Active = True
        self.HexGrid.bindEvents()
        self.Camera.continue_()
    
    def end(self):
        self.HexGrid.destroy()
        self.Camera.destroy()
        del self.HexGrid
        del self.Camera

class CampaignScene(BaseScene):
    _SCENE_TYPE_STR = "Campaign"
    def loadSkybox(self):
        self.Camera.loadSkybox(getRandomSkyboxPath(sector=True, sun=False))

class BattleScene(BaseScene):
    _SCENE_TYPE_STR = "Battle"
    def loadSkybox(self):
        self.Camera.loadSkybox(getRandomSkyboxPath(sector=True, sun=True))










    #region For future use: These methods are not used currently but will probably be useful in the future. Ignore them for now
    #def makeStatusLabel(self, i):
    #    """
    #    Macro-like function to reduce the amount of code needed to create the
    #    onscreen instructions
    #    """
    #    return OnscreenText(
    #        parent=base().a2dTopLeft, align=p3dc.TextNode.ALeft,
    #        style=1, fg=(1, 1, 0, 1), shadow=(0, 0, 0, .4),
    #        pos=(0.06, -0.1 -(.06 * i)), scale=.05, mayChange=True)
    #
    #def updateStatusLabel(self):
    #    """Builds the onscreen instruction labels"""
    #    self.updateLabel(self.lightingPerPixelText, "(l) Per-pixel lighting is", self.perPixelEnabled)
    #    self.updateLabel(self.lightingShadowsText, "(e) Shadows are", self.shadowsEnabled)
    #
    #def updateLabel(self, obj, base, var):
    #    """Appends either (on) or (off) to the base string based on the base value"""
    #    if var:
    #        s = " (on)"
    #    else:
    #        s = " (off)"
    #    obj.setText(base + s)
    #
    #def togglePerPixelLighting(self):
    #    """This function turns per-pixel lighting on or off."""
    #    if self.perPixelEnabled:
    #        self.perPixelEnabled = False
    #        if self.shadowsEnabled:
    #            self.shadowsEnabled = False
    #            self.light.setShadowCaster(False)
    #            #  self.light2.setShadowCaster(False)
    #        render().clearShader()
    #    else:
    #        self.perPixelEnabled = True
    #        render().setShaderAuto()
    #    self.updateStatusLabel()
    #
    #def toggleShadows(self):
    #    """This function turns shadows on or off."""
    #    if self.shadowsEnabled:
    #        self.shadowsEnabled = False
    #        self.light.setShadowCaster(False)
    #        #  self.light2.setShadowCaster(False)
    #    else:
    #        if not self.perPixelEnabled:
    #            self.togglePerPixelLighting()
    #        self.shadowsEnabled = True
    #        self.light.setShadowCaster(True, 1024, 1024)
    #        #  self.light2.setShadowCaster(True, 1024, 1024)
    #    self.updateStatusLabel()
    #endregion For future use
