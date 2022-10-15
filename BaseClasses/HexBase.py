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
from BaseClasses import compat # don't remove this import. It does have side effects.
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

# Game Imports
from BaseClasses import get
if TYPE_CHECKING:
    from BaseClasses import Unit
    from BaseClasses import FleetBase

#region Exceptions
class HexException(Exception): pass

class HexOccupiedException(HexException):
    """
    This exception is raised when a hex is already occupied.
    """
    def __init__(self, hex=None):
        # type: (_Hex) -> None
        if hex:
            super().__init__(f"{hex.Name} is already occupied by {hex.fleet().Name}.")
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
    return get.engine().getHex(i).Pos

def getHex(i:typing.Tuple[int,int]):
    """
    This function is only intended for use in the interactive AGeIDE. \n
    To properly get a hex you should always use the method of the HexGrid instance. \n
    Furthermore the HexGrid instance should be accessed unambiguously (optimally by getting it from another Hex._Hex instace) since we might have two hex grids in the future (one for the main game and one for battles)!
    """
    return get.engine().getHex(i)

#endregion Helper Functions

#region Hex Map
class HexGrid():
    OnHoverDo:typing.Union[None,typing.Callable[['_Hex'],None]]
    def __init__(self, scene:ape.APEScene=None, root:p3dc.NodePath = None, size: typing.Tuple[int,int] = (50,50), TransparentHexRings=True) -> None:
        self.Active = True
        self.OnHoverDo:typing.Union[typing.Callable[['_Hex'],None],None] = None # This must be a function that takes a hexagon and does stuff. This member can be set on demand to, for example, preview things
        self.OnLMBDo:typing.Union[typing.Callable[['_Hex'],None],typing.Tuple[bool,bool]] = None # This must be a function that takes a hexagon and does stuff. This member can be set on demand to, for example, target abilities
        self.OnRMBDo:typing.Union[typing.Callable[['_Hex'],None],typing.Tuple[bool,bool]] = None # This must be a function that takes a hexagon and does stuff. This member can be set on demand to, for example, cancel abilities
        self.OnClearDo: typing.Union[typing.Callable[[None],None],None] = None # This must be a function that takes nothing and is called when the other interactions get reset. Used to clean up i.e. highlighting
        self.Scene = scene if scene else get.engine().Scene
        if root:
            self.Root = root
        else:
            self.Root = render().attachNewNode("hexRoot")
            self.Root.setPos((0,0,0))
        self.Hexes = [] # type: typing.List[typing.List[_Hex]]
        self.Size = size
        self.m_material = None
        self.m_colour = None
        self.TransparentHexRings = TransparentHexRings
        self.generateHex()
        
        # This will represent the index of the currently highlighted hex
        self.HighlightedHex = False # type: _Hex
        # This wil represent the index of the hex where currently dragged piece was grabbed from
        self.SelectedHex = False # type: _Hex
        
        self.bindEvents()
    
    def bindEvents(self):
        # Start the task that handles the picking
        self.mouseTask = base().taskMgr.add(self._mouseTask, 'mouseTask')
        base().accept("mouse1", lambda: self._lmbOnHex()) # LMB
        base().accept("mouse3", lambda: self._rmbOnHex()) # RMB
    
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
            return self.Hexes[i[0]][i[1]]
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
            self.clearAllHexHighlighting()
        if (edge or face) or not clearFirst:
            for i in hexes:
                i.highlight(edge = edge, face = face)
    
    def clearAllHexHighlighting(self):
        for i in self.Hexes:
            for ii in i:
                if ii.Highlighted:
                    ii.highlight(edge = False, face = False)
    
    def clearAllSelections(self):
        for i in self.Hexes:
            for ii in i:
                ii.select(False)
    
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
                get.window().Statusbar.showMessage(i.Name)
                if self.OnHoverDo:
                    self.OnHoverDo(i)
        
        return Task.cont
    
    def clearInteractionFunctions(self):
        if self.OnClearDo:
            self.OnClearDo()
        self.OnLMBDo = None
        self.OnRMBDo = None
        self.OnHoverDo = None
        self.OnClearDo = None
    
    def _lmbOnHex(self):
        select = True
        if self.OnLMBDo:
            select, clear = self.OnLMBDo(self.HighlightedHex)
            if clear: self.clearInteractionFunctions()
        if select:
            self._selectHighlightedHex()
    
    def _rmbOnHex(self):
        if self.OnRMBDo:
            select, clear = self.OnRMBDo(self.HighlightedHex)
            if clear: self.clearInteractionFunctions()
            if select: self._selectHighlightedHex()
        else:
            self._interactWithHighlightedHex()
    
    def _selectHighlightedHex(self):
        if not self.Active: return
        self.clearInteractionFunctions()
        if self.SelectedHex is not False:
            if self.SelectedHex is self.HighlightedHex:
                self.SelectedHex.select(False)
                self.SelectedHex.hoverHighlight()
                self.SelectedHex = False
                return
            else:
                self.SelectedHex.select(False)
                self.SelectedHex = False
        if self.HighlightedHex is not False:
            self.SelectedHex = self.HighlightedHex
            self.SelectedHex.select()
            self.HighlightedHex = False
        else:
            pass #TODO: Clean up the interface since nothing is selected (it should already be cleaned up but better save than sorry)
            #unitManager().selectUnit(None)
    
    def _interactWithHighlightedHex(self):
        if not self.Active: return
        if self.SelectedHex is not False and self.HighlightedHex is not False:
            if self.SelectedHex.interactWith(self.HighlightedHex):
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
            self.TransparentHexRings = grid.TransparentHexRings
            self.grid = weakref.ref(grid)
            
            # Save cube coordinates
            self.CubeCoordinates = grid.coordToCube(coordinates)
            
            self.Pos = p3dc.LPoint3(pos)
            mesh = "Models/Simple Geometry/hexagon.ply"
            meshRing = "Models/Simple Geometry/hexagonRing.ply"
            # Load, parent, colour, and position the model (a hexagon-shaped ring consisting of 6 polygons)
            self.Model:p3dc.NodePath = loader().loadModel(meshRing)
            self.Model.reparentTo(root)
            self.Model.setPos(self.Pos)
            if self.TransparentHexRings:
                self.Model.setTransparency(p3dc.TransparencyAttrib.MAlpha)
            self._setColor(self.Colour)
            # Load, parent, hide, and position the face (a single hexagon polygon)
            self.Face:p3dc.NodePath = loader().loadModel(mesh)
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
            self.content = [] # type: typing.List[Unit.Object]
            self.fleet = None # type: weakref.ref[FleetBase.FleetBase]
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
    
    def interactWith(self,other):
        # type: (_Hex) -> bool
        """
        Makes the contents of this hex interact with the `other` hex. \n
        Returns `True` if the new hex should be selected after this interaction. 
        """
        if self.fleet:
            return self.fleet().interactWith(other)
    
    
  #region Content
    # These Methods should be overwritten by subclasses
    def selectContent(self, select:bool = True): #TODO:OVERHAUL
        if select:
            get.unitManager().selectUnit(self.fleet)
        else:
            get.unitManager().selectUnit(None)
    
    def addContent(self, content): #TODO:OVERHAUL
        #TODO: If the this is already selected while new content is added the new content should be informed about this and act accordingly (display/update movement range, add/update UI elements, etc).
        #       Furthermore the other content might need to be informed that there is new content which might require them to update their UI elements or highlighting
        raise NotImplementedError("_Hex.addContent is not implemented yet")
  #endregion Content
    
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
            if self.TransparentHexRings:
                self.Model.setTransparency(p3dc.TransparencyAttrib.MNone)
            self._setColor(self.COLOUR_HIGHLIGHT)
        else:
            if self.TransparentHexRings and not self.CurrentColour_Edge == self.COLOUR_SELECT:
                self.Model.setTransparency(p3dc.TransparencyAttrib.MAlpha)
            self._setColor(self.CurrentColour_Edge)
    
    def highlight(self, edge = False, face = False):
        if not face and not edge:
            if self.TransparentHexRings and not self.CurrentColour_Edge == self.COLOUR_SELECT:
                self.Model.setTransparency(p3dc.TransparencyAttrib.MAlpha)
            if self.isSelected():
                self.CurrentColour_Edge = self.COLOUR_SELECT
                self.CurrentColour_Face = self.COLOUR_SELECT_FACE
                self._setColor(self.CurrentColour_Edge)
                self._setColorFace(self.CurrentColour_Face)
                if self.TransparentHexRings:
                    self.Model.setTransparency(p3dc.TransparencyAttrib.MNone)
                self.Face.setTransparency(p3dc.TransparencyAttrib.MAlpha)
                self.Face.show()
            else:
                self.CurrentColour_Edge = self.COLOUR_NORMAL
                self.CurrentColour_Face = self.COLOUR_SELECT_FACE
                self._setColor(self.CurrentColour_Edge)
                self._setColorFace(self.CurrentColour_Face)
                if self.TransparentHexRings:
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
            if self.TransparentHexRings:
                self.Model.setTransparency(p3dc.TransparencyAttrib.MNone)
            self._setColor(self.COLOUR_SELECT)
            self._setColorFace(self.COLOUR_SELECT_FACE)
            self.Face.setTransparency(p3dc.TransparencyAttrib.MAlpha)
            self.Face.show()
        else:
            self.CurrentColour_Edge = self.Colour
            if self.TransparentHexRings:
                self.Model.setTransparency(p3dc.TransparencyAttrib.MAlpha)
            self._setColor(self.Colour)
            self.Face.setTransparency(p3dc.TransparencyAttrib.MNone)
            self.Face.hide()
        self.selectContent(select)
    
  #endregion Highlighting
  #region Hex Math
    def getNeighbour(self,direction=-1) -> typing.Union['_Hex',typing.List['_Hex']]:
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
    
    def distance(self, other:'typing.Union[_Hex,typing.Iterable[int,int,int]]'):
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

def findPath(start:_Hex, destination:_Hex, navigable = lambda hex: hex.Navigable, cost = lambda hex: 1) -> typing.Tuple[typing.List[_Hex],float]:
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