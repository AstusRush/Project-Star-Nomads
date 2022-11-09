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
from BaseClasses import get
from BaseClasses import ListLoader
from BaseClasses import ModelBase
from ProceduralGeneration import GeomBuilder_Ships
from ProceduralGeneration import ProceduralModels

#REMINDER: use node.place() to get a gui to position and transform a node! That sounds very cool and useful and might even allow for an in-game ship-model editor!

class Directions:
    rear    = "rear"
    front   = "front"
    left    = "left"
    right   = "right"
    dorsal  = "dorsal"
    ventral = "ventral"
    @classmethod
    def getOpposite(cls, direction:str) -> str:
        if   direction == cls.rear   : return cls.front
        elif direction == cls.front  : return cls.rear
        elif direction == cls.left   : return cls.right
        elif direction == cls.right  : return cls.left
        elif direction == cls.dorsal : return cls.ventral
        elif direction == cls.ventral: return cls.dorsal
        else: raise Exception(f"{direction} is an invalid direction")
    
    @classmethod
    def getVector(cls, direction:str) -> p3dc.LVector3f:
        if   direction == cls.rear   : return p3dc.LVector3f(0,+1,0)
        elif direction == cls.front  : return p3dc.LVector3f(0,-1,0)
        elif direction == cls.left   : return p3dc.LVector3f(+1,0,0) #VALIDATE: Are these directions correct?
        elif direction == cls.right  : return p3dc.LVector3f(-1,0,0) #VALIDATE: Are these directions correct?
        elif direction == cls.dorsal : return p3dc.LVector3f(0,0,+1)
        elif direction == cls.ventral: return p3dc.LVector3f(0,0,-1)
        else: raise Exception(f"{direction} is an invalid direction")

class ModuleTypes:
    class ModuleType:
        @classmethod
        def random(cls, gb:'GeomBuilder_Ships.ShipBuilder',module:'ShipModule') -> 'GeomBuilder_Ships.ShipBuilder':
            d = cls.__dict__.copy()
            if "random" in d.keys(): del d["random"]
            for i in list(d.keys()):
                if i.startswith("__"): del d[i]
            return getattr(random.choice(list(d.values())),'__func__')(cls,gb,module)
    class FrontSection(ModuleType):
        @classmethod
        def wedge(cls, gb:'GeomBuilder_Ships.ShipBuilder',module:'ShipModule') -> 'GeomBuilder_Ships.ShipBuilder':
            return gb.add_frontSection_wedge(module, connection=p3dc.Point3(0,0,0), connection_size=2, width=4, length=8, height=2.5, color=(0.6,0.4,1,1))
    class MidSection(ModuleType):
        @classmethod
        def block(cls, gb:'GeomBuilder_Ships.ShipBuilder',module:'ShipModule') -> 'GeomBuilder_Ships.ShipBuilder':
            return gb.add_midSection_block(module, connection_front=p3dc.Point3(0,0,0), connection_front_size=2, connection_rear=p3dc.Point3(0,-10,0), connection_rear_size=2, width=4, height=2.5, color=(1,0.3,1,1))
    class AftSection(ModuleType):
        @classmethod
        def cone(cls, gb:'GeomBuilder_Ships.ShipBuilder',module:'ShipModule') -> 'GeomBuilder_Ships.ShipBuilder':
            return gb.add_aftSection_cone(module, connection_front=p3dc.Point3(0,0,0), connection_front_size=2, width=4, height=2.5, length=10, color=(0,1,1,1))

class ProceduralShip(ProceduralModels._ProceduralModel):
    IconPath = ""
    ModelPath = ""
    def __init__(self, loadImmediately=True, seed:int=None) -> None:
        style = ""
        self.Modules:'list[ShipModule]' = []
        self.ProceduralShipCentralNode:'p3dc.NodePath' = None
        self.CentralModule:'ShipModule' = None
        super().__init__(loadImmediately=loadImmediately,seed=seed)
    
    def _init_model(self):
        self.clearProceduralNodes()
        return super()._init_model()
    
    def destroy(self):
        self.clearProceduralNodes()
        return super().destroy()
    
    def clearProceduralNodes(self):
        if hasattr(self,"CentralModule") and self.CentralModule:
            self.CentralModule.destroy()
        for module in self.Modules:
            if not module.Destroyed:
                NC(4,"A modules was not destroyed automatically and had to be destroyed directly", func="ProceduralShip.clearProceduralNodes",input=str(module))
                module.destroy()
        self.Modules = []
        if hasattr(self,"ProceduralShipCentralNode") and self.ProceduralShipCentralNode:
            self.ProceduralShipCentralNode.removeNode()
    
    def createModule(self, type_:'type[ModuleTypes.ModuleType]') -> 'ShipModule':
        return self.addModule(ShipModule(self, type_, self.Seed))
    
    def addModule(self, module:'ShipModule') -> 'ShipModule':
        self.Modules.append(module)
        return module
    
    def generateModel(self):
        self.clearProceduralNodes()
        self.ProceduralShipCentralNode = p3dc.NodePath(p3dc.PandaNode(f"Central node of procedural ship model: {id(self)}"))
        front = self.createModule(ModuleTypes.FrontSection).setAsCentralModule()
        centre = self.createModule(ModuleTypes.MidSection).connectTo(front)
        engines = self.createModule(ModuleTypes.AftSection).connectTo(centre)
        return self.ProceduralShipCentralNode

class ShipModule():
    def __init__(self, ship:'ProceduralShip', type_:'type[ModuleTypes.ModuleType]', seed:int=None) -> None:
        self.Destroyed = False
        self.Type:'type[ModuleTypes.ModuleType]' = type_
        if seed is None:
            seed = np.random.randint(1000000)
        self.rng = np.random.default_rng(seed)
        self.ship:'weakref.ref[ProceduralShip]' = weakref.ref(ship)
        
        self.emptyConnectorDict()
        
        self.Node:p3dc.NodePath = p3dc.NodePath(p3dc.PandaNode(f"Central node of module: {id(self)}"))
        self.generate()
    
    def destroy(self):
        for v in self.Connectors.values():
            for d in v:
                d.destroy()
        if hasattr(self,"Model") and self.Model:
            self.Model.removeNode()
        if hasattr(self,"Node") and self.Node:
            self.Node.removeNode()
        self.Destroyed = True
    
    def emptyConnectorDict(self):
        self.Connectors:'dict[str,list[Connector]]' = {
            Directions.rear    : [],
            Directions.front   : [],
            Directions.left    : [],
            Directions.right   : [],
            Directions.dorsal  : [],
            Directions.ventral : [],
        }
    
    def setAsCentralModule(self) -> 'ShipModule':
        self.reparentTo(self.ship().ProceduralShipCentralNode)
        self.ship().CentralModule = self
        return self
    
    def reparentTo(self, node:'p3dc.NodePath'):
        self.Node.reparentTo(node)
    
    def connectTo(self, other:'ShipModule') -> 'ShipModule':
        #print("self.Connectors\n",self.Connectors,"\n\nother.Connectors\n",other.Connectors,"\n\n")
        for d,dCon in self.Connectors.items():
            for con in dCon:
                if not con.connection:
                    for otherCon in other.Connectors[Directions.getOpposite(d)]:
                        if not otherCon.connection:
                            otherCon.connect(con)
                            return self
        raise Exception("Could not find matching connectors")
    
    def generate(self):
        if hasattr(self,"Model") and self.Model:
            self.Model.removeNode()
        gb = GeomBuilder_Ships.ShipBuilder("Module", rng=self.rng)
        self.Type.random(gb, self)
        self.Model = p3dc.NodePath(gb.get_geom_node())
        self.Model.reparentTo(self.Node)
    
    def addConnector(self,
                direction:'str',
                position:'typing.Union[p3dc.Point3,typing.Iterable[float,float,float]]',
                connection_size:float,
                color:'tuple[float,float,float,float]' = (0,0,0,1),
                ) -> 'Connector':
        con = Connector(self, direction, position, connection_size, color)
        self.Connectors[direction].append(con)
        return con

class Connector():
    def __init__(self,
                module:'ShipModule',
                direction:'str',
                position:'typing.Union[p3dc.Point3,typing.Iterable[float,float,float]]',
                connection_size:float,
                color:'tuple[float,float,float,float]' = (0,0,0,1),
                ) -> None:
        self.Direction:'str' = direction
        self.Size:'float' = connection_size
        self.module:'weakref.ref[ShipModule]' = weakref.ref(module)
        self.connection:'weakref.ref[Connector]' = None
        self.IsMaster:'bool' = False
        gb = GeomBuilder_Ships.ShipBuilder('Connector', rng=module.rng)
        self.Position = gb.toPoint3(position)
        gb.add_connection(direction=direction, connection=p3dc.Point3(0,0,0), connection_size=connection_size, color=color)
        self.Model = p3dc.NodePath(gb.get_geom_node())
        self.Node:p3dc.NodePath = p3dc.NodePath(p3dc.PandaNode(f"Central node of connector: {id(self)}"))
        self.Model.reparentTo(self.Node)
        self.Node.reparentTo(module.Node)
        self.Node.setPos(position)
    
    def destroy(self):
        if self.connection and self.IsMaster:
            try:
                self.connection().module().destroy()
            except:
                ExceptionOutput()
        if hasattr(self,"Model") and self.Model:
            self.Model.removeNode()
        if hasattr(self,"Node") and self.Node:
            self.Node.removeNode()
    
    def connect(self, other:'Connector'):
        #MAYBE: Also accept ShipModule as a type and try to figure out what connector of the other module is appropriate to use
        self.connection = weakref.ref(other)
        other.connection = weakref.ref(self)
        self.IsMaster = True
        other.module().reparentTo(self.Node)
        other.module().Node.setPos(-other.Position)
