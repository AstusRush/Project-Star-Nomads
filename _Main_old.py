"""
    Copyright (C) 2021  Robin Albers
"""

SupportsRenderPipeline = False
TRANSPARENT_HEX_RINGS = True

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

def window():
    # type: () -> MainWindowClass
    #w:MainWindowClass = _window()
    return _window()#w

def unitManager():
    # type: () -> UnitManager
    return engine().UnitManager

#region Exceptions
class HexException(Exception): pass

class HexOccupiedException(HexException):
    """
    This exception is raised when a hex is already occupied.
    """
    def __init__(self, hex=None):
        # type: (_Hex) -> None
        if hex:
            super().__init__(f"{hex.Name} is already occupied by {hex.Unit.Name}.")
        else:
            super().__init__(f"The hex is already occupied.")

class HexInvalidException(HexException):
    """
    This exception is raised when a hex does not exist.
    """
    def __init__(self, coords:typing.Tuple[int,int] = None):
        if coords:
            super().__init__(f"There is no hex at {coords}.")
        else:
            super().__init__(f"The specified hex does not exist.")
#endregion Exceptions

#region Helper Functions

def PointAtZ(z, point, vec):
    """
    This function, given a line (vector plus origin point) and a desired z value,
    will give us the point on the line where the desired z value is what we want.
    This is how we know where to position an object in 3D space based on a 2D mouse
    position. It also assumes that we are SelectedHex in the XY plane.
    
    This is derived from the mathematical of a plane, solved for a given point.
    """
    return point + vec * ((z - point.getZ()) / vec.getZ())

def getHexPos(i:typing.Tuple[int,int]):
    """A handy little function for getting the proper position for a given square1"""
    return window().getHex(i).Pos

def getHex(i:typing.Tuple[int,int]):
    """
    This function is only intended for use in the interactive AGeIDE. \n
    To properly get a hex you should always use the method of the HexGrid instance. \n
    Furthermore the HexGrid instance should be accessed unambiguously (optimally by getting it from another _Hex instace) since we might have two hex grids in the future (one for the main game and one for battles)!
    """
    return window().getHex(i)

#endregion Helper Functions

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

#region Hex Map
class HexGrid():
    #TODO: Write a method that checks if given coordinates exist i.e. if they lie within the grid and use it in getHex
    def __init__(self, scene:ape.APEScene=None, root:p3dc.NodePath = None, size: typing.Tuple[int,int] = (50,50)) -> None:
        self.Scene = scene if scene else engine().Scene
        if root:
            self.Root = root
        else:
            self.Root = render().attachNewNode("hexRoot")
            self.Root.setPos((0,0,0))
        self.Hexes = [] # type: typing.List[typing.List[_Hex]]
        self.Size = size
        self.m_material = None
        self.m_colour = None
        self.generateHex()
        
        # This will represent the index of the currently highlighted hex
        self.HighlightedHex = False # type: _Hex
        # This wil represent the index of the hex where currently dragged piece was grabbed from
        self.SelectedHex = False # type: _Hex
        
        # Start the task that handles the picking
        self.mouseTask = base().taskMgr.add(self._mouseTask, 'mouseTask')
        
        base().accept("mouse1", lambda: self._selectHighlightedHex()) # LMB
        base().accept("mouse3", lambda: self._interactWithHighlightedHex()) # RMB
        
    def clearHexes(self):
        self.HighlightedHex = False # type: _Hex
        self.SelectedHex = False # type: _Hex
        for i in self.Hexes:
            for j in i:
                del j
            del i
        del self.Hexes
        self.Hexes = []
        
    def generateHex(self):
        self.clearHexes()
        #TODO: When the number oh Hexes is even the offset must be subtracted from the first limit but if it is odd half the offset bust be +/- to both!
        limx1 = -self.Size[0]/2*3/2
        limx2 = self.Size[0]/2*3/2 - 3/2
        limy1 = -self.Size[1]/2*np.sqrt(3)
        limy2 = self.Size[1]/2*np.sqrt(3)-np.sqrt(3)
        
        for i,x in enumerate(np.linspace(limx1, limx2, self.Size[0])):
            l = []
            for j,y in enumerate(np.linspace(limy1, limy2, self.Size[1])):
                if i%2:
                    y += np.sqrt(3)/2
                l.append(_Hex(self, self.Scene, self.Root, f"Hex ({i},{j})", (i,j), (y,x,0)))
            self.Hexes.append(l)
            
    def getHex(self, i):
        # type: ( typing.Union[typing.Tuple[int,int], typing.Tuple[int,int,int]] ) -> _Hex
        if len(i) == 3:
            i = self.cubeToCoord(i)
        if len(i) == 2:
            i = ( round(i[0]) , round(i[1]) )
        else:
            raise HexInvalidException(i)
        if self._isValidCoordinate(i):
            return self.Hexes[round(i[0])][round(i[1])]
        else:
            raise HexInvalidException(i)
            
    def _isValidCoordinate(self, i):
        # type: ( typing.Union[typing.Tuple[int,int], typing.Tuple[int,int,int]] ) -> bool
        if len(i) == 3:
            i = self.cubeToCoord(i)
        if len(i) != 2:
            return False
        if i[0] < 0 or i[0] >= len(self.Hexes):
            return False
        if i[1] < 0 or i[1] >= len(self.Hexes[i[0]]):
            return False
        return True
    
    def cubeToCoord(self, cube:typing.Tuple[int,int,int]) -> typing.Tuple[int,int]:
        # Note: Casting to int (by using round) is necessary here since inputs are often floats (for which for example the "&" operation is invalid)
        col = round(cube[0])
        row = round(cube[2]) + (round(cube[0]) - (round(cube[0])&1)) / 2
        return (round(col), round(row))
    
    def coordToCube(self, coord:typing.Tuple[int,int]) -> typing.Tuple[int,int,int]:
        # Note: Casting to int (by using round) is necessary here since inputs are often floats (for which for example the "&" operation is invalid)
        x = round(coord[0])
        z = round(coord[1]) - (round(coord[0]) - (round(coord[0])&1)) / 2
        y = -x-z
        return (round(x), round(y), round(z))
        
    def highlightHexes(self, hexes = [], edge = False, face = False, clearFirst = True):
        # type: (typing.List[_Hex], typing.Union[QtGui.QColor,QtGui.QBrush,typing.Tuple[int,int,int,int],str,False], typing.Union[QtGui.QColor,QtGui.QBrush,typing.Tuple[int,int,int,int],str,False], bool) -> None
        if clearFirst:
            for i in self.Hexes:
                for ii in i:
                    if ii.Highlighted:
                        ii.highlight(edge = False, face = False)
        if (edge or face) or not clearFirst:
            for i in hexes:
                i.highlight(edge = edge, face = face)
    
  #region Interaction
    def _mouseTask(self, task):
        # This task deals with the highlighting and selection based on the mouse
        
        # First, clear the current highlighted hex
        if self.HighlightedHex is not False:
            self.HighlightedHex.hoverHighlight(False)
            self.HighlightedHex = False
        
        # Check to see if we can access the mouse since we obviously need it to do anything else
        if base().mouseWatcherNode.hasMouse():
            # Get the mouse position
            mpos = base().mouseWatcherNode.getMouse()
            
            # Set the position of the ray based on the mouse position
            base().pickerRay.setFromLens(base().camNode, mpos.getX(), mpos.getY())
            
            # Do the actual collision pass (Do it only on the hexes for efficiency purposes)
            base().picker.traverse(self.Root)
            if base().pq.getNumEntries() > 0:
                # If we have hit something, sort the hits so that the closest is first, and hoverHighlight that node
                base().pq.sortEntries()
                i:str = base().pq.getEntry(0).getIntoNode().getTag('hex')
                i = self.getHex((int(i.split(" ")[0]), int(i.split(" ")[1]))) # type: _Hex
                # Highlight the picked hex and store it as a member
                i.hoverHighlight()
                self.HighlightedHex = i
                window().Statusbar.showMessage(i.Name)
        
        return Task.cont
    
    def _selectHighlightedHex(self):
        if self.SelectedHex is not False:
            if self.SelectedHex is self.HighlightedHex:
                self.SelectedHex.select(False)
                self.SelectedHex.hoverHighlight()
                self.SelectedHex = False
                unitManager().selectUnit(None)
                return
            else:
                self.SelectedHex.select(False)
                self.SelectedHex = False
        if self.HighlightedHex is not False:
            self.SelectedHex = self.HighlightedHex
            self.SelectedHex.select()
            self.HighlightedHex = False
        else:
            unitManager().selectUnit(None)
    
    def _interactWithHighlightedHex(self):
        if self.SelectedHex is not False and self.HighlightedHex is not False:
            if self.SelectedHex.moveUnitToHex(self.HighlightedHex):
                self._selectHighlightedHex()
  #endregion Interaction

class _Hex():
    COLOUR_NORMAL = "Blue"
    COLOUR_SELECT = "Yellow"
    COLOUR_SELECT_FACE = "Light Blue"
    COLOUR_HIGHLIGHT = "Light Blue"
    COLOUR_REACHABLE = "Green"
    NW = np.array(( 1,  0, -1))
    W  = np.array(( 0,  1, -1))
    SW = np.array((-1,  1,  0))
    SE = np.array((-1,  0,  1))
    E  = np.array(( 0, -1,  1))
    NE = np.array(( 1, -1,  0))
    ALL_DIRECTIONS = np.array([NW, NE, E, SE, SW, W, ])
    
    def __init__(self, grid:HexGrid, scene:ape.APEScene, root, name:str, coordinates:typing.Tuple[int,int], pos:typing.Tuple[int,int,int]):
        try:
            # What we need:
            # -DONE- A hexagonal mesh for the click-detection and to highlight the hex
            # -DONE- A Hexagonal ring to highlight the edges of all hexes
            # -PART- These two meshes must be as simple as possible but must be able to be visible, blink, and be hidden independently of one another
            #
            self.Name = name
            self.Colour = self.COLOUR_NORMAL
            self.CurrentColour_Edge = self.COLOUR_NORMAL
            self.CurrentColour_Face = self.COLOUR_SELECT_FACE
            self.Coordinates = coordinates
            self.grid = weakref.ref(grid)
            
            # Save cube coordinates
            self.CubeCoordinates = grid.coordToCube(coordinates)
            
            self.Pos = p3dc.LPoint3(pos)
            mesh = "Models/Simple Geometry/hexagon.ply"
            meshRing = "Models/Simple Geometry/hexagonRing.ply"
            # Load, parent, colour, and position the model (a hexagon-shaped ring consisting of 6 polygons)
            self.Model = loader().loadModel(meshRing)
            self.Model.reparentTo(root)
            self.Model.setPos(self.Pos)
            if TRANSPARENT_HEX_RINGS:
                self.Model.setTransparency(p3dc.TransparencyAttrib.MAlpha)
            self._setColor(self.Colour)
            # Load, parent, hide, and position the face (a single hexagon polygon)
            self.Face = loader().loadModel(mesh)
            self.Face.reparentTo(self.Model)
            self.Face.setPos(p3dc.LPoint3((0,0,-0.01)))
            self._setColorFace(self.CurrentColour_Face)
            #TODO: Make transparent
            self.Face.hide()
            # Set the Model itself to be collideable with the ray. If this Model was
            # any more complex than a single polygon, you should set up a collision
            # sphere around it instead. But for single polygons this works fine.
            self.Face.find("").node().setIntoCollideMask(p3dc.BitMask32.bit(1))
            # Set a tag on the square's node so we can look up what square this is later during the collision pass
            # We will use this variable as a pointer to whatever piece is currently in this square
            self.Face.find("").node().setTag('hex', str(coordinates[0])+" "+str(coordinates[1]))
            
            # We will use this list to store all objects that occupy this hexagon
            self.content = [] # type: typing.List[Object]
            self.unit = None # type: 'weakref.ref[Unit]'
            self.Navigable = True
            
            self.Highlighted = False
        except:
            NC(1,f"Error while creating {name}",exc=True)  #CRITICAL: Clean up all nodes by removing them if they were created!!
    
    def __del__(self):
        del self.content
        self.Face.removeNode()
        self.Model.removeNode()
        
    def isSelected(self):
        return self is self.grid().HighlightedHex
    
  #region Unit Movement
    def swapContentsWith(self,other):
        # type: (_Hex) -> None
        oContent = other.content
        other.content = self.content
        self.content = oContent
        for i in self.content:
            i.moveToHex(self)
        for i in other.content:
            i.moveToHex(other)
            
    def moveUnitToHex(self,other):
        # type: (_Hex) -> bool
        if self.unit:
            return self.unit().moveTo(other)
        #if self.unit and not other.Unit:
        #    self.unit.moveToHex(other)
        #    other.unit = self.unit
        #    self.unit = None
        #    return True
        #else:
        #    return False
        
  #endregion Unit Movement
    
  #region Colour
    def _setColor(self, colour, alpha = 0.2):
        """
        Set the colour of the edge to `colour`. \n
        `colour` can be a QColor, a QBrush, a tuple, or a string from AGeLib's PenColours dictionary. \n
        If `colour` is a PenColours-string `alpha` can be given. (Otherwise `alpha` is ignored since the other input variants already support specifying the alpha value.)
        """
        return self._setColour(colour,alpha)
    def _setColour(self, colour, alpha = 0.2):
        """
        Set the colour of the edge to `colour`. \n
        `colour` can be a QColor, a QBrush, a tuple, or a string from AGeLib's PenColours dictionary. \n
        If `colour` is a PenColours-string `alpha` can be given. (Otherwise `alpha` is ignored since the other input variants already support specifying the alpha value.)
        """
        if isinstance(colour,str):
            colour = App().PenColours[colour].color()
            colour.setAlphaF(alpha)
        self.Model.setColor(ape.colour(colour))
    
    def _setColorFace(self, colour, alpha = 0.2):
        """
        Set the colour of the face to `colour`. \n
        `colour` can be a QColor, a QBrush, a tuple, or a string from AGeLib's PenColours dictionary. \n
        If `colour` is a PenColours-string `alpha` can be given. (Otherwise `alpha` is ignored since the other input variants already support specifying the alpha value.)
        """
        return self._setColourFace(colour,alpha)
    def _setColourFace(self, colour, alpha = 0.2):
        """
        Set the colour of the face to `colour`. \n
        `colour` can be a QColor, a QBrush, a tuple, or a string from AGeLib's PenColours dictionary. \n
        If `colour` is a PenColours-string `alpha` can be given. (Otherwise `alpha` is ignored since the other input variants already support specifying the alpha value.)
        """
        if isinstance(colour,str):
            colour = App().PenColours[colour].color()
            colour.setAlphaF(alpha)
        self.Face.setColor(ape.colour(colour))
  #endregion Colour
  #region Highlighting
        
    def hoverHighlight(self, highlight:bool = True):
        if highlight:
            if TRANSPARENT_HEX_RINGS:
                self.Model.setTransparency(p3dc.TransparencyAttrib.MNone)
            self._setColor(self.COLOUR_HIGHLIGHT)
        else:
            if TRANSPARENT_HEX_RINGS and not self.CurrentColour_Edge == self.COLOUR_SELECT:
                self.Model.setTransparency(p3dc.TransparencyAttrib.MAlpha)
            self._setColor(self.CurrentColour_Edge)
            
    def highlight(self, edge = False, face = False):
        if not face and not edge:
            if TRANSPARENT_HEX_RINGS and not self.CurrentColour_Edge == self.COLOUR_SELECT:
                self.Model.setTransparency(p3dc.TransparencyAttrib.MAlpha)
            if self.isSelected():
                self.CurrentColour_Edge = self.COLOUR_SELECT
                self.CurrentColour_Face = self.COLOUR_SELECT_FACE
                self._setColor(self.CurrentColour_Edge)
                self._setColorFace(self.CurrentColour_Face)
                if TRANSPARENT_HEX_RINGS:
                    self.Model.setTransparency(p3dc.TransparencyAttrib.MNone)
                self.Face.setTransparency(p3dc.TransparencyAttrib.MAlpha)
                self.Face.show()
            else:
                self.CurrentColour_Edge = self.COLOUR_NORMAL
                self.CurrentColour_Face = self.COLOUR_SELECT_FACE
                self._setColor(self.CurrentColour_Edge)
                self._setColorFace(self.CurrentColour_Face)
                if TRANSPARENT_HEX_RINGS:
                    self.Model.setTransparency(p3dc.TransparencyAttrib.MAlpha)
                self.Face.setTransparency(p3dc.TransparencyAttrib.MNone)
                self.Face.hide()
            self.Highlighted = False
        else:
            self.Highlighted = True
            if edge:
                self.CurrentColour_Edge = edge
                self._setColor(self.CurrentColour_Edge)
            if face:
                self.CurrentColour_Edge = edge
                self._setColor(self.CurrentColour_Edge)
                self.Face.show()
    
    def select(self, select:bool = True):
        if select:
            self.CurrentColour_Edge = self.COLOUR_SELECT
            if TRANSPARENT_HEX_RINGS:
                self.Model.setTransparency(p3dc.TransparencyAttrib.MNone)
            self._setColor(self.COLOUR_SELECT)
            self._setColorFace(self.COLOUR_SELECT_FACE)
            self.Face.setTransparency(p3dc.TransparencyAttrib.MAlpha)
            self.Face.show()
            unitManager().selectUnit(self.unit)
        else:
            self.CurrentColour_Edge = self.Colour
            if TRANSPARENT_HEX_RINGS:
                self.Model.setTransparency(p3dc.TransparencyAttrib.MAlpha)
            self._setColor(self.Colour)
            self.Face.setTransparency(p3dc.TransparencyAttrib.MNone)
            self.Face.hide()
    
  #endregion Highlighting
  #region Hex Math
    def getNeighbour(self,direction=-1):
        """
        Returns the specified neighbour in direction if 0<=direction<=5 or else all neighbours. \n
        Raises HexInvalidException if the specified neighbour does not exist (which can happen if this hex is at the edge of the map). \n
        Also accepts one of `_Hex.ALL_DIRECTIONS` (eg `NW, NE, E, SE, SW, W`) \n
        (Theoretically accepts all tuples of length 3 which allows to get relative positions but this behaviour is not explicitly intended nor supported and should not be used.)
        """
        try:
            if len(direction) == 3:
                return self.grid().getHex( [a+b for a,b in zip(self.CubeCoordinates, direction)])
        except:
            pass
        if 0 <= direction and direction <= 5:
            return self.grid().getHex( [a+b for a,b in zip(self.CubeCoordinates, self.ALL_DIRECTIONS[direction])])
        else:
            l = []
            for i in self.ALL_DIRECTIONS:
                try:
                    l.append(self.grid().getHex([a+b for a,b in zip(self.CubeCoordinates, i)]))
                except HexInvalidException:
                    pass
            return l
    
    def distance(self, other):
        """
        Returns the distance in number of hexagon steps.
        """
        x1, y1, z1 = self.CubeCoordinates
        x2, y2, z2 = other.CubeCoordinates if isinstance(other, _Hex) else other
        return max(abs(x1 - x2), abs(y1 - y2), abs(z1 - z2))
    
    def _getRing_cubeCoords(self, radius):
        center = self.CubeCoordinates
        if radius < 0:
            return []
        if radius == 0:
            return [center]
        
        radHex = np.zeros((6 * radius, 3))
        count = 0
        for i in range(0, 6):
            for k in range(0, radius):
                radHex[count] = self.ALL_DIRECTIONS[i - 1] * (radius - k) + self.ALL_DIRECTIONS[i] * (k)
                count += 1
        
        return (np.squeeze(radHex) + center).tolist()
        
    def getRing(self, radius):
        coords = self._getRing_cubeCoords(radius)
        ring: typing.List[_Hex] = []
        for i in coords:
            try:
                ring.append(self.grid().getHex(i))
            except HexInvalidException:
                pass
        return ring
        
    def getDisk(self, radius, radius2=0):
        """
        Takes one or two integers as the outer and optional inner radius for a ring (order does not matter). \n
        Returns a list of all hexes that form the specified ring around this hex.
        """
        radiusInner = min(radius, radius2)
        radiusOuter = max(radius, radius2)
        circle: typing.List[_Hex] = []
        for i in range(radiusInner,radiusOuter+1):
            circle.extend(self.getRing(i))
        return circle
        
    def __lt__(self, other):
        "Needed for comparissons in `findPath` (specifically the heap operations)"
        # type: (_Hex) -> bool
        return self.CubeCoordinates < other.CubeCoordinates
    
  #endregion Hex Math

def findPath(start:_Hex, destination:_Hex, navigable = lambda hex: hex.Navigable, cost = lambda hex: 1) -> typing.List[_Hex]:
    """
    The hex path finder. \n
    Returns a list containing the hexes that form a shortest path between start and destination (including destination but excluding start). \n
    start       : Starting hex for path finding. \n
    destination : Destination hex for path finding. \n
    navigable   : A function that, given a _Hex, tells us whether we can move through this hex. \n
    cost        : A cost function for moving through a hex. Should return a value >= 1. By default all costs are 1. \n
    """
    #TODO: This should be able to take movement points and endsure that the returned path does not exceed this (if given)
    Found = False
    Done = False
    Path: typing.List[_Hex] = None
    Closedset = set()
    Openset = [(destination.distance(start), 0, start, ())]
    
    def _compute_path(path):
        result = []
        while path:
            pos, path = path
            result.append(pos)
        return result[::-1]
    
    while not Done:
        for i in range(100):
            if not Openset:
                Done = True
                break
            h, cur_cost, pos, path = heappop(Openset)
            if pos in Closedset:
                continue
            new_path = (pos, path)
            if pos == destination:
                Path = _compute_path(new_path)
                Found = Done = True
                del Openset[:]
                break
            Closedset.add(pos)
            for new_pos in pos.getNeighbour():
                if (not navigable(new_pos)) or (new_pos in Closedset):
                    continue
                new_cost = cur_cost + cost(new_pos)
                new_h = new_cost + destination.distance(new_pos)
                heappush(Openset, (new_h, new_cost, new_pos, new_path))
    try:
        if len(Path) > 1:
            Path = Path[1:] # We do not return the starting position
            return Path, sum([cost(i) for i in Path])
        else:
            return [], 0
    except: #Catches the case that Path is None #TODO: handle this case more cleanly
        return [], 0

#endregion Hex Map

#region Objects
class Object():
    def __init__(self, coordinates, colour, model):
        self.Node = loader().loadModel(model)
        try:
            self.Node.reparentTo(render())
            self.Node.setColor(ape.colour(colour))
            self.Node.setPos(window().getHex(coordinates).Pos)
        except Exception as inst:
            self.Node.removeNode()
            raise inst
        window().getHex(coordinates).content.append(self)
        
    def moveToPos(self,pos):
        self.setPos(pos)
        
    def moveToHex(self,hex:_Hex):
        self.setPos(hex.Pos)
        
    def moveToCoordinates(self,coordinates):
        self.setPos(getHexPos(coordinates))
        
    def setPos(self, pos):
        self.Node.lookAt(pos)
        self.Node.posInterval(pos,min(6,abs(sum(self.Node.getPos()-pos))))
    
    def __del__(self):
        self.Node.removeNode()
        
class Unit():
    #TODO: There should be a method to replace the model
    #TODO: There should be a method that marks the current Unit as the active unit that brings up the UI for the Unit and highlights all reachable hexes (highlighting using method of HexClass)
    #       For this the unit mangaer should have a member that stores the active unit and when activating a new unit the old unit is first deactivated (if any was active)
    #           This way we avoid errors where multiple units become selected by mistake
    #       Selecting an empty hex should deactivate the currently active unit
    def __init__(self, coordinates, team=1, name="a Unit", model="Models/Simple Geometry/cube.ply", colour=(1,1,1,1)):
        self.Name = name
        self.Team = team
        self.BaseMovePoints = 6 #float("inf") #10
        self.MovePoints = self.BaseMovePoints
        self.hex: 'weakref.ref[_Hex]' = None
        self.Node = p3dc.NodePath(p3dc.PandaNode("Central node of unit: "+name))
        self.ActiveTurn = team == 1 #TODO: This should be taken from the Unit manager to check whose turn it actually is since enemy ships are mostly initialized during enemy turns (but not always which means we can not always set this to True!)
        # self.CameraCenter = p3dc.NodePath(p3dc.PandaNode("CameraCenter"))
        # self.CameraCenter.reparentTo(ape.render())
        # self.CameraCenter.setPos(p3dc.Vec3(0,0,0))
        # self.CameraRotCenter = p3dc.NodePath(p3dc.PandaNode("CameraRotCenter"))
        # self.CameraRotCenter.reparentTo(self.CameraCenter)
        try:
            self.Node.reparentTo(render())
            self.Model = loader().loadModel(model)
        except:# Exception as inst:  #VALIDATE: Does this work as intended?
            self.Node.removeNode()
            raise# inst
        try:
            self.Model.reparentTo(self.Node)
            self.Model.setColor(ape.colour(colour))
            self.moveToCoordinates(coordinates)
        except:# Exception as inst:  #VALIDATE: Does this work as intended?
            self.Model.removeNode()
            self.Node.removeNode()
            raise# inst
        unitManager().Teams[self.Team].append(self)
        
        self.init_combat()
        self.init_effects()
        
    #def moveToPos(self,pos):
    #    self.Node.setPos(pos)
    
    def __del__(self):
        if self.ExplosionEffect:
            self.ExplosionEffect.removeNode()
        if self.ExplosionEffect2:
            self.ExplosionEffect2.removeNode()
        if self.isSelected:
            unitManager().selectUnit(None)
        if self.hex:
            self.hex().unit = None
        self.Model.removeNode()
        self.Node.removeNode()
        
    def destroy(self, task=None):
        unitManager().Teams[self.Team].remove(self)
        self.__del__()
        #if task:
        #    return Task.cont
        
    def __str__(self) -> str:
        if self.hex:
            return f"{self.Name} (team {self.Team}) at {self.hex().Coordinates}"
        else:
            return f"{self.Name} (team {self.Team}) lost in the warp..."
        
    def __repr__(self) -> str:
        if self.hex:
            return f"Unit( coordinates = {self.hex().Coordinates} , team = {self.Team} , name = \"{self.Name}\" )"
        else:
            return f"Unit( coordinates = (None,None) , team = {self.Team} , name = \"{self.Name}\" )"
    
  #region Turn and Selection
    def startTurn(self):
        self.MovePoints = self.BaseMovePoints
        self.ActiveTurn = True
        
        self.healAtTurnStart()
        
    def endTurn(self):
        self.ActiveTurn = False
        
    def isSelected(self):
        return unitManager().isSelectedUnit(self)
    
    def select(self):
        self.highlightRanges(True)
    
    def unselect(self):
        self.highlightRanges(False)
    
  #endregion Turn and Selection
  #region Movement
    def moveToHex(self, hex:_Hex, animate= True):
        self.Coordinates = hex.Coordinates
        if hex.unit:
            raise HexOccupiedException(hex)
        else:
            if animate and self.hex:
                self.Node.lookAt(hex.Pos)
                #time = min(6, np.sqrt(sum([i**2 for i in list(self.Node.getPos()-hex.Pos)])) )/6
                time = min(6, self.hex().distance(hex) )/6
                self.Node.posInterval(time, hex.Pos).start()
            else:
                self.Node.setPos(hex.Pos)
            hex.unit = weakref.ref(self)
            self.hex = weakref.ref(hex)
        
    def _navigable(self, hex:_Hex):
        return (not bool(hex.unit)) and hex.Navigable
        
    def _tileCost(self, hex:_Hex):
        return 1
        
    def moveTo(self, hex:_Hex):
        if not self._navigable(hex):
            # The figure can not move to the hex but we can at least make it look at the hex
            lastAngle = self.Node.getHpr()[0]
            theta = np.arctan2(hex.Pos[0] - self.hex().Pos[0], self.hex().Pos[1] - hex.Pos[1])
            if (theta < 0.0):
                theta += 2*np.pi
            angle = np.rad2deg(theta) + 180
            #INVESTIGATE: Why do I need to add 180°? The formula above should be correct and the 180° should be wrong here but whitout adding them the object looks in the wrong direction...
            #       .lookAt makes the object look in the correct direction therefore the object itself is not modeled to look in the wrong direction.
            #       Furthermore I can pretty much rule out that the further processing of the angle is wrong since the 180° were necessary even before the processing was added.
            #       Thereby the formula must be mistaken, which, as mentioned, should be the correct formula... So where is the problem?!?
            angleBefore, angleAfter = self.improveRotation(lastAngle,angle)
            self.Node.hprInterval(abs(angleBefore - angleAfter)/(360), (angleAfter,0,0), (angleBefore,0,0)).start()
            return False
        else:
            path, cost = findPath(self.hex(), hex, self._navigable, self._tileCost)
            if not path or cost > self.MovePoints:
                # The figure can not move to the hex but we can at least make it look at the hex
                lastAngle = self.Node.getHpr()[0]
                theta = np.arctan2(hex.Pos[0] - self.hex().Pos[0], self.hex().Pos[1] - hex.Pos[1])
                if (theta < 0.0):
                    theta += 2*np.pi
                angle = np.rad2deg(theta) + 180
                #INVESTIGATE: Why do I need to add 180°? The formula above should be correct and the 180° should be wrong here but whitout adding them the object looks in the wrong direction...
                #       .lookAt makes the object look in the correct direction therefore the object itself is not modeled to look in the wrong direction.
                #       Furthermore I can pretty much rule out that the further processing of the angle is wrong since the 180° were necessary even before the processing was added.
                #       Thereby the formula must be mistaken, which, as mentioned, should be the correct formula... So where is the problem?!?
                angleBefore, angleAfter = self.improveRotation(lastAngle,angle)
                self.Node.hprInterval(abs(angleBefore - angleAfter)/(360), (angleAfter,0,0), (angleBefore,0,0)).start()
                return False
            else:
                self.highlightRanges(False)
                seq = p3ddSequence(name = self.Name+" move")
                lastPos = self.hex().Pos
                lastAngle = self.Node.getHpr()[0]
                for i in path:
                    theta = np.arctan2(i.Pos[0] - lastPos[0], lastPos[1] - i.Pos[1])
                    if (theta < 0.0):
                        theta += 2*np.pi
                    angle = np.rad2deg(theta) + 180
                    #INVESTIGATE: Why do I need to add 180°? The formula above should be correct and the 180° should be wrong here but whitout adding them the object looks in the wrong direction...
                    #       .lookAt makes the object look in the correct direction therefore the object itself is not modeled to look in the wrong direction.
                    #       Furthermore I can pretty much rule out that the further processing of the angle is wrong since the 180° were necessary even before the processing was added.
                    #       Thereby the formula must be mistaken, which, as mentioned, should be the correct formula... So where is the problem?!?
                    angleBefore, angleAfter = self.improveRotation(lastAngle,angle)
                    if abs(angleBefore - angleAfter) > 2:
                        #seq.append( self.Node.hprInterval(0, (angleBefore,0,0) )
                        seq.append( self.Node.hprInterval(abs(angleBefore - angleAfter)/(360), (angleAfter,0,0), (angleBefore,0,0)) )
                    seq.append( self.Node.posInterval(0.4, i.Pos) ) #, startPos=Point3(0, 10, 0)))
                    lastPos = i.Pos
                    lastAngle = angle
                seq.start()
                self.hex().unit = None
                hex.unit = weakref.ref(self)
                self.hex = weakref.ref(hex)
                self.Coordinates = hex.Coordinates
                self.MovePoints -= cost
                self.highlightRanges(True)
                return True
    
    def improveRotation(self,c,t):
        """
        c is current rotation, t is target rotation. \n
        returns two values that are equivalent to c and t but have values between -360 and 360 and have a difference of at most 180 degree.
        """
        ci = c%360
        if ci > 180: ci -= 360
        ti = t%360
        if not abs(ci-ti) <= 180:
            ti -= 360
            if not abs(ci-ti) <= 180:
                NC(2,"improveRotation needs improvements!!\nPlease send all contents of this notification to the developer Robin Albers!"
                        ,func="improveRotation",input="c = {}\nt = {}\nci = {}\nti = {}\nd = {}\nsolution = {}".format(c,t,ci,ti,abs(ci-ti),abs(ci-ti) <= 180))
        return ci,ti
    
    def moveToCoordinates(self,coordinates):
        self.moveToHex(window().getHex(coordinates))
    
    def getReachableHexes(self):
        #TODO
        # This method returns a list with all the hexes that can be reached (with the current movement points) by this unit
        # Variant 1:
        #    For this get all hex rings around the current hex with at most a distance equal to the current movement points
        #    Throw all of these hexes into a single list (beginning with the most distant once!!)
        #    Then go through the list calculate the path to each hex
        #      If a path is found add the hex and all hexes on the path to the output list
        #      We can skip all hexes that are already on the output list since which dramatically reduces the amount of hexes that we must go through!
        # Variant 2:
        #    Use a different pathfinding algorithm that walks all possible path up to a specific distance and highlight all of them. This should be even more effective
        # Variant 3:
        #    If method 1 and 2 are too slow
        #       Instead of highlighting all hexes that can be reached just highlight the path to the hex under the cursor whenever the cursor moves to a different cell.
        #    If this is still too slow highlight the path to the cell under the cursor only when the user requests this by pressing a key.
        # Variant 4:
        #    Make your own pathfinding algorithm that walks all possible path up to a specific distance and highlight all of them. (Does not take into account movement cost)
        # Variant 5: (This seems to be the same as variant 2...)
        #    Make your own pathfinding algorithm that walks all possible path up to a specific distance and highlight all of them.
        #    This one takes into account movement cost by using recursion and keeping track of available movement points from that tile on
        #    This also requires checking if a hex has been visited before and only continuing to calculate from that tile on if the new cost is lower
        #    ... wait... this is variant 2 all over again!!! I have just described the same algorithm that I want to use in variant 2!
        Variant = 4
        
        if Variant == 1: #Too slow...
            t1 = time.time()
            ####
            mPoints = self.MovePoints if self.ActiveTurn else self.BaseMovePoints # To allow calculations while it's not this unit's turn we use the BaseMovePoints then
            l: typing.Set[_Hex] = set() # Using a set instead of a list is 5% faster... which is still not fast enough
            for i in self.hex().getDisk(mPoints): #FEATURE:MOVECOST: This does not take into account that hexes could have a negative movement point cost...
                #                                       Therefore we could miss some more distant tiles. But this method is already far too slow so we can not really afford to increase the radius of the disk...
                if not i in l:
                    path, cost = findPath(self.hex(), i, self._navigable, self._tileCost)
                    if path:
                        if cost <= mPoints:
                            l.update(path)
                        else:
                            l.update(path[:mPoints])
            ####
            print("list",time.time()-t1)
            return l
        if Variant == 2:
            pass # https://www.reddit.com/r/gamemaker/comments/1eido8/mp_grid_for_tactics_grid_movement_highlights/
        if Variant == 3:
            pass
        if Variant == 4: #FEATURE:MOVECOST: This does not take into account different tile movement cost
            # This is VERY fast
            mPoints = self.MovePoints if self.ActiveTurn else self.BaseMovePoints # To allow calculations while it's not this unit's turn we use the BaseMovePoints then
            l: typing.Set[_Hex] = set() # Using a set instead of a list is 5% faster... which is still not fast enough
            tl: typing.List[typing.Set[_Hex]] = [set([self.hex()]),]
            for i in range(mPoints):
                temp = set()
                for ii in tl[i]:
                    for iii in ii.getNeighbour():
                        if self._navigable(iii):
                            temp.add(iii)
                tl.append(temp.difference(tl[i-1]).difference(tl[i]))
                l.update(temp)
            return l
    
    
  #endregion Movement
  #region Highlighting
    def highlightRanges(self, highlight=True):
        """
        Highlights all hexes that are relevant (movementrange, weaponrange, etc). \n
        If `highlight = False` the highlighted hexes are instead un-highlighted.
        """
        self.hex().grid().highlightHexes(clearFirst=True)
        if highlight:
            self.highlightMovementRange(highlight, clearFirst=False)
    
    def highlightMovementRange(self, highlight=True, clearFirst=True):
        """
        Highlights all hexes that can be reached with the current movement points. \n
        If `highlight = False` the highlighted hexes are instead un-highlighted.
        """
        self.hex().grid().highlightHexes(self.getReachableHexes(), _Hex.COLOUR_REACHABLE, False, clearFirst=clearFirst)
        ##TODO: TEMPORARY
        #for i in self.getReachableHexes():
        #    i.highlight(highlight)
        ##TODO: TEMPORARY
  #endregion Highlighting
  #region Combat Defensive
    def init_combat(self):
        self.init_HP()
        
    def init_HP(self):
        #FEATURE:HULLTYPES
        self.Evasion = 0.1
        self.HP_Hull_max = 100
        self.HP_Shields_max = 400
        self.HP_Hull = self.HP_Hull_max
        self.HP_Shields = self.HP_Shields_max
        self.HP_Hull_Regeneration = self.HP_Hull_max / 20
        self.HP_Shields_Regeneration = self.HP_Shields_max / 8
        self.WasHitLastTurn = False
        self.ShieldsWereOffline = False
        
    def healAtTurnStart(self):
        #TODO: This should be 2 methods: One that calculates the healing and one that the first one and then actually updates the values. This way the first method can be used to display a prediction to the user
        #REMINDER: When displaying this to the user there should also be a short text explaining that taking noticeable damage halves the regeneration for one turn and that shields need one turn to restart after being taken down.
        regenFactor = 1 if not self.WasHitLastTurn else 0.5
        self.HP_Hull = min(self.HP_Hull + self.HP_Hull_Regeneration*regenFactor , self.HP_Hull_max)
        if self.ShieldsWereOffline:
            self.ShieldsWereOffline = False
        else:
            self.HP_Shields = min(self.HP_Shields + self.HP_Shields_Regeneration*regenFactor , self.HP_Shields_max)
        
    def takeDamage(self, damage:float, accuracy:float = 1 ,shieldFactor:float = 1, normalHullFactor:float = 1, shieldPiercing:bool = False) -> typing.Tuple[bool,bool,float]:
        """
        This method handles sustaining damage. \n
        TODO: describe parameters \n
        returns bool[shot hit the target], bool[destroyed the target], float[the amount of inflicted damage]
        """
        #FEATURE:HULLTYPES
        #FEATURE:WEAPONSTRUCTURES: instead of handing over a bazillion parameters there should be a class for weapons which can handle everything. That class should probably replace this takeDamage method all together
        hit = np.random.random_sample() < accuracy-self.Evasion
        finalDamage = 0
        destroyed = False
        if hit:
            if shieldPiercing or self.HP_Shields <= 0:
                finalDamage = damage*normalHullFactor
                self.HP_Hull -= finalDamage
                if self.HP_Hull <= 0:
                    destroyed = True
            else:
                finalDamage = damage*shieldFactor
                self.HP_Shields -= finalDamage
                if self.HP_Shields <= 0:
                    self.HP_Shields = 0
                    self.ShieldsWereOffline = True
            self.WasHitLastTurn = finalDamage > self.HP_Hull_max / 10
        if destroyed: self.explode()
        return hit, destroyed, finalDamage
  #endregion Combat Defensive
  #region Combat Offensive
  #endregion Combat Offensive
  #region Effects
    def init_effects(self):
        self.ExplosionEffect = None
        self.ExplosionEffect2 = None
    
    def explode(self):
        explosionDuration = 1.0
        self.Model.setColor((0.1,0.1,0.1,1))
        
        self.ExplosionEffect = loader().loadModel("Models/Simple Geometry/sphere.ply")
        colour = App().PenColours["Orange"].color()
        colour.setAlphaF(0.6)
        self.ExplosionEffect.setColor(ape.colour(colour))
        self.ExplosionEffect.setTransparency(p3dc.TransparencyAttrib.MAlpha)
        #self.ExplosionEffect.setSize(0.1)
        self.ExplosionEffect.reparentTo(self.Node)
        self.ExplosionEffect.scaleInterval(explosionDuration, 1.5, 0.1).start()
        
        self.ExplosionEffect2 = loader().loadModel("Models/Simple Geometry/sphere.ply")
        colour = App().PenColours["Red"].color()
        #colour.setAlphaF(0.5)
        self.ExplosionEffect2.setColor(ape.colour(colour))
        #self.ExplosionEffect2.setTransparency(p3dc.TransparencyAttrib.MAlpha)
        #self.ExplosionEffect2.setSize(0.1)
        self.ExplosionEffect2.reparentTo(self.Node)
        self.ExplosionEffect2.scaleInterval(explosionDuration, 1.1, 0.05).start()
        
        base().taskMgr.doMethodLater(explosionDuration, self.destroy, str(id(self)))
  #endregion Effects
  #region ...
  #endregion ...
  #region ...
  #endregion ...

#endregion Objects

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
        self.selectedUnit: 'weakref.ref[Unit]' = None
        
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

class MainWindowClass(ape.APELabWindow):#APEWindow):
    def setupUI(self):
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.pandaContainer)
        
        self.genWidget = QtWidgets.QWidget(self)
        genLayout = QtWidgets.QHBoxLayout()
        genLayout.setContentsMargins(0,0,0,0)
        
        #self.genCB = QtWidgets.QCheckBox(self)
        #self.genCB.setText("Use seed 6")
        #genLayout.addWidget(self.genCB)
        self.EndTurnButton = AGeWidgets.Button(self,"End Turn",lambda: unitManager().endTurn())
        genLayout.addWidget(self.EndTurnButton)
        
        self.genWidget.setLayout(genLayout)
        layout.addWidget(self.genWidget)
        
        self.cw.setLayout(layout)
        
        #self.Console1.setText("self.Pawn = Unit((25,25),App().MiscColours[\"Self\"])\n")
        self.Console1.setText(ENTERPRISE_IMPORT)
        self.Console2.setText("self.Pawn.takeDamage(400)\n")
    
    def gen(self):
        self.HexGrid.generateHex()
            
    def start(self):
        self.HexGrid = HexGrid()
        Unit((25,25),name="self"  ,model="Models/Simple Geometry/cube.ply", colour=App().MiscColours["Self"]   )
        Unit((27,22),name="a pawn",model="Models/Simple Geometry/cube.ply", colour=App().MiscColours["Neutral"])
        Unit((26,23),name="a pawn",model="Models/Simple Geometry/cube.ply", colour=App().MiscColours["Neutral"])
        Unit((25,23),name="a pawn",model="Models/Simple Geometry/cube.ply", colour=App().MiscColours["Neutral"])
        Unit((24,23),name="a pawn",model="Models/Simple Geometry/cube.ply", colour=App().MiscColours["Neutral"])
        Unit((23,22),name="a pawn",model="Models/Simple Geometry/cube.ply", colour=App().MiscColours["Neutral"])
        
    def getHex(self, i:typing.Tuple[int,int]) -> _Hex:
        return self.HexGrid.getHex(i)

class PandaWidget(ape.PandaWidget):
    pass

ENTERPRISE_IMPORT = """self.Pawn = Unit((25,24),name="USS Enterprise",model="/Users/Robin/Desktop/Projects/AstusGameEngine_dev/3DModels/NCC-1701-D.gltf")
self.Pawn.Model.setY(-0.2)
self.Pawn.Model.setH(180)
self.Pawn.Model.setScale(0.1)

self.Pawn2 = Unit((25,26),name="USS Enterprise",model="/Users/Robin/Desktop/Projects/AstusGameEngine_dev/3DModels/NCC-1701-D.gltf")
self.Pawn2.Model.setY(-0.2)
self.Pawn2.Model.setH(180)
self.Pawn2.Model.setScale(0.1)
"""



#endregion real main
if __name__ == '__main__':
    ape.start(WindowTitle, EngineClass, BaseClass, AppClass, MainWindowClass, PandaWidget, True, SupportsRenderPipeline)
