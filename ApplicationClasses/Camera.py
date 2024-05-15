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

from BaseClasses import get

if TYPE_CHECKING:
    from BaseClasses import HexBase

class StrategyCamera(DirectObject):
    def __init__(self):
        ape.base().win.setClearColor(p3dc.Vec4(0,0,0,1))
        self.Active = True
        self.Plane = p3dc.Plane(p3dc.Vec3(0, 0, 1), p3dc.Point3(0, 0, 0))
        
        self.SpaceSkyBoxCentre = None
        self.SpaceSkyBox = None
        
        self._MouseTask = None
        self._MoveCameraTask = None
        
        self.CameraCenter = p3dc.NodePath(p3dc.PandaNode("CameraCenter"))
        self.CameraCenter.reparentTo(ape.render())
        self.CameraCenter.setPos(p3dc.Vec3(0,0,0))
        self.CameraRotCenter = p3dc.NodePath(p3dc.PandaNode("CameraRotCenter"))
        self.CameraRotCenter.reparentTo(self.CameraCenter)
        self.CameraRotCenter.setPos(p3dc.Vec3(0,0,0))
        self.CameraRotCenter.setP(-45)
        ape.base().camera.reparentTo(self.CameraRotCenter)
        ape.base().camera.setPos(0,-15,0)
        ape.base().camera.lookAt(self.CameraCenter)
        ape.base().camLens.set_near(0.1)
        
        self.LimitX: typing.Tuple[float,float] = (float("-inf"), float("inf"))
        self.LimitY: typing.Tuple[float,float] = (float("-inf"), float("inf"))
        
        self.SmoothCam = False
        self.CamMouseControl = False
        self.CamMouseControlRotate = False
        self.CamMouseControlCentre = p3dc.Vec3(0,0,0)
        self.bindEvents()
    
    def bindEvents(self):
        self._MouseTask = base().taskMgr.add(lambda task: self._mouseTask(task), 'mouseTask')
        
        self.KeyMap = {"cam-left":0, "cam-right":0, "cam-forward":0, "cam-backward":0, "cam-rot-left":0, "cam-rot-right":0}
        self.acceptAllCombinations("a", self.setKey, ["cam-left",1])
        self.acceptAllCombinations("d", self.setKey, ["cam-right",1])
        self.acceptAllCombinations("w", self.setKey, ["cam-forward",1])
        self.acceptAllCombinations("s", self.setKey, ["cam-backward",1])
        self.acceptAllCombinations("arrow_left", self.setKey, ["cam-left",1])
        self.acceptAllCombinations("arrow_right", self.setKey, ["cam-right",1])
        self.acceptAllCombinations("arrow_up", self.setKey, ["cam-forward",1])
        self.acceptAllCombinations("arrow_down", self.setKey, ["cam-backward",1])
        self.acceptAllCombinations("a-up", self.setKey, ["cam-left",0])
        self.acceptAllCombinations("d-up", self.setKey, ["cam-right",0])
        self.acceptAllCombinations("w-up", self.setKey, ["cam-forward",0])
        self.acceptAllCombinations("s-up", self.setKey, ["cam-backward",0])
        self.acceptAllCombinations("arrow_left-up", self.setKey, ["cam-left",0])
        self.acceptAllCombinations("arrow_right-up", self.setKey, ["cam-right",0])
        self.acceptAllCombinations("arrow_up-up", self.setKey, ["cam-forward",0])
        self.acceptAllCombinations("arrow_down-up", self.setKey, ["cam-backward",0])
        self.acceptAllCombinations("q", self.setKey, ["cam-rot-left",1])
        self.acceptAllCombinations("e", self.setKey, ["cam-rot-right",1])
        self.acceptAllCombinations("q-up", self.setKey, ["cam-rot-left",0])
        self.acceptAllCombinations("e-up", self.setKey, ["cam-rot-right",0])
        self.accept("end", lambda: self.resetCameraOrientation())
        self.accept("home", lambda: self.resetCameraPosition())
        
        self._MoveCameraTask = base().taskMgr.add(lambda task: self.moveCamera(task), "moveCameraTask")
        self.acceptAllCombinations("wheel_up",   lambda: self.zoomCamera(-1))
        self.acceptAllCombinations("wheel_down", lambda: self.zoomCamera(+1))
        # When the MMB (middle mouse button) is pressed the camera control is started depending on which modifier key was pressed
        self.accept("mouse2",        lambda: self.setCamMouseControl(True,False,False)) # only MMB    -- drag   movement
        self.accept("shift-mouse2",  lambda: self.setCamMouseControl(True,False,True )) # shift + MMB -- smooth movement
        self.accept("control-mouse2",lambda: self.setCamMouseControl(True,True, False)) # ctrl + MMB  -- drag   rotation
        self.accept("alt-mouse2",    lambda: self.setCamMouseControl(True,True, True )) # alt + MMB   -- smooth rotation
        # When the MMB is released the camera control is ended
        self.accept("mouse2-up", lambda: self.setCamMouseControl(False,False,False)) # MMB
    
    def unbindEvents(self):
        if self._MouseTask:
            base().taskMgr.remove(self._MouseTask)
            self._MouseTask = None
        if self._MoveCameraTask:
            base().taskMgr.remove(self._MoveCameraTask)
            self._MoveCameraTask = None
        self.ignoreAll()
    
    def destroy(self):
        self.unbindEvents()
        self.Active = False
        if self.SpaceSkyBox:
            self.SpaceSkyBox.removeNode()
        if self.SpaceSkyBoxCentre:
            self.SpaceSkyBoxCentre.removeNode()
        self.CameraRotCenter.removeNode()
        self.CameraCenter.removeNode()
        #TODO: unbind all of the event bindings
    
    def pause(self):
        self.unbindEvents()
        self.Active = False
        if self.SpaceSkyBoxCentre:
            self.SpaceSkyBoxCentre.hide()
    
    def continue_(self):
        if self.SpaceSkyBoxCentre:
            self.SpaceSkyBoxCentre.show()
        self.bindEvents()
        
        self.CameraCenter = p3dc.NodePath(p3dc.PandaNode("CameraCenter"))
        self.CameraCenter.reparentTo(ape.render())
        self.CameraCenter.setPos(p3dc.Vec3(0,0,0))
        self.CameraRotCenter = p3dc.NodePath(p3dc.PandaNode("CameraRotCenter"))
        self.CameraRotCenter.reparentTo(self.CameraCenter)
        self.CameraRotCenter.setPos(p3dc.Vec3(0,0,0))
        self.CameraRotCenter.setP(-45)
        ape.base().camera.reparentTo(self.CameraRotCenter)
        ape.base().camera.setPos(0,-15,0)
        ape.base().camera.lookAt(self.CameraCenter)
        self.Active = True
        self.bindEvents()
    
    def resetCameraPosition(self):
        self.resetCameraOrientation()
        self.CameraCenter.setPos(p3dc.Vec3(0,0,0))
    
    def resetCameraOrientation(self):
        self.CameraRotCenter.setPos(p3dc.Vec3(0,0,0))
        self.CameraRotCenter.setP(-45)
        self.CameraCenter.setH(0)
        ape.base().camera.setPos(0,-15,0)
        ape.base().camera.lookAt(self.CameraCenter)
    
    def focusRandomFleet(self, team:'int'=1):
        try:
            if get.unitManager().Teams[team]:
                self.moveToHex(random.choice(get.unitManager().Teams[team]).hex())
            else:
                NC(2,f"There are no fleets in {get.unitManager().Teams[team].name()} for the camera to focus on.")
        except:
            NC(1,"Could not focus camera on random fleet.", exc=True, input=f"{team = }")
    
    def moveToHex(self, hex_:'HexBase._Hex'):
        self.CameraCenter.setPos(hex_.Pos)
    
    def loadSkybox(self, skyboxPath='Models/Skyboxes/Sector/GreenSpace1/GreenSpace1.egg'):
        if self.SpaceSkyBox:
            self.SpaceSkyBox.removeNode()
        if self.SpaceSkyBoxCentre:
            self.SpaceSkyBoxCentre.removeNode()
        size = 500
        self.SpaceSkyBoxCentre = p3dc.NodePath(p3dc.PandaNode("SpaceSkyBoxCentre"))
        self.SpaceSkyBoxCentre.reparentTo(ape.render())
        self.SpaceSkyBox = ape.loadModel(skyboxPath)
        self.SpaceSkyBox.setScale(size)
        self.SpaceSkyBox.setBin('background', 0)
        self.SpaceSkyBox.setDepthWrite(0)
        self.SpaceSkyBox.setTwoSided(True)
        self.SpaceSkyBox.setTexGen(p3dc.TextureStage.getDefault(),p3dc.TexGenAttrib.MWorldCubeMap)
        self.SpaceSkyBox.reparentTo(self.SpaceSkyBoxCentre)
        directions = [0,90,180,270]
        self.SpaceSkyBox.setHpr(random.choice(directions),random.choice(directions),random.choice(directions))
        #self.SpaceSkyBox.setPos((-size/2,-size/2,-size/2)) #VALIDATE: I think it already is centred correctly...
    
    def acceptAllCombinations(self, key, *args):
        if not self.Active:
            return
        self.accept(key, *args)
        self.accept("control-"+key, *args)
        self.accept("alt-"+key, *args)
        self.accept("shift-"+key, *args)
    
    def setLimits(self, limitX: typing.Tuple[float,float], limitY: typing.Tuple[float,float]):
        if not self.Active:
            return
        self.LimitX = (min(limitX),max(limitX))
        self.LimitY = (min(limitY),max(limitY))
    
    def _enforceLimits(self):
        if not self.Active:
            return
        if   self.CameraCenter.getX() < self.LimitX[0]:
            self .CameraCenter.setX(    self.LimitX[0])
        elif self.CameraCenter.getX() > self.LimitX[1]:
            self .CameraCenter.setX(    self.LimitX[1])
        if   self.CameraCenter.getY() < self.LimitY[0]:
            self .CameraCenter.setY(    self.LimitY[0])
        elif self.CameraCenter.getY() > self.LimitY[1]:
            self .CameraCenter.setY(    self.LimitY[1])
        self.SpaceSkyBoxCentre.setPos(self.CameraCenter.getPos())
    
    def setKey(self, key, value):
        """Records the state of camera movement keys"""
        if not self.Active:
            return
        self.KeyMap[key] = value
    
    def moveCamera(self, task):
        if not self.Active:
            return
        if (self.KeyMap["cam-rot-left"]!=0):
            self.CameraCenter.setH(self.CameraCenter, +100 * p3dc.ClockObject.getGlobalClock().getDt())
        if (self.KeyMap["cam-rot-right"]!=0):
            self.CameraCenter.setH(self.CameraCenter, -100 * p3dc.ClockObject.getGlobalClock().getDt())
        if (self.KeyMap["cam-forward"]!=0):
            self.CameraCenter.setY(self.CameraCenter, + 20 * p3dc.ClockObject.getGlobalClock().getDt())
        if (self.KeyMap["cam-backward"]!=0):
            self.CameraCenter.setY(self.CameraCenter, - 20 * p3dc.ClockObject.getGlobalClock().getDt())
        if (self.KeyMap["cam-right"]!=0):
            self.CameraCenter.setX(self.CameraCenter, + 20 * p3dc.ClockObject.getGlobalClock().getDt())
        if (self.KeyMap["cam-left"]!=0):
            self.CameraCenter.setX(self.CameraCenter, - 20 * p3dc.ClockObject.getGlobalClock().getDt())
        self._enforceLimits()
        return task.cont
    
    def zoomCamera(self, sign): #TODO: Support zoom-to-cursor and use it as a standard as it feels way more intuitive. Make a flag (as a member) that governs this behaviour
        if not self.Active:
            return
        if -ape.base().camera.getY() <= 1:
            y = -ape.base().camera.getY() + sign*0.1
            if y > 1: y = 2
            elif y < 0.1: y = 0.1
        elif -ape.base().camera.getY() <= 5:
            y = -ape.base().camera.getY() + sign
            if y > 5: y = 10
            elif y < 1: y = 1
        elif -ape.base().camera.getY() <= 50:
            y = -ape.base().camera.getY() + sign*5
            if y > 50: y = 60
            elif y < 5: y = 5
        else:
            y = -ape.base().camera.getY() + sign*10
            if y > 130: y = 130
            elif y < 55: y = 50
        ape.base().camera.setY(-y)
        ape.base().camera.lookAt(self.CameraCenter)
    
    def setCamMouseControl(self, active, rotate, smooth):
        if not self.Active:
            return
        self.SmoothCam = smooth
        if active and base().mouseWatcherNode.hasMouse():
            mpos = tuple(base().mouseWatcherNode.getMouse())
            if rotate or self.SmoothCam:
                self.CamMouseControl = True
                self.CamMouseControlRotate = rotate
                self.CamMouseControlCentre = mpos
            else:
                self.CamMouseControlRotate = False
                pos3d = p3dc.Point3()
                nearPoint = p3dc.Point3()
                farPoint = p3dc.Point3()
                base().camLens.extrude(mpos, nearPoint, farPoint)
                if self.Plane.intersectsLine(
                        pos3d,
                        render().getRelativePoint(ape.base().camera, nearPoint),
                        render().getRelativePoint(ape.base().camera, farPoint)
                        ):
                    self.CamMouseControl = True
                    self.CamMouseControlCentre = pos3d
                else:
                    self.CamMouseControl = False
        else:
            self.CamMouseControl = False
            self.CamMouseControlRotate = False
    
    def _mouseTask(self, task):
        if not self.Active:
            return
        if base().mouseWatcherNode.hasMouse() and self.CamMouseControl:
            mpos = base().mouseWatcherNode.getMouse()
            if self.CamMouseControlRotate:
                if self.SmoothCam:
                    d = (mpos - self.CamMouseControlCentre)
                    self.CameraCenter.setH(self.CameraCenter, 10*d[0])
                    p = self.CameraRotCenter.getP() + 10*d[1]
                    if p < -90: p = -90
                    elif p > 90: p = 90
                    self.CameraRotCenter.setP(p)
                else:
                    d = (mpos - self.CamMouseControlCentre)
                    self.CameraCenter.setH(self.CameraCenter, 100*d[0])
                    p = self.CameraRotCenter.getP() + 100*d[1]
                    if p < -90: p = -90
                    elif p > 90: p = 90
                    self.CameraRotCenter.setP(p)
                    self.CamMouseControlCentre = tuple(mpos)
            else:
                if self.SmoothCam:
                    d = (mpos - self.CamMouseControlCentre)
                    self.CameraCenter.setX(self.CameraCenter, 0.5*d[0])
                    self.CameraCenter.setY(self.CameraCenter, 0.5*d[1])
                else:
                    pos3d = p3dc.Point3()
                    nearPoint = p3dc.Point3()
                    farPoint = p3dc.Point3()
                    base().camLens.extrude(mpos, nearPoint, farPoint)
                    if self.Plane.intersectsLine(
                            pos3d,
                            render().getRelativePoint(ape.base().camera, nearPoint),
                            render().getRelativePoint(ape.base().camera, farPoint)
                            ):
                        self.CameraCenter.setPos(self.CameraCenter.getPos()+self.CamMouseControlCentre-pos3d)
                self._enforceLimits()
        
        return Task.cont
