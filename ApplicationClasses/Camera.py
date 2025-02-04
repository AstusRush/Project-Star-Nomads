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
from pandac.PandaModules import WindowProperties

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
    from BaseClasses import FleetBase

class StrategyCamera(DirectObject):
    def __init__(self):
        ape.base().win.setClearColor(p3dc.Vec4(0,0,0,1))
        self.LastValidMousePosition = p3dc.LPoint2f(0.0,0.0)
        self.LastMousePosition = p3dc.LPoint2f(0.0,0.0)
        self.CurrentMousePosition = p3dc.LPoint2f(0.0,0.0)
        self.Active = True
        self.Plane = p3dc.Plane(p3dc.Vec3(0, 0, 1), p3dc.Point3(0, 0, 0))
        
        self.SpaceSkyBoxCentre = None
        self.SpaceSkyBox = None
        
        self._MouseTask = None
        self._MoveCameraTask = None
        
        self.MouseIsHidden = False
        
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
        
        self.MouseCamControl_active = False
        self.MouseCamControl_rotate = False
        self.MouseCamControl_smooth = False
        self.MouseCamControl_isSetup = True
        
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
    
    def focusRandomFleet(self, team:'int'=1) -> 'typing.Union[None,FleetBase.FleetBase]':
        fleet = None
        try:
            if get.unitManager().Teams[team]:
                fleet = random.choice(get.unitManager().Teams[team])
                self.moveToHex(fleet.hex())
            else:
                NC(2,f"There are no fleets in {get.unitManager().Teams[team].name()} for the camera to focus on.")
        except:
            NC(1,"Could not focus camera on random fleet.", exc=True, input=f"{team = }")
        return fleet
    
    def moveToHex(self, hex_:'HexBase._Hex'):
        self.CameraCenter.setPos(hex_.Pos)
    
    def makeSkybox(self, seed=None, sector=True, sun=False) -> 'float':
        if self.SpaceSkyBox:
            self.SpaceSkyBox.hide()
            self.SpaceSkyBox.removeNode()
        if self.SpaceSkyBoxCentre:
            self.SpaceSkyBoxCentre.removeNode()
        size = 20000
        self.SpaceSkyBoxCentre = p3dc.NodePath(p3dc.PandaNode("SpaceSkyBoxCentre"))
        self.SpaceSkyBoxCentre.reparentTo(ape.render())
        try:
            from ProceduralGeneration import SkyboxGeneration
            if not seed: seed = random.randint(1,999999999)
            rand = random.Random(seed)
            bgBoost = 32 if get.menu().SkyboxOptionsWidget.NonBlackSpace() else 3
            params = {
                "seed": str(seed),
                "backgroundColor": [pow(rand.random(),2)*bgBoost,pow(rand.random(),2)*bgBoost,pow(rand.random(),2)*bgBoost],
                "pointStars": get.menu().SkyboxOptionsWidget.PointStars(),
                "pointStarDensity": get.menu().SkyboxOptionsWidget.PointStarDensity(),
                "pointStarSize": get.menu().SkyboxOptionsWidget.PointStarSize(),
                "stars": 200*int(get.menu().SkyboxOptionsWidget.BrightStars()),
                "sun": False, #TODO
                "sunFalloff": 100,
                "jpegQuality": 0.85,
                "nebulaColorBegin": [rand.random()*255,rand.random()*255,rand.random()*255],
                "nebulaColorEnd": [rand.random()*255,rand.random()*255,rand.random()*255],
                "nebulae": get.menu().SkyboxOptionsWidget.Nebulae(),
                "resolution": 512*pow(2, get.menu().SkyboxOptionsWidget.SkyboxResolution()), #1024*4,
                "renderToTexture": True,
            }
            if get.menu().SkyboxOptionsWidget.SkyboxStatic():
                old_pos_cam = ape.base().camera.getPos()
                old_pos_cen = self.CameraCenter.getPos()
                self.CameraCenter.setPos(0,0,0)
                ape.base().camera.setPos(0,0,0)
                ape.base().camera.lookAt(0,1,0)
                self.SpaceSkyBox = SkyboxGeneration.SkyboxGenerator().getSkybox(params)
                self._skyboxHelper(size)
                self.CameraCenter.setPos(old_pos_cen)
                ape.base().camera.setPos(old_pos_cam)
                ape.base().camera.lookAt(self.CameraCenter)
            else:
                self.SpaceSkyBox = SkyboxGeneration.SkyboxGenerator().makeWithShader(params, size)
                self.SpaceSkyBox.reparentTo(self.SpaceSkyBoxCentre)
            #raise Exception()
        except:
            NC(exc=True)
            #self.SpaceSkyBox = ape.loadModel('Models/Skyboxes/LastGenerated/RandomSpace.egg')
            self.SpaceSkyBox = ape.loadModel('Models/Skyboxes/Sector/GreenSpace1/GreenSpace1.egg')
            self._skyboxHelper(size)
        #directions = [0,90,180,270]
        #self.SpaceSkyBox.setHpr(random.choice(directions),random.choice(directions),random.choice(directions))
        #SkyboxGeneration.SkyboxGenerator().getSkybox(params)
        return seed
    
    def makeSkybox_alt(self, sector, sun):
        try:
            from ProceduralGeneration import SkyboxGeneration
            
            params = {
                "seed": "The very best seed!",
                "backgroundColor": [pow(random.random(),2)*32,pow(random.random(),2)*32,pow(random.random(),2)*32],
                "pointStars": True,
                "stars": 200,
                "sun": False,
                "sunFalloff": 100,
                "jpegQuality": 0.85,
                "nebulaColorBegin": [random.random()*255,random.random()*255,random.random()*255],
                "nebulaColorEnd": [random.random()*255,random.random()*255,random.random()*255],
                "nebulae": True,
                "resolution": 512*pow(2, get.menu().SkyboxOptionsWidget.SkyboxResolution()), #1024*4,
                "renderToTexture": True,
            }
            ape.base().camera.setPos(0,0,0)
            ape.base().camera.lookAt(0,1,0)
            if self.SpaceSkyBoxCentre:
                self.SpaceSkyBoxCentre.hide()
            SkyboxGeneration.SkyboxGenerator().makeSkybox(params)
            if self.SpaceSkyBoxCentre:
                self.SpaceSkyBoxCentre.show()
            path = "Models/Skyboxes/LastGenerated/RandomSpace.egg"
        except:
            NC(exc=True)
            path = 'Models/Skyboxes/Sector/GreenSpace1/GreenSpace1.egg'
        self.loadSkybox(path)
    
    def loadSkybox(self, skyboxPath='Models/Skyboxes/Sector/GreenSpace1/GreenSpace1.egg'):
        if self.SpaceSkyBox:
            self.SpaceSkyBox.removeNode()
        if self.SpaceSkyBoxCentre:
            self.SpaceSkyBoxCentre.removeNode()
        size = 500
        self.SpaceSkyBoxCentre = p3dc.NodePath(p3dc.PandaNode("SpaceSkyBoxCentre"))
        self.SpaceSkyBoxCentre.reparentTo(ape.render())
        lo = p3dc.LoaderOptions()
        lo.setFlags(lo.LF_no_cache)
        #self.SpaceSkyBox = ape.loadModel(skyboxPath, noCache=True, loaderOptions=lo)
        self.SpaceSkyBox = loader().loadModel(skyboxPath, noCache=True, loaderOptions=lo)
        self._skyboxHelper(size)
        directions = [0,90,180,270]
        self.SpaceSkyBox.setHpr(random.choice(directions),random.choice(directions),random.choice(directions))
        #self.SpaceSkyBox.setPos((-size/2,-size/2,-size/2)) #VALIDATE: I think it already is centred correctly...
    
    def _skyboxHelper(self, size):
        self.SpaceSkyBox.setTwoSided(True)
        self.SpaceSkyBox.setTexGen(p3dc.TextureStage.getDefault(),p3dc.TexGenAttrib.MWorldCubeMap)
        self.SpaceSkyBox.setScale(size)
        self.SpaceSkyBox.setBin('background', 0)
        self.SpaceSkyBox.setDepthWrite(0)
        self.SpaceSkyBox.reparentTo(self.SpaceSkyBoxCentre)
        self.SpaceSkyBox.setLightOff()
        self.SpaceSkyBox.setMaterialOff()
    
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
    
    def zoomCamera(self, sign):
        if not self.Active:
            return
        
        move = False
        
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
        
        if base().mouseWatcherNode.hasMouse() and get.menu().ControlsOptionsWidget.ZoomToCursor():
            mpos = self.getMousePosition()
            pos3d_org = p3dc.Point3()
            nearPoint = p3dc.Point3()
            farPoint = p3dc.Point3()
            base().camLens.extrude(mpos, nearPoint, farPoint)
            move = self.Plane.intersectsLine(
                    pos3d_org,
                    render().getRelativePoint(ape.base().camera, nearPoint),
                    render().getRelativePoint(ape.base().camera, farPoint)
                    )
        
        ape.base().camera.setY(-y)
        ape.base().camera.lookAt(self.CameraCenter)
        
        if move:
            mpos = self.getMousePosition()
            pos3d = p3dc.Point3()
            nearPoint = p3dc.Point3()
            farPoint = p3dc.Point3()
            base().camLens.extrude(mpos, nearPoint, farPoint)
            if self.Plane.intersectsLine(
                    pos3d,
                    render().getRelativePoint(ape.base().camera, nearPoint),
                    render().getRelativePoint(ape.base().camera, farPoint)
                    ):
                self.CameraCenter.setPos(self.CameraCenter.getPos()+(pos3d_org-pos3d))
    
    def zoomCameraFullyOut(self):
        if not self.Active:
            return
        ape.base().camera.setY(-130)
        ape.base().camera.lookAt(self.CameraCenter)
    
    def setCamMouseControl(self, active, rotate, smooth):
        if not self.Active:
            return
        
        self.MouseCamControl_active = active
        self.MouseCamControl_rotate = rotate
        self.MouseCamControl_smooth = smooth
        self.MouseCamControl_isSetup = False
    
    def getMousePosition(self):
        mpos = p3dc.LPoint2f(base().mouseWatcherNode.getMouse())
        if abs(mpos.getX()) > 1.0 or abs(mpos.getY()) > 1.0:
            if (self.CurrentMousePosition-mpos).length() > 2:
                # The cursor position can be widely wrong when pressing MMB while moving the mouse fast
                # This resets the cursor position
                base().win.movePointer(0, int(base().win.getXSize() / 2), int(base().win.getYSize() / 2))
                mpos = p3dc.LPoint2f(0.0,0.0)
        else:
            self.LastValidMousePosition = mpos
        self.LastMousePosition = self.CurrentMousePosition
        self.CurrentMousePosition = mpos
        return mpos
    
    def isValidMousePosition(self, mpos:'p3dc.LPoint2f'):
        return not (abs(mpos.getX()) > 1.0 or abs(mpos.getY()) > 1.0)
    
    def _setCamMouseControl(self, active, rotate, smooth, mpos=None):
        if not self.Active:
            return
        self.SmoothCam = smooth
        if active and base().mouseWatcherNode.hasMouse():
            if not mpos: mpos = self.getMousePosition()
            if rotate or self.SmoothCam:
                self.CamMouseControlRotate = rotate
                self.CamMouseControlCentre = mpos
                self.CamMouseControl = True
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
                    self.CamMouseControlCentre = pos3d
                    self.CamMouseControl = True
                else:
                    self.CamMouseControl = False
        else:
            self.CamMouseControl = False
            self.CamMouseControlRotate = False
    
    def _mouseTask(self, task):
        if not self.Active or not base().mouseWatcherNode.hasMouse():
            if self.MouseIsHidden:
                props = WindowProperties()
                props.setCursorHidden(False)
                props.setMouseMode(WindowProperties.M_absolute)
                base().win.requestProperties(props)
                self.MouseIsHidden = False
            return Task.cont
        
        #p3dc.MouseWatcher.getMouse
        mpos = self.getMousePosition()
        #mpos = p3dc.GraphicsWindow.get_pointer(0)
        #mpos:'p3dc.PointerData' = base().win.get_pointer(0)
        #mpos = p3dc.LVecBase2f(mpos.get_x(),mpos.get_y())
        #mpos = p3dc.Vec3(mpos.get_x(),mpos.get_y(),0)
        
        if not self.MouseCamControl_isSetup:
            if not self.MouseIsHidden and self.MouseCamControl_active and get.menu().ControlsOptionsWidget.BindMouseWhileCamControl():
                self.MouseIsHidden = True
                props = WindowProperties()
                props.setCursorHidden(True)
                props.setMouseMode(WindowProperties.M_relative)
                base().win.requestProperties(props)
                return Task.cont
            
            mpos = self.getMousePosition()
            
            self._setCamMouseControl(self.MouseCamControl_active, self.MouseCamControl_rotate, self.MouseCamControl_smooth, mpos)
            self.MouseCamControl_active = False
            self.MouseCamControl_rotate = False
            self.MouseCamControl_smooth = False
            self.MouseCamControl_isSetup = True
            return Task.cont
        
        if self.CamMouseControl:
            if not self.MouseIsHidden and get.menu().ControlsOptionsWidget.BindMouseWhileCamControl():
                self.MouseIsHidden = True
                props = WindowProperties()
                props.setCursorHidden(True)
                props.setMouseMode(WindowProperties.M_relative)
                base().win.requestProperties(props)
            
            if self.CamMouseControlRotate:
                if self.SmoothCam:
                    d = (mpos - self.CamMouseControlCentre)
                    self.CameraCenter.setH(self.CameraCenter, 0.4*d[0])
                    p = self.CameraRotCenter.getP() + 0.4*d[1]
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
        elif self.MouseIsHidden:
            props = WindowProperties()
            props.setCursorHidden(False)
            props.setMouseMode(WindowProperties.M_absolute)
            base().win.requestProperties(props)
            self.MouseIsHidden = False
        
        return Task.cont
