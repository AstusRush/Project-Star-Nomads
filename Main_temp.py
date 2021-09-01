"""
    Copyright (C) 2021  Robin Albers
"""

SupportsRenderPipeline = False

# Python standard imports 1/2
import datetime
import platform

# Print into the console that the program is starting and set the application ID if we are on windows
WindowTitle = "Project-Star-Nomads"
if __name__ == "__main__":
    print()
    print(datetime.datetime.now().strftime('%H:%M:%S'))
    print(WindowTitle)
    print("Loading Modules")#, end = "")
    if platform.system() == 'Windows':
        try:
            import ctypes
            myAppId = u'{}{}'.format(WindowTitle , datetime.datetime.now().strftime('%H:%M:%S')) # arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myAppId)
        except:
            pass

# Python standard imports 2/2
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
    from ..AstusPandaEngine.AGeLib import *
    from ..AstusPandaEngine import AstusPandaEngine as ape
    from ..AstusPandaEngine.AstusPandaEngine import engine, base, render, loader
    from ..AstusPandaEngine.AstusPandaEngine import window as _window
else:
    # These imports make Python happy
    sys.path.append('../AstusPandaEngine')
    from AGeLib import *
    import AstusPandaEngine as ape
    from AstusPandaEngine import engine, base, render, loader
    from AstusPandaEngine import window as _window

# Game Imports
from BaseClasses import HexBase as Hex
from BaseClasses.Unit import Unit
from BaseClasses.getter import unitManager, window
from GUI.Windows import MainWindowClass

#def window():
#    # type: () -> MainWindowClass
#    #w:MainWindowClass = _window()
#    return _window()#w
#
#def unitManager():
#    # type: () -> UnitManager
#    return engine().UnitManager

class BattleScene(ape.APEScene):
    
    def start(self):
        self.Camera = StrategyCamera()
        ape.base().win.setClearColor(p3dc.Vec4(0,0,0,1))
        self.loadSkybox()
        
        # Per-pixel lighting and shadows are initially on
        self.perPixelEnabled = True
        self.shadowsEnabled = True
        
        #base().accept("l", self.togglePerPixelLighting)
        #base().accept("e", self.toggleShadows)
        
    def loadSkybox(self):
        self.Camera.loadSkybox()
        
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

class StrategyCamera():
    def __init__(self):
        ape.base().win.setClearColor(p3dc.Vec4(0,0,0,1))
        self.Plane = p3dc.Plane(p3dc.Vec3(0, 0, 1), p3dc.Point3(0, 0, 0))
        
        self.SpaceSkyBoxCentre = None
        self.SpaceSkyBox = None
        
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
        
        self.LimitX: typing.Tuple[float,float] = (float("-inf"), float("inf"))
        self.LimitY: typing.Tuple[float,float] = (float("-inf"), float("inf"))
        
        self.SmoothCam = False
        self.CamMouseControl = False
        self.CamMouseControlRotate = False
        self.CamMouseControlCentre = p3dc.Vec3(0,0,0)
        self.mouseTask = base().taskMgr.add(lambda task: self._mouseTask(task), 'mouseTask')
        
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
        
        base().taskMgr.add(lambda task: self.moveCamera(task), "moveCamereTask")
        self.acceptAllCombinations("wheel_up",   lambda: self.zoomCamera(-1))
        self.acceptAllCombinations("wheel_down", lambda: self.zoomCamera(+1))
        # When the MMB (middle mouse button) is pressed the camera control is started depending on which modifier key was pressed
        base().accept("mouse2",        lambda: self.setCamMouseControl(True,False,False)) # only MMB    -- drag   movement
        base().accept("shift-mouse2",  lambda: self.setCamMouseControl(True,False,True )) # shift + MMB -- smooth movement
        base().accept("control-mouse2",lambda: self.setCamMouseControl(True,True, False)) # ctrl + MMB  -- drag   rotation
        base().accept("alt-mouse2",    lambda: self.setCamMouseControl(True,True, True )) # alt + MMB   -- smooth rotation
        # When the MMB is released the camera control is ended
        base().accept("mouse2-up", lambda: self.setCamMouseControl(False,False,False)) # MMB
        
    
    def loadSkybox(self):
        if self.SpaceSkyBox:
            self.SpaceSkyBox.removeNode()
        if self.SpaceSkyBoxCentre:
            self.SpaceSkyBoxCentre.removeNode()
        size = 500
        self.SpaceSkyBoxCentre = p3dc.NodePath(p3dc.PandaNode("SpaceSkyBoxCentre"))
        self.SpaceSkyBoxCentre.reparentTo(ape.render())
        self.SpaceSkyBox = loader().loadModel('Models/Skyboxes/Green Space 1/GreenSpace1.egg')
        self.SpaceSkyBox.setScale(size)
        self.SpaceSkyBox.setBin('background', 0)
        self.SpaceSkyBox.setDepthWrite(0)
        self.SpaceSkyBox.setTwoSided(True)
        self.SpaceSkyBox.setTexGen(p3dc.TextureStage.getDefault(),p3dc.TexGenAttrib.MWorldCubeMap)
        self.SpaceSkyBox.reparentTo(self.SpaceSkyBoxCentre)
        #self.SpaceSkyBox.setPos((-size/2,-size/2,-size/2)) #VALIDATE: I think it already is centred correctly...
        
    def acceptAllCombinations(self, key, *args):
        base().accept(key, *args)
        base().accept("control-"+key, *args)
        base().accept("alt-"+key, *args)
        base().accept("shift-"+key, *args)
        
    def setLimits(self, limitX: typing.Tuple[float,float], limitY: typing.Tuple[float,float]):
        self.LimitX = (min(limitX),max(limitX))
        self.LimitY = (min(limitY),max(limitY))
        
    def _enforceLimits(self):
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
        self.KeyMap[key] = value
    
    def moveCamera(self, task):
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
        y = -ape.base().camera.getY() + sign*5
        if y > 100: y = 100
        elif y < 5: y = 5
        ape.base().camera.setY(-y)
        ape.base().camera.lookAt(self.CameraCenter)
    
    def setCamMouseControl(self, active, rotate, smooth):
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


#region Unit Manager
class UnitManager():
    def __init__(self) -> None:
        self.Units_Environmental = UnitList()
        self.Units_Neutral = UnitList()
        self.Units_Team1 = UnitList()
        self.Units_Team2 = UnitList()
        self.Units_Team3 = UnitList()
        self.Teams = {
            -1 : self.Units_Environmental,
            0  : self.Units_Neutral,
            1  : self.Units_Team1,
            2  : self.Units_Team2,
            3  : self.Units_Team3,
        }
        self.selectedUnit: weakref.ref[Unit] = None
        
    def selectUnit(self, unit):
        if isinstance(unit, weakref.ref):
            unit = unit()
        if not ( unit is self.selectedUnit ):
            if self.selectedUnit:
                self.selectedUnit().unselect()
                self.selectedUnit = None
            if unit:
                self.selectedUnit =  weakref.ref(unit)
                self.selectedUnit().select()
        
    def isSelectedUnit(self, unit):
        if isinstance(unit, weakref.ref):
            unit = unit()
        return unit is self.selectedUnit()
        
    def endTurn(self):
        "Ends the player turn, processes all other turns and returns control back to the player"
        self.Units_Team1.endTurn()
        
        self.Units_Team2.startTurn()
        self.Units_Team2.endTurn()
        self.Units_Team3.startTurn()
        self.Units_Team3.endTurn()
        self.Units_Environmental.startTurn()
        self.Units_Environmental.endTurn()
        self.Units_Neutral.startTurn()
        self.Units_Neutral.endTurn()
        
        self.Units_Team1.startTurn()
        if self.selectedUnit:
            self.selectedUnit().highlightRanges(False)
            self.selectedUnit().highlightRanges(True)
            self.selectedUnit().diplayStats(True)
    
class UnitList(typing.List[Unit]): 
    def append(self, unit):
        # type: (Unit) -> None
        if not unit in self:
            return super().append(unit)
    
    def startTurn(self):
        for i in self:
            i.startTurn()
    
    def endTurn(self):
        for i in self:
            i.endTurn()
            
    def __str__(self) -> str:
        return f"Unit list:\n\t"+"\n\t".join([str(i) for i in self])+"\n"
    
#endregion Unit Manager

#region  main


# Function to put instructions on the screen.
#def addInstructions(pos, msg):
#    return OnscreenText(text = msg, style = 1, fg = (1, 1, 1, 1), 
#                        pos = (-0.9, pos - 0.2), align = p3dc.TextNode.ALeft, scale = .035)

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
        
class EngineClass(ape.APE):
    def start(self):
        self.base.start()
        self.UnitManager = UnitManager()
        self.Scene = BattleScene()
        self.Scene.start()
        window().start()

class AppClass(ape.APEApp):
    pass


class PandaWidget(ape.PandaWidget):
    pass


#endregion real main
if __name__ == '__main__':
    ape.start(WindowTitle, EngineClass, BaseClass, AppClass, MainWindowClass, PandaWidget, True, SupportsRenderPipeline)
