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
            self.add_frontSection(color=(0.6,0.4,1,1), connection=p3dc.Point3(0,0,0), connection_size=connection_size, width=4, length=8, height=2.5)
            self.add_midSection(color=(1,0.3,1,1), connection_front=p3dc.Point3(0,0,0), connection_front_size=connection_size, connection_rear=p3dc.Point3(0,-10,0), connection_rear_size=connection_size, width=4, height=2.5)
            return self
        except:
            NC(1,exc=True)
    
    def add_connection(self,
                direction:str,
                connection:'typing.Union[p3dc.Point3,typing.Iterable[float,float,float]]',
                connection_size:float,
                thickness:float = 0.25,
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
        size = (p3dc.Point3(1,1,1)-dVecAbs)*connection_size+dVecAbs*thickness
        size = (abs(size.x),abs(size.y),abs(size.z))
        self.add_block(center=connection-dVec*thickness/2, size=size, color=color) # (connection_size,0.5,connection_size)
        #if   direction == ProceduralShips.Directions.rear   : self.add_block(center=connection+p3dc.Point3(0,+0.25,0), size=(connection_size,0.5,connection_size), color=color)
        #elif direction == ProceduralShips.Directions.front  : self.add_block(center=connection+p3dc.Point3(0,-0.25,0), size=(connection_size,0.5,connection_size), color=color)
        #elif direction == ProceduralShips.Directions.left   : self.add_block(center=connection+p3dc.Point3(0,0.25,0), size=(connection_size,0.5,connection_size), color=color)
        #elif direction == ProceduralShips.Directions.right  : self.add_block(center=connection+p3dc.Point3(0,0.25,0), size=(connection_size,0.5,connection_size), color=color)
        #elif direction == ProceduralShips.Directions.dorsal : self.add_block(center=connection+p3dc.Point3(0,0.25,0), size=(connection_size,0.5,connection_size), color=color)
        #elif direction == ProceduralShips.Directions.ventral: self.add_block(center=connection+p3dc.Point3(0,0.25,0), size=(connection_size,0.5,connection_size), color=color)
        #else: NC(2,f"{direction = } is invalid!",tb=True,func="ShipBuilder.add_connection")
        return self
    
    def add_frontSection_wedge_old(self,
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
        self.add_wedge(base=connection+p3dc.Point3(0,length,0), top=connection+p3dc.Point3(0,0,+height/2), width=width, rot=p3dc.LRotationf(0,180,0), color=color)
        self.add_wedge(base=connection+p3dc.Point3(0,length,0), top=connection+p3dc.Point3(0,0,-height/2), width=width, rot=p3dc.LRotationf(0,180,0), color=color)
        return self
    
    def add_frontSection(self,
                module:'ProceduralShips.ShipModule',
                connection:'typing.Union[p3dc.Point3,typing.Iterable[float,float,float]]',
                connection_size:float,
                width:float,
                length:float,
                height:float,
                color:'tuple[float,float,float,float]' = (0,0,0,1),
                shape:str=""):
        connection = self.toPoint3(connection)
        module.addConnector("rear", position=connection, connection_size=connection_size, color=color)
        self.add_wedge(base=connection+p3dc.Point3(0,length,0), top=connection+p3dc.Point3(0,0,+height/2), width=width, rot=p3dc.LRotationf(0,180,0), color=color)
        self.add_wedge(base=connection+p3dc.Point3(0,length,0), top=connection+p3dc.Point3(0,0,-height/2), width=width, rot=p3dc.LRotationf(0,180,0), color=color)
        return self
    
    def add_midSection_block_old(self,
                module:'ProceduralShips.ShipModule',
                connection_front:'typing.Union[p3dc.Point3,typing.Iterable[float,float,float]]',
                connection_front_size:float,
                connection_rear:'typing.Union[p3dc.Point3,typing.Iterable[float,float,float]]',
                connection_rear_size:float,
                width:float,
                height:float,
                color:'tuple[float,float,float,float]' = (0,0,0,1),
                ):
        from ProceduralGeneration import ProceduralShips
        from BaseClasses import BaseModules
        connection_front, connection_rear = self.toPoint3(connection_front), self.toPoint3(connection_rear)
        block_center = connection_rear+(connection_front-connection_rear)/2
        module.addConnector(ProceduralShips.Directions.front, position=connection_front, connection_size=connection_front_size, color=color)
        self.add_block(center=block_center, size=(width,((connection_front-connection_rear)).y,height), color=color)
        module.addConnector(ProceduralShips.Directions.rear, position=connection_rear, connection_size=connection_rear_size, color=color)
        return self
    
    def add_midSection(self,
                    module: 'ProceduralShips.ShipModule',
                    connection_front: 'typing.Union[p3dc.Point3, typing.Iterable[float, float, float]]',
                    connection_front_size: float,
                    connection_rear: 'typing.Union[p3dc.Point3, typing.Iterable[float, float, float]]',
                    connection_rear_size: float,
                    width: float,
                    height: float,
                    color: 'tuple[float, float, float, float]' = (0, 0, 0, 1),
                    shape:'typing.Union[str,typing.List[str],typing.Tuple[str],None]'=""):
        connection_front, connection_rear = self.toPoint3(connection_front), self.toPoint3(connection_rear)
        block_center = connection_rear + (connection_front - connection_rear) / 2
        module.addConnector("front", position=connection_front, connection_size=connection_front_size, color=color)
        module.addConnector("rear", position=connection_rear, connection_size=connection_rear_size, color=color)
        
        if not shape:
            shape = self.rng.choice([
                                            "block",
                                            "cylinder",
                                            #"dome", #TODO: Does not look good yet...
                                            "tapered",
                                            #"winged", #TODO: Does not look good yet...
                                            "ribbed",
                                            #"scaled", #TODO: Does not look good yet...
                                            #"spherical", #TODO: Does not look good yet...
                                            "multi",
                                            ])
        if not isinstance(shape, str):
            shape = self.rng.choice(shape)
        
        if shape == "block":
            self.add_block(center=block_center, size=(width, ((connection_front - connection_rear)).y, height), color=color)
        elif shape == "cylinder":
            self.add_cylindrical_midsection(center=block_center, radius=width / 2, height=((connection_front - connection_rear)).y, color=color)
        elif shape == "dome":
            self.add_dome_midsection(center=block_center, radius=width / 2, height=height, color=color)
        elif shape == "tapered":
            self.add_tapered_midsection(base_center=block_center, top_center=block_center, base_width=width, top_width=width / 2, height=((connection_front - connection_rear)).y, color=color)
        elif shape == "winged":
            self.add_winged_midsection(center=block_center, width=width, length=((connection_front - connection_rear)).y, thickness=height / 4, color=color)
        elif shape == "ribbed":
            self.add_ribbed_midsection(center=block_center, width=width, height=((connection_front - connection_rear)).y, depth=height, rib_count=5, rib_thickness=0.2, color=color)
        elif shape == "scaled":
            self.add_scaled_midsection(center=block_center, width=width, height=((connection_front - connection_rear)).y, depth=height, scale_count=5, scale_spacing=0.5, color=color)
        elif shape == "spherical":
            self.add_spherical_midsection(center=block_center, radius=width / 4, sphere_count=3, spacing=width / 2, color=color)
        elif shape == "multi":
            self.add_multi_layered_midsection(center=block_center, width=width, height=((connection_front - connection_rear)).y, depth=height, layer_count=5, variance_divisor=4, color=color)
        else:
            NC(2,f"\"{shape}\" is an invalid mid-section shape for ships!",tb=True)
            self.add_block(center=block_center, size=(width, ((connection_front - connection_rear)).y, height), color=color)
        
        # GeomBuilder_Ships.ShipBuilder.add_midSection_block
        return self
    
    def add_cylindrical_midsection(self,
                                    center: 'tuple[float, float, float]',
                                    radius: float,
                                    height: float,
                                    color: 'tuple[float, float, float, float]' = (0, 0, 0, 1)):
        base = p3dc.Point3(center[0], center[1] - height / 2, center[2])
        top = p3dc.Point3(center[0], center[1] + height / 2, center[2])
        self.add_cylinder(base=base, base_radius=radius, top=top, top_radius=radius, color=color)
        return self
    
    def add_dome_midsection(self,
                            center: 'tuple[float, float, float]',
                            radius: float,
                            height: float,
                            color: 'tuple[float, float, float, float]' = (0, 0, 0, 1)):
        dome_center = (center[0], center[1] + height / 2, center[2])
        self.add_dome(center=dome_center, radius=radius, color=color)
        return self
    
    def add_tapered_midsection(self,
                                base_center: 'tuple[float, float, float]',
                                top_center: 'tuple[float, float, float]',
                                base_width: float,
                                top_width: float,
                                height: float,
                                color: 'tuple[float, float, float, float]' = (0, 0, 0, 1)):
        base = p3dc.Point3(base_center[0], base_center[1] - height / 2, base_center[2])
        top = p3dc.Point3(top_center[0], top_center[1] + height / 2, top_center[2])
        self.add_cylinder(base=base, base_radius=base_width / 2, top=top, top_radius=top_width / 2, color=color)
        return self
    
    def add_winged_midsection(self,
                            center: 'tuple[float, float, float]',
                            width: float,
                            length: float,
                            thickness: float,
                            color: 'tuple[float, float, float, float]' = (0, 0, 0, 1)):
        self.add_block(center=center, size=(width, length, thickness), color=color)
        # Add wings
        wing_offset = width / 2 + thickness / 2
        self.add_wedge(base=p3dc.Point3(center[0] - wing_offset, center[1], center[2]),
                        top=p3dc.Point3(center[0] - wing_offset - length / 2, center[1], center[2] + thickness / 2),
                        width=length, color=color)
        self.add_wedge(base=p3dc.Point3(center[0] + wing_offset, center[1], center[2]),
                        top=p3dc.Point3(center[0] + wing_offset + length / 2, center[1], center[2] + thickness / 2),
                        width=length, color=color)
        return self
    
    def add_ribbed_midsection(self,
                            center: 'tuple[float, float, float]',
                            width: float,
                            height: float,
                            depth: float,
                            rib_count: int,
                            rib_thickness: float,
                            color: 'tuple[float, float, float, float]' = (0, 0, 0, 1)):
        self.add_block(center=center, size=(width, height, depth), color=color)
        # Add ribs
        rib_spacing = height / (rib_count + 1)
        for i in range(1, rib_count + 1):
            rib_center = (center[0], center[1] - height / 2 + i * rib_spacing, center[2])
            self.add_block(center=rib_center, size=(width + rib_thickness, rib_thickness, depth + rib_thickness), color=color)
        return self
    
    def add_multi_layered_midsection(self,
                                    center: 'tuple[float, float, float]',
                                    width: float,
                                    height: float,
                                    depth: float,
                                    layer_count: int,
                                    variance_divisor: float,
                                    color: 'tuple[float, float, float, float]' = (0, 0, 0, 1)):
        for i in range(layer_count):
            layer_center = (center[0], center[1]-height/2 + i * height/layer_count+height/(layer_count)/2, center[2])
            j = i if i > layer_count/2 else layer_count-1-i
            layer_size = (width *(1+ layer_count/(j+1)/variance_divisor), height/(layer_count), depth*(1+ layer_count/(j+1)/variance_divisor))
            self.add_block(center=layer_center, size=layer_size, color=color)
        return self
    
    def add_scaled_midsection(self,
                            center: 'tuple[float, float, float]',
                            width: float,
                            height: float,
                            depth: float,
                            scale_count: int,
                            scale_spacing: float,
                            color: 'tuple[float, float, float, float]' = (0, 0, 0, 1)):
        for i in range(scale_count):
            scale_center = (center[0], center[1] - height / 2 + i * scale_spacing, center[2])
            scale_size = (width - i * scale_spacing, depth, height / scale_count)
            self.add_wedge(base=p3dc.Point3(scale_center[0], scale_center[1], scale_center[2] - scale_size[1] / 2),
                            top=p3dc.Point3(scale_center[0], scale_center[1], scale_center[2] + scale_size[1] / 2),
                            width=scale_size[0], color=color)
        return self
    
    def add_spherical_midsection(self,
                                center: 'tuple[float, float, float]',
                                radius: float,
                                sphere_count: int,
                                spacing: float,
                                color: 'tuple[float, float, float, float]' = (0, 0, 0, 1)):
        for i in range(sphere_count):
            sphere_center = (center[0], center[1] - (sphere_count / 2 - i) * spacing, center[2])
            self.add_sphere(center=sphere_center, radius=radius, color=color)
        return self
    
    def add_hardpointSection_block(self,
                module:'ProceduralShips.ShipModule',
                connection_front:'typing.Union[p3dc.Point3,typing.Iterable[float,float,float]]',
                connection_front_size:float,
                connection_rear:'typing.Union[p3dc.Point3,typing.Iterable[float,float,float]]',
                connection_rear_size:float,
                width:float,
                height:float,
                color:'tuple[float,float,float,float]' = (0,0,0,1),
                ):
        from ProceduralGeneration import ProceduralShips
        from BaseClasses import BaseModules
        connection_front, connection_rear = self.toPoint3(connection_front), self.toPoint3(connection_rear)
        block_center = connection_rear+(connection_front-connection_rear)/2
        module.addConnector(ProceduralShips.Directions.front, position=connection_front, connection_size=connection_front_size, color=color)
        self.add_block(center=block_center, size=(width,((connection_front-connection_rear)).y,height), color=color)
        module.addConnector(ProceduralShips.Directions.rear, position=connection_rear, connection_size=connection_rear_size, color=color)
        
        
        connection_size_turret = 1
        TurretConnectorOffset = 0
        numHardpoints:int = module.ExtraInfo.get("numHardpoints", 4)
        if numHardpoints > 4: raise Exception(f"{numHardpoints} is an invalid number of hardpoints for this module")
        if numHardpoints > 1: module.addConnector(ProceduralShips.Directions.left, position=block_center+(width/2+TurretConnectorOffset,0,0), connection_size=connection_size_turret, color=color)
        if numHardpoints > 1: module.addConnector(ProceduralShips.Directions.right, position=block_center+(-width/2-TurretConnectorOffset,0,0), connection_size=connection_size_turret, color=color)
        if numHardpoints != 2: module.addConnector(ProceduralShips.Directions.dorsal, position=block_center+(0,0,height/2+TurretConnectorOffset), connection_size=connection_size_turret, color=color)
        if numHardpoints == 4: module.addConnector(ProceduralShips.Directions.ventral, position=block_center+(0,0,-height/2-TurretConnectorOffset), connection_size=connection_size_turret, color=color)
        
        return self
    
    def add_aftSection_cone_static(self,
                module:'ProceduralShips.ShipModule',
                connection_front:'typing.Union[p3dc.Point3,typing.Iterable[float,float,float]]',
                connection_front_size:float,
                width:float,
                height:float,
                length:float,
                color:'tuple[float,float,float,float]' = (0,0,0,1),
                ):
        connection_front = self.toPoint3(connection_front)
        module.addConnector("front", position=connection_front, connection_size=connection_front_size, color=color)
        self.add_block(center=connection_front-p3dc.Point3(0,length/4,0), size=(width,length/2,height), color=color)
        self.add_cylinder(  base = connection_front-p3dc.Point3(0,length/2,0),
                            base_radius = height/4,
                            top = connection_front-p3dc.Point3(0,length,0),
                            top_radius = height/2,
                            radial_resolution = 10,
                            color = color,
                            top_cap_color= (1,0,0),
                            )
        return self
    
    def add_aftSection_cone(self,
                module:'ProceduralShips.ShipModule',
                width:float,
                height:float,
                length:float,
                connection_front_size:float = 2,
                color:'tuple[float,float,float,float]' = (0,0,0,1),
                ):
        connection_front = p3dc.Point3(0,0,0)
        module.addConnector("front", position=connection_front, connection_size=connection_front_size, color=color)
        self.add_block(center=connection_front-p3dc.Point3(0,length/2,0), size=(width,length,height), color=color)
        self.add_cylinder(  base = connection_front-p3dc.Point3(0,length,0),
                            base_radius = height/4,
                            top = connection_front-p3dc.Point3(0,length+(module.logicalModule().Thrust/4)**(0.8),0),
                            top_radius = height/2,
                            radial_resolution = 10,
                            color = color,
                            top_cap_color= (1,0,0),
                            )
        return self
    
    def add_turret_basic(self,
                module:'ProceduralShips.ShipModule',
                color:'tuple[float,float,float,float]' = (0,0,0,1),
                ):
        from BaseClasses import BaseModules
        if not module.logicalModule or not isinstance(module.logicalModule(),BaseModules.Weapon): raise Exception("A turret model must be connected to a turret module!")
        module.addConnector("radial", position=(0,0,-1), connection_size=1, thickness=0.5 ,color=color)
        self.add_block(center=(0,0,0), size=(2,2,2), color=color)
        self.add_cylinder(  base = (0,1,0),
                            base_radius = module.logicalModule().Damage/100,
                            top = (0,1+module.logicalModule().Range*1.5,0),
                            top_radius = module.logicalModule().Damage/100,
                            radial_resolution = 10,
                            color = color,
                            top_cap_color= (1,0,0),
                            )
        return self
