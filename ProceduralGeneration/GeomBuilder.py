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

import math
from ProceduralGeneration import GeomBuilder_base
from ProceduralGeneration.GeomBuilder_base import pol_to_cart


#CRITICAL: All the rotations might be wrong in regards to the game. Everything lies on its side... This must be fixed!
#FEATURE: Procedurally generate textures and materials like in ProcTer_1_static_Function.p line 759-802


def getRotation(base:'p3dc.LPoint3f',top:'p3dc.LPoint3f') -> 'p3dc.LRotationf':
    d = (top-base).normalized()
    h = math.atan2(d.x, d.z) * 180 / math.pi # originally was d.x, d.y
    p = -math.asin(d.y) * 180 / math.pi # originally was d.z
    r = 0
    return p3dc.LRotationf(h,p,r)

class Convert:
    @classmethod
    def pol_to_cart(cls, r:float, φ:float, θ:float):
        x = r * math.sin(φ) * math.cos(θ)
        y = r * math.sin(φ) * math.sin(θ)
        z = r * math.cos(φ)
        return (x, y, z)
    @classmethod
    def cylinder_to_cart(cls, r:float, θ:float, z:float):
        return (r*math.cos(θ), r*math.sin(θ), z)

class VertexDataWriter(GeomBuilder_base.VertexDataWriter):
    def add_vertex(self, point: 'p3dc.LVector3f', normal: 'p3dc.LVector3f', color: 'tuple[float,float,float,float]', texcoord: 'tuple[float,float]'):
        if len(color) == 3: color = (*color,1)
        return super().add_vertex(point, normal, color, texcoord)

class Polygon(GeomBuilder_base.Polygon):
    pass

class GeomBuilder(GeomBuilder_base.GeomBuilder):
    def __init__(self, name: str = 'tris', rng:np.random.Generator = None):
        if rng is None: rng = np.random.default_rng()
        self.rng:np.random.Generator = rng
        self.name = name
        self.vdata = p3dc.GeomVertexData(name, p3dc.GeomVertexFormat.get_v3n3cpt2(), p3dc.Geom.UHDynamic)
        self.writer = VertexDataWriter(self.vdata)
        self.tris = p3dc.GeomTriangles(p3dc.Geom.UHDynamic)
    
    def _commit_polygon(self, poly:Polygon, color:'tuple[float,float,float,float]', uv:'list[tuple[float,float]]'=None):
        """
        Transmutes colors and vertices for tris and quads into visible geometry.
        """
        point_id = self.writer.count
        if uv is None: uv = [(0.0,0.0),(1.0,0.0),(1.0,1.0),(0.0,1.0),(0.0,0.0),(1.0,0.0),(1.0,1.0),(0.0,1.0)]
        for i,p in enumerate(poly.points):
            self.writer.add_vertex(p, poly.get_normal(), color, uv[i]) # (0.0, 1.0)
        if len(poly.points) == 3:
            self.tris.add_consecutive_vertices(point_id, 3)
            self.tris.close_primitive()
        elif len(poly.points) == 4:
            self.tris.add_vertex(point_id)
            self.tris.add_vertex(point_id + 1)
            self.tris.add_vertex(point_id + 3)
            self.tris.close_primitive()
            self.tris.add_consecutive_vertices(point_id + 1, 3)
            self.tris.close_primitive()
        else:
            raise GeomBuilder_base.InvalidPrimitive
    
    def toPoint3(self, p):
        if not isinstance(p,p3dc.Point3): p = p3dc.Point3(*p)
        return p
    
    def add_tri(self,
                points:'list[p3dc.LVector3f]',
                color:'tuple[float,float,float,float]' = (0,0,0,1),
                ):
        self._commit_polygon(Polygon(points), color)
        self._commit_polygon(Polygon(points[::-1]), color)
        return self
    
    def add_rect(self,
                x1:float,
                y1:float,
                z1:float,
                x2:float,
                y2:float,
                z2:float,
                color:'tuple[float,float,float,float]' = (0,0,0,1),
                ):
        p1 = p3dc.Point3(x1, y1, z1)
        p3 = p3dc.Point3(x2, y2, z2)
        
        # Make sure we draw the rect in the right plane.
        if x1 != x2:
            p2 = p3dc.Point3(x2, y1, z1)
            p4 = p3dc.Point3(x1, y2, z2)
        else:
            p2 = p3dc.Point3(x2, y2, z1)
            p4 = p3dc.Point3(x1, y1, z2)
        
        self._commit_polygon(Polygon([p1, p2, p3, p4]), color)
        
        return self
    
    def add_block(self,
                center:'tuple[float,float,float]',
                size:'tuple[float,float,float]',
                rot:'p3dc.LRotationf'=None,
                color:'tuple[float,float,float,float]' = (0,0,0,1),
                ):
        x_shift = size[0] / 2.0
        y_shift = size[1] / 2.0
        z_shift = size[2] / 2.0
        rot = p3dc.LRotationf(0, 0, 0) if rot is None else rot
        
        vertices = (
            p3dc.Point3(-x_shift, +y_shift, +z_shift),
            p3dc.Point3(-x_shift, -y_shift, +z_shift),
            p3dc.Point3(+x_shift, -y_shift, +z_shift),
            p3dc.Point3(+x_shift, +y_shift, +z_shift),
            p3dc.Point3(+x_shift, +y_shift, -z_shift),
            p3dc.Point3(+x_shift, -y_shift, -z_shift),
            p3dc.Point3(-x_shift, -y_shift, -z_shift),
            p3dc.Point3(-x_shift, +y_shift, -z_shift),
        )
        vertices = [rot.xform(v) + p3dc.LVector3f(*center) for v in vertices]
        
        faces = (
            # XY
            [vertices[0], vertices[1], vertices[2], vertices[3]],
            [vertices[4], vertices[5], vertices[6], vertices[7]],
            # XZ
            [vertices[0], vertices[3], vertices[4], vertices[7]],
            [vertices[6], vertices[5], vertices[2], vertices[1]],
            # YZ
            [vertices[5], vertices[4], vertices[3], vertices[2]],
            [vertices[7], vertices[6], vertices[1], vertices[0]],
        )
        
        if size[0] and size[1]:
            self._commit_polygon(Polygon(faces[0]), color)
            self._commit_polygon(Polygon(faces[1]), color)
        if size[0] and size[2]:
            self._commit_polygon(Polygon(faces[2]), color)
            self._commit_polygon(Polygon(faces[3]), color)
        if size[1] and size[2]:
            self._commit_polygon(Polygon(faces[4]), color)
            self._commit_polygon(Polygon(faces[5]), color)
        
        return self
    
    def add_ramp(self,
                base:'typing.Union[p3dc.Point3,typing.Iterable[float,float,float]]',
                top:'typing.Union[p3dc.Point3,typing.Iterable[float,float,float]]',
                width:float,
                thickness:float,
                rot:'p3dc.LRotationf'=None,
                color:'tuple[float,float,float,float]' = (0,0,0,1),
                ):
        base, top = self.toPoint3(base), self.toPoint3(top)
        midpoint = p3dc.Point3((top + base) / 2.0)
        rot = p3dc.LRotationf(0, 0, 0) if rot is None else rot
        
        # Temporarily move `base` and `top` to positions relative to a midpoint
        # at (0, 0, 0).
        if midpoint != p3dc.Point3(0, 0, 0):
            base = p3dc.Point3(base - (midpoint - p3dc.Point3(0, 0, 0)))
            top = p3dc.Point3(top - (midpoint - p3dc.Point3(0, 0, 0)))
        p3 = p3dc.Point3(top.get_x(), top.get_y() - thickness, top.get_z())
        p4 = p3dc.Point3(base.get_x(), base.get_y() - thickness, base.get_z())
        
        # Use three points to calculate an offset vector we can apply to `base`
        # and `top` in order to find the required vertices.
        offset = (p3dc.Point3(top + p3dc.Vec3(0, -1000, 0)) - base).cross(top - base)
        offset.normalize()
        offset *= (width / 2.0)
        
        vertices = (
            p3dc.Point3(top - offset),
            p3dc.Point3(base - offset),
            p3dc.Point3(base + offset),
            p3dc.Point3(top + offset),
            p3dc.Point3(p3 + offset),
            p3dc.Point3(p3 - offset),
            p3dc.Point3(p4 - offset),
            p3dc.Point3(p4 + offset),
        )
        vertices = [rot.xform(v) + p3dc.LVector3f(*midpoint) for v in vertices]
        
        faces = (
            # Top and bottom.
            [vertices[0], vertices[1], vertices[2], vertices[3]],
            [vertices[7], vertices[6], vertices[5], vertices[4]],
            # Back and front.
            [vertices[0], vertices[3], vertices[4], vertices[5]],
            [vertices[6], vertices[7], vertices[2], vertices[1]],
            # Left and right.
            [vertices[0], vertices[5], vertices[6], vertices[1]],
            [vertices[7], vertices[4], vertices[3], vertices[2]],
        )
        
        if width and (p3 - base).length():
            self._commit_polygon(Polygon(faces[0]), color)
            self._commit_polygon(Polygon(faces[1]), color)
        if width and thickness:
            self._commit_polygon(Polygon(faces[2]), color)
            self._commit_polygon(Polygon(faces[3]), color)
        if thickness and (p3 - base).length():
            self._commit_polygon(Polygon(faces[4]), color)
            self._commit_polygon(Polygon(faces[5]), color)
        
        return self
    
    def add_wedge(self,
                base:'typing.Union[p3dc.Point3,typing.Iterable[float,float,float]]',
                top:'typing.Union[p3dc.Point3,typing.Iterable[float,float,float]]',
                width:float,
                rot:'p3dc.LRotationf'=None,
                color:'tuple[float,float,float,float]' = (0,0,0,1),
                ):
        base, top = self.toPoint3(base), self.toPoint3(top)
        delta_y = top.get_y() - base.get_y()
        midpoint = p3dc.Point3((top + base) / 2.0)
        rot = p3dc.LRotationf(0, 0, 0) if rot is None else rot
        
        # Temporarily move `base` and `top` to positions relative to a midpoint
        # at (0, 0, 0).
        if midpoint != p3dc.Point3(0, 0, 0):
            base = p3dc.Point3(base - (midpoint - p3dc.Point3(0, 0, 0)))
            top = p3dc.Point3(top - (midpoint - p3dc.Point3(0, 0, 0)))
        p3 = p3dc.Point3(top.get_x(), base.get_y(), top.get_z())
        
        # Use three points to calculate an offset vector we can apply to `base`
        # and `top` in order to find the required vertices. Ideally we'd use
        # `p3` as the third point, but `p3` can potentially be the same as `top`
        # if delta_y is 0, so we'll just calculate a new point relative to top
        # that differs in elevation by 1000, because that sure seems unlikely.
        # The "direction" of that point relative to `top` does depend on whether
        # `base` or `top` is higher. Honestly, I don't know why that's important
        # for wedges but not for ramps.
        if base.get_y() > top.get_y():
            direction = p3dc.Vec3(0, 1000, 0)
        else:
            direction = p3dc.Vec3(0, -1000, 0)
        offset = (p3dc.Point3(top + direction) - base).cross(top - base)
        offset.normalize()
        offset *= (width / 2.0)
        
        vertices = (
            p3dc.Point3(top - offset),
            p3dc.Point3(base - offset),
            p3dc.Point3(base + offset),
            p3dc.Point3(top + offset),
            p3dc.Point3(p3 + offset),
            p3dc.Point3(p3 - offset),
        )
        vertices = [rot.xform(v) + p3dc.LVector3f(*midpoint) for v in vertices]
        
        faces = (
            # The slope.
            [vertices[0], vertices[1], vertices[2], vertices[3]],
            # The bottom.
            [vertices[5], vertices[4], vertices[2], vertices[1]],
            # The back.
            [vertices[0], vertices[3], vertices[4], vertices[5]],
            # The sides.
            [vertices[5], vertices[1], vertices[0]],
            [vertices[4], vertices[3], vertices[2]],
        )
        
        if width or delta_y:
            self._commit_polygon(Polygon(faces[0]), color)
        if width and (p3 - base).length():
            self._commit_polygon(Polygon(faces[1]), color)
        if width and delta_y:
            self._commit_polygon(Polygon(faces[2]), color)
        if delta_y and (p3 - base).length():
            self._commit_polygon(Polygon(faces[3]), color)
            self._commit_polygon(Polygon(faces[4]), color)
        
        return self
    
    def add_dome(self,
                center:'tuple[float,float,float]'=(0,0,0),
                radius:float=1,
                samples:int=40,
                planes:int=20,
                rot:'p3dc.LRotationf'=None,
                color:'tuple[float,float,float,float]' = (0,0,0,1),
                ):
        two_pi = math.pi * 2
        half_pi = math.pi / 2
        azimuths = [(two_pi * i) / samples for i in range(samples + 1)]
        elevations = [(half_pi * i) / (planes - 1) for i in range(planes)]
        rot = p3dc.LRotationf(0, 0, 0) if rot is None else rot
        
        # Generate polygons for all but the top tier. (Quads)
        for i in range(0, len(elevations) - 2):
            for j in range(0, len(azimuths) - 1):
                x1, y1, z1 = pol_to_cart(azimuths[j], elevations[i], radius)
                x2, y2, z2 = pol_to_cart(azimuths[j], elevations[i + 1], radius)
                x3, y3, z3 = pol_to_cart(azimuths[j + 1], elevations[i + 1], radius)
                x4, y4, z4 = pol_to_cart(azimuths[j + 1], elevations[i], radius)
                
                vertices = (
                    p3dc.Point3(x1, y1, z1),
                    p3dc.Point3(x2, y2, z2),
                    p3dc.Point3(x3, y3, z3),
                    p3dc.Point3(x4, y4, z4),
                )
                vertices = [rot.xform(v) + p3dc.LVector3f(*center) for v in vertices]
                
                self._commit_polygon(Polygon(vertices), color)
        
        # Generate polygons for the top tier. (Tris)
        for k in range(0, len(azimuths) - 1):
            x1, y1, z1 = pol_to_cart(azimuths[k], elevations[len(elevations) - 2], radius)
            x2, y2, z2 = p3dc.Vec3(0, radius, 0)
            x3, y3, z3 = pol_to_cart(azimuths[k + 1], elevations[len(elevations) - 2], radius)
            
            vertices = (
                p3dc.Point3(x1, y1, z1),
                p3dc.Point3(x2, y2, z2),
                p3dc.Point3(x3, y3, z3),
            )
            vertices = [rot.xform(v) + p3dc.LVector3f(*center) for v in vertices]
            
            self._commit_polygon(Polygon(vertices), color)
        
        return self
    
    def add_sphere(self,
                center:'tuple[float,float,float]'=(0,0,0),
                radius:float=1,
                samples:int=60,
                planes:int=20,
                color:'tuple[float,float,float,float]' = (0,0,0,1),
                ):
        #MAYBE: Handle this with pyvista so that the uv coordinates ca be generated by pyvista which would save a lot of work to handle this manually (especially important for planets)
        two_pi = math.pi * 2
        half_pi = math.pi / 2
        azimuths = [(two_pi * i) / samples for i in range(samples + 1)]
        elevations = [(math.pi * i) / (planes - 1)-half_pi for i in range(planes)]
        # Generate polygons for all but the top tier. (Quads)
        for i in range(1, len(elevations) - 2):
            for j in range(0, len(azimuths) - 1):
                x1, y1, z1 = pol_to_cart(azimuths[j], elevations[i], radius)
                x2, y2, z2 = pol_to_cart(azimuths[j], elevations[i + 1], radius)
                x3, y3, z3 = pol_to_cart(azimuths[j + 1], elevations[i + 1], radius)
                x4, y4, z4 = pol_to_cart(azimuths[j + 1], elevations[i], radius)
                
                vertices = (
                    p3dc.Point3(x1, y1, z1),
                    p3dc.Point3(x2, y2, z2),
                    p3dc.Point3(x3, y3, z3),
                    p3dc.Point3(x4, y4, z4),
                )
                vertices = [v + p3dc.LVector3f(*center) for v in vertices]
                
                self._commit_polygon(Polygon(vertices), color)
        
        # Generate polygons for the top tier. (Tris)
        for k in range(0, len(azimuths) - 1):
            x1, y1, z1 = pol_to_cart(azimuths[k], elevations[len(elevations) - 2], radius)
            x2, y2, z2 = p3dc.Vec3(0, radius, 0)
            x3, y3, z3 = pol_to_cart(azimuths[k + 1], elevations[len(elevations) - 2], radius)
            
            vertices = (
                p3dc.Point3(x1, y1, z1),
                p3dc.Point3(x2, y2, z2),
                p3dc.Point3(x3, y3, z3),
            )
            vertices = [v + p3dc.LVector3f(*center) for v in vertices]
            
            self._commit_polygon(Polygon(vertices), color)
        
        # Generate polygons for the bottom tier. (Tris)
        for k in range(0, len(azimuths) - 1):
            x1, y1, z1 = pol_to_cart(azimuths[k+1], elevations[1], radius)
            x2, y2, z2 = p3dc.Vec3(0, -radius, 0)
            x3, y3, z3 = pol_to_cart(azimuths[k], elevations[1], radius)
            
            vertices = (
                p3dc.Point3(x1, y1, z1),
                p3dc.Point3(x2, y2, z2),
                p3dc.Point3(x3, y3, z3),
            )
            vertices = [v + p3dc.LVector3f(*center) for v in vertices]
            
            self._commit_polygon(Polygon(vertices), color)
        
        return self
    
    def add_cylinder(self,
                base:'typing.Union[p3dc.Point3,typing.Iterable[float,float,float]]' = (0,0,0),
                base_radius:'float' = 1,
                top:'typing.Union[p3dc.Point3,typing.Iterable[float,float,float]]' = (0,0,1),
                top_radius:'float' = None,
                radial_resolution:'int' = 10,
                base_cap:'bool' = True,
                top_cap:'bool' = True,
                color:'tuple[float,float,float,float]' = (0,0,0,1),
                base_cap_color:'tuple[float,float,float,float]' = None,
                top_cap_color:'tuple[float,float,float,float]' = None,
                ):
        base = self.toPoint3(base)
        top = self.toPoint3(top)
        if top_radius is None: top_radius = base_radius
        if top_radius == 0 and base_radius == 0: raise Exception("ERROR: A cylinder was requested with no radius")
        if radial_resolution <= 0: raise Exception("ERROR: A cylinder was requested with no (or a negative) resolution")
        if base_cap_color is None: base_cap_color = color
        if top_cap_color is None: top_cap_color = color
        azimuths = [(2*np.pi*i) / radial_resolution for i in range(radial_resolution + 1)]
        
        length = (base-top).length()
        rot = getRotation(base,top)
        
        # Generate polygons for the mantle. (Quads)
        for j in range(0, len(azimuths) - 1):
            x1, y1, z1 = Convert.cylinder_to_cart(base_radius, azimuths[j], 0)
            x2, y2, z2 = Convert.cylinder_to_cart(base_radius, azimuths[j+1], 0)
            x3, y3, z3 = Convert.cylinder_to_cart(top_radius, azimuths[j+1], length)
            x4, y4, z4 = Convert.cylinder_to_cart(top_radius, azimuths[j], length)
            
            vertices = (
                p3dc.Point3(x1, y1, z1),
                p3dc.Point3(x2, y2, z2),
                p3dc.Point3(x3, y3, z3),
                p3dc.Point3(x4, y4, z4),
            )
            vertices = [rot.xform(v) + base for v in vertices]
            self._commit_polygon(Polygon(vertices), color)
        
        if base_cap:
            # Generate polygons for the base cap. (Tris)
            for j in range(0, len(azimuths) - 1):
                x1, y1, z1 = Convert.cylinder_to_cart(base_radius, azimuths[j+1], 0)
                x2, y2, z2 = Convert.cylinder_to_cart(base_radius, azimuths[j], 0)
                x3, y3, z3 = Convert.cylinder_to_cart(0, 0, 0)
                
                vertices = (
                    p3dc.Point3(x1, y1, z1),
                    p3dc.Point3(x2, y2, z2),
                    p3dc.Point3(x3, y3, z3),
                )
                vertices = [rot.xform(v) + base for v in vertices]
                self._commit_polygon(Polygon(vertices), base_cap_color)
        
        if top_cap:
            # Generate polygons for the top cap. (Tris)
            for j in range(0, len(azimuths) - 1):
                x1, y1, z1 = Convert.cylinder_to_cart(top_radius, azimuths[j], length)
                x2, y2, z2 = Convert.cylinder_to_cart(top_radius, azimuths[j+1], length)
                x3, y3, z3 = Convert.cylinder_to_cart(0, 0, length)
                
                vertices = (
                    p3dc.Point3(x1, y1, z1),
                    p3dc.Point3(x2, y2, z2),
                    p3dc.Point3(x3, y3, z3),
                )
                vertices = [rot.xform(v) + base for v in vertices]
                self._commit_polygon(Polygon(vertices), top_cap_color)
        
        return self
    
    def add_asteroid(self,
                color_randomness:'tuple[float,float]' = (0.6,1),
                color_variance:'tuple[float,float]' = (0.2,0.4),
                center:'tuple[float,float,float]' = (0,0,0),
                radius:float = 1,
                phi_resolution:int = 10,
                theta_resolution:int = 10,
                frequency_variance:'tuple[float,float]' = (0.2,0.7),
                amplitude_variance:'tuple[float,float]' = (0.2,1),
                noise_passes:int = 3,
                rot:'p3dc.LRotationf' = None,
                color:'tuple[float,float,float,float]' = (200/255,100/255,70/255,1),
                colour_faces = False,
                ):
        if rot is None: rot = p3dc.LRotationf(self.rng.uniform(0,360),self.rng.uniform(0,360),self.rng.uniform(0,360))
        import pyvista as pv
        #freq = [self.rng.uniform(0.2,0.7),self.rng.uniform(0.2,0.7),self.rng.uniform(0.2,0.7)]
        #noise = pv.perlin_noise(self.rng.uniform(0.2,0.7), freq, (0, 0, 0))
        
        c_min,c_max = color_randomness # c_min,c_max later get redefined! The variable names should not be the same between them but the name is perfect for both and I don't want the naming to get too complicated...
        color = (color[0]*self.rng.uniform(c_min,c_max), color[1]*self.rng.uniform(c_min,c_max), color[2]*self.rng.uniform(c_min,c_max), color[3])
        
        c_min,c_max = color_variance
        f_min,f_max = frequency_variance
        a_min,a_max = amplitude_variance
        amplitude = self.rng.uniform(a_min,a_max)
        
        mesh:'pv.PolyData' = pv.Sphere(radius=radius, phi_resolution=phi_resolution, theta_resolution=theta_resolution)
        # query the noise at each point manually
        for _ in range(noise_passes):
            freq = [self.rng.uniform(f_min,f_max),self.rng.uniform(f_min,f_max),self.rng.uniform(f_min,f_max)]
            phase = [self.rng.uniform(0,1),self.rng.uniform(0,1),self.rng.uniform(0,1)]
            noise = pv.perlin_noise(amplitude, freq, phase)
            #CRITICAL: The perlin noise moves from -amplitude to amplitude. Therefore the parameter must be amplitude/2 and we must add amplitude to all values
            mesh['scalars'] = [noise.EvaluateFunction(point) for point in mesh.points]
            mesh = mesh.warp_by_scalar('scalars')
            mesh = mesh.extract_surface()
        
        mesh = mesh.warp_by_scalar('scalars')
        mesh = mesh.extract_surface()
        #
        #from pyvista import examples
        #tex = examples.download_masonry_texture()
        mesh.texture_map_to_sphere(inplace=True)
        #mesh.text
        #mesh.plot(texture=tex)
        #
        faces = mesh.faces.reshape(-1, 4)
        for face in faces:
            x1, y1, z1 = mesh.points[face[1]]
            x2, y2, z2 = mesh.points[face[2]]
            x3, y3, z3 = mesh.points[face[3]]
            
            vertices = (
                p3dc.Point3(x1, y1, z1),
                p3dc.Point3(x2, y2, z2),
                p3dc.Point3(x3, y3, z3),
            )
            uv = (
                mesh.active_t_coords[face[1]],
                mesh.active_t_coords[face[2]],
                mesh.active_t_coords[face[3]],
                #((i)/len(faces), (i)/len(faces)),
                #((i+1)/len(faces), (i+1)/len(faces)),
                #((i)/len(faces), (i+1)/len(faces)),
            )
            vertices = [rot.xform(v) + p3dc.LVector3f(*center) for v in vertices]
            if colour_faces: c = (color[0]*self.rng.uniform(c_min,c_max), color[1]*self.rng.uniform(c_min,c_max), color[2]*self.rng.uniform(c_min,c_max), color[3])
            else: c = (1,1,1,1)
            self._commit_polygon(Polygon(vertices), c, uv)#c)
        
        return self
