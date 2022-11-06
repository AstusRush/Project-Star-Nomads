"""
Copyright 2021 D. Watson, J. Voss, R. Herriman, A. Halstead
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

# Source: https://gist.github.com/assertivist/4598253afda3562c1960
# This file has been slightly modified by Robin 'Astus' Albers: improved imports and added type hints

# USAGE:
# First instantiate GeomBuilder with a name:
#
#     gb = GeomBuilder('box')
#
# Next call an add_<shape> method on GeomBuilder. For example we have "add_block" which takes color, center origin, and extents:
#
#     gb.add_block([1,0,1,1], (0,0,0), (1,1,1)) # for a purple unit cube
#
# Finally, call get_geom_node() and pass its result into NodePath() to get a node to attach to render:
#
#     node = NodePath(gb.get_geom_node())
#     node.attach_to(render)
# 
# The methods available on GeomBuilder are:
# add_tri - Adds a double-sided triangle mesh
# add_rect - Single sided quad made from two triangles
# add_block - Cube shape
# add_ramp - This is basically a rectangle that is tilted to form a ramp
# add_wedge - This is pretty much an extruded triangle shape
# add_dome - Very simple UV half-sphere generation

import math
import panda3d.core as p3dc

class InvalidPrimitive(Exception):
    pass

class VertexDataWriter():
    def __init__(self, vdata:'p3dc.GeomVertexData'):
        self.count = 0
        self.vertex = p3dc.GeomVertexWriter(vdata, 'vertex')
        self.normal = p3dc.GeomVertexWriter(vdata, 'normal')
        self.color = p3dc.GeomVertexWriter(vdata, 'color')
        self.texcoord = p3dc.GeomVertexWriter(vdata, 'texcoord')
    
    def add_vertex(self, point:'p3dc.LVector3f', normal:'p3dc.LVector3f', color:'tuple[float,float,float,float]', texcoord:'tuple[float,float]'):
        self.vertex.add_data3f(point)
        self.normal.add_data3f(normal)
        self.color.add_data4f(*color)
        self.texcoord.add_data2f(*texcoord)
        self.count += 1

class Polygon():
    def __init__(self, points:'list[p3dc.LVector3f]'=None):
        self.points = points or []
    
    def get_normal(self) -> 'p3dc.LVector3f':
        seen = set()
        points = [p for p in self.points if p not in seen and not seen.add(p)]
        if len(points) >= 3:
            v1 = points[0] - points[1]
            v2 = points[1] - points[2]
            normal = v1.cross(v2)
            normal.normalize()
        else:
            normal = p3dc.Vec3.up()
        return normal

class GeomBuilder():
    def __init__(self, name:str='tris'):
        self.name = name
        self.vdata = p3dc.GeomVertexData(name, p3dc.GeomVertexFormat.get_v3n3cpt2(), p3dc.Geom.UHDynamic)
        self.writer = VertexDataWriter(self.vdata)
        self.tris = p3dc.GeomTriangles(p3dc.Geom.UHDynamic)
    
    def _commit_polygon(self, poly:Polygon, color:'tuple[float,float,float,float]'):
        """
        Transmutes colors and vertices for tris and quads into visible geometry.
        """
        point_id = self.writer.count
        for p in poly.points:
            self.writer.add_vertex(p, poly.get_normal(), color, (0.0, 1.0))
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
            raise InvalidPrimitive
    
    def add_tri(self, color:'tuple[float,float,float,float]', points:'list[p3dc.LVector3f]'):
        self._commit_polygon(Polygon(points), color)
        self._commit_polygon(Polygon(points[::-1]), color)
        return self
    
    def add_rect(self, color:'tuple[float,float,float,float]', x1:float, y1:float, z1:float, x2:float, y2:float, z2:float):
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
    
    def add_block(self, color:'tuple[float,float,float,float]', center:'tuple[float,float,float]', size:'tuple[float,float,float]', rot:'p3dc.LRotationf'=None):
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
    
    def add_ramp(self, color:'tuple[float,float,float,float]', base:'p3dc.Point3', top:'p3dc.Point3', width:float, thickness:float, rot:'p3dc.LRotationf'=None):
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
    
    def add_wedge(self, color:'tuple[float,float,float,float]', base:'p3dc.Point3', top:'p3dc.Point3', width:float, rot:'p3dc.LRotationf'=None):
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
    
    def add_dome(self, color:'tuple[float,float,float,float]'=(0,0,0,0), center:'tuple[float,float,float]'=(0,0,0), radius:float=1, samples:int=40, planes:int=20, rot:'p3dc.LRotationf'=None):
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
        
        return selfare
    def get_geom(self):
        geom = p3dc.Geom(self.vdata)
        geom.add_primitive(self.tris)
        return geom
    
    def get_geom_node(self):
        node = p3dc.GeomNode(self.name)
        node.add_geom(self.get_geom())
        return node


def pol_to_cart(azimuth:float, elevation:float, length:float): # Originally named to_cartesian
    x = length * math.sin(azimuth) * math.cos(elevation)
    y = length * math.sin(elevation)
    z = -length * math.cos(azimuth) * math.cos(elevation)
    return (x, y, z)
