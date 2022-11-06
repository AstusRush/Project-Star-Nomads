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

if TYPE_CHECKING:
    from ProceduralGeneration import ProceduralShips

import math
from ProceduralGeneration import GeomBuilder
from ProceduralGeneration.GeomBuilder import pol_to_cart, Polygon, VertexDataWriter

class ShipBuilder(GeomBuilder.GeomBuilder):
    def genShip(self):
        try:
            connection_size = 2
            self.add_frontSection_wedge(color=(0.6,0.4,1,1), connection=p3dc.Point3(0,0,0), connection_size=connection_size, width=4, length=8, height=2.5)
            self.add_midSection_block(color=(1,0.3,1,1), connection_front=p3dc.Point3(0,0,0), connection_front_size=connection_size, connection_rear=p3dc.Point3(0,-10,0), connection_rear_size=connection_size, width=4, height=2.5)
            return self
        except:
            NC(1,exc=True)
    
    def add_connection(self,
                direction:str,
                connection:'typing.Union[p3dc.Point3,typing.Iterable[float,float,float]]',
                connection_size:float,
                color:'tuple[float,float,float,float]' = (0,0,0,1),
                ):
        connection = self.toPoint3(connection)
        #TODO: Connections should be stored and it should then be possible to get a list of all unconnected connections and generate things for them
        #       It should also be possible to walk the ship via these connections and see what modules are already connected and change modules and stuff like that
        #       This way we can generate models for all ship modules and turn them into ship model modules.
        #       Thus a ship's look reflects its capabilities and purpose
        #       In order to realize these plans the model must be handled in terms of modules that can all be deleted and regenerated independently and that can also be rearranged when modules change or disappear
        #       This will give the ship models great flexibility!
        from ProceduralGeneration import ProceduralShips
        dVec = ProceduralShips.Directions.getVector(direction)
        dVecAbs = p3dc.LVecBase3f(abs(dVec.x),abs(dVec.y),abs(dVec.z))
        size = (p3dc.Point3(1,1,1)-dVecAbs)*connection_size+dVec*0.5
        size = (size.x,size.y,size.z)
        self.add_block(center=connection+dVec*0.25, size=size , color=color) # (connection_size,0.5,connection_size)
        #if   direction == ProceduralShips.Directions.rear   : self.add_block(center=connection+p3dc.Point3(0,+0.25,0), size=(connection_size,0.5,connection_size), color=color)
        #elif direction == ProceduralShips.Directions.front  : self.add_block(center=connection+p3dc.Point3(0,-0.25,0), size=(connection_size,0.5,connection_size), color=color)
        #elif direction == ProceduralShips.Directions.left   : self.add_block(center=connection+p3dc.Point3(0,0.25,0), size=(connection_size,0.5,connection_size), color=color)
        #elif direction == ProceduralShips.Directions.right  : self.add_block(center=connection+p3dc.Point3(0,0.25,0), size=(connection_size,0.5,connection_size), color=color)
        #elif direction == ProceduralShips.Directions.dorsal : self.add_block(center=connection+p3dc.Point3(0,0.25,0), size=(connection_size,0.5,connection_size), color=color)
        #elif direction == ProceduralShips.Directions.ventral: self.add_block(center=connection+p3dc.Point3(0,0.25,0), size=(connection_size,0.5,connection_size), color=color)
        #else: NC(2,f"{direction = } is invalid!",tb=True,func="ShipBuilder.add_connection")
        return self
    
    def add_frontSection_wedge(self,
                module:'ProceduralShips.ShipModule',
                connection:'typing.Union[p3dc.Point3,typing.Iterable[float,float,float]]',
                connection_size:float,
                width:float,
                length:float,
                height:float,
                color:'tuple[float,float,float,float]' = (0,0,0,1),
                ):
        connection = self.toPoint3(connection)
        module.addConnector("rear", position=connection, connection_size=connection_size, color=color)
        self.add_wedge(base=connection+p3dc.Point3(0,length,0), top=connection+p3dc.Point3(0,0.25,+height/2), width=width, rot=p3dc.LRotationf(0,180,0), color=color)
        self.add_wedge(base=connection+p3dc.Point3(0,length,0), top=connection+p3dc.Point3(0,0.25,-height/2), width=width, rot=p3dc.LRotationf(0,180,0), color=color)
        return self
    
    def add_midSection_block(self,
                module:'ProceduralShips.ShipModule',
                connection_front:'typing.Union[p3dc.Point3,typing.Iterable[float,float,float]]',
                connection_front_size:float,
                connection_rear:'typing.Union[p3dc.Point3,typing.Iterable[float,float,float]]',
                connection_rear_size:float,
                width:float,
                height:float,
                color:'tuple[float,float,float,float]' = (0,0,0,1),
                ):
        connection_front, connection_rear = self.toPoint3(connection_front), self.toPoint3(connection_rear)
        module.addConnector("front", position=connection_front, connection_size=connection_front_size, color=color)
        self.add_block(center=connection_rear+(connection_front-connection_rear)/2, size=(width,((connection_front-connection_rear)).y-0.5,height), color=color)
        module.addConnector("rear", position=connection_rear, connection_size=connection_rear_size, color=color)
        return self
