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
from ProceduralGeneration.GeomBuilder_base import to_cartesian

#CRITICAL: All the rotations are wrong in regards to the game. Everything lies on its side... This must be fixed!

class VertexDataWriter(GeomBuilder_base.VertexDataWriter):
    pass

class Polygon(GeomBuilder_base.Polygon):
    pass

class GeomBuilder(GeomBuilder_base.GeomBuilder):
    def add_sphere(self, color:'tuple[float,float,float,float]'=(0,0,0,0), center:'tuple[float,float,float]'=(0,0,0), radius:float=1, samples:int=60, planes:int=20):
        two_pi = math.pi * 2
        half_pi = math.pi / 2
        azimuths = [(two_pi * i) / samples for i in range(samples + 1)]
        elevations = [(math.pi * i) / (planes - 1)-half_pi for i in range(planes)]
        # Generate polygons for all but the top tier. (Quads)
        for i in range(1, len(elevations) - 2):
            for j in range(0, len(azimuths) - 1):
                x1, y1, z1 = to_cartesian(azimuths[j], elevations[i], radius)
                x2, y2, z2 = to_cartesian(azimuths[j], elevations[i + 1], radius)
                x3, y3, z3 = to_cartesian(azimuths[j + 1], elevations[i + 1], radius)
                x4, y4, z4 = to_cartesian(azimuths[j + 1], elevations[i], radius)
                
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
            x1, y1, z1 = to_cartesian(azimuths[k], elevations[len(elevations) - 2], radius)
            x2, y2, z2 = p3dc.Vec3(0, radius, 0)
            x3, y3, z3 = to_cartesian(azimuths[k + 1], elevations[len(elevations) - 2], radius)
            
            vertices = (
                p3dc.Point3(x1, y1, z1),
                p3dc.Point3(x2, y2, z2),
                p3dc.Point3(x3, y3, z3),
            )
            vertices = [v + p3dc.LVector3f(*center) for v in vertices]
            
            self._commit_polygon(Polygon(vertices), color)
        
        # Generate polygons for the bottom tier. (Tris)
        for k in range(0, len(azimuths) - 1):
            x1, y1, z1 = to_cartesian(azimuths[k+1], elevations[1], radius)
            x2, y2, z2 = p3dc.Vec3(0, -radius, 0)
            x3, y3, z3 = to_cartesian(azimuths[k], elevations[1], radius)
            
            vertices = (
                p3dc.Point3(x1, y1, z1),
                p3dc.Point3(x2, y2, z2),
                p3dc.Point3(x3, y3, z3),
            )
            vertices = [v + p3dc.LVector3f(*center) for v in vertices]
            
            self._commit_polygon(Polygon(vertices), color)
        
        return self
    
    def add_asteroid(self,
                color:'tuple[float,float,float,float]' = (200/255,100/255,70/255,1),
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
                rng:np.random.Generator = None,
                ):
        if rng is None: rng = np.random.default_rng()
        if rot is None: rot = p3dc.LRotationf(rng.uniform(0,360),rng.uniform(0,360),rng.uniform(0,360))
        import pyvista as pv
        #freq = [rng.uniform(0.2,0.7),rng.uniform(0.2,0.7),rng.uniform(0.2,0.7)]
        #noise = pv.perlin_noise(rng.uniform(0.2,0.7), freq, (0, 0, 0))
        
        c_min,c_max = color_randomness # c_min,c_max later get redefined! The variable names should not be the same between them but the name is perfect for both and I don't want the naming to get too complicated...
        color = (color[0]*rng.uniform(c_min,c_max), color[1]*rng.uniform(c_min,c_max), color[2]*rng.uniform(c_min,c_max), color[3])
        
        c_min,c_max = color_variance
        f_min,f_max = frequency_variance
        a_min,a_max = amplitude_variance
        
        mesh:'pv.PolyData' = pv.Sphere(radius=radius, phi_resolution=phi_resolution, theta_resolution=theta_resolution)
        # query the noise at each point manually
        for _ in range(noise_passes):
            freq = [rng.uniform(f_min,f_max),rng.uniform(f_min,f_max),rng.uniform(f_min,f_max)]
            phase = [rng.uniform(0,1),rng.uniform(0,1),rng.uniform(0,1)]
            noise = pv.perlin_noise(rng.uniform(a_min,a_max), freq, phase)
            mesh['scalars'] = [noise.EvaluateFunction(point) for point in mesh.points]
            mesh = mesh.warp_by_scalar('scalars')
            mesh = mesh.extract_surface()
        
        mesh = mesh.warp_by_scalar('scalars')
        mesh = mesh.extract_surface()
        faces = mesh.faces.reshape(-1, 4)
        for i in faces:
            x1, y1, z1 = mesh.points[i[1]]
            x2, y2, z2 = mesh.points[i[2]]
            x3, y3, z3 = mesh.points[i[3]]
            #x4, y4, z4 = mesh.points[i[]]
            
            vertices = (
                p3dc.Point3(x1, y1, z1),
                p3dc.Point3(x2, y2, z2),
                p3dc.Point3(x3, y3, z3),
                #p3dc.Point3(x4, y4, z4),
            )
            vertices = [rot.xform(v) + p3dc.LVector3f(*center) for v in vertices]
            c = (color[0]*rng.uniform(c_min,c_max), color[1]*rng.uniform(c_min,c_max), color[2]*rng.uniform(c_min,c_max), color[3])
            self._commit_polygon(Polygon(vertices), c)
        
        return self
