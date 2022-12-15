"""
#TODO:Note
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
from BaseClasses import get
from BaseClasses import ListLoader
from BaseClasses import ModelBase
from ProceduralGeneration import GeomBuilder, GeomBuilder_Ships
from ProceduralGeneration import ProceduralModels

if TYPE_CHECKING:
    from BaseClasses import ShipBase, FleetBase, BaseModules, HexBase

#REMINDER: use node.place() to get a gui to position and transform a node! That sounds very cool and useful and might even allow for an in-game ship-model editor!

class NoMatchingConnectorException(Exception):
    pass

class HasNoShipException(Exception):
    pass

class Directions:
    rear     = "rear"
    front    = "front"
    left     = "left"
    right    = "right"
    dorsal   = "dorsal"
    ventral  = "ventral"
    any      = "any"
    notRear  = "notRear"
    notFront = "notFront"
    radial   = "radial"
    #invalid  = "invalid"
    @classmethod
    def getOpposite(cls, direction:str) -> str:
        if   direction == cls.rear    : return cls.front
        elif direction == cls.front   : return cls.rear
        elif direction == cls.left    : return cls.right
        elif direction == cls.right   : return cls.left
        elif direction == cls.dorsal  : return cls.ventral
        elif direction == cls.ventral : return cls.dorsal
        elif direction == cls.any     : return cls.any
        elif direction == cls.notRear : return cls.notFront
        elif direction == cls.notFront: return cls.notRear
        elif direction == cls.radial  : return cls.radial
        else: raise Exception(f"{direction} is an invalid direction")
    
    @classmethod
    def getVector(cls, direction:str) -> p3dc.LVector3f:
        if   direction == cls.rear   : return p3dc.LVector3f(0,-1,0)
        elif direction == cls.front  : return p3dc.LVector3f(0,+1,0)
        elif direction == cls.left   : return p3dc.LVector3f(+1,0,0) #VALIDATE: Is this direction correct?
        elif direction == cls.right  : return p3dc.LVector3f(-1,0,0) #VALIDATE: Is this direction correct?
        elif direction == cls.dorsal : return p3dc.LVector3f(0,0,+1)
        elif direction == cls.ventral: return p3dc.LVector3f(0,0,-1)
        else: raise Exception(f"{direction} is an invalid direction")
    
    @classmethod
    def getHpr(cls, direction:str) -> p3dc.LVector3f:
        if   direction == cls.rear   : return p3dc.LVector3f(0,-90,0) #VALIDATE: Is this rotation correct?
        elif direction == cls.front  : return p3dc.LVector3f(0,+90,0) #VALIDATE: Is this rotation correct?
        elif direction == cls.left   : return p3dc.LVector3f(0,0,+90)
        elif direction == cls.right  : return p3dc.LVector3f(0,0,-90)
        elif direction == cls.dorsal : return p3dc.LVector3f(0,0,0)
        elif direction == cls.ventral: return p3dc.LVector3f(0,0,180)
        else: raise Exception(f"{direction} is an invalid direction")
    
    @classmethod
    def isUnspecific(cls, direction:str) -> p3dc.LVector3f:
        if (   direction == cls.rear
            or direction == cls.front
            or direction == cls.left
            or direction == cls.right
            or direction == cls.dorsal
            or direction == cls.ventral
            ):
            return False
        else: return True

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
            return gb.add_midSection_block(module, connection_front=p3dc.Point3(0,0,0), connection_front_size=2, connection_rear=p3dc.Point3(0,-3,0), connection_rear_size=2, width=4, height=2.5, color=(1,0.3,1,1))
    class AftSection(ModuleType):
        @classmethod
        def cone(cls, gb:'GeomBuilder_Ships.ShipBuilder',module:'ShipModule') -> 'GeomBuilder_Ships.ShipBuilder':
            from BaseClasses import BaseModules
            if not module.logicalModule or not isinstance(module.logicalModule(),BaseModules.Thruster):
                return gb.add_aftSection_cone_static(module, connection_front=p3dc.Point3(0,0,0), connection_front_size=2, width=4, height=2.5, length=10, color=(0,1,1,1))
            else: return gb.add_aftSection_cone(module, width=4, height=2.5, length=3, color=(0,1,1,1))
    class Turret(ModuleType):
        @classmethod
        def basic(cls, gb:'GeomBuilder_Ships.ShipBuilder',module:'ShipModule') -> 'GeomBuilder_Ships.ShipBuilder':
            return gb.add_turret_basic(module, color=(0.15,0,0,1))
    class ConstructionBay(ModuleType):
        @classmethod
        def block(cls, gb:'GeomBuilder_Ships.ShipBuilder',module:'ShipModule') -> 'GeomBuilder_Ships.ShipBuilder':
            return gb.add_midSection_block(module, connection_front=p3dc.Point3(0,0,0), connection_front_size=2, connection_rear=p3dc.Point3(0,-10,0), connection_rear_size=2, width=8, height=4, color=(1,0.3,1,1))
    class ShieldGenerator(ModuleType):
        @classmethod
        def block(cls, gb:'GeomBuilder_Ships.ShipBuilder',module:'ShipModule') -> 'GeomBuilder_Ships.ShipBuilder':
            return gb.add_midSection_block(module, connection_front=p3dc.Point3(0,0,0), connection_front_size=2, connection_rear=p3dc.Point3(0,-module.logicalModule().HP_Shields_max/100,0), connection_rear_size=2, width=4, height=2.5, color=(0.7,0.2,1,1))
    class HardpointSection(ModuleType):
        @classmethod
        def block(cls, gb:'GeomBuilder_Ships.ShipBuilder',module:'ShipModule') -> 'GeomBuilder_Ships.ShipBuilder':
            return gb.add_hardpointSection_block(module, connection_front=p3dc.Point3(0,0,0), connection_front_size=2, connection_rear=p3dc.Point3(0,-3,0), connection_rear_size=2, width=4, height=2.5, color=(1,0.3,1,1))

class ProceduralShip(ProceduralModels._ProceduralModel):
    IconPath = ""
    ModelPath = ""
    AutogenerateOnAssignment = True
    def __init__(self, loadImmediately=True, seed:int=None, ship:'ShipBase.ShipBase'=None) -> None:
        style = ""
        self.Modules:'list[ShipModule]' = []
        self.ProceduralShipCentralNode:'p3dc.NodePath' = None
        self.CentralModule:'ShipModule' = None
        super().__init__(loadImmediately=loadImmediately,seed=seed,ship=ship)
    
    def tocode_AGeLib(self, name="", indent=0, indentstr="    ", ignoreNotImplemented = False) -> typing.Tuple[str,dict]:
        # We save the models by not saving them since this tells the ships to autogenerate new procedural models which is exactly what we want
        # Later on we might want to save the seed and maybe the style and so on but for now saving literally nothing is entirely sufficient to accurately restore everything
        ret, imp = "None", {}
        return ret, imp
    
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
    
    def createModule(self, type_:'type[ModuleTypes.ModuleType]', module:'typing.Union[BaseModules.Module,None]'=None, extraInfo:'typing.Union[dict,None]'=None) -> 'ShipModule':
        if module and module.getModuleModelBuilder():
            return module.getModuleModelBuilder()(self, type_, self.Seed, module, extraInfo=extraInfo)
        return self.addModule(ShipModule(self, type_, self.Seed, module, extraInfo=extraInfo))
    
    def addModule(self, module:'ShipModule') -> 'ShipModule':
        self.Modules.append(module)
        return module
    
    def removeModule(self, module:'ShipModule') -> 'ShipModule':
        if module in self.Modules:
            self.Modules.remove(module)
            module.destroy()
        return module
    
    def updateConnectorsDict(self) -> 'ConnectorDict':
        self.Connectors:'ConnectorDict' = ConnectorDict().init()
        for module in self.Modules:
            for d, dCon in module.Connectors.items():
                self.Connectors.add(d,dCon)
        return self.Connectors
    
    def connectModule(self, module:'ShipModule', setAsRoot=False) -> 'ShipModule':
        if setAsRoot: return module.setAsCentralModule()
        connectors = self.updateConnectorsDict()
        #print(f"\nsearching for {module.Type}") # This line is for debugging purposes
        for d,dCon in module.Connectors.items():
            for con in dCon:
                #print(f"for con {d} which is opposed by {Directions.getOpposite(d)}\nThe Options are {connectors[Directions.getOpposite(d)]}") # This line is for debugging purposes
                if not con.connection:
                    for otherCon in connectors[Directions.getOpposite(d)]:
                        if otherCon.module() is not module and not otherCon.connection:
                            otherCon.connect(con)
                            #print("Connected!\n") # This line is for debugging purposes
                            return module
        raise NoMatchingConnectorException("Could not find any free matching connector")
    
    def createAndConnectModule(self, type_:'type[ModuleTypes.ModuleType]', module:'typing.Union[BaseModules.Module,None]'=None, extraInfo:'typing.Union[dict,None]'=None) -> 'ShipModule':
        asRoot = not bool(len(self.Modules))
        return self.connectModule(self.createModule(type_,module,extraInfo),asRoot)
    
    def generateModel(self):
        try:
            node = self.generateModelFromShipModules()
        except HasNoShipException as e:
            print(f"{self} could not generate a model from the ship modules: {e.args}")
            node = self.generateGenericModel()
        
        if get.menu().GraphicsOptionsWidget.ShipTexture(): self.applyTexture(node)
        return node
    
    def generateGenericModel(self):
        self.clearProceduralNodes()
        self.ProceduralShipCentralNode = p3dc.NodePath(p3dc.PandaNode(f"Central node of procedural ship model: {id(self)}"))
        #front = self.createModule(ModuleTypes.FrontSection).setAsCentralModule()
        front = self.createAndConnectModule(ModuleTypes.FrontSection)
        #centre = self.createModule(ModuleTypes.MidSection).connectTo(front)
        centre = self.createAndConnectModule(ModuleTypes.MidSection)
        #engines = self.createModule(ModuleTypes.AftSection).connectTo(centre)
        engines = self.createAndConnectModule(ModuleTypes.AftSection)
        return self.ProceduralShipCentralNode
    
    def generateModelFromShipModules(self):
        if not self.ship: raise HasNoShipException("This model is not yet assigned to a ship.")
        if not self.ship().Modules: raise HasNoShipException("This model is assigned to a ship without any modules.")
        
        from BaseClasses import ShipBase, FleetBase, BaseModules #, HexBase
        
        self.clearProceduralNodes()
        self.ProceduralShipCentralNode = p3dc.NodePath(p3dc.PandaNode(f"Central node of procedural ship model: {id(self)}"))
        
        front = self.createAndConnectModule(ModuleTypes.FrontSection)
        
        numWeapons = len(self.ship().Weapons)
        #for _ in range(math.ceil(len(self.ship().Weapons)/4)):
        while numWeapons > 0:
            hardpoints = self.createAndConnectModule(ModuleTypes.HardpointSection, extraInfo={"numHardpoints":4 if numWeapons>4 else numWeapons})
            numWeapons -= 4
        
        for module in self.ship().Modules:
            if isinstance(module, BaseModules.Hull):
                hull = self.createAndConnectModule(ModuleTypes.MidSection, module)
            if isinstance(module, BaseModules.ConstructionModule):
                constructionBay = self.createAndConnectModule(ModuleTypes.ConstructionBay, module)
            if isinstance(module, BaseModules.Shield):
                shield = self.createAndConnectModule(ModuleTypes.ShieldGenerator, module)
            if isinstance(module, (BaseModules._Economic, BaseModules.Augment, BaseModules.Support, BaseModules.Special,)):
                other = self.createAndConnectModule(ModuleTypes.MidSection, module)
        
        if self.ship().thruster:
            engines = self.createAndConnectModule(ModuleTypes.AftSection, self.ship().thruster())
        
        for module in self.ship().Weapons:
            weapon = self.createAndConnectModule(ModuleTypes.Turret, module)
        
        return self.ProceduralShipCentralNode
    
    def applyTexture(self, node:'p3dc.NodePath'):
        try: #if True: #texture:
            import io
            import PIL
            col = self.generateTexture()
            cMap = PIL.Image.fromarray(np.uint8((np.flip(col,(1)).transpose(1,0,2))),'RGBA')
            cBuf = io.BytesIO()
            cMap.save(cBuf, format="png")
            ciMap = p3dc.PNMImage()
            ciMap.read(p3dc.StringStream(cBuf.getvalue()),"t.png")
            
            panda_tex = p3dc.Texture("default")
            panda_tex.load(ciMap)
            panda_mat = p3dc.Material("default")
            #panda_mat.emission = 0
            panda_mat.setEmission((0.1,0.1,0.1,1))
            node.set_material(panda_mat)
            node.set_texture(panda_tex)
        except:
            ExceptionOutput()
    
    def generateTexture(self):
        a, b = 200, 256 # col ∈ [a,b)
        col = self.rng.random((50,50,4))*(b-a)+a
        col[:,:3] = 1
        col = col.astype(int)
        
        #from matplotlib import pyplot as plt
        #plt.figure()
        #plt.imshow(col[:,:,:3]/255)
        #plt.show()
        #input("WAITING")
        return col

class ShipModule():
    def __init__(self, ship:'ProceduralShip', type_:'type[ModuleTypes.ModuleType]', seed:int=None, module:'typing.Union[BaseModules.Module,None]'=None, extraInfo:'typing.Union[dict,None]'=None) -> None:
        self.Destroyed = False
        self.Type:'type[ModuleTypes.ModuleType]' = type_
        if seed is None:
            seed = np.random.randint(1000000)
        self.rng = np.random.default_rng(seed)
        self.ship:'weakref.ref[ProceduralShip]' = weakref.ref(ship)
        self.logicalModule:'typing.Union[weakref.ref[BaseModules.Module],None]' = weakref.ref(module) if module else None
        self.ExtraInfo:'dict' = extraInfo if extraInfo is not None else {}
        if module: module.moduleModel = weakref.ref(self)
        
        self.emptyConnectorDict()
        
        self.Node:p3dc.NodePath = p3dc.NodePath(p3dc.PandaNode(f"Central node of module: {id(self)}"))
        self._generate()
    
    def destroy(self, returnLooseModuleGroups = False) -> 'typing.Union[list[ShipModule],None]':
        r = [] if returnLooseModuleGroups else None
        for v in self.Connectors.values():
            for d in v:
                t = d.destroy(returnDisconnectedModuleIfSelfIsMaster = returnLooseModuleGroups)
                if returnLooseModuleGroups and t: r.append(t)
        if hasattr(self,"Model") and self.Model:
            self.Model.removeNode()
        if hasattr(self,"Node") and self.Node:
            self.Node.removeNode()
        self.Destroyed = True
        #TODO: We probably also want to break up all connections of all loose Modules and throw those into the list so that a restructuring can be done from the ground up
        return r
    
    def emptyConnectorDict(self):
        #self.Connectors:'dict[str,list[Connector]]' = {
        self.Connectors:'ConnectorDict' = ConnectorDict().init()
    
    def getNumConnectors(self) -> int:
        return sum([len(c) for c in self.Connectors.values()])
    
    def getNumFreeConnectors(self) -> int:
        num = 0
        for dCon in self.Connectors.values():
            for con in dCon:
                if con.connection is None:
                    num += 1
        return num
    
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
        raise NoMatchingConnectorException("Could not find any free matching connector")
    
    def _generate(self):
        if hasattr(self,"Model") and self.Model:
            self.Model.removeNode()
        gb = GeomBuilder_Ships.ShipBuilder("Module", rng=self.rng)
        gb = self.generate(gb=gb)
        self.Model = p3dc.NodePath(gb.get_geom_node())
        self.Model.reparentTo(self.Node)
    
    def generate(self, gb:'GeomBuilder_Ships.ShipBuilder'):
        self.Type.random(gb, self)
        return gb
    
    def addConnector(self,
                direction:'str',
                position:'typing.Union[p3dc.Point3,typing.Iterable[float,float,float]]',
                connection_size:float,
                thickness:float = 0.125,
                color:'tuple[float,float,float,float]' = (0,0,0,1),
                ) -> 'Connector':
        con = Connector(module=self, direction=direction, position=position, connection_size=connection_size, thickness=thickness, color=color)
        self.Connectors.add(direction,con)
        return con

class Connector():
    def __init__(self,
                module:'ShipModule',
                direction:'str',
                position:'typing.Union[p3dc.Point3,typing.Iterable[float,float,float]]',
                connection_size:float,
                thickness:float = 0.125,
                color:'tuple[float,float,float,float]' = (0,0,0,1),
                ) -> None:
        #print(f"{thickness = }")
        self.Direction:'str' = direction
        self.Size:'float' = connection_size
        self.module:'weakref.ref[ShipModule]' = weakref.ref(module)
        self.connection:'typing.Union[weakref.ref[Connector],None]' = None
        self.IsMaster:'bool' = False
        gb = GeomBuilder_Ships.ShipBuilder('Connector', rng=module.rng)
        if Directions.isUnspecific(self.Direction): direction = Directions.ventral
        self.Position = gb.toPoint3(position)+Directions.getVector(direction)*thickness
        gb.add_connection(direction=direction, connection=p3dc.Point3(0,0,0), connection_size=connection_size, thickness=thickness, color=color)
        self.Model = p3dc.NodePath(gb.get_geom_node())
        self.Node:p3dc.NodePath = p3dc.NodePath(p3dc.PandaNode(f"Central node of connector: {id(self)}"))
        self.Model.reparentTo(self.Node)
        self.Node.reparentTo(module.Node)
        self.Node.setPos(self.Position)
    
    def destroy(self, returnDisconnectedModuleIfSelfIsMaster = False) -> 'typing.Union[ShipModule,None]':
        r = None
        if self.connection:
            self.connection().connection = None
            if self.IsMaster and not returnDisconnectedModuleIfSelfIsMaster:
                try:
                    self.connection().module().destroy()
                except:
                    ExceptionOutput()
            else:
                r = self.connection().module()
            self.connection = None
        if hasattr(self,"Model") and self.Model:
            self.Model.removeNode()
        if hasattr(self,"Node") and self.Node:
            self.Node.removeNode()
        return r
    
    def connect(self, other:'Connector'):
        #MAYBE: Also accept ShipModule as a type and try to figure out what connector of the other module is appropriate to use
        if Directions.isUnspecific(self.Direction):
            raise Exception(f"A Connector that is not facing in any specific direction (in this case {self.Direction}) can not be the master of a connection but only the apprentice.")
        self.Node.setHpr(0,0,0)
        self.connection = weakref.ref(other)
        other.connection = weakref.ref(self)
        self.IsMaster = True
        other.module().reparentTo(self.Node)
        if Directions.isUnspecific(other.Direction) and self.Direction != Directions.dorsal:
            #TODO: unspecific is handled as ventral/down
            #       the module must be rotated such that the apprentices dorsal side is facing in the same direction as the master connector
            #       The apprentices front should always face the same direction as the masters front, except if the master connector is on the front or rear in which case it should face up/dorsal
            self.Node.setHpr(Directions.getHpr(self.Direction))
            self.Model.setHpr(-Directions.getHpr(self.Direction))
            other.module().Node.setPos(-other.Position)
        else:
            other.module().Node.setPos(-other.Position)

class ConnectorDict(typing.Dict[str,typing.List[Connector]]):
    def init(self):
        self.update({
            Directions.rear    : [],
            Directions.front   : [],
            Directions.left    : [],
            Directions.right   : [],
            Directions.dorsal  : [],
            Directions.ventral : [],
            Directions.any     : [],
            Directions.notRear : [],
            Directions.notFront: [],
            Directions.radial  : [],
        })
        return self
    
    def __getitem__(self, _key: str) -> 'list[Connector]':
        ret = []
        if _key == Directions.any:
            for v in self.values():
                ret += v
        elif _key == Directions.notRear:
            for k,v in self.items():
                if not Directions.isUnspecific(k) and k != Directions.rear: ret += v
        elif _key == Directions.notFront:
            for k,v in self.items():
                if not Directions.isUnspecific(k) and k != Directions.front: ret += v
        elif _key == Directions.radial:
            for k,v in self.items():
                if not Directions.isUnspecific(k) and k != Directions.front and k != Directions.rear: ret += v
        else:
            ret = super().__getitem__(_key)
        return ret
    
    def add(self, direction:str, connector:'typing.Union[Connector,list[Connector]]'):
        if isinstance(connector,list):
            self[direction] = self.get(direction) + connector
        else:
            self.get(direction).append(connector)
        return self
