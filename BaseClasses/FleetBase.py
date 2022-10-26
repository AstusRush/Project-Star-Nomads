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
import math

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

# Game Imports
if TYPE_CHECKING:
    from BaseClasses import ShipBase
from BaseClasses import get
from BaseClasses import HexBase
from BaseClasses import AI_Base
from BaseClasses import AI_Fleet

IMP_FLEETBASE = [("PSN get","from BaseClasses import get"),("PSN FleetBase","from BaseClasses import FleetBase")]
IMP_FLEET = IMP_FLEETBASE + [("PSN FleetConstructor","""
def createFleet(d:dict):
    fleet = FleetBase.Fleet(d["Team"])
    fleet.Name = d["Name"]
    fleet.addShips(d["Ships"])
    fleet.moveToHex(get.hexGrid().getHex(d["Coordinates"]))
    
    return fleet
""")]

class ShipList(typing.List['ShipBase.ShipBase']):
    pass

class TeamRing():
    def __init__(self, fleet, team, node) -> None:
        self.fleet:'weakref.ref[FleetBase]' = weakref.ref(fleet)
        self.TeamRing:p3dc.NodePath = loader().loadModel("Models/Simple Geometry/hexagonRing.ply")
        self.TeamRing.reparentTo(node)
        self.TeamRing.setColor(ape.colour(App().Theme["Star Nomads"][f"Team {team}"]))
        self.TeamRing.setScale(0.9)
        self.TeamRing.setPos(p3dc.LPoint3((0,0,-0.02)))
        self.C_ColourChangedConnection = App().S_ColourChanged.connect(self.recolour)
    
    def destroy(self):
        if self.C_ColourChangedConnection:
            App().S_ColourChanged.disconnect(self.C_ColourChangedConnection)
            self.C_ColourChangedConnection = None
        if self.TeamRing:
            self.TeamRing.removeNode()
            self.TeamRing = None
    
    def __del__(self):
        self.destroy()
    
    def recolour(self):
        self.TeamRing.setColor(ape.colour(App().Theme["Star Nomads"][f"Team {self.fleet().Team}"]))

class FleetBase():
  #region init and destroy
    def __init__(self, strategic: bool = False, team = 1) -> None:
        """
        If `strategic` the fleet is a fleet on the strategic map, \n
        otherwise the 'fleet' is a flotilla on the tactical map.
        """
        self._IsFleet, self._IsFlotilla = strategic, not strategic
        self.AI = AI_Fleet.FleetAI(self) if strategic else AI_Fleet.FlotillaAI(self)
        self.Ships:ShipList = ShipList()
        self.Node = p3dc.NodePath(p3dc.PandaNode(f"Central node of fleet {id(self)}"))
        #self.Node.reparentTo(render())
        self.Node.reparentTo(get.engine().getSceneRootNode())
        self.TeamRing = TeamRing(self, team, self.Node)
        
        self.Widget = None
        self.MovementSequence:p3ddSequence = None
        
        self.Name = "name"
        self.Team = team
        self.Destroyed = False
        self.IsMoving = False
        
        #TEMPORARY
        self.hex: 'weakref.ref[HexBase._Hex]' = None
        self.ActiveTurn = 1 == 1
        get.unitManager(self._IsFleet).Teams[self.Team].append(self)
    
    def completelyDestroy(self):
        ships = self.Ships.copy()
        for i in ships:
            i.destroy()
        self.destroy()
    
    def destroy(self):
        self.Destroyed = True
        try:
            get.unitManager(self._IsFleet).Teams[self.Team].remove(self)
        except:
            if self in get.unitManager(self._IsFleet).Teams[self.Team]:
                raise
        if self.isSelected():
            get.unitManager(self._IsFleet).selectUnit(None)
        if self.hex:
            if self.hex().fleet:
                if self.hex().fleet() is self:
                    self.hex().fleet = None
            self.hex = None
        if self.TeamRing:
            self.TeamRing.destroy()
            self.TeamRing = None
        if self.Node:
            self.Node.removeNode()
            self.Node = None
    
    def __del__(self):
        self.destroy()
    
    @property
    def MovePoints(self) -> float:
        raise NotImplementedError()
    def spendMovePoints(self, value:float):
        raise NotImplementedError()
    @property
    def MovePoints_max(self) -> float:
        raise NotImplementedError()
    
  #endregion init and destroy
  #region manage ship list
    def _addShip(self, ship:'ShipBase.ShipBase'):
        if not ship in self.Ships:
            self.Ships.append(ship)
        ship.reparentTo(self)
    
    def addShip(self, ship:'ShipBase.ShipBase'):
        self._addShip(ship)
        self.arrangeShips()
    
    def addShips(self, ships:typing.List['ShipBase.ShipBase']):
        for ship in ships:
            self._addShip(ship)
        self.arrangeShips()
    
    def removeShip(self, ship:'ShipBase.ShipBase', arrange:bool=True, notifyIfNotContained:bool=True) -> bool:
        """
        Remove `ship` from this fleet and rearranges the ship positions if `arrange`. \n
        Returns True if the Fleet still exists afterwards, otherwise returns False
        """
        if ship in self.Ships:
            self.Ships.remove(ship)
            if self.Ships and arrange: self.arrangeShips()
        else:
            if notifyIfNotContained: NC(2,f"SHIP WAS NOT IN SHIP LIST\nFleet name: {self.Name}\nShip name: {ship.Name}", tb=True) #TODO: give more info
        if not self.Ships:
            self.destroy()
            return False
        else:
            return True
    
    def isDestroyed(self):
        """
        Returns `True` if `self.Ships` is empty or all ships in `self.Ships` have the attribute `Destroyed` set to `True` or `self.Destroyed` is `True`. Otherwise returns False.\n
        This if different to the attribute `self.Destroyed` which is only set to True when the fleet AND ITS MODELS no longer exist.
        """
        if self.Destroyed: return True
        return all([i.Destroyed for i in self.Ships])
    
    def isActiveTurn(self):
        return get.unitManager().isCurrentTurnOfTeam(self.Team)
    
    def team(self):
        "This function only exists for interface homogeneity"
        return self.Team
    
    def isPlayer(self):
        return self.Team == 1
    
    def value(self) -> float:
        return sum([i.Stats.Value for i in self.Ships])
    
    def threat(self) -> float:
        return sum([i.Stats.Threat for i in self.Ships])
    
  #endregion manage ship list
  #region Turn and Selection
    def startTurn(self):
        if not self.Ships:
            self.destroy()
        self.ActiveTurn = True
        
        for i in self.Ships:
            if get.engine().CurrentlyInBattle: i.handleNewCombatTurn()
            else: i.handleNewCampaignTurn()
        if self.isSelected():
            self.displayStats(True)
        
        #self.healAtTurnStart()
    
    def endTurn(self): #TODO:OVERHAUL --- DOES NOT WORK CURRENTLY!
        self.ActiveTurn = False
    
    def isSelected(self): #TODO:OVERHAUL --- DOES NOT WORK CURRENTLY!
        return get.unitManager(self._IsFleet).isSelectedUnit(self)
    
    def select(self): #TODO:OVERHAUL --- DOES NOT WORK CURRENTLY!
        self.highlightRanges(True)
        self.displayStats(True)
    
    def unselect(self): #TODO:OVERHAUL --- DOES NOT WORK CURRENTLY!
        self.highlightRanges(False)
        self.displayStats(False)
    
  #endregion Turn and Selection
  #region Interaction
    def interactWith(self, hex:'HexBase._Hex', mustBePlayer:bool=True): #TODO:OVERHAUL --- DOES NOT WORK CURRENTLY!
        """
        Makes this unit interact with the hex. \n
        Returns `True` if the new hex should be selected after this interaction (eg in case this unit has moved to the hex or has joined a fleet in the hex due to this interaction) \n
        This method is only for player interactions!
        """
        "This method is only for player interactions!"
        if self.Destroyed or not self.isActiveTurn() or (mustBePlayer and not self.isPlayer()): return False
        if hex.fleet:
            if not hex.fleet() is self and not get.unitManager().isAllied(hex.fleet().Team, self.Team):
                base().taskMgr.add(self.attack(hex))
                #self.highlightRanges(True)
            else:
                self.lookAt(hex)
            return False
        else:
            return self.moveTo(hex)
    
  #endregion Interaction
  #region Movement
    def moveToHex(self, hex:'HexBase._Hex', animate=True): #TODO:OVERHAUL --- DOES NOT WORK CURRENTLY!
        self.Coordinates = hex.Coordinates
        if hex.fleet:
            raise HexBase.HexOccupiedException(hex)
        else:
            if animate and self.hex:
                self.Node.lookAt(hex.Pos)
                #time = min(6, np.sqrt(sum([i**2 for i in list(self.Node.getPos()-hex.Pos)])) )/6
                time = min(6, self.hex().distance(hex) )/6
                self.Node.posInterval(time, hex.Pos).start()
            else:
                self.Node.setPos(hex.Pos)
            hex.fleet = weakref.ref(self)
            if not hex.fleet: #TODO: We have a serious problem when this occurs. What do we do in that case?
                raise Exception("Could not assign unit to Hex")
            if hex.fleet() != self: #TODO: We have a serious problem when this occurs. What do we do in that case?
                raise Exception(f"Could not assign unit to Hex. (The Hex has a different fleet assigned that is named {hex.fleet()})")
            self.hex = weakref.ref(hex)
    
    def _navigable(self, hex:'HexBase._Hex'): #TODO:OVERHAUL --- DOES NOT WORK CURRENTLY!
        return (not bool(hex.fleet)) and hex.Navigable
    
    def _tileCost(self, hex:'HexBase._Hex'): #TODO:OVERHAUL --- DOES NOT WORK CURRENTLY!
        return 1
    
    def lookAt(self, hex:'HexBase._Hex'): #TODO:OVERHAUL --- DOES NOT WORK CURRENTLY!
        if self.MovementSequence and self.MovementSequence.isPlaying():
            self.MovementSequence.finish()
        lastAngle = self.Node.getHpr()[0]
        theta = np.arctan2(hex.Pos[0] - self.hex().Pos[0], self.hex().Pos[1] - hex.Pos[1])
        if (theta < 0.0):
            theta += 2*np.pi
        angle = np.rad2deg(theta) + 180
        #INVESTIGATE: Why do I need to add 180°? The formula above should be correct and the 180° should be wrong here but without adding them the object looks in the wrong direction...
        #       .lookAt makes the object look in the correct direction therefore the object itself is not modelled to look in the wrong direction.
        #       Furthermore I can pretty much rule out that the further processing of the angle is wrong since the 180° were necessary even before the processing was added.
        #       Thereby the formula must be mistaken, which, as mentioned, should be the correct formula... So where is the problem?!?
        angleBefore, angleAfter = self.improveRotation(lastAngle,angle)
        self.MovementSequence = self.Node.hprInterval(abs(angleBefore - angleAfter)/(360), (angleAfter,0,0), (angleBefore,0,0))
        self.MovementSequence.start()
        #CRITICAL: In order to not break other animations we must usually wait before other animations until this animation is completed. How can we do that!?!
        #       This will probably be necessary for other animations, too... For example a ship should only explode once a rocket has hit it - not when the rocket was fired by the other ship...
    
    def findPath(self,hex:'HexBase._Hex') -> typing.Tuple[typing.List['HexBase._Hex'],float]:
        "returns (path, cost)"
        return HexBase.findPath(self.hex(), hex, self._navigable, self._tileCost)
    
    def moveTo_AI(self, hex:'HexBase._Hex'):
        select = self.moveTo(hex)
        if select:
            hex.select(True)
    
    def moveTo(self, hex:'HexBase._Hex'): #TODO:OVERHAUL --- DOES NOT WORK CURRENTLY!
        if self.Destroyed or not self.isActiveTurn():
            return False
        if not self._navigable(hex):
            # The figure can not move to the hex but we can at least make it look at the hex
            self.lookAt(hex)
            return False
        else:
            path, cost = self.findPath(hex)
            if not path or cost > self.MovePoints:
                # The figure can not move to the hex but we can at least make it look at the hex
                self.lookAt(hex)
                #lastAngle = self.Node.getHpr()[0]
                #theta = np.arctan2(hex.Pos[0] - self.hex().Pos[0], self.hex().Pos[1] - hex.Pos[1])
                #if (theta < 0.0):
                #    theta += 2*np.pi
                #angle = np.rad2deg(theta) + 180
                ##INVESTIGATE: Why do I need to add 180°? The formula above should be correct and the 180° should be wrong here but whitout adding them the object looks in the wrong direction...
                ##       .lookAt makes the object look in the correct direction therefore the object itself is not modeled to look in the wrong direction.
                ##       Furthermore I can pretty much rule out that the further processing of the angle is wrong since the 180° were necessary even before the processing was added.
                ##       Thereby the formula must be mistaken, which, as mentioned, should be the correct formula... So where is the problem?!?
                #angleBefore, angleAfter = self.improveRotation(lastAngle,angle)
                #self.Node.hprInterval(abs(angleBefore - angleAfter)/(360), (angleAfter,0,0), (angleBefore,0,0)).start()
                return False
            else:
                if self.isSelected():
                    self.highlightRanges(False)
                    self.IsMoving = True
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
                self.hex().fleet = None
                hex.fleet = weakref.ref(self)
                self.hex = weakref.ref(hex)
                self.Coordinates = hex.Coordinates
                self.spendMovePoints(cost)
                #if self.isSelected():
                #    self.highlightRanges(True) # This is done in the unit manager since the previous hex will get de-highlighted after this method returns
                self.MovementSequence = seq
                if not hex.fleet: #TODO: We have a serious problem when this occurs. What do we do in that case?
                    raise Exception("Could not assign unit to Hex")
                if not hex.fleet() == self: #TODO: We have a serious problem when this occurs. What do we do in that case?
                    raise Exception("Could not assign unit to Hex")
                return self.isSelected()
    
    def moveClose(self, hex:'HexBase._Hex', distance:int = 3, tries:int = 8):
        """
        Tries to get within `distance` tiles of `hex` but will only try to navigate to `tries` random tiles within this distance.
        Returns a tuple of 2 bools. The first bool tells you if the fleet is within `distance` tiles and the second bool tells you if the fleet has moved.
        """
        if self.Destroyed or not self.isActiveTurn():
            return False, False
        distance, tries = int(distance), int(tries)
        startMovePoints = self.MovePoints
        #TODO: What if the fleet and the target hex are on 2 different sides of a wall? We need a method to figure out that distance and use that for the first check. Otherwise we will never get around that wall...
        #       But we should not count other fleets as part of a wall, otherwise we will run into problems with tight formations and cluttered maps...
        if self.hex().distance(hex)<=distance: return True, False # Are we already close enough?
        path, cost = self.findPath(hex)
        if path and cost <= self.MovePoints: # Can we just move to the hex?
            self.moveTo_AI(hex)
            return self.hex().distance(hex)<=distance, self.MovePoints<startMovePoints
        targetOptions = hex.getDisk(distance)
        path, cost = [], float("inf")
        newHex = hex
        for _ in range(tries):
            newHex = random.choice(targetOptions)
            path, cost = self.findPath(newHex)
            if path:
                break
        if not path: # Did we find a way to get Close?
            NC(4,f"{self.Name} @{self.hex().Coordinates} could not find a path near {hex.Coordinates}!",input=f"{distance = }\n{tries = }")
            return False, False
        else:
            if cost <= self.MovePoints: # Can we move to that close hex?
                self.moveTo_AI(newHex)
                return self.hex().distance(hex)<=distance, self.MovePoints<startMovePoints
            else: # Let's move closer to that close hex
                _, cost = self.findPath(path[int(self.MovePoints)-1])
                self.moveTo_AI(path[int(self.MovePoints)-1])
                return self.hex().distance(hex)<=distance, self.MovePoints<startMovePoints
    
    def improveRotation(self,c,t): #TODO:OVERHAUL --- DOES NOT WORK CURRENTLY!
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
    
    def moveToCoordinates(self,coordinates): #TODO:OVERHAUL --- DOES NOT WORK CURRENTLY!
        self.moveToHex(get.engine().getHex(coordinates))
    
    def getReachableHexes(self) -> typing.Set['HexBase._Hex']: #TODO:OVERHAUL --- DOES NOT WORK CURRENTLY!
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
            mPoints = self.MovePoints if self.ActiveTurn else self.MovePoints_max # To allow calculations while it's not this unit's turn we use the MovePoints_max then
            l: typing.Set['HexBase._Hex'] = set() # Using a set instead of a list is 5% faster... which is still not fast enough
            for i in self.hex().getDisk(mPoints): #FEATURE:MOVECOST: This does not take into account that hexes could have a negative movement point cost...
                #                                       Therefore we could miss some more distant tiles. But this method is already far too slow so we can not really afford to increase the radius of the disk...
                if not i in l:
                    path, cost = HexBase.findPath(self.hex(), i, self._navigable, self._tileCost)
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
            mPoints = self.MovePoints if self.ActiveTurn else self.MovePoints_max # To allow calculations while it's not this unit's turn we use the MovePoints_max then
            l: typing.Set['HexBase._Hex'] = set() # Using a set instead of a list is 5% faster... which is still not fast enough
            tl: typing.List[typing.Set['HexBase._Hex']] = [set([self.hex()]),]
            for i in range(math.floor(mPoints)):
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
    def highlightRanges(self, highlight=True): #TODO:OVERHAUL --- DOES NOT WORK CURRENTLY!
        """
        Highlights all hexes that are relevant (movementrange, weaponrange, etc). \n
        If `highlight = False` the highlighted hexes are instead un-highlighted.
        """
        #self.hex().grid().highlightHexes(clearFirst=True)
        self.hex().grid().clearAllHexHighlighting(forceAll=get.window().Menu.HighlightOptionsWidget.RedrawEntireGridWhenHighlighting())
        if highlight:
            self.highlightMovementRange(highlight, clearFirst=False)
    
    def highlightMovementRange(self, highlight=True, clearFirst=True): #TODO:OVERHAUL --- DOES NOT WORK CURRENTLY!
        """
        Highlights all hexes that can be reached with the current movement points. \n
        If `highlight = False` the highlighted hexes are instead un-highlighted.
        """
        if highlight:
            self.hex().grid().highlightHexes(self.getReachableHexes(), HexBase._Hex.COLOUR_REACHABLE, False, False, clearFirst=clearFirst)
        else:
            self.hex().grid().highlightHexes(self.getReachableHexes(), False, False, False, clearFirst=True)
        ##TODO: TEMPORARY
        #for i in self.getReachableHexes():
        #    i.highlight(highlight)
        ##TODO: TEMPORARY
  #endregion Highlighting
  #region model
    def arrangeShips(self): #TODO: OVERHAUL
        # https://github.com/topics/packing-algorithm?o=desc&s=forks
        # https://github.com/jerry800416/3D-bin-packing
        num = len(self.Ships)
        if not num:
            self.destroy()
            return
        for i,s in enumerate(self.Ships):
            s.Model.centreModel()
        if num == 1:
            self.Ships[0].setPos(0,0,0)
        else:
            maxSize = max([i.Model.Model.getBounds().getRadius() for i in self.Ships])
            #maxSize = [0,0,0]
            #for i in self.Ships:
            #    bounds = i.Model.Model.getTightBounds()
            #    bounds = (bounds[1]-bounds[0])
            #    maxSize = [max(maxSize[i],bounds[i]) for i in range(3)]
            for i,s in enumerate(self.Ships): #TODO: Invert the order in which the ships are displayed so that the first one in the list is the leftmost and so on
                s.Model.resetModel()
                s.setPos((1/num)*((num-1)/2-i),0,0)
                s.Model.setScale((0.8/num)/(s.Model.Model.getBounds().getRadius()))
  #endregion model
    
  #endregion Detection #TODO: Should we distinguish between campaign and battle sensors? These are different scales but I can't think of a good gameplay reason...
    def getSensorRanges(self) -> typing.Tuple[float,float,float,float,float]: #TODO: The sensors of the ships in the fleet should enhance each other
        """
        Sensor ranges: no resolution, low resolution, medium resolution, high resolution, perfect resolution \n
        Note: no resolution is always infinite and only exist so that the indices match with the information levels 0='Not visible' to 4='Fully visible' \n
        """
        ranges = np.asarray([i.Stats.SensorRanges for i in self.Ships])
        return float("inf"), max(ranges[:,1]), max(ranges[:,2]), max(ranges[:,3]), max(ranges[:,4])
        
    def getSensorRanges_Int(self) -> typing.Tuple[int,int,int,int,int]: #TODO: The sensors of the ships in the fleet should enhance each other
        """
        Sensor ranges: no resolution, low resolution, medium resolution, high resolution, perfect resolution \n
        But as integers \n
        Note: no resolution is always 10000 and only exist so that the indices match with the information levels 0='Not visible' to 4='Fully visible' \n
        """
        ranges = self.getSensorRanges()
        return int(10000), int(ranges[1]), int(ranges[2]), int(ranges[3]), int(ranges[4])
    
    def detectEnemies(self) -> typing.List[typing.Tuple[int,'FleetBase']]:
        "Returns a list of tuples with the detection level of a fleet and the fleet in question. Only considers hostile fleets"
        ranges = list(self.getSensorRanges_Int())+[0,]
        fleets:typing.List[typing.Tuple[int,'FleetBase']] = []
        for i,r in enumerate(ranges):
            if i == 0 or i == 5: continue
            potentialFleets = [h.fleet() for h in self.hex().getDisk(r,ranges[i+1]) if h.fleet]
            fleets += [(f.detectCheck(i), f) for f in potentialFleets if f.detectCheck(i) and not get.unitManager().isAllied(self.Team,f.Team)]
        return fleets
    
    def findClosestEnemy(self) -> typing.Union['FleetBase',bool]:
        "Returns the closest enemy fleet or False if none is detected"
        detectedEnemies = []
        for team in get.unitManager().getAllies(self.Team):
            for fleet in get.unitManager().Teams[team]:
                detectedEnemies += fleet.detectEnemies()
        if not detectedEnemies:
            return False
        f = min([(self.hex().distance(f[1].hex()), f[1]) for f in detectedEnemies], key=lambda i:i[0])[1]
        return f
    
    def detectCheck(self, level:int) -> int:
        """Returns which information level a scan at `level` can procure. 0 means that it can not detect this fleet at all and 4 means that all information are visible"""
        #TODO: make some checks for the ships stealth capabilities
        return level
  #region Detection
    
  #region overwrite
    async def attack(self, target: 'HexBase._Hex'):
        raise NotImplementedError("attack is only implemented for fleets and flotillas but not for the base fleet. How was a base fleet even created!?")
    
    def displayStats(self, display=True, forceRebuild=False):
        raise NotImplementedError("displayStats is only implemented for fleets and flotillas but not for the base fleet. How was a base fleet even created!?")
    
    def getAttackableHexes(self, _hex:'HexBase._Hex'=None) -> typing.List['HexBase._Hex']:
        raise NotImplementedError("getAttackableHexes is only implemented for fleets and flotillas but not for the base fleet. How was a base fleet even created!?")
  #endregion overwrite

class Fleet(FleetBase):
    """
    A fleet on the strategic map. \n
    Every ship on the strategic map is part of a fleet. \n
    The fleet object coordinates the UI creation, the movement, and all other interactions of all its ships.
    """
    def __init__(self, team = 1) -> None:
        super().__init__(strategic=True, team=team)
    
    @property
    def MovePoints(self) -> float:
        return min([i.Stats.Movement_FTL[0] for i in self.Ships])
    
    def spendMovePoints(self, value:float):
        for i in self.Ships:
            i.Stats.spendMovePoints_FTL(value)
            i.updateInterface()
    
    @property
    def MovePoints_max(self) -> float:
        return min([i.Stats.Movement_FTL[1] for i in self.Ships])
    
    def battleEnded(self) -> float:
        """
        Handles the End of the Battle for this Fleet. \n
        This Includes removing all destroyed ships and re-parenting all other ships from their flotillas back to this fleet. \n
        If all ships were destroyed this fleet will delete itself. \n
        Returns the salvage Value of all destroyed ships.
        """
        print("Battle Ended for", self.Name)
        print("Ships in fleet before cleanup:", len(self.Ships))
        ships_to_be_removed:typing.List['ShipBase.ShipBase'] = []
        for ship in self.Ships:
            if ship.Destroyed:
                ships_to_be_removed.append(ship)
        salvageValue = 0
        for ship in ships_to_be_removed:
            salvageValue += ship.Stats.Value/5
            self.removeShip(ship,arrange=False)
        print("Ships in fleet after cleanup:", len(self.Ships))
        if self.Destroyed:
            return salvageValue
        else:
            for ship in self.Ships:
                ship.reparentTo(self)
            self.arrangeShips()
        return salvageValue
    
  #region Combat Offensive
    async def attack(self, target: 'HexBase._Hex', orders:AI_Base.Orders = None, performOutOfTurn = False):
        if self.Destroyed or (not performOutOfTurn and not self.isActiveTurn()):
            return False
        if self.MovementSequence and self.MovementSequence.isPlaying():
            try: await self.MovementSequence
            except: self.MovementSequence.finish()
        self.lookAt(target)
        if self.MovementSequence and self.MovementSequence.isPlaying():
            try: await self.MovementSequence
            except: self.MovementSequence.finish()
        involvedFleets = self.getInvolvedFleetsForPotentialBattle(self.hex(), target)
        get.engine().startBattleScene(involvedFleets)
    
    def getInvolvedFleetsForPotentialBattle(self, hex:'HexBase._Hex', target:'HexBase._Hex') -> 'list[Fleet]':
        involvedFleets = [self,target.fleet()]
        for i in hex.getNeighbour()+target.getNeighbour():
            if i.fleet:
                if not i.fleet() in involvedFleets:
                    involvedFleets.append(i.fleet())
        return involvedFleets
    
    def getAttackableHexes(self, _hex:'HexBase._Hex'=None) -> typing.List['HexBase._Hex']:
        if not _hex:
            _hex = self.hex()
        l: typing.Set['HexBase._Hex'] = set()
        for i in _hex.getDisk(1):
            if i.fleet:
                if not get.unitManager().isAllied(self.Team, i.fleet().Team):
                    l.add(i)
        return list(l)
  #endregion Combat Offensive
  #region Display Information
    def displayStats(self, display=True, forceRebuild=False): #TODO: Overhaul this! The displayed information should not be the combat interface but the campaign interface!
        if display:
            if forceRebuild or not self.Widget:
                get.window().UnitStatDisplay.addWidget(self.getInterface())
            else:
                for i in self.Ships:
                    i.updateInterface()
            text = textwrap.dedent(f"""
            Name: {self.Name}
            Team: {self.Team}
            Positions: {self.hex().Coordinates}
            Movement Points: {self.MovePoints}/{self.MovePoints_max}
            """)
            # Hull HP: {[f"{i.Stats.HP_Hull}/{i.Stats.HP_Hull_max}" for i in self.Ships]}
            # Shield HP: {[f"{i.Stats.HP_Shields}/{i.Stats.HP_Shields_max}" for i in self.Ships]}
            #Hull: {self.HP_Hull}/{self.HP_Hull_max} (+{self.HP_Hull_Regeneration} per turn (halved if the ship took a single hit that dealt at least {self.NoticeableDamage} damage last turn))
            #Shields: {self.HP_Shields}/{self.HP_Shields_max} (+{self.HP_Shields_Regeneration} per turn (halved if the ship took a single hit that dealt at least {self.NoticeableDamage} damage last turn))
            #get.window().UnitStatDisplay.Text.setText(text)
            self.Label.setText(text)
        else:
            #get.window().UnitStatDisplay.Text.setText("No unit selected")
            get.window().UnitStatDisplay.removeWidget(self.Widget)
            self.Widget = None
    
    def getInterface(self): #TODO: Overhaul this! The displayed information should not be the combat interface but the campaign interface!
        self.Widget = AGeWidgets.TightGridFrame()
        self.Label = self.Widget.addWidget(QtWidgets.QLabel(self.Widget))
        for i in self.Ships:
            self.Widget.addWidget(i.getQuickView())
        return self.Widget
    
  #endregion Display Information
  #region Save/Load
    def tocode_AGeLib(self, name="", indent=0, indentstr="    ", ignoreNotImplemented = False) -> typing.Tuple[str,dict]:
        ret, imp = "", {}
        # ret is the ship data that calls a function which is stored as an entry in imp which constructs the ship
        # Thus, ret, when executed, will be this ship. This can then be nested in a list so that we can reproduce entire fleets.
        imp.update(IMP_FLEET)
        ret = indentstr*indent
        if name:
            ret += name + " = "
        ret += f"createFleet(\n"
        r,i = AGeToPy._topy(self.tocode_AGeLib_GetDict(), indent=indent+2, indentstr=indentstr, ignoreNotImplemented=ignoreNotImplemented)
        ret += f"{r}\n{indentstr*(indent+1)})"
        imp.update(i)
        return ret, imp
    
    def tocode_AGeLib_GetDict(self) -> dict:
        d = {
            "Name" : self.Name ,
            "Team" : self.Team ,
            "Ships" : self.Ships ,
            "Coordinates" : self.hex().Coordinates ,
        }
        get.shipClasses() # This is called to ensure that all custom ship have the INTERNAL_NAME set
        if hasattr(self, "INTERNAL_NAME"):
            d["INTERNAL_NAME"] = self.INTERNAL_NAME
        return d
  #endregion Save/Load


class Flotilla(FleetBase):
    """
    A flotilla on the tactical map. \n
    Every ship on the tactical map is part of a flotilla, therefore one-ship-flotillas are quite common. \n
    The flotilla object coordinates the UI creation, the movement, and all other interactions of all its ships.
    """
    def __init__(self, team = 1) -> None:
        super().__init__(strategic=False, team=team)
    
    @property
    def MovePoints(self) -> float:
        return min([i.Stats.Movement_Sublight[0] for i in self.Ships])
    
    def spendMovePoints(self, value:float):
        for i in self.Ships:
            i.Stats.spendMovePoints_Sublight(value)
            i.updateInterface()
    
    @property
    def MovePoints_max(self) -> float:
        return min([i.Stats.Movement_Sublight[1] for i in self.Ships])
    
  #region Combat Offensive
    async def attack(self, target: 'HexBase._Hex', orders:AI_Base.Orders = None):
        if self.Destroyed or not self.isActiveTurn():
            return False
        if self.MovementSequence and self.MovementSequence.isPlaying():
            try: await self.MovementSequence
            except: self.MovementSequence.finish()
        self.lookAt(target)
        if self.MovementSequence and self.MovementSequence.isPlaying():
            try: await self.MovementSequence
            except: self.MovementSequence.finish()
        for i in self.Ships:
            if not i.Destroyed:
                i.attack(target)
        if self.isSelected():
            # Re-highlight everything in case the target was destroyed or moved by the attack or a ship with an inhibitor was destroyed
            self.highlightRanges()
    
    def getHexesInAttackRange(self, _hex:'HexBase._Hex'=None) -> typing.List['HexBase._Hex']:
        if not _hex:
            _hex = self.hex()
        maxRanges = []
        minRanges = []
        for ship in self.Ships:
            for weapon in ship.Weapons:
                if hasattr(weapon,"Range"): maxRanges.append(weapon.Range)
                if hasattr(weapon,"MinimalRange"): minRanges.append(weapon.MinimalRange)
        if maxRanges: maxRange = int(max(maxRanges))
        else: maxRange = 1
        if minRanges: minRange = int(max(minRanges))
        else: minRange = 1
        return _hex.getDisk(minRange, maxRange)
    
    def getAttackRange(self) -> typing.Tuple[int,int,int]:
        "returns shortest, median, and longest weapon range"
        ranges = []
        for ship in self.Ships:
            for weapon in ship.Weapons:
                ranges.append(weapon.Range)
        return int(min(ranges)), int(np.median(ranges)), int(max(ranges))
        # min([min([j.Range for j in i.Weapons]) for i in self.Ships])
    
    def getAttackableHexes(self, _hex:'HexBase._Hex'=None) -> typing.List['HexBase._Hex']:
        if not _hex:
            _hex = self.hex()
        l: typing.Set['HexBase._Hex'] = set()
        for i in self.getHexesInAttackRange(_hex):
            if i.fleet:
                if not get.unitManager().isAllied(self.Team, i.fleet().Team):
                    l.add(i)
        return list(l)
  #endregion Combat Offensive
    
  #region Display Information
    def displayStats(self, display=True, forceRebuild=False):
        if display:
            if forceRebuild or not self.Widget:
                get.window().UnitStatDisplay.addWidget(self.getInterface())
            else:
                for i in self.Ships:
                    i.updateInterface()
            text = textwrap.dedent(f"""
            Name: {self.Name}
            Team: {self.Team}
            Positions: {self.hex().Coordinates}
            Movement Points: {self.MovePoints}/{self.MovePoints_max}
            """)
            # Hull HP: {[f"{i.Stats.HP_Hull}/{i.Stats.HP_Hull_max}" for i in self.Ships]}
            # Shield HP: {[f"{i.Stats.HP_Shields}/{i.Stats.HP_Shields_max}" for i in self.Ships]}
            #Hull: {self.HP_Hull}/{self.HP_Hull_max} (+{self.HP_Hull_Regeneration} per turn (halved if the ship took a single hit that dealt at least {self.NoticeableDamage} damage last turn))
            #Shields: {self.HP_Shields}/{self.HP_Shields_max} (+{self.HP_Shields_Regeneration} per turn (halved if the ship took a single hit that dealt at least {self.NoticeableDamage} damage last turn))
            #get.window().UnitStatDisplay.Text.setText(text)
            self.Label.setText(text)
        else:
            #get.window().UnitStatDisplay.Text.setText("No unit selected")
            get.window().UnitStatDisplay.removeWidget(self.Widget)
            self.Widget = None
    
    def getInterface(self):
        self.Widget = AGeWidgets.TightGridFrame()
        self.Label = self.Widget.addWidget(QtWidgets.QLabel(self.Widget))
        for i in self.Ships:
            self.Widget.addWidget(i.getQuickView())
        return self.Widget
    
  #endregion Display Information
  #region Highlighting
    def highlightRanges(self, highlight=True): #TODO:OVERHAUL --- DOES NOT WORK CURRENTLY!
        """
        Highlights all hexes that are relevant (movementrange, weaponrange, etc). \n
        If `highlight = False` the highlighted hexes are instead un-highlighted.
        """
        super().highlightRanges(highlight)
        if highlight and get.window().Menu.HighlightOptionsWidget.HighlightWeaponRange():
            self.highlightAttackRange(highlight, clearFirst=False)
    
    def highlightAttackRange(self, highlight=True, clearFirst=True): #TODO:OVERHAUL --- DOES NOT WORK CURRENTLY!
        """
        Highlights all hexes that can be reached with the current movement points. \n
        If `highlight = False` the highlighted hexes are instead un-highlighted.
        """
        if highlight:
            self.hex().grid().highlightHexes(self.getHexesInAttackRange(), False, HexBase._Hex.COLOUR_ATTACKABLE, False, clearFirst=clearFirst)
        else:
            self.hex().grid().highlightHexes(self.getHexesInAttackRange(), False, False, False, clearFirst=True)
  #endregion Highlighting
