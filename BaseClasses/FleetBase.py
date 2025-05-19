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
    from Economy import EconomyManager
    from GUI import BaseInfoWidgets
from BaseClasses import get
from BaseClasses import HexBase
from BaseClasses import AI_Base
from BaseClasses import AI_Fleet
from Economy import Resources

IMP_FLEETBASE = [("PSN get","from BaseClasses import get"),("PSN FleetBase","from BaseClasses import FleetBase")]
IMP_FLEET = IMP_FLEETBASE + [("PSN FleetConstructor","""
def createFleet(d:dict):
    fleet = FleetBase.Fleet(d["Team"])
    fleet.Name = d["Name"]
    fleet.addShips(d["Ships"])
    fleet.moveToHex(get.hexGrid().getHex(d["Coordinates"]), False)
    
    return fleet
""")]

class ShipList(typing.List['ShipBase.ShipBase']):
    pass

class TeamRing():
    def __init__(self, fleet, team, node) -> None:
        self.fleet:'weakref.ref[FleetBase]' = weakref.ref(fleet)
        self.TeamRing:p3dc.NodePath = ape.loadModel("Models/Simple Geometry/hexagonRing.ply")
        self.TeamRing.reparentTo(node)
        self.TeamRing.setColor(ape.colour(App().Theme["Star Nomads"][f"Team {team}"]))
        self.TeamRing.setScale(0.9)
        self.TeamRing.setPos(p3dc.LPoint3((0,0,-0.02)))
        self.C_ColourChangedConnection = App().S_ColourChanged.connect(self.recolour)
        if team == -1: self.hide()
        self.hide() #TODO: This is temporary to see if the team colours on the ships is good enough
    
    def destroy(self):
        if self.C_ColourChangedConnection:
            App().S_ColourChanged.disconnect(self.C_ColourChangedConnection)
            self.C_ColourChangedConnection = None
        if self.TeamRing:
            self.TeamRing.removeNode()
            self.TeamRing = None
    
    def hide(self):
        self.TeamRing.hide()
    
    def show(self):
        self.TeamRing.show()
    
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
        
        from Economy import EconomyManager
        self.EconomyManager = EconomyManager.FleetEconomyManager(self)
        
        self.Node = p3dc.NodePath(p3dc.PandaNode(f"Central node of fleet {id(self)}"))
        #self.Node.reparentTo(render())
        #self.Node.reparentTo(get.engine().getSceneRootNode())
        self.Node.reparentTo(get.engine().getScene(self._IsFleet).HexGrid.Root)
        
        self.TeamRing = TeamRing(self, team, self.Node)
        
        self.MovementSequence:p3ddSequence = None
        
        self.Name = "name"
        self.Team = team
        self.Destroyed = False
        self.IsMovingFrom:'typing.Union[bool,tuple[int,int]]' = False # Used to suppress clearing of UI when moving fleets
        self.Hidden = False
        
        self.widget: 'weakref.ref[BaseInfoWidgets.FleetStats]' = None
        self.hex: 'weakref.ref[HexBase._Hex]' = None
        get.unitManager(self._IsFleet).Teams[self.Team].append(self)
        
        #TEMPORARY
        self.ActiveTurn = 1 == 1
    
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
            self.hex().removeContent(self)
            self.hex = None
        if self.TeamRing:
            self.TeamRing.destroy()
            self.TeamRing = None
        if self.Node:
            self.Node.removeNode()
            self.Node = None
        get.window().HexInfoDisplay.updateInfo()
    
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
    
    @property
    def ResourceManager(self) -> 'EconomyManager.FleetResourceManager':
        return self.EconomyManager.ResourceManager
    
    @property
    def TeamName(self) -> str:
        return get.unitManager().Teams[self.Team].name()
  #endregion init and destroy
  #region manage ship list
    def _addShip(self, ship:'ShipBase.ShipBase'):
        if self.isBackgroundObject() and not ship.IsBackgroundObject and self.hex:
            if self.hex().fleet:
                if self.hex().fleet() is not self:
                    NC(1,"A ship that is not a background object was added to a fleet which is a background object but is on a tile which already has a foreground-fleet."
                        "Therefore this fleet can not be converted into a foreground fleet. This might lead to many problems...",
                        tb=True, input=f"This Fleet: {self.Name}\nOther Fleet: {self.hex().fleet().Name}\nShip: {ship.Name}")
            else:
                self.hex().removeContent(self)
                self.hex().fleet = weakref.ref(self)
        if not ship in self.Ships:
            self.Ships.append(ship)
        ship.reparentTo(self)
    
    def addShip(self, ship:'ShipBase.ShipBase'):
        self._addShip(ship)
        self.arrangeShips()
        self.updateInterface()
    
    def addShips(self, ships:typing.List['ShipBase.ShipBase']):
        for ship in ships:
            self._addShip(ship)
        self.arrangeShips()
        self.updateInterface()
    
    def removeShip(self, ship:'ShipBase.ShipBase', arrange:bool=True, notifyIfNotContained:bool=True) -> bool:
        """
        Remove `ship` from this fleet and rearranges the ship positions if `arrange`. \n
        Returns True if the Fleet still exists afterwards, otherwise returns False
        """
        if ship in self.Ships:
            self.Ships.remove(ship)
            self.updateInterface()
            if self.Ships and arrange: self.arrangeShips()
        else:
            if notifyIfNotContained: NC(2,f"SHIP WAS NOT IN SHIP LIST\nFleet name: {self.Name}\nShip name: {ship.Name}", tb=True) #TODO: give more info
        if not self.Ships:
            self.destroy()
            if get.engine().DebugPrintsEnabled:
                if arrange: print(f"{self.Name} was destroyed!")
                else: print(f"{self.Name} was emptied")
            return False
        else:
            #TODO: check if fleet is now a background fleet and move it into the background if appropriate
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
        return sum([i.Stats.Value for i in self.Ships]) if self.Ships else 0
    
    def threat(self) -> float:
        return sum([i.Stats.Threat for i in self.Ships]) if self.Ships else 0
    
    def isBackgroundObject(self):
        if not (self.Ships): return False
        return all([i.IsBackgroundObject for i in self.Ships])
    
    def isBlockingTilePartially(self):
        return any([i.IsBlockingTilePartially for i in self.Ships])
    
    def isBlockingTileCompletely(self):
        return any([i.IsBlockingTileCompletely for i in self.Ships])
    
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
            pass #self.displayStats(True)
        
        #self.healAtTurnStart()
    
    def endTurn(self):
        self.ActiveTurn = False
    
    def isSelected(self):
        return get.unitManager(self._IsFleet).isSelectedUnit(self)
    
    def select(self):
        self.highlightRanges(True)
        #self.displayStats(True)
        self.clearIsMovingFlag()
    
    def unselect(self):
        self.highlightRanges(False)
        #self.displayStats(False)
        self.clearIsMovingFlag()
    
  #endregion Turn and Selection
  #region Interaction
    def interactWith(self, hex:'HexBase._Hex', mustBePlayer:bool=True):
        """
        Makes this unit interact with the hex. \n
        Returns `True` if the new hex should be selected after this interaction (eg in case this unit has moved to the hex or has joined a fleet in the hex due to this interaction) \n
        This method is only for player interactions!
        """
        "This method is only for player interactions!"
        if self.Destroyed or not self.isActiveTurn() or (mustBePlayer and not self.isPlayer()): return False
        if hex.fleet:
            if not hex.fleet() is self and get.unitManager().isHostile(hex.fleet().Team, self.Team):
                base().taskMgr.add(self.attack(hex))
                #self.highlightRanges(True)
            else:
                self.lookAt(hex)
            return False
        else:
            return self.moveTo(hex)
    
  #endregion Interaction
  #region Movement
    def moveToHex(self, hex:'HexBase._Hex', animate=True):
        if self.isBackgroundObject():
            self.Coordinates = hex.Coordinates
            if animate and self.hex:
                self.Node.lookAt(hex.Pos)
                #time = min(6, np.sqrt(sum([i**2 for i in list(self.Node.getPos()-hex.Pos)])) )/6
                time = min(6, self.hex().distance(hex) )/6
                self.Node.posInterval(time, hex.Pos).start()
            else:
                self.Node.setPos(hex.Pos)
            hex.addContent(self)
            #if not hex.fleet: #TODO: We have a serious problem when this occurs. What do we do in that case?
            #    raise Exception("Could not assign unit to Hex")
            #if hex.fleet() != self: #TODO: We have a serious problem when this occurs. What do we do in that case?
            #    raise Exception(f"Could not assign unit to Hex. (The Hex has a different fleet assigned that is named {hex.fleet()})")
            if self.hex: self.hex().content.remove(self)
            self.hex = weakref.ref(hex)
        elif hex.fleet:
            if hex.fleet() is not self:
                raise HexBase.HexOccupiedException(hex)
        else:
            self.Coordinates = hex.Coordinates
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
            if self.hex: self.hex().fleet = None
            self.hex = weakref.ref(hex)
    
    def _navigable(self, hex:'HexBase._Hex'):
        #if self.isBackgroundObject(): return True
        #return (not bool(hex.fleet)) and hex.Navigable
        return hex.isNavigable(self.isBlockingTilePartially(), self.isBlockingTileCompletely(), self.isBackgroundObject())
    
    def _tileCost(self, hex:'HexBase._Hex'):
        #TODO: Implement tile cost function
        #FEATURE:MOVECOST: Implement tile cost function
        from BaseClasses import BaseModules
        cost_modifier = 1
        for c in hex.content:
            try:
                if c:
                    for ship in c().Ships:
                        for module in ship.Modules:
                            if isinstance(module, BaseModules.TileCostModifier):
                                cost_modifier *= module.getTileCostMultiplier(self)
            except:
                hex.content.remove(c)
        try:
            if hex.fleet:
                for ship in hex.fleet().Ships:
                    for module in ship.Modules:
                        if isinstance(module, BaseModules.TileCostModifier):
                            cost_modifier *= module.getTileCostMultiplier(self)
        except:
            NC(1, exc=True)
        return cost_modifier
    
    def lookAt(self, hex:'HexBase._Hex'):
        #if not self.hex: return
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
        #TODO: In order to not break other animations we must usually wait before other animations until this animation is completed. How can we do that!?!
        #       This will probably be necessary for other animations, too... For example a ship should only explode once a rocket has hit it - not when the rocket was fired by the other ship...
        #     This is already sorta done by the `self.MovementSequence.finish()` in the beginning of this function but there needs to ba a more reliable system to handle animations and interactions
    
    def findPath(self,hex:'HexBase._Hex') -> typing.Tuple[typing.List['HexBase._Hex'],float]:
        "returns (path, cost)"
        return HexBase.findPath(self.hex(), hex, self._navigable, self._tileCost)
    
    def moveTo_AI(self, hex:'HexBase._Hex'):
        select = self.moveTo(hex)
        self.handleSensors() # To ensure the new hex does not get selected if enemies move out of sensor range
        if select and not self.Hidden:
            hex.select(True)
        if self.isSelected() and self.Hidden: # To clear the selection of the fleet
            get.unitManager().unselectAll()
    
    def moveTo(self, hex:'HexBase._Hex'):
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
                    self.IsMovingFrom = self.hex().Coordinates
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
                
                from direct.interval.FunctionInterval import Func
                seq.append(Func(self.clearIsMovingFlag))
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
    
    def clearIsMovingFlag(self):
        #NOTE: The IsMovingFrom flag is cleared in BaseInfoWidgets.HexInfoDisplay._addNew
        #      All other calls to clearIsMovingFlag are merely backups for special situations
        self.IsMovingFrom = False
    
    def moveClose(self, hex:'HexBase._Hex', distance:int = 3, tries:int = 8):
        """
        Tries to get within `distance` tiles of `hex` but will only try to navigate to `tries` random tiles within this distance.
        Returns a tuple of 2 bools. The first bool tells you if the fleet is within `distance` tiles and the second bool tells you if the fleet has moved.
        """
        if self.Destroyed or not self.isActiveTurn(): # or not self.hex:
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
        self.moveToHex(get.engine().getHex(coordinates))
    
    def getReachableHexes(self) -> typing.Set['HexBase._Hex']:
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
        # Variant 6:
        #    Ask that newfangled ChatGPT thingy, which chose to implement Dijkstra
        Variant = 6
        
        if Variant == 1: #Too slow...
            t1 = time.time()
            ####
            mPoints = self.MovePoints if self.ActiveTurn else self.MovePoints_max # To allow calculations while it's not this unit's turn we use the MovePoints_max then
            l: typing.Set['HexBase._Hex'] = set() # Using a set instead of a list is 5% faster... which is still not fast enough
            for i in self.hex().getDisk(math.floor(mPoints)): #NOTE:MOVECOST: This does not take into account that hexes could have a negative movement point cost...
                #                                       Therefore we could miss some more distant tiles. But this method is already far too slow so we can not really afford to increase the radius of the disk...
                if not i in l:
                    path, cost = HexBase.findPath(self.hex(), i, self._navigable, self._tileCost)
                    if path:
                        if cost <= mPoints:
                            l.update(path)
                        #else:
                        #    l.update(path[:math.floor(mPoints)])
            ####
            if get.engine().DebugPrintsEnabled: print("list",time.time()-t1)
            return l
        if Variant == 2:
            pass # https://www.reddit.com/r/gamemaker/comments/1eido8/mp_grid_for_tactics_grid_movement_highlights/
        if Variant == 3:
            pass
        if Variant == 4: #NOTE:MOVECOST: This does not take into account different tile movement cost
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
        if Variant == 5:
            pass
        if Variant == 6:
            from heapq import heappush, heappop
            mPoints = self.MovePoints if self.ActiveTurn else self.MovePoints_max  # Use max points if not the unit's turn
            start_hex = self.hex()
            reachable_hexes: typing.Set['HexBase._Hex'] = set()
            open_set = [(0, start_hex)]  # Priority queue: (current_cost, hex)
            visited = {}  # Dictionary to store the minimum cost to reach each hex
            
            while open_set:
                current_cost, current_hex = heappop(open_set)
                
                # Skip if we've already visited this hex with a lower cost
                if current_hex in visited and visited[current_hex] <= current_cost:
                    continue
                
                # Mark this hex as visited with the current cost
                visited[current_hex] = current_cost
                reachable_hexes.add(current_hex)
                
                # Explore neighbors
                for neighbour in current_hex.getNeighbour():
                    if not self._navigable(neighbour):
                        continue
                    
                    # Calculate the cost to move to the neighbour
                    move_cost = self._tileCost(neighbour)
                    new_cost = current_cost + move_cost
                    
                    # If the new cost exceeds movement points, skip this neighbour
                    if new_cost > mPoints:
                        continue
                    
                    # Add the neighbour to the open set for further exploration
                    heappush(open_set, (new_cost, neighbour))
            reachable_hexes.remove(self.hex())
            return reachable_hexes
    
    
  #endregion Movement
  #region Highlighting
    def highlightRanges(self, highlight=True):
        """
        Highlights all hexes that are relevant (movementrange, weaponrange, etc). \n
        If `highlight = False` the highlighted hexes are instead un-highlighted.
        """
        if self.Destroyed or not self.hex: return
        #self.hex().grid().highlightHexes(clearFirst=True)
        self.hex().grid().clearAllHexHighlighting(forceAll=get.menu().GraphicsOptionsWidget.RedrawEntireGridWhenHighlighting())
        if highlight and not self.Hidden:
            self.highlightMovementRange(highlight, clearFirst=False)
        self.handleSensors()
    
    def highlightMovementRange(self, highlight=True, clearFirst=True):
        """
        Highlights all hexes that can be reached with the current movement points. \n
        If `highlight = False` the highlighted hexes are instead un-highlighted.
        """
        if self.Destroyed or not self.hex: return
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
        massOfFleet = False
        rootFac = 2#3 #REMINDER: Might want to set this to the realistic 3 in the future
        num = len(self.Ships)
        if not num:
            self.destroy()
            return
        for i,s in enumerate(self.Ships):
            s.Model.centreModel()
        if num == 1: # Case for only one ship
            s = self.Ships[0]
            if self.Team > 0 and not massOfFleet:
                #REMINDER: Might want to use ship volume instead of merely ship length for all these calculations
                maxMass = max([max(((j.Stats.Mass,j) for j in s), default=(0,None), key=lambda a:a[0]) for s in [i.Ships for i in get.unitManager() if i.Team > 0]], default=(0,None), key=lambda a:a[0]) # mass of the heaviest ship on the map
                maxMassCRoot = pow(maxMass[0],1/rootFac)/maxMass[1].Model.LengthFactor
                s.Model.resetModel()
                s.Model.setScale((1.5/3)/(s.Model.Model.getBounds().getRadius())*pow(s.Stats.Mass,1/rootFac)/maxMassCRoot/s.Model.LengthFactor)
                s.Model._centreModel()
                s.setPos(0,0,0)
                #MAYBE: If the ship is a Background Object, maybe it would be good to lower the position to ensure that fleets are better visible when occupying the same tile (so setPos(0,0,-1) or something like that)
            else:
                s.setPos(0,0,0)
                #MAYBE: If the ship is a Background Object, maybe it would be good to lower the position to ensure that fleets are better visible when occupying the same tile (so setPos(0,0,-1) or something like that)
        else: # Case for fleets with multiple ships
            #maxSize = max([i.Model.Model.getBounds().getRadius() for i in self.Ships])
            #maxSize = [0,0,0]
            #for i in self.Ships:
            #    bounds = i.Model.Model.getTightBounds()
            #    bounds = (bounds[1]-bounds[0])
            #    maxSize = [max(maxSize[i],bounds[i]) for i in range(3)]
            
            #REMINDER: Might want to use ship volume instead of merely ship length for all these calculations
            
            if massOfFleet:
                maxMass = max([(s.Stats.Mass, s) for s in self.Ships], key=lambda a:a[0])
            else:
                maxMass = max([max(((j.Stats.Mass,j) for j in s), default=(0,None), key=lambda a:a[0]) for s in [i.Ships for i in get.unitManager() if i.Team > 0]], default=(0,None), key=lambda a:a[0]) # mass of the heaviest ship
            
            maxMassCRoot = pow(maxMass[0],1/rootFac)/maxMass[1].Model.LengthFactor
            for i,s in reversed(list(enumerate(self.Ships))):
                s.Model.resetModel()
                s.Model.setScale((1.5/max(num,3))/(s.Model.Model.getBounds().getRadius())*pow(s.Stats.Mass,1/rootFac)/maxMassCRoot/s.Model.LengthFactor)
                s.Model._centreModel()
                s.setPos((1/num)*((num-1)/2-i),0,0) #REMINDER: Might want to change this to set the spacing relative to ship width to ensure that small ships are tighter/get less space than large ships in fleets
                #MAYBE: If the ship is a Background Object, maybe it would be good to lower the position to ensure that fleets are better visible when occupying the same tile (so setPos((1/num)*((num-1)/2-i),0,-1) or something like that)
  #endregion model
    
  #region Detection #TODO: Should we distinguish between campaign and battle sensors? These are different scales but I can't think of a good gameplay reason...
    def getSensorRanges(self) -> typing.Tuple[float,float,float,float,float]: #TODO: The sensors of the ships in the fleet should enhance each other
        """
        Sensor ranges: no resolution, low resolution, medium resolution, high resolution, perfect resolution \n
        Note: no resolution is always infinite and only exist so that the indices match with the information levels 0='Not visible' to 4='Fully visible' \n
        """
        ranges = np.asarray([i.Stats.SensorRanges for i in self.Ships]) if self.Ships else np.zeros((1,5))
        return float("inf"), max(ranges[:,1]), max(ranges[:,2]), max(ranges[:,3]), max(ranges[:,4])
    
    def getSensorRanges_Int(self) -> typing.Tuple[int,int,int,int,int]: #TODO: The sensors of the ships in the fleet should enhance each other
        """
        Sensor ranges: no resolution, low resolution, medium resolution, high resolution, perfect resolution \n
        But as integers \n
        Note: no resolution is always 10000 and only exist so that the indices match with the information levels 0='Not visible' to 4='Fully visible' \n
        """
        ranges = self.getSensorRanges()
        return int(10000), int(ranges[1]), int(ranges[2]), int(ranges[3]), int(ranges[4])
    
    def detectEnemies(self, onlyPlayer=False) -> typing.List[typing.Tuple[int,'FleetBase']]:
        "Returns a list of tuples with the detection level of a fleet and the fleet in question. Only considers hostile fleets"
        if self.Destroyed or not self.hex: return []
        ranges = list(self.getSensorRanges_Int())+[-1,]
        fleets:typing.List[typing.Tuple[int,'FleetBase']] = []
        for i,r in enumerate(ranges):
            if i == 0 or i == 5: continue
            if ranges[i+1] >= ranges[i]: continue
            potentialFleets = [h.fleet() for h in self.hex().getDisk(r,ranges[i+1]+1) if h.fleet]
            if onlyPlayer:
                fleets += [(f.detectCheck(i), f) for f in potentialFleets if f.detectCheck(i) and (f.Team == 1)]
            else:
                fleets += [(f.detectCheck(i), f) for f in potentialFleets if f.detectCheck(i) and get.unitManager().isHostile(self.Team,f.Team)]
        return fleets
    
    def findClosestEnemy(self, onlyPlayer=False, shareIntel=True) -> typing.Union['FleetBase',bool]:
        "Returns the closest enemy fleet or False if none is detected"
        if self.Destroyed or not self.hex: return False
        detectedEnemies = []
        if shareIntel:
            for team in get.unitManager().getAllies(self.Team):
                for fleet in get.unitManager().Teams[team]:
                    detectedEnemies += fleet.detectEnemies(onlyPlayer=onlyPlayer)
        else:
            detectedEnemies += self.detectEnemies(onlyPlayer=onlyPlayer)
        if not detectedEnemies:
            return False
        f = min([(self.hex().distance(f[1].hex()), f[1]) for f in detectedEnemies], key=lambda i:i[0])[1]
        return f
    
    def detectCheck(self, level:int) -> int:
        """Returns which information level a scan at `level` can procure. 0 means that it can not detect this fleet at all and 4 means that all information are visible"""
        #TODO: make some checks for the ships stealth capabilities
        return level
    
    def hide(self):
        if get.unitManager().isHostile(self.Team, 1):
            self.Hidden = True
            self.Node.hide()
    
    def show(self):
        self.Hidden = False
        self.Node.show()
    
    def handleSensors(self):
        for i in get.hexGrid().Hexes:
            for j in i:
                j.hideContent()
        for team in get.unitManager().getAllies(1):
            for fleet in get.unitManager().Teams[team]:
                if fleet.hex:
                    fleet.hex().showContent()
                    fleet._showAllEnemies()
    
    def _showAllEnemies(self):
        for i in self.detectEnemies():
            i[1].hex().showContent()
  #endregion Detection
    
  #region interface
    #def displayStats(self, display=True, forceRebuild=False):
    #    if display and not self.Hidden:
    #        if forceRebuild or not self.widget:
    #            from GUI import BaseInfoWidgets
    #            get.window().UnitStatDisplay.addWidget(self) #TODO
    #        self.widget().updateInterface()
    #    else:
    #        #get.window().UnitStatDisplay.Text.setText("No unit selected")
    #        if self.widget:
    #            get.window().UnitStatDisplay.removeWidget(self.widget())
    #            self.widget().deleteLater()
    #        self.widget = None
    def updateInterface(self):
        if self.widget:
            try:
                self.widget().updateInterface()
            except RuntimeError:
                self.widget = None # This usually means that the widget is destroyed but I don't know of a better way to test for it...
  #endregion interface
  #region overwrite
    async def attack(self, target: 'HexBase._Hex'):
        raise NotImplementedError("attack is only implemented for fleets and flotillas but not for the base fleet. How was a base fleet even created!?")
    
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
        return min([i.Stats.Movement_FTL[0] for i in self.Ships]) if self.Ships else 0
    
    def spendMovePoints(self, value:float):
        for i in self.Ships:
            i.Stats.spendMovePoints_FTL(value)
        self.updateInterface()
    
    @property
    def MovePoints_max(self) -> float:
        return min([i.Stats.Movement_FTL[1] for i in self.Ships]) if self.Ships else 0
    
    def battleEnded(self) -> 'dict':
        """
        Handles the End of the Battle for this Fleet. \n
        This Includes removing all destroyed ships and re-parenting all other ships from their flotillas back to this fleet. \n
        If all ships were destroyed this fleet will delete itself. \n
        Returns a log containing information about the battle
        """
        if get.engine().DebugPrintsEnabled:
            print("Battle Ended for", self.Name)
            print("Ships in fleet before cleanup:", len(self.Ships))
        hex_ = self.hex()
        ships_to_be_removed:typing.List['ShipBase.ShipBase'] = []
        for ship in self.Ships:
            if ship.Destroyed:
                ships_to_be_removed.append(ship)
        salvage = Resources.Salvage(0)
        for ship in ships_to_be_removed:
            salvage += ship.Stats.Value/8
            self.removeShip(ship,arrange=False)
        if get.engine().DebugPrintsEnabled: print("Ships in fleet after cleanup:", len(self.Ships))
        
        #hex_.ResourcesHarvestable.add(salvage)
        if salvage != 0:
            from Environment import EnvironmentalObjectGroups
            debrisFleet = EnvironmentalObjectGroups.EnvironmentalObjectGroup_Campaign()
            debrisFleet.Name = "Debris of Fleet: "+self.Name
            from Economy import HarvestableObjects
            debris = HarvestableObjects.Debris()
            debris.ResourceManager.addDirect(salvage)
            debrisFleet.addShip(debris)
            debrisFleet.moveToHex(hex_, False)
        
        if self.Destroyed:
            return {"salvage":Resources._ResourceDict.new(salvage)}
        else:
            for ship in self.Ships:
                ship.reparentTo(self)
            self.arrangeShips()
        return {"salvage":Resources._ResourceDict.new(salvage)}
    
  #region Combat Offensive
    async def attack(self, target: 'HexBase._Hex', orders:AI_Base.Orders = None, performOutOfTurn = False):
        if self.Destroyed or (not performOutOfTurn and not self.isActiveTurn()):
            return False
        if self.hex().distance(target) > 1:
            #REMINDER: The maximum attack distance should be 1 but since larger battles are more fun
            #           a distance of 2 should make it easier for the player to engage those.
            #           The AI, however, is still limited to 1 to not cause any confusion.
            #NOTE: Set this to one again due to the reinforcement changes
            return False
        if self.MovementSequence and self.MovementSequence.isPlaying():
            try: await self.MovementSequence
            except: self.MovementSequence.finish()
        self.lookAt(target)
        if self.MovementSequence and self.MovementSequence.isPlaying():
            try: await self.MovementSequence
            except: self.MovementSequence.finish()
        involvedFleets = self.getInvolvedFleetsForPotentialBattle(self.hex(), target)
        get.engine().startBattleScene(involvedFleets, aggressorHex = self.hex(), defenderHex = target)
    
    def getInvolvedFleetsForPotentialBattle(self, hex:'HexBase._Hex', target:'HexBase._Hex') -> 'list[Fleet]':
        involvedFleets = [self,target.fleet()]
        #for i in hex.getNeighbour()+target.getNeighbour():
        #    if i.fleet:
        #        if not i.fleet() in involvedFleets:
        #            involvedFleets.append(i.fleet())
        return involvedFleets
    
    def getAttackableHexes(self, _hex:'HexBase._Hex'=None) -> typing.List['HexBase._Hex']:
        if not _hex:
            if not self.hex: return []
            _hex = self.hex()
        l: typing.Set['HexBase._Hex'] = set()
        for i in _hex.getDisk(1):
            if i.fleet:
                if get.unitManager().isHostile(self.Team, i.fleet().Team):
                    l.add(i)
        return list(l)
  #endregion Combat Offensive
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
        return min([i.Stats.Movement_Sublight[0] for i in self.Ships]) if self.Ships else 0
    
    def spendMovePoints(self, value:float):
        for i in self.Ships:
            i.Stats.spendMovePoints_Sublight(value)
        self.updateInterface()
    
    @property
    def MovePoints_max(self) -> float:
        return min([i.Stats.Movement_Sublight[1] for i in self.Ships]) if self.Ships else 0
    
  #region Combat Offensive
    async def attack(self, target: 'HexBase._Hex', orders:AI_Base.Orders = None):
        #TODO: Ships that are firing should be visible to the player they are firing on... But maybe not for all weapons? Stealth torpedo salvo?
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
        else: maxRange = 0
        if minRanges: minRange = int(max(minRanges))
        else: minRange = 0
        return _hex.getDisk(minRange, maxRange)
    
    def getAttackRange(self) -> typing.Tuple[int,int,int]:
        "returns shortest, median, and longest weapon range"
        ranges = []
        for ship in self.Ships:
            for weapon in ship.Weapons:
                ranges.append(weapon.Range)
        return int(min(ranges)), int(np.median(ranges)), int(max(ranges))
        # min([min([j.Range for j in i.Weapons]) for i in self.Ships]) if self.Ships else 0
    
    def getAttackableHexes(self, _hex:'HexBase._Hex'=None) -> typing.List['HexBase._Hex']:
        if not _hex:
            if not self.hex: return []
            _hex = self.hex()
        l: typing.Set['HexBase._Hex'] = set()
        for i in self.getHexesInAttackRange(_hex):
            if i.fleet:
                if get.unitManager().isHostile(self.Team, i.fleet().Team):
                    l.add(i)
        return list(l)
  #endregion Combat Offensive
    
  #region Highlighting
    def highlightRanges(self, highlight=True):
        """
        Highlights all hexes that are relevant (movementrange, weaponrange, etc). \n
        If `highlight = False` the highlighted hexes are instead un-highlighted.
        """
        super().highlightRanges(highlight)
        if highlight and get.menu().HighlightOptionsWidget.HighlightWeaponRange() and not self.Hidden:
            self.highlightAttackRange(highlight, clearFirst=False)
    
    def highlightAttackRange(self, highlight=True, clearFirst=True):
        """
        Highlights all hexes that can be reached with the current movement points. \n
        If `highlight = False` the highlighted hexes are instead un-highlighted.
        """
        if not self.hex: return
        if highlight:
            self.hex().grid().highlightHexes(self.getHexesInAttackRange(), False, HexBase._Hex.COLOUR_ATTACKABLE, False, clearFirst=clearFirst)
        else:
            self.hex().grid().highlightHexes(self.getHexesInAttackRange(), False, False, False, clearFirst=True)
  #endregion Highlighting
