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
from Economy import Resources
if TYPE_CHECKING:
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
    def __init__(self, coords:typing.Tuple[int,int] = None, hexGrid:'HexGrid' = None):
        if coords:
            message = f"There is no hex at {coords}."
        else:
            message = f"The specified hex does not exist."
        if hexGrid:
            message += f" The hex grid in question is named {hexGrid.Name}."
        message += get.engine()._getNumOfGridsFormatted()
        super().__init__(message)
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
class HexGrid(DirectObject):
    OnHoverDo:typing.Union[None,typing.Callable[['_Hex'],None]]
    def __init__(self, scene:ape.APEScene=None, root:p3dc.NodePath = None, size: typing.Tuple[int,int] = (50,50), TransparentHexRings=True, name:str="Unnamed Hex Grid") -> None:
        self.Active = True
        self.Name = name
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
        
        self._MouseTask = None
        
        # This will represent the index of the currently highlighted hex
        self.HighlightedHex = False # type: _Hex
        # This wil represent the index of the hex where currently dragged piece was grabbed from
        self.SelectedHex = False # type: _Hex
        
        self.generateHex()
    
    def bindEvents(self):
        # Start the task that handles the picking
        self._MouseTask = base().taskMgr.add(self._mouseTask, 'mouseTask')
        self.accept("mouse1", lambda: self._lmbOnHex()) # LMB
        self.accept("mouse3", lambda: self._rmbOnHex()) # RMB
    
    def unbindEvents(self):
        if self._MouseTask:
            base().taskMgr.remove(self._MouseTask)
            self._MouseTask = None
        self.ignore("mouse1") # LMB
        self.ignore("mouse3") # RMB
    
    def clearHexes(self):
        self.unbindEvents()
        self.HighlightedHex = False # type: _Hex
        self.SelectedHex = False # type: _Hex
        for i in self.Hexes:
            for j in i:
                del j #TODO: we might want a destroy method
            del i
        del self.Hexes
        self.Hexes = []
    
    def destroy(self):
        self.Active = False
        self.clearHexes()
        #TODO: If we have created the self.Root node we should also destroy it. But what if we were given one? We should probably not destroy it then because we don't know anything about it
    
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
        self.bindEvents()
    
    def getHex(self, i):
        # type: ( typing.Union[typing.Tuple[int,int], typing.Tuple[int,int,int]] ) -> _Hex
        if len(i) == 3:
            i = self.cubeToCoord(i)
        if len(i) == 2:
            i = ( round(i[0]) , round(i[1]) )
        else:
            raise HexInvalidException(i ,self)
        if self._isValidCoordinate(i):
            return self.Hexes[i[0]][i[1]]
        else:
            raise HexInvalidException(i ,self)
    
    def getEdgeHexes(self, directions:str="NEWS", distance:int=1) -> typing.List["_Hex"]:
        """
        Returns a list with all hexes at the edge of the grid.\n
        Takes a string containing one or more of the letters N, E, W, or S.
        If it contains an N, all hexes at the northern edge of the grid will be included in the list, etc.
        The letters are case insensitive. Duplicates and letters other than N, E, W, and S will be ignored.\n
        Also takes an integer (>=1) that determines how thick the edge is.
        """
        directions = directions.upper()
        if distance < 1:
            raise Exception(f"Distance must be >=1 but is {distance}")
        if distance > self.Size[0] and ("W" in directions or "E" in directions):
            raise Exception(f"Distance {distance} is out of bounds for grid of size {self.Size} in WE-direction")
        if distance > self.Size[1] and ("N" in directions or "S" in directions):
            raise Exception(f"Distance {distance} is out of bounds for grid of size {self.Size} in NS-direction")
        return_set:typing.Set["_Hex"] = set()
        if "N" in directions:
            for i in range(self.Size[1]):
                for d in range(distance):
                    if (h:= self.getHex((self.Size[1]-1-d,i))) not in return_set:
                        return_set.add(h)
        if "S" in directions:
            for i in range(self.Size[1]):
                for d in range(distance):
                    if (h:= self.getHex((0+d,i))) not in return_set:
                        return_set.add(h)
        if "W" in directions:
            for i in range(self.Size[0]):
                for d in range(distance):
                    if (h:= self.getHex((i,0+d))) not in return_set:
                        return_set.add(h)
        if "E" in directions:
            for i in range(self.Size[0]):
                for d in range(distance):
                    if (h:= self.getHex((i,self.Size[1]-1-d))) not in return_set:
                        return_set.add(h)
        return list(return_set)
    
    def getCentreHexes(self, radius:int=1) -> typing.List["_Hex"]:
        """
        Returns a list with all hexes at the centre of the grid.\n
        Takes an integer (>=1) that determines the radius.
        """
        return self.getHex((int(self.Size[1]/2),int(self.Size[0]/2))).getDisk(int(radius))
    
    def getCornerHexes(self, corner:int, radius:int=1) -> typing.List["_Hex"]:
        """
        Returns a list with all hexes at the specified corner of the grid.\n
        Takes two integer:\n
        The first one determines the corner where 0 is the bottom left corner and the others are numbered clockwise.\n
        The other one determines the radius around the corner that should be included in the output.
        """
        if corner == 0:
            return self.getHex((0,0)).getDisk(int(radius))
        elif corner == 1:
            return self.getHex((self.Size[1]-1, 0)).getDisk(int(radius))
        elif corner == 2:
            return self.getHex((self.Size[1]-1,self.Size[0]-1)).getDisk(int(radius))
        elif corner == 3:
            return self.getHex((0,self.Size[0]-1)).getDisk(int(radius))
        else:
            raise Exception(f"corner must be 0, 1, 2, or 3 but it is {corner}")
    
    def getAll4CornerHexes(self) -> typing.List["_Hex"]:
        """
        Returns a list with the 4 hexes at corners of the grid.
        """
        return [self.getHex((0,0)),
            self.getHex((self.Size[1]-1, 0)),
            self.getHex((self.Size[1]-1,self.Size[0]-1)),
            self.getHex((0,self.Size[0]-1))]
    
    #TODO: write another method that works similarly to getCornerHexes but for the sides
    #TODO: Write a method that divides the map into 10 (or generalize to n if feasible) equal areas of similar size and returns them.
    #           This can then be used to place all the flotillas in the correct position in regard to the relative fleet positions on the campaign map
    
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
    
    def highlightHexes(self, hexes = [], edge = False, inner = False, face = False, clearFirst = True):
        # type: (typing.List[_Hex], typing.Union[QtGui.QColor,QtGui.QBrush,typing.Tuple[int,int,int,int],str,False], typing.Union[QtGui.QColor,QtGui.QBrush,typing.Tuple[int,int,int,int],str,False], typing.Union[QtGui.QColor,QtGui.QBrush,typing.Tuple[int,int,int,int],str,False], bool) -> None
        if clearFirst:
            self.clearAllHexHighlighting()
        if (edge or face) or not clearFirst:
            for i in hexes:
                i.highlight(edge = edge, inner = inner, face = face, clearFirst=False)
    
    def clearAllHexHighlighting(self,forceAll=False):
        for i in self.Hexes:
            for ii in i:
                if (ii.Highlighted or forceAll) and ii is not self.SelectedHex:
                    ii.highlight(edge = False, inner = False, face = False)
    
    def clearAllSelections(self):
        for i in self.Hexes:
            for ii in i:
                ii.select(False, False)
        get.app().S_HexSelectionChanged.emit()
    
  #region Interaction
    def _mouseTask(self, task):
        # This task deals with the highlighting and selection based on the mouse
        
        # If the mouse currently controls the camera we want to disable any interactions
        if get.engine().getScene().Camera.CamMouseControl:
            return Task.cont
        
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
                i.highlightText()
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
                #self.SelectedHex.hoverHighlight()
                #self.SelectedHex = False
                return
            else:
                self.SelectedHex.select(False)
                #self.SelectedHex = False
        if self.HighlightedHex is not False:
            self.HighlightedHex.select(True)
            #self.SelectedHex = self.HighlightedHex
            #self.SelectedHex.select()
            #self.HighlightedHex = False
        else:
            pass #TODO: Clean up the interface since nothing is selected (it should already be cleaned up but better save than sorry)
            #unitManager().selectUnit(None)
    
    def selectHex(self, hex_:"_Hex", select:bool = True, emit:bool = True):
        if not self.Active: return
        self.clearInteractionFunctions()
        if self.SelectedHex is not False:
            if self.SelectedHex is hex_:
                if not select:
                    self.SelectedHex._select(False)
                    if self.SelectedHex is self.HighlightedHex:
                        self.SelectedHex.hoverHighlight()
                    self.SelectedHex = False
            elif select:
                self.SelectedHex._select(False)
                self.SelectedHex = False
        if hex_ is not False and select:
            self.SelectedHex = hex_
            self.SelectedHex._select()
            if self.HighlightedHex is self.SelectedHex:
                self.HighlightedHex = False
        if emit: get.app().S_HexSelectionChanged.emit()
    
    def _interactWithHighlightedHex(self):
        if not self.Active: return
        if self.SelectedHex is not False and self.HighlightedHex is not False:
            if self.SelectedHex.interactWith(self.HighlightedHex):
                self._selectHighlightedHex()
  #endregion Interaction

class _Hex():
    #TODO: These Hex colours should be in the 
    COLOUR_NORMAL = "HEX_COLOUR_NORMAL"
    COLOUR_RESOURCES = "HEX_COLOUR_RESOURCES"
    COLOUR_SELECT = "HEX_COLOUR_SELECT"
    COLOUR_SELECT_FACE = "HEX_COLOUR_SELECT_FACE"
    COLOUR_HIGHLIGHT = "HEX_COLOUR_HIGHLIGHT"
    COLOUR_REACHABLE = "HEX_COLOUR_REACHABLE"
    COLOUR_ATTACKABLE = "HEX_COLOUR_ATTACKABLE"
    COLOUR_ATTACKABLE_FACE = "HEX_COLOUR_ATTACKABLE_FACE"
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
            
            # We will use this list to store all objects that occupy this hexagon
            self.content = [] # type: 'list[weakref.ref[FleetBase.FleetBase]]' #TODO: Fleets can not be the content but what will be the content?
            self.fleet = None # type: 'weakref.ref[FleetBase.FleetBase]'
            #self.Navigable = True
            
            self.Selected = False
            self.Highlighted = False
            self.HighlightedEdge = False
            self.HighlightedInner = False
            self.HighlightedFace = False
            
            self.Name = name
            self.Colour = self.COLOUR_NORMAL
            self.CurrentColour_Edge = self.COLOUR_NORMAL
            self.CurrentColour_InnerRing = self.COLOUR_NORMAL
            self.CurrentColour_Face = self.COLOUR_SELECT_FACE
            self.Coordinates = coordinates
            self.TransparentHexRings = grid.TransparentHexRings
            self.grid = weakref.ref(grid)
            self.ResourcesFree = Resources._ResourceDict()
            self.ResourcesHarvestable = Resources._ResourceDict()
            #TODO: The resources should either be saved or we should get rid of this system and just create container Background Objects!
            
            # Save cube coordinates
            self.CubeCoordinates = grid.coordToCube(coordinates)
            
            self.Pos = p3dc.LPoint3(pos)
            mesh = "Models/Simple Geometry/hexagon.ply"
            meshRing = "Models/Simple Geometry/hexagonRing.ply"
            meshRingInner = "Models/Simple Geometry/hexagonRingInner.ply"
            # Load, parent, colour, and position the model (a hexagon-shaped ring consisting of 6 polygons)
            self.Node:p3dc.NodePath = p3dc.NodePath(p3dc.PandaNode(f"Central node of hex: {name}"))
            self.Node.reparentTo(root)
            self.Node.setPos(self.Pos)
            self.Model:p3dc.NodePath = ape.loadModel(meshRing)
            self.Model.reparentTo(self.Node)
            if self.TransparentHexRings:
                self.Model.setTransparency(p3dc.TransparencyAttrib.MAlpha)
            self._setColor(self.Colour)
            # Load, parent, hide, and position the face (a single hexagon polygon)
            self.Face:p3dc.NodePath = ape.loadModel(mesh)
            self.Face.reparentTo(self.Node)
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
            
            # Load, parent, colour, and position the model (a hexagon-shaped ring consisting of 6 polygons)
            self.InnerRing:p3dc.NodePath = ape.loadModel(meshRingInner)
            self.InnerRing.reparentTo(self.Node)
            self.InnerRing.setPos(p3dc.LPoint3((0,0,0)))
            if self.TransparentHexRings:
                self.InnerRing.setTransparency(p3dc.TransparencyAttrib.MAlpha)
            self._setColorInnerRing(self.Colour)
            self.InnerRing.hide()
        except:
            NC(1,f"Error while creating {name}",exc=True) #MAYBE: Since we re-raise the exception after cleanup we might as well remove the notification
            nodes = "InnerRing,Face,Model,Node".split(",")
            for node in nodes:
                if hasattr(self,node):
                    getattr(self,node).removeNode()
            raise
    
    @property
    def Navigable(self):
        for i in self.content:
            if i and i().isBlockingTileCompletely(): return False
        if self.fleet and self.fleet().isBlockingTileCompletely(): return False
        return True
    
    def isNavigable(self, isBlockingTilePartially, isBlockingTileCompletely, isBackgroundObject):
        if not isBackgroundObject and self.fleet: return False
        if isBlockingTilePartially or isBlockingTileCompletely:
            for i in self.content:
                if i and i().isBlockingTilePartially(): return False
            if self.fleet and self.fleet().isBlockingTilePartially(): return False
        return self.Navigable
    
    def __del__(self):
        del self.content
        self.InnerRing.removeNode()
        self.Face.removeNode()
        self.Model.removeNode()
        self.Node.removeNode()
    
    def isHighlighted(self):
        return self is self.grid().HighlightedHex
    
    def interactWith(self,other):
        # type: (_Hex) -> bool
        """
        Makes the contents of this hex interact with the `other` hex. \n
        Returns `True` if the new hex should be selected after this interaction.
        """
        if self.fleet:
            return self.fleet().interactWith(other)
        return False
    
    def __repr__(self) -> str:
        if self.fleet: fleet = self.fleet()
        else: fleet = self.fleet
        return f"\n### Hex {id(self)}\n\tName: {self.Name}\n\tHex at {self.Coordinates}\n\tID: {id(self)}\n\tParent Grid: {self.grid()}\n\tOccupied by Fleet: {fleet}\n### End Hex {id(self)}\n"
    
  #region Content
    def __iter__(self):
        for i in [self.fleet, *self.content]:
            if i:
                if i() is None:
                    NC(2,"A hex iterated over content that was already deleted but te reference was not removed.\n"
                        "The reference wil now be removed but this case should not happen in the first place.",
                        input=f"Hex:\n{repr(self)}\n\nIs Fleet: {i is self.fleet}\nIs in content: {i in self.content}")
                    if i in self.content:
                        self.content.remove(i)
                    elif i is self.fleet:
                        self.fleet = None
                else:
                    yield i()
    
    def selectFleet(self, select:bool = True):
        if select:
            get.unitManager().selectUnit(self.fleet)
        else:
            get.unitManager().selectUnit(None)
    
    def selectContent(self, select:bool = True):
        return
        #if select:
        #    get.unitManager().selectUnit(self.fleet)
        #else:
        #    get.unitManager().selectUnit(None)
    
    def addContent(self, content): #TODO:OVERHAUL
        if not content: NC(2,"A hex was requested to add the content: "+str(content),tb=True)
        else:
            self.content.append(weakref.ref(content))
        #TODO: If the this is already selected while new content is added the new content should be informed about this and act accordingly (display/update movement range, add/update UI elements, etc).
        #       Furthermore the other content might need to be informed that there is new content which might require them to update their UI elements or highlighting
    
    def removeContent(self, fleet:'FleetBase.FleetBase'):
        for i in self.content:
            if not i:
                self.content.remove(i)
            elif i() == fleet:
                self.content.remove(i)
    
    def hideContent(self):
        for i in self.content:
            if i and i(): #TODO: When there was a game with fleets and one then loads a new game this method says that None-Type has no attribute "hide". Reproduce by removing the "and i()" from this line, starting a new game, moving the starting fleet, ending the turn, and then loading the AutoSave that was created when ending the turn
                try:
                    i().hide()
                except:
                    NC(2,exc=True)
            else:
                self.content.remove(i)
        if self.fleet:
            self.fleet().hide()
            if self.CurrentColour_Edge == self.getNormalEdgeColour():
                Highlighted = self.Highlighted
                HighlightedEdge = self.HighlightedEdge
                self.highlight(edge=self.COLOUR_NORMAL, clearFirst=False)
                self.Highlighted = Highlighted
                self.HighlightedEdge = HighlightedEdge
    
    def showContent(self):
        for i in self.content:
            if i:
                try:
                    i().show()
                except:
                    NC(2,exc=True)
            else:
                self.content.remove(i)
        if self.fleet:
            self.fleet().show()
            if self.CurrentColour_Edge == self.COLOUR_NORMAL:
                Highlighted = self.Highlighted
                HighlightedEdge = self.HighlightedEdge
                self.highlight(edge=self.getNormalEdgeColour(), clearFirst=False)
                self.Highlighted = Highlighted
                self.HighlightedEdge = HighlightedEdge
  #endregion Content
    
  #region Colour
    
    def getNormalEdgeColour(self):
        if self.fleet:
            s = "Team "+str(self.fleet().Team)
            if s in App().Theme["Star Nomads"]:
                return s
        return self.COLOUR_NORMAL
    
    def _setColor(self, colour, alpha = 0.2):
        """
        TODO: This information is outdated. We now use the "Star Nomads" colour dictionary. \n
        Set the colour of the edge to `colour`. \n
        `colour` can be a QColor, a QBrush, a tuple, or a string from AGeLib's PenColours dictionary. \n
        If `colour` is a PenColours-string `alpha` can be given. (Otherwise `alpha` is ignored since the other input variants already support specifying the alpha value.)
        """
        return self._setColour(colour,alpha)
    def _setColour(self, colour, alpha = 0.2):
        """
        TODO: This information is outdated. We now use the "Star Nomads" colour dictionary. \n
        Set the colour of the edge to `colour`. \n
        `colour` can be a QColor, a QBrush, a tuple, or a string from AGeLib's PenColours dictionary. \n
        If `colour` is a PenColours-string `alpha` can be given. (Otherwise `alpha` is ignored since the other input variants already support specifying the alpha value.)
        """
        if isinstance(colour,str):
            colour = App().Theme["Star Nomads"][colour].color()
            colour.setAlphaF(alpha)
        self.Model.setColor(ape.colour(colour))
    
    def _setColorInnerRing(self, colour, alpha = 0.2):
        """
        TODO: This information is outdated. We now use the "Star Nomads" colour dictionary. \n
        Set the colour of the inner ring to `colour`. \n
        `colour` can be a QColor, a QBrush, a tuple, or a string from AGeLib's PenColours dictionary. \n
        If `colour` is a PenColours-string `alpha` can be given. (Otherwise `alpha` is ignored since the other input variants already support specifying the alpha value.)
        """
        return self._setColourInnerRing(colour,alpha)
    def _setColourInnerRing(self, colour, alpha = 0.2):
        """
        TODO: This information is outdated. We now use the "Star Nomads" colour dictionary. \n
        Set the colour of the inner ring to `colour`. \n
        `colour` can be a QColor, a QBrush, a tuple, or a string from AGeLib's PenColours dictionary. \n
        If `colour` is a PenColours-string `alpha` can be given. (Otherwise `alpha` is ignored since the other input variants already support specifying the alpha value.)
        """
        if isinstance(colour,str):
            colour = App().Theme["Star Nomads"][colour].color()
            colour.setAlphaF(alpha)
        self.InnerRing.setColor(ape.colour(colour))
    
    def _setColorFace(self, colour, alpha = 0.2):
        """
        TODO: This information is outdated. We now use the "Star Nomads" colour dictionary. \n
        Set the colour of the face to `colour`. \n
        `colour` can be a QColor, a QBrush, a tuple, or a string from AGeLib's PenColours dictionary. \n
        If `colour` is a PenColours-string `alpha` can be given. (Otherwise `alpha` is ignored since the other input variants already support specifying the alpha value.)
        """
        return self._setColourFace(colour,alpha)
    def _setColourFace(self, colour, alpha = 0.2):
        """
        TODO: This information is outdated. We now use the "Star Nomads" colour dictionary. \n
        Set the colour of the face to `colour`. \n
        `colour` can be a QColor, a QBrush, a tuple, or a string from AGeLib's PenColours dictionary. \n
        If `colour` is a PenColours-string `alpha` can be given. (Otherwise `alpha` is ignored since the other input variants already support specifying the alpha value.)
        """
        if isinstance(colour,str):
            colour = App().Theme["Star Nomads"][colour].color()
            colour.setAlphaF(alpha)
        self.Face.setColor(ape.colour(colour))
  #endregion Colour
  #region Highlighting
    
    def highlightText(self):
        text = f"{self.Name}"
        if self.ResourcesFree: text += f" | Floating Cargo Present ({self.ResourcesFree.UsedCapacity})"
        if self.ResourcesHarvestable: text += f" | Harvestable Resources Present ({self.ResourcesHarvestable.UsedCapacity})"
        get.window().Statusbar.showMessage(text)
    
    def hoverHighlight(self, highlight:bool = True):
        if highlight:
            if self.TransparentHexRings:
                self.Model.setTransparency(p3dc.TransparencyAttrib.MNone)
            self._setColor(self.COLOUR_HIGHLIGHT)
            self.Model.show()
        else:
            if self.TransparentHexRings and not self.CurrentColour_Edge == self.COLOUR_SELECT:
                self.Model.setTransparency(p3dc.TransparencyAttrib.MAlpha)
            self._setColor(self.CurrentColour_Edge)
            if get.menu().HighlightOptionsWidget.HideGrid() and not self.HighlightedEdge and not self.Selected:
                self.Model.hide()
    
    def highlight(self, edge = False, inner = False, face = False, clearFirst = False):
        if clearFirst:
            self.highlight(edge = False, inner = False, face = False, clearFirst = False)
        if not edge and not inner and not face:
            if self.TransparentHexRings and not self.CurrentColour_Edge == self.COLOUR_SELECT:
                self.Model.setTransparency(p3dc.TransparencyAttrib.MAlpha)
                if get.menu().HighlightOptionsWidget.HideGrid() and not self.Selected: self.Model.hide()
            if not get.menu().HighlightOptionsWidget.HideGrid(): self.Model.show()
            #if self.isHighlighted():
            #    self.CurrentColour_Edge = self.COLOUR_SELECT
            #    self.CurrentColour_Face = self.COLOUR_SELECT_FACE
            #    self._setColor(self.CurrentColour_Edge)
            #    self._setColorFace(self.CurrentColour_Face)
            #    if self.TransparentHexRings:
            #        self.Model.setTransparency(p3dc.TransparencyAttrib.MNone)
            #    self.Face.setTransparency(p3dc.TransparencyAttrib.MAlpha)
            #    self.Face.show()
            #else:
            self.CurrentColour_Edge = self.COLOUR_NORMAL
            self.CurrentColour_InnerRing = self.COLOUR_NORMAL
            self.CurrentColour_Face = self.COLOUR_SELECT_FACE
            if self.ResourcesHarvestable or self.ResourcesFree:
                self.CurrentColour_InnerRing = self.COLOUR_RESOURCES
            self._setColor(self.CurrentColour_Edge)
            self._setColorInnerRing(self.CurrentColour_InnerRing)
            self._setColorFace(self.CurrentColour_Face)
            if self.TransparentHexRings:
                self.Model.setTransparency(p3dc.TransparencyAttrib.MAlpha)
                self.InnerRing.setTransparency(p3dc.TransparencyAttrib.MAlpha)
            self.Face.setTransparency(p3dc.TransparencyAttrib.MNone)
            self.Face.hide()
            self.hideInnerRing()
            self.Highlighted = False
            self.HighlightedEdge = False
            self.HighlightedInner = False
            self.HighlightedFace = False
        else:
            self.Highlighted = True
            if edge:
                self.HighlightedEdge = True
                if self.TransparentHexRings:
                    self.Model.setTransparency(p3dc.TransparencyAttrib.MAlpha)
                self.CurrentColour_Edge = edge
                self._setColor(self.CurrentColour_Edge)
                self.Model.show()
            if inner:
                self.HighlightedInner = True
                if self.TransparentHexRings:
                    self.InnerRing.setTransparency(p3dc.TransparencyAttrib.MAlpha)
                self.CurrentColour_InnerRing = inner
                self._setColorInnerRing(self.CurrentColour_InnerRing)
                self.InnerRing.show()
            if face:
                self.HighlightedFace = True
                self.Face.setTransparency(p3dc.TransparencyAttrib.MAlpha)
                self.CurrentColour_Face = face
                self._setColourFace(self.CurrentColour_Face)
                self.Face.show()
    
    def select(self, select:bool = True, emit:bool = True):
        self.grid().selectHex(self, select, emit)
    
    def _select(self, select:bool = True):
        self._select_highlighting(select)
        self.selectFleet(select)
        self.selectContent(select)
    
    def _select_highlighting(self, select:bool = True):
        self.Selected = select
        if select:
            self.CurrentColour_Edge = self.COLOUR_SELECT
            if self.TransparentHexRings:
                self.Model.setTransparency(p3dc.TransparencyAttrib.MNone)
            self._setColor(self.COLOUR_SELECT)
            self._setColorFace(self.COLOUR_SELECT_FACE)
            self.Face.setTransparency(p3dc.TransparencyAttrib.MAlpha)
            self.Face.show()
            self.Model.show()
            self.hideInnerRing()
        else:
            self.CurrentColour_Edge = self.Colour
            if self.TransparentHexRings:
                self.Model.setTransparency(p3dc.TransparencyAttrib.MAlpha)
            self._setColor(self.Colour)
            self.Face.setTransparency(p3dc.TransparencyAttrib.MNone)
            self.Face.hide()
            self.hideInnerRing()
            if get.menu().HighlightOptionsWidget.HideGrid() and not self.HighlightedEdge: self.Model.hide()
    
    def hideInnerRing(self):
        if self.ResourcesHarvestable or self.ResourcesFree:
            self.CurrentColour_InnerRing = self.COLOUR_RESOURCES
            self._setColorInnerRing(self.CurrentColour_InnerRing)
            self.InnerRing.show()
        else:
            self.CurrentColour_InnerRing = self.COLOUR_NORMAL
            self._setColorInnerRing(self.CurrentColour_InnerRing)
            self.InnerRing.hide()
    
  #endregion Highlighting
  #region Hex Math
    def getNeighbour(self,direction:typing.Union[int,typing.Tuple[int,int,int]]=-1) -> typing.Union['_Hex',typing.List['_Hex']]:
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

def findPath(start:_Hex, destination:_Hex, navigable = lambda hex: hex.Navigable, cost = lambda hex: 1, movementPoints:float=None) -> typing.Tuple[typing.List[_Hex],float]:
    """
    The hex path finder. \n
    Returns a list containing the hexes that form a shortest path between start and destination (including destination but excluding start). \n
    Also returns the cost of the entire path. \n
    start       : Starting hex for path finding. \n
    destination : Destination hex for path finding. \n
    navigable   : A function that, given a _Hex, tells us whether we can move through this hex. \n
    cost        : A cost function for moving through a hex. Should return a value >= 1. By default all costs are 1. \n
    movementPoints : If a float is given the returned path will only include those tiles that can be reached using the given amount of movementPoints. If movementPoints is None the whole path is returned.
    """
    #TODO: This should be able to take movement points and ensure that the returned path does not exceed this (if given)
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
            assert Path[0] == start
            assert Path[-1] == destination
            Path = Path[1:] # We do not return the starting position
            if movementPoints is not None:
                #print("Path", f"from {start.Name} to {destination.Name}:", "->".join([str(i.Coordinates) for i in Path]))
                p = []
                c = 0
                for i in Path:
                    c += cost(i)
                    if c > movementPoints: break
                    else: p.append(i)
                Path = p
            return Path, sum([cost(i) for i in Path])
        else:
            return [], 0
    except: #Catches the case that Path is None #TODO: handle this case more cleanly
        return [], 0

#endregion Hex Map
