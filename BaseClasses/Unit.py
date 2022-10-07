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

# Game Imports
from . import get
#if TYPE_CHECKING:
from . import HexBase as Hex

#region Objects
class Object():
    def __init__(self, coordinates, colour, model):
        self.Node = loader().loadModel(model)
        try:
            self.Node.reparentTo(render())
            self.Node.setColor(ape.colour(colour))
            self.Node.setPos(get.engine().getHex(coordinates).Pos)
        except Exception as inst:
            self.Node.removeNode()
            raise inst
        get.engine().getHex(coordinates).content.append(self)
        
    def moveToPos(self,pos):
        self.setPos(pos)
        
    def moveToHex(self,hex:'Hex._Hex'):
        self.setPos(hex.Pos)
        
    def moveToCoordinates(self,coordinates):
        self.setPos(Hex.getHexPos(coordinates))
        
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
  #region init and destroy
    def __init__(self, coordinates, team=1, name="a Unit", model="Models/Simple Geometry/cube.ply", colour=(1,1,1,1)):
        self.Name = name
        self.Team = team
        self.ModelPath = model
        self.Destroyed = False
        self.MovePoints_max = 6 #float("inf") #10
        self.MovePoints = self.MovePoints_max
        self.hex: weakref.ref['Hex._Hex'] = None
        self.ActiveTurn = team == 1 #TODO: This should be taken from the Unit manager to check whose turn it actually is since enemy ships are mostly initialized during enemy turns (but not always which means we can not always set this to True!)
        self.init_model(coordinates, colour)
        self.init_combat()
        self.init_effects()
        get.unitManager().Teams[self.Team].append(self)
        try:
            self.centreModel()
        except:
            NC(2,"Could not centre model",exc=True)
        
    #def moveToPos(self,pos):
    #    self.Node.setPos(pos)
    
    def __del__(self):
        self.Destroyed = True
        if self.ExplosionEffect:
            self.ExplosionEffect.removeNode()
        if self.ExplosionEffect2:
            self.ExplosionEffect2.removeNode()
        if self.isSelected():
            get.unitManager().selectUnit(None)
        if self.hex:
            if self.hex().unit:
                if self.hex().unit() is self:
                    self.hex().unit = None
        self.Model.removeNode()
        self.Node.removeNode()
        
    def destroy(self, task=None):
        self.Destroyed = True
        try:
            get.unitManager().Teams[self.Team].remove(self)
        except:
            if self in get.unitManager().Teams[self.Team]:
                raise
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
        
    def removeNode(self, node, time = 1):
        base().taskMgr.doMethodLater(time, lambda task: self._removeNode(node), str(id(node)))
    
    def _removeNode(self, node):
        #try:
        node.removeNode()
    
  #endregion init and destroy
  #region Turn and Selection
    def startTurn(self):
        self.MovePoints = self.MovePoints_max
        self.ActiveTurn = True
        
        self.healAtTurnStart()
        
    def endTurn(self):
        self.ActiveTurn = False
        
    def isSelected(self):
        return get.unitManager().isSelectedUnit(self)
    
    def select(self):
        self.highlightRanges(True)
        self.diplayStats(True)
    
    def unselect(self):
        self.highlightRanges(False)
        self.diplayStats(False)
    
  #endregion Turn and Selection
  #region Interaction
    def interactWith(self, hex:'Hex._Hex'): #TODO:OVERHAUL
        """
        Makes this unit interact with the hex. \n
        Returns `True` if the new hex should be selected after this interaction (eg in case this unit has moved to the hex or has joined a fleet in the hex due to this interaction)
        """
        if self.Destroyed:
            return False
        if hex.fleet:
            self.lookAt(hex)
            if not ( hex.fleet() is self ): #TODO: Teams check
                self.attack(hex.fleet())
            return False
        else:
            return self.moveTo(hex)
    
  #endregion Interaction
  #region Movement
    def moveToHex(self, hex:'Hex._Hex', animate= True):
        self.Coordinates = hex.Coordinates
        if hex.fleet:
            raise Hex.HexOccupiedException(hex)
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
                raise Exception("Could not assign unit to Hex")
            self.hex = weakref.ref(hex)
        
    def _navigable(self, hex:'Hex._Hex'):
        return (not bool(hex.fleet)) and hex.Navigable
        
    def _tileCost(self, hex:'Hex._Hex'):
        return 1
        
    def lookAt(self, hex:'Hex._Hex'):
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
    
    def moveTo(self, hex:'Hex._Hex'):
        if not self._navigable(hex):
            # The figure can not move to the hex but we can at least make it look at the hex
            self.lookAt(hex)
            return False
        else:
            path, cost = Hex.findPath(self.hex(), hex, self._navigable, self._tileCost)
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
                hex.fleet = weakref.ref(self)
                self.hex = weakref.ref(hex)
                self.Coordinates = hex.Coordinates
                self.MovePoints -= cost
                self.highlightRanges(True)
                if not hex.fleet: #TODO: We have a serious problem when this occurs. What do we do in that case?
                    raise Exception("Could not assign unit to Hex")
                if not hex.fleet() == self: #TODO: We have a serious problem when this occurs. What do we do in that case?
                    raise Exception("Could not assign unit to Hex")
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
        self.moveToHex(get.engine().getHex(coordinates))
    
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
            mPoints = self.MovePoints if self.ActiveTurn else self.MovePoints_max # To allow calculations while it's not this unit's turn we use the MovePoints_max then
            l: typing.Set['Hex._Hex'] = set() # Using a set instead of a list is 5% faster... which is still not fast enough
            for i in self.hex().getDisk(mPoints): #FEATURE:MOVECOST: This does not take into account that hexes could have a negative movement point cost...
                #                                       Therefore we could miss some more distant tiles. But this method is already far too slow so we can not really afford to increase the radius of the disk...
                if not i in l:
                    path, cost = Hex.findPath(self.hex(), i, self._navigable, self._tileCost)
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
            l: typing.Set['Hex._Hex'] = set() # Using a set instead of a list is 5% faster... which is still not fast enough
            tl: typing.List[typing.Set['Hex._Hex']] = [set([self.hex()]),]
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
        self.hex().grid().highlightHexes(self.getReachableHexes(), Hex._Hex.COLOUR_REACHABLE, False, clearFirst=clearFirst)
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
        self.NoticeableDamage = self.HP_Hull_max / 10
        
    def healAtTurnStart(self):
        #TODO: This should be 2 methods: One that calculates the healing and one that the first one and then actually updates the values. This way the first method can be used to display a prediction to the user
        #REMINDER: When displaying this to the user there should also be a short text explaining that taking noticeable damage halves the regeneration for one turn and that shields need one turn to restart after being taken down.
        regenFactor = 1 if not self.WasHitLastTurn else 0.5
        self.HP_Hull = min(self.HP_Hull + self.HP_Hull_Regeneration*regenFactor , self.HP_Hull_max)
        if self.ShieldsWereOffline:
            self.ShieldsWereOffline = False
        else:
            self.HP_Shields = min(self.HP_Shields + self.HP_Shields_Regeneration*regenFactor , self.HP_Shields_max)
        self.WasHitLastTurn = False
        
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
                self.showShield()
            self.WasHitLastTurn = finalDamage >= self.NoticeableDamage
        if self.isSelected():
            self.diplayStats(True)
        if destroyed and not self.Destroyed: self.explode()
        return hit, destroyed, finalDamage
  #endregion Combat Defensive
  #region Combat Offensive
    def attack(self, target):
        # type: (Unit) -> None
        hit , targetDestroyed, damageDealt = target.takeDamage(50,0.9)
        self.fireLaserEffectAt(target, hit)
        if targetDestroyed:
            self.highlightRanges()
    
  #endregion Combat Offensive
  #region Effects
    def init_effects(self):
        self.ExplosionEffect = None
        self.ExplosionEffect2 = None
    
    def explode(self):
        #CRITICAL: The ship should already count as destroyed at this point (thus before the animation is played)
        #           Otherwise it is still possible to accidentally attack "the explosion" when giving orders hastily
        #           Maybe the destroy method should take a time in seconds. Then all the removal of game logic is handled before the nodes are destroyed.
        #               The timer should then be started at the start of the function so that the removal of the game logic does not desync the timer.
        #               I like it that the Unit is deselected only after the explosion so that the UI stays up during the explosion (this way one can see the overkill damage). This effect should be kept.
        #           Reminder: Removing the game logic also includes to make it impossible to give orders to the ship. (At the time of writing this you can move the explosion around... which looks kinda funny...)
        self.Destroyed = True
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
        
    def fireLaserEffectAt(self, unit, hit=True):
        # type: (Unit, bool) -> None
        laserEffect = loader().loadModel("Models/Simple Geometry/rod.ply")
        try:
            laserEffect.reparentTo(self.Node)
            #laserEffect.setZ(1.5)
            # This prevents lights from affecting this particular node
            laserEffect.setLightOff()
            
            hitPos = unit.Model.getPos(render())
            beamLength = (hitPos - self.Model.getPos(render())).length()
            if not hit:
                beamLength += 1
            #laserEffect.setZ(beamLength/2)
            laserEffect.setScale(0.02,beamLength,0.02)
            colour = App().PenColours["Orange"].color()
            laserEffect.setColor(ape.colour(colour))
            if not hit:
                miss = np.random.random_sample()
                miss1s = 1 if np.random.random_sample() > 0.5 else -1
                miss2s = 1 if np.random.random_sample() > 0.5 else -1
                miss1o = np.random.random_sample()*0.3-0.15
                miss2o = np.random.random_sample()*0.3-0.15
                laserEffect.setH(20*miss1s*(miss+miss1o))
                laserEffect.setP(20*miss2s*(1-miss+miss2o))
        finally:
            #base().taskMgr.doMethodLater(1, lambda task: self._removeNode(laserEffect), str(id(laserEffect)))
            self.removeNode(laserEffect, 1)
        
    def fireLaserEffectAt_bamboo(self, unit, hit=True): #CLEANUP: Remove this as it is no longer needed
        # type: (Unit, bool) -> None
        laserEffect = loader().loadModel("tempModels/BambooLaser/bambooLaser")
        try:
            laserEffect.reparentTo(self.Node)
            #laserEffect.setZ(1.5)
            # This prevents lights from affecting this particular node
            laserEffect.setLightOff()
            
            hitPos = unit.Model.getPos(render())
            beamLength = (hitPos - self.Model.getPos(render())).length()
            if not hit:
                beamLength += 1
            laserEffect.setSy(beamLength)
            if not hit:
                miss = np.random.random_sample()
                miss1s = 1 if np.random.random_sample() > 0.5 else -1
                miss2s = 1 if np.random.random_sample() > 0.5 else -1
                miss1o = np.random.random_sample()*0.3-0.15
                miss2o = np.random.random_sample()*0.3-0.15
                laserEffect.setH(20*miss1s*(miss+miss1o))
                laserEffect.setP(20*miss2s*(1-miss+miss2o))
        finally:
            #base().taskMgr.doMethodLater(1, lambda task: self._removeNode(laserEffect), str(id(laserEffect)))
            self.removeNode(laserEffect, 1)
            
    def showShield(self, time = 1):
        
        shieldEffect = loader().loadModel("Models/Simple Geometry/sphere.ply")
        try:
            if self.HP_Shields >= self.HP_Shields_max / 2:
                c = "Green"
            elif self.HP_Shields >= self.HP_Shields_max / 4:
                c = "Orange"
            else:
                c = "Red"
            colour = App().PenColours[c].color()
            colour.setAlphaF(0.3)
            shieldEffect.setColor(ape.colour(colour))
            shieldEffect.setTransparency(p3dc.TransparencyAttrib.MAlpha)
            #shieldEffect.setSize(0.1)
            shieldEffect.reparentTo(self.Node)
            
            bounds = self.Model.getTightBounds()
            bounds = (bounds[1]-bounds[0])
            shieldEffect.setScale(bounds)
            #shieldEffect.setSx()
            #shieldEffect.setSy()
            #shieldEffect.setSz()
            
            shieldEffect.show()
        finally:
            self.removeNode(shieldEffect, time)
        
    
  #endregion Effects
  #region Display Information
    def diplayStats(self, display=True):
        if display:
            text = textwrap.dedent(f"""
            Name: {self.Name}
            Team: {self.Team}
            Positions: {self.hex().Coordinates}
            
            Movement Points: {self.MovePoints}/{self.MovePoints_max}
            
            Hull: {self.HP_Hull}/{self.HP_Hull_max} (+{self.HP_Hull_Regeneration} per turn (halfed if the ship took a single hit that dealt at least {self.NoticeableDamage} damage last turn))
            Shields: {self.HP_Shields}/{self.HP_Shields_max} (+{self.HP_Shields_Regeneration} per turn (halfed if the ship took a single hit that dealt at least {self.NoticeableDamage} damage last turn))
            """)
            get.window().UnitStatDisplay.Text.setText(text)
        else:
            get.window().UnitStatDisplay.Text.setText("No unit selected")
  #endregion Display Information
  #region model
    def init_model(self, coordinates, colour = (1,1,1,1)):
        self.Node = p3dc.NodePath(p3dc.PandaNode("Central node of unit: "+self.Name))
        try:
            self.Node.reparentTo(render())
            self.Model = loader().loadModel(self.ModelPath)
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
    
    def centreModel(self):
        self.Model.setH(0)
        self.Model.setPos(0,0,0)
        self.Model.setScale(1)
        self.Model.setScale(0.8/self.Model.getBounds().getRadius()) #REMINDER: Use this and the next line to make shields (adjust the scale factor here accordingly so that the shields have a decend distance to the ship but are smaller than 1.0 to avoid clipping)
        if self.ModelPath == "/Users/Robin/Desktop/Projects/AstusGameEngine_dev/3DModels/NCC-1701-D.gltf": #REMINDER: This is temporary
            self.Model.setH(180)
        self.Model.setPos(-self.Model.getBounds().getApproxCenter())
  #endregion model
  #region ...
  #endregion ...
  #region ...
  #endregion ...

#endregion Objects