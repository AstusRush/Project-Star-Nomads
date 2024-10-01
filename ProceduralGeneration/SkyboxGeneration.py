"""
This module handles the Skybox Generation \n
Inspired by https://github.com/ProPuke/space-3d
(which is a fork of a fork of https://github.com/wwwtyro/space-3d ) \n
"""
"""
    Copyright (C) 2021  Robin Albers
"""

#from panda3d.core import loadPrcFileData
#loadPrcFileData('', 'notify-level-glgsg debug')

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
import math
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

from ProceduralGeneration import ShaderTools

# Helper function to create a box geometry
def buildBox_old(radius, shader):
    format = p3dc.GeomVertexFormat.getV3()
    vdata = p3dc.GeomVertexData('box', format, p3dc.Geom.UHStatic)
    
    vertex = p3dc.GeomVertexWriter(vdata, 'vertex')
    vertices = [
        (-radius, -radius, -radius),
        (radius, -radius, -radius),
        (radius, radius, -radius),
        (-radius, -radius, -radius),
        (radius, radius, -radius),
        (-radius, radius, -radius),
        
        (radius, -radius, radius),
        (-radius, -radius, radius),
        (-radius, radius, radius),
        (radius, -radius, radius),
        (-radius, radius, radius),
        (radius, radius, radius)
    ]
    
    for v in vertices:
        vertex.addData3f(*v)
    
    prim = p3dc.GeomTriangles(p3dc.Geom.UHStatic)
    indices = [
        (0, 1, 2), (0, 2, 3),
        (4, 5, 6), (4, 6, 7),
        (8, 9, 10), (8, 10, 11)
    ]
    
    for idx in indices:
        prim.addVertices(*idx)
        prim.closePrimitive()
    
    geom = p3dc.Geom(vdata)
    geom.addPrimitive(prim)
    
    node = p3dc.GeomNode('gnode')
    node.addGeom(geom)
    gnode_path = p3dc.NodePath(node)
    gnode_path.setShader(shader)
    
    return gnode_path


#NOTE: self.pStar.setUniform("uFalloff", "1f", s.falloff);
#       The `.setUniform` is performed on the node in panda3d with `.setShaderInput("uFalloff", s.falloff)` (omitting the "1f")

"""
params = {
    "seed": menu.seed,
    "backgroundColor": menu.backgroundColor,
    "pointStars": menu.pointStars,
    "stars": menu.stars,
    "sun": menu.sun,
    "sunFalloff": menu.sunFalloff,
    "jpegQuality": menu.jpegQuality,
    "nebulaColorBegin": menu.nebulaColorBegin,
    "nebulaColorEnd": menu.nebulaColorEnd,
    "nebulae": menu.nebulae,
    "resolution": menu.resolution
}
"""

class SkyboxGenerator:
    NSTARS = 100000
    def getSkybox(self,params:"typing.Dict[str,typing.Any]") -> 'p3dc.NodePath':
        tex = self.render(params)
        self.cleanUp()
        skyShader = ShaderTools.loadShader("skybox.glsl")
        skybox = self.buildBox(1, skyShader)
        
        skybox.setTexGen(p3dc.TextureStage.getDefault(), p3dc.TexGenAttrib.MWorldCubeMap)
        
        skybox.setTexture(tex)
        self.updateUniforms(skybox,{"skybox":tex})
        return skybox
    
    #MAYBE: Add a method that uses the shader skybox but turns it into a screenshot to as with the static skybox
    
    def __init__(self) -> None:
        self.Skybox = p3dc.NodePath(p3dc.PandaNode("SpaceSkyBox"))
        self.gl = None
        self.canvas = None
        
        self.Scene = p3dc.NodePath("My Scene")
        self.Scene.reparentTo(render())
        self.AmbientLight = p3dc.AmbientLight("ambientLight")
        self.AmbientLight.setColor((.8, .8, .8, 1))
        self.Scene.setLight(self.Scene.attachNewNode(self.AmbientLight))
        
        ## Initialize the gl context.
        #self.gl.enable(self.gl.BLEND);
        #self.gl.blendFuncSeparate(
        #    self.gl.SRC_ALPHA,
        #    self.gl.ONE_MINUS_SRC_ALPHA,
        #    self.gl.ZERO,
        #    self.gl.ONE
        #);
        
        # Load the programs.
        self.pPointStars = ShaderTools.loadShader("point-stars.glsl")
        self.pNebula = ShaderTools.loadShader("nebula.glsl")
        self.pStar = ShaderTools.loadShader("star.glsl")
        self.pSun = ShaderTools.loadShader("sun.glsl")
        
        self.TheBuffer:'typing.Union[p3dc.GraphicsOutput,None]' = None
        self.rStars:'typing.List[p3dc.NodePath]' = []
        self.rPointStars:'typing.Union[p3dc.NodePath,None]' = None
        self.rNebulae:'typing.List[p3dc.NodePath]' = []
        
        self.SkyShader = ShaderTools.loadShader("skyboxShader.glsl")
        self.Skybox:'typing.Union[p3dc.NodePath,None]' = None
        
        self.CubeDisplay = self.buildBox(1/2, None, False)
        self.CubeDisplay.reparentTo(self.Scene)
        self.CubeDisplay.setColor(1,1,1)
        self.CubeDisplay.hide()
        self.CubeDisplay.setPos(-0.5,1,0)
        
        ## self.attribs = p3dc.ColorAttrib
        #self.attribs = webgl.buildAttribs(self.gl, { aPosition: 3, aColor: 3 })
        #self.attribs.aPosition.buffer.set(position)
        #self.attribs.aColor.buffer.set(color)
        #count = position.length / 9
        #self.rPointStars = p3dc.render
        #self.rPointStars = webgl.Renderable(
        #    self.gl,
        #    self.pPointStars,
        #    self.attribs,
        #    count
        #)
        #
        ## Create the nebula, sun, and star renderables.
        #self.rNebula = self.buildBox(self.gl, 1.0, self.pNebula)
        #self.rSun = self.buildBox(self.gl, 0.45, self.pSun)
        #self.rStar = self.buildBox(self.gl, 0.0055, self.pStar)
    
    def __del__(self):
        self.cleanUp()
        self.CubeDisplay.removeNode()
        self.Scene.removeNode()
    
    def randomUniformMirror(self, rand:'random.Random',minDistance=0.5):
        return rand.choice((-1,1)) * rand.uniform(minDistance,1)
    
    def randomUniformMirrorVec3(self, rand:'random.Random',minDistance=0.5):
        l = [self.randomUniformMirror(rand,minDistance), rand.uniform(-1,1), rand.uniform(-1,1)]
        rand.shuffle(l)
        return p3dc.Vec3(*l)
    
    def randomPointOnSphere(self, rand:'random.Random', minDistance=0.5, maxDistance=1):
        # This Function was actually written by ChatGPT4o
        # It usually only produces un-useable garbage code but it got this method right 2nd try!
        
        # Ensure minDistance is less than or equal to maxDistance
        if minDistance > maxDistance:
            raise ValueError("minDistance must be less than or equal to maxDistance")
        
        # Generate a random distance between minDistance and maxDistance
        distance = rand.uniform(minDistance, maxDistance)
        
        # Generate a random azimuthal angle theta between 0 and 2*pi
        theta = rand.uniform(0, 2 * math.pi)
        
        # Generate a uniform random value for cos(phi) between -1 and 1
        cos_phi = rand.uniform(-1, 1)
        
        # Calculate the polar angle phi from cos_phi
        phi = math.acos(cos_phi)
        
        # Convert spherical coordinates to Cartesian coordinates
        x = distance * math.sin(phi) * math.cos(theta)
        y = distance * math.sin(phi) * math.sin(theta)
        z = distance * math.cos(phi)
        
        return p3dc.Vec3(x,y,z)
    
    def randomVec3(self, rand:'random.Random'):
        return p3dc.Vec3(rand.random(), rand.random(), rand.random())
    
    def buildBox(self, radius, shader, applyShader=True):
        "Helper function to create a box geometry"
        gnode_path = ape.loadModel("../Project-Star-Nomads/Models/Simple Geometry/cube.ply")
        if applyShader: gnode_path.setShader(shader)
        gnode_path.setScale(radius*2)
        return gnode_path
    
    def buildSphere(self, radius, shader, applyShader=True):
        "Helper function to create a box geometry"
        gnode_path = ape.loadModel("../Project-Star-Nomads/Models/Simple Geometry/sphere.ply")
        if applyShader: gnode_path.setShader(shader)
        gnode_path.setScale(radius*2)
        return gnode_path
    
    def createRenderable(self, shader, attribs):
        node = p3dc.GeomNode('renderable')
        node.addGeom(attribs)
        node_path = p3dc.NodePath(node)
        node_path.setShader(shader)
        return node_path
    
    def buildAttribs(self, position, color):
        format = p3dc.GeomVertexFormat.getV3c4()
        vdata = p3dc.GeomVertexData('points', format, p3dc.Geom.UHStatic)
        
        vertex = p3dc.GeomVertexWriter(vdata, 'vertex')
        color_writer = p3dc.GeomVertexWriter(vdata, 'color')
        
        for i in range(0, len(position), 3):
            vertex.addData3f(position[i], position[i+1], position[i+2])
            color_writer.addData4f(color[i], color[i+1], color[i+2], 1.0)
        
        geom = p3dc.Geom(vdata)
        prim = p3dc.GeomTriangles(p3dc.Geom.UHStatic)
        
        for i in range((len(position) // 3)-2):
            prim.addVertices(i, (i + 1) % len(position), (i + 2) % len(position))
            prim.closePrimitive()
        
        geom.addPrimitive(prim)
        return geom
    
    def buildStar(self, size, pos, dist, rand:'random.Random'):
        #color = [(rand.random() ** 4.0,rand.random() ** 4.0,rand.random() ** 4.0,1) for i in range(6)]
        color = [(rand.uniform(0.9,1.0) ** 4.0,rand.uniform(0.9,1.0) ** 4.0,rand.uniform(0.9,1.0) ** 4.0,1) for i in range(6)]
        vertices = [
            (-size, -size, 0),
            (size, -size, 0),
            (size, size, 0),
            (-size, -size, 0),
            (size, size, 0),
            (-size, size, 0)
        ]
        position = []
        
        for vertex in vertices:
            v = p3dc.Vec3(*vertex)
            v += pos * dist
            position.append([v.x, v.y, v.z])
        
        return {'position': position, 'color': color}
    
    def cleanUp(self):
        for i in self.rStars:
            i.removeNode()
        self.rStars:'typing.List[p3dc.NodePath]' = []
        if self.rPointStars:
            self.rPointStars.removeNode()
            self.rPointStars = None
        for i in self.rNebulae:
            i.removeNode()
        self.rNebulae:'typing.List[p3dc.NodePath]' = []
        self.CubeDisplay.hide()
        if self.TheBuffer:
            base().graphicsEngine.removeWindow(self.TheBuffer)
            self.TheBuffer = None
    
    def render(self, params:"typing.Dict[str,typing.Any]"):
        self.cleanUp()
        
        # Render the scene.
        backgroundColor = params["backgroundColor"]
        backgroundColorVec = p3dc.Vec4F(backgroundColor[0]/255.0, backgroundColor[1]/255.0, backgroundColor[2]/255.0, 1.0)
        base().win.setClearColor(backgroundColorVec)
        base().win.setClearColorActive(True)
        
        if True:
            view = p3dc.LMatrix4()
            projection = p3dc.LMatrix4(math.pi / 2, 1.0, 0.1, 256)
            
            if params["pointStars"]:
                self.makePointStars(params, view, projection)
            if params["stars"]:
                self.makeBrightStars(params, view, projection)
            if params["sun"]:
                self.makeSun(params, view, projection)
            if params["nebulae"]:
                self.makeNebulae(params, view, projection)
        
        base().graphicsEngine.renderFrame()
        textures = self.makeCubeMap("Models/Skyboxes/LastGenerated/Skybox_#.jpeg",size=params['resolution'])#,0,buffer)
        
        return textures
    
    def makeCubeMap(self, namePrefix = 'cube_map_#.png',
                    defaultFilename = 0, source:"p3dc.GraphicsOutput" = None,
                    camera:"p3dc.Camera" = None, size = 128,
                    cameraMask = p3dc.PandaNode.getAllCameraMask(),
                    sourceLens:"p3dc.Lens" = None,
                    save = False):
        
        if source is None:
            source = base().win
        
        if camera is None:
            if hasattr(source, "getCamera"):
                camera = source.getCamera()
            if camera is None:
                camera = base().camera
        
        if sourceLens is None:
            sourceLens = base().camLens
        
        if hasattr(source, "getWindow"):
            source = source.getWindow()
        
        rig = p3dc.NodePath(namePrefix)
        buffer = source.makeCubeMap(namePrefix, size, rig, cameraMask, 1)
        if buffer is None:
            raise Exception("Could not make cube map.")
        
        # Set the near and far planes from the default lens.
        lens:"p3dc.Lens" = rig.find('**/+Camera').node().getLens()
        
        lens.setNearFar(sourceLens.getNear(), sourceLens.getFar())
        
        # Now render a frame to fill up the texture.
        rig.reparentTo(camera)
        base().graphicsEngine.openWindows()
        base().graphicsEngine.renderFrame()
        base().graphicsEngine.renderFrame()
        base().graphicsEngine.syncFrame()
        
        tex = buffer.getTexture()
        if save:
            saved = base().screenshot(namePrefix = namePrefix,
                                    defaultFilename = defaultFilename,
                                    source = tex)
        
        base().graphicsEngine.removeWindow(buffer)
        rig.removeNode()
        
        return tex # saved
    
    def makePointStars(self, params, view, projection):
        #num_stars = 200
        num_stars = self.NSTARS
        rand = random.Random(hash(params["seed"]) + 5000)
        
        # Create vertex data
        vformat = p3dc.GeomVertexFormat.getV3c4()
        vdata = p3dc.GeomVertexData("point_stars", vformat, p3dc.Geom.UHStatic)
        vdata.setNumRows(num_stars*6)
        vertex_writer = p3dc.GeomVertexWriter(vdata, 'vertex')
        color_writer = p3dc.GeomVertexWriter(vdata, 'color')
        
        # Generate star data for a batch
        for _ in range(num_stars):
            #size = 0.05
            size = 0.0005
            #pos = self.randomVec3(rand)
            #pos = self.randomUniformMirrorVec3(rand, 0.8)
            pos = self.randomPointOnSphere(rand, 0.8)
            #star = self.buildStar(size, pos, 128.0, rand)
            star = self.buildStar(size, pos, 10.0, rand)
            for i in star['position']:
                #vertex_writer.addData3f(*i)
                vertex_writer.setData3(*i)
            for i in star['color']:
                color_writer.addData4f(*i)
        
        # Create geometry and renderable
        primitive = p3dc.GeomPoints(p3dc.Geom.UHStatic)
        primitive.add_next_vertices(num_stars*6)
        geom = p3dc.Geom(vdata)
        geom.addPrimitive(primitive)
        node = p3dc.GeomNode('gnode')
        node.addGeom(geom)
        self.rPointStars = p3dc.NodePath("point_stars")
        self.rPointStars.attachNewNode(node)
        if True:
            self.rPointStars.setShader(self.pPointStars)
            
            # Set shader uniforms (view and projection once)
            self.rPointStars.set_shader_input("uView", view)
            self.rPointStars.set_shader_input("uModel", view)
            self.rPointStars.set_shader_input("uProjection", projection)
        
        self.rPointStars.reparentTo(self.Scene)
        self.rPointStars.show()
        
        #self.rPointStars.setPos(-self.rPointStars.getTightBounds()[0])
        self.rPointStars.setPos(-self.rPointStars.getBounds().getApproxCenter())
    
    def makePointStars_o(self, params, view, projection):
        # Create the point stars renderable.
        rand = random.Random(hash(params["seed"]) + 5000)
        position = np.zeros(18 * self.NSTARS)
        color = np.zeros(18 * self.NSTARS)
        for i in range(self.NSTARS):
            size = 0.05
            pos = p3dc.Vec3(rand.random(),rand.random(),rand.random())
            star = self.buildStar(size, pos, 128.0, rand)
            position[i*18:(i+1)*18] = star['position']
            color[i*18:(i+1)*18] = star['color']
        
        self.attribs = self.buildAttribs(position, color)
        self.rPointStars = self.createRenderable(self.pPointStars, self.attribs)
        self.rPointStars.reparentTo(self.Scene)
        
        # Initialize the point star parameters.
        rand = random.Random(hash(params["seed"]) + 1000)
        pStarParams = []
        model = p3dc.LMatrix4()
        while params['pointStars']:
            model = model * p3dc.LMatrix4.rotateMat(rand.random() * 360, p3dc.LVector3(rand.random(), rand.random(), rand.random()))
            pStarParams.append({
                'uView': view,
                'uProjection': projection,
                'uModel': model,
            })
            if rand.random() < 0.2:
                break
        for i in pStarParams:
            self.updateUniforms(self.rPointStars, i)
        self.rPointStars.show()
    
    def makeBrightStars(self, params, view, projection):
        # Initialize the star parameters.
        rand = random.Random(hash(params['seed']) + 3000)
        count = 0
        for _ in range(params['stars']):
            count += 1
            if count == 1:
                rStar = self.buildSphere(0.0055, self.pStar)
                rStar.reparentTo(self.Scene)
            else:
                rStar = rStar.copy_to(self.Scene)
                rStar.setShader(self.pStar)
            
            self.rStars.append(rStar)
            colours = [1, rand.uniform(0.4,0.8), rand.uniform(0.4,0.8)]
            rand.shuffle(colours)
            cl = p3dc.LVector3(colours[0], colours[1], colours[2])
            #pos = p3dc.LVector3(rand.random(), rand.random(), rand.random())
            pos = self.randomPointOnSphere(rand, 14, 20)
            rStar.setPos(pos)
            model = p3dc.LMatrix4(p3dc.LMatrix3(), pos)
            starParams = {
                'uView': view,
                'uModel': model,
                'uPosition': pos,
                'uColor': cl,
                'uSize': rand.random() * 0.00000002 + 0.00000001,
                'uFalloff': rand.random() * (2**15) + (2**15),
                'uProjection': projection,
            }
            self.updateUniforms(rStar, starParams)
            rStar.show()
        self.Scene.flatten_strong()
    
    def makeNebulaObject(self):
        nebula = self.buildSphere(20000.0, self.pNebula)
        nebula.setDepthWrite(False)
        nebula.setTransparency(p3dc.TransparencyAttrib.M_alpha)
        
        skybox_texture = p3dc.Texture('NebulaTexture')
        skybox_texture.set_minfilter(p3dc.SamplerState.FT_linear)
        skybox_texture.set_magfilter(p3dc.SamplerState.FT_linear)
        skybox_texture.set_wrap_u(p3dc.SamplerState.WM_repeat)
        skybox_texture.set_wrap_v(p3dc.SamplerState.WM_mirror)
        skybox_texture.set_anisotropic_degree(16)
        
        ts = p3dc.TextureStage
        skybox_texture_stage = p3dc.TextureStage('NebulaTextureStage')
        skybox_texture_stage.setCombineRgb(ts.CMModulate, ts.CS_texture, ts.CO_src_alpha, ts.CS_previous, ts.CO_one_minus_src_alpha)
        skybox_texture_stage.setCombineAlpha(ts.CM_replace, ts.CS_texture, ts.CO_src_alpha)
        
        nebula.setTexture(skybox_texture_stage, skybox_texture)
        nebula.reparentTo(self.Scene)
        return nebula
    
    def makeNebulae(self, params, view, projection):
        rand = random.Random(hash(params['seed']) + 2000)
        nebulaParams = []
        beginColor = params['nebulaColorBegin']
        endColor = params['nebulaColorEnd']
        countNebulas = int(2 + rand.random() * 3)
        if params['nebulae']:
            model = p3dc.LMatrix4()
            for ni in range(countNebulas):
                middleColor = [
                    (beginColor[0] + ni * (endColor[0] - beginColor[0]) / (countNebulas - 1)) / 255,
                    (beginColor[1] + ni * (endColor[1] - beginColor[1]) / (countNebulas - 1)) / 255,
                    (beginColor[2] + ni * (endColor[2] - beginColor[2]) / (countNebulas - 1)) / 255
                ]
                nebulaParams.append({
                    'uView': view,
                    'uModel': model,
                    'uScale': rand.random() * 0.5 + 0.25,
                    'uColor': middleColor,
                    'uIntensity': rand.random() * 0.2 + 0.9,
                    'uFalloff': rand.random() * 3.0 + 3.0,
                    'uOffset': p3dc.Vec3(
                        rand.random() * 2000 - 1000,
                        rand.random() * 2000 - 1000,
                        rand.random() * 2000 - 1000
                    ),
                    'uProjection': projection,
                })
        
        for i in nebulaParams:
            nebula = self.makeNebulaObject()
            self.rNebulae.append(nebula)
            self.updateUniforms(nebula, i)
    
    def makeSun(self, params, view, projection): #TODO: WIP
        pass
        ## Initialize the sun parameters.
        #self.rSun.reparentTo(self.Scene)
        #self.rSun = self.buildBox(0.45, self.pSun)
        #rand = random.Random(hash(params['seed']) + 4000)
        #sunParams = []
        #if params['sun']:
        #    model = p3dc.LMatrix4()
        #    sunParams.append({
        #        'uView': view,
        #        'uModel': model,
        #        'uPosition': p3dc.LVector3(rand.random(), rand.random(), rand.random()),
        #        'uColor': [rand.random(), rand.random(), rand.random()],
        #        'uSize': rand.random() * 0.0001 + 0.0001,
        #        'uFalloff': params['sunFalloff'],
        #        'uProjection': projection,
        #    })
        #
        #for i in sunParams:
        #    self.updateUniforms(self.rSun, i)
        #self.rSun.show()
    
    def updateUniforms(self, node_path:"p3dc.NodePath", uniforms:"typing.Dict[str,typing.Any]"):
        for key, value in uniforms.items():
            try:
                node_path.set_shader_input(key, value)
            except:
                NC(1,exc=True,input=f"{key = }\n{value = }")
    
    def makeWithShader(self, params:"typing.Dict[str,typing.Any]", size=20000.0):
        nMin = 2
        nMax = 6
        
        #TODO: Remove later
        self.SkyShader = ShaderTools.loadShader("skyboxShader.glsl")
        
        if self.Skybox:
            self.Skybox.removeNode()
            self.Skybox = None
        
        backgroundColor = params["backgroundColor"]
        backgroundColorVec = p3dc.Vec4F(backgroundColor[0]/255.0, backgroundColor[1]/255.0, backgroundColor[2]/255.0, 1.0)
        base().win.setClearColor(backgroundColorVec)
        base().win.setClearColorActive(True)
        
        #self.Skybox = self.buildSphere(20000.0, self.SkyShader)
        self.Skybox = self.buildBox(size, self.SkyShader)
        
        
        skybox_texture = p3dc.Texture('SkyboxTexture')
        skybox_texture.set_minfilter(p3dc.SamplerState.FT_linear)
        skybox_texture.set_magfilter(p3dc.SamplerState.FT_linear)
        skybox_texture.set_wrap_u(p3dc.SamplerState.WM_repeat)
        skybox_texture.set_wrap_v(p3dc.SamplerState.WM_mirror)
        skybox_texture.set_anisotropic_degree(16)
        
        ts = p3dc.TextureStage
        skybox_texture_stage = p3dc.TextureStage('SkyboxTextureStage')
        skybox_texture_stage.setCombineRgb(ts.CMModulate, ts.CS_texture, ts.CO_src_alpha, ts.CS_previous, ts.CO_one_minus_src_alpha)
        skybox_texture_stage.setCombineAlpha(ts.CM_replace, ts.CS_texture, ts.CO_src_alpha)
        
        self.Skybox.setTexture(skybox_texture_stage, skybox_texture)
        #self.Skybox.reparentTo(self.Scene)
        
        rand = random.Random(hash(params['seed']) + 2000)
        
        uniforms = {
            "Seed": rand.randint(7,10000),
            "bgColor": backgroundColorVec,
            "Star_Count": self.NSTARS,
            "MakeSun": params["sun"],
            "BrightStar_Count": params["stars"],
            "MakePointStars": params["pointStars"],
        }
        
        uniforms["Nebula_Color"] = p3dc.PTA_LVecBase3()
        uniforms["Nebula_Intensity"] = p3dc.PTA_float()
        uniforms["Nebula_Falloff"] = p3dc.PTA_float()
        uniforms["Nebula_Offset"] = p3dc.PTA_LVecBase3()
        if not params['nebulae']:
            uniforms["Nebula_Count"] = 0
        else:
            countNebulas = rand.choice(list(range(nMin,nMax+1)))
            uniforms["Nebula_Count"] = countNebulas
            beginColor = params['nebulaColorBegin']
            endColor = params['nebulaColorEnd']
            for ni in range(countNebulas):
                uniforms['Nebula_Intensity'].pushBack(rand.random() * 0.2 + 0.9)
                uniforms['Nebula_Falloff'].pushBack(rand.random() * 3.0 + 3.0)
                uniforms['Nebula_Color'].pushBack(p3dc.LVecBase3f(
                    (beginColor[0] + ni * (endColor[0] - beginColor[0]) / (countNebulas - 1)) / 255,
                    (beginColor[1] + ni * (endColor[1] - beginColor[1]) / (countNebulas - 1)) / 255,
                    (beginColor[2] + ni * (endColor[2] - beginColor[2]) / (countNebulas - 1)) / 255
                ))
                uniforms['Nebula_Offset'].pushBack(p3dc.LVecBase3f(
                    rand.random() * 2000 - 1000,
                    rand.random() * 2000 - 1000,
                    rand.random() * 2000 - 1000
                ))
        
        self.updateUniforms(self.Skybox, uniforms)
        
        self.Skybox.reparentTo(render())
        
        return self.Skybox
