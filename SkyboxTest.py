"""
    Copyright (C) 2021  Robin Albers
"""

SupportsRenderPipeline = False#True

# Python standard imports 1/2
import datetime
import platform
import sys

sys.path.insert(0, "/home/astus/Projects/AstusPandaEngine/tobsprRenderPipeline")

# Print into the console that the program is starting and set the application ID if we are on windows
WindowTitle = "space3d-test"
if __name__ == "__main__":
    print()
    print(datetime.datetime.now().strftime('%H:%M:%S'))
    print(WindowTitle)
    print("Loading Modules")#, end = "")
    if platform.system() == 'Windows':
        try:
            import ctypes
            myAppId = u'{}{}'.format(WindowTitle , datetime.datetime.now().strftime('%H:%M:%S')) # arbitrary string
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myAppId)
        except:
            pass

# Python standard imports 2/2
import os
import sys
import time
import random
import typing
import math
import weakref
import inspect
import importlib
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
    from ..AstusPandaEngine.AGeLib import *
    from ..AstusPandaEngine import AstusPandaEngine as ape
    from ..AstusPandaEngine.AstusPandaEngine import engine, base, render, loader
    from ..AstusPandaEngine.AstusPandaEngine import window as _window
else:
    # These imports make Python happy
    sys.path.append('../AstusPandaEngine')
    from AGeLib import *
    import AstusPandaEngine as ape
    from AstusPandaEngine import engine, base, render, loader
    from AstusPandaEngine import window as _window

from ProceduralGeneration import SkyboxGeneration as SkyGen

class EngineClass(ape.APE):
    def start(self):
        
        self.Gen = SkyGen.SkyboxGenerator()
        
        #self.Params = {
        #    "seed": "The very best seed!",
        #    "backgroundColor": [pow(random.random(),2)*32,pow(random.random(),2)*32,pow(random.random(),2)*32],
        #    "pointStars": True,
        #    "stars": 200,
        #    "sun": True,
        #    "sunFalloff": 100,
        #    "jpegQuality": 0.85,
        #    "nebulaColorBegin": [random.random()*255,random.random()*255,random.random()*255],
        #    "nebulaColorEnd": [random.random()*255,random.random()*255,random.random()*255],
        #    "nebulae": True,
        #    "resolution": 1024,
        #    "renderToTexture": True,
        #}
        
        App().MW.Console1.executeCode()
        self.gen()
        
        return super().start()
    
    def gen(self):
        #self.Gen.render(self.Params)
        self.Gen.makeWithShader(self.Params)

class BaseClass(ape.APEPandaBase):
    def __init__(self,rp):
        super().__init__(rp)
        #self.taskMgr.add(self.spinCameraTask, "SpinCameraTask")
    
    def spinCameraTask(self, task):
        angleDegrees = task.time * 6.0
        angleRadians = angleDegrees * (3.14159 / 180.0)
        self.camera.setPos(p3dc.LVector3f(5 * math.sin(angleRadians), -5 * math.cos(angleRadians), 3))
        self.camera.lookAt(p3dc.LVector3f(0,0,0))
        return Task.cont

class AppClass(ape.APEApp):
    pass

class MainWindowClass(ape.APELabWindow):
    def __init__(self, widget=...):
        super().__init__(widget)
        # render
        self.Overload_render = AGeIDE.OverloadWidget(self, SkyGen.SkyboxGenerator.render, "render", SkyGen.SkyboxGenerator)
        self.Overload_render.setGlobals(self.globals())
        self.TabWidget.addTab(self.Overload_render, "render")
        # createRenderable
        self.Overload_createRenderable = AGeIDE.OverloadWidget(self, SkyGen.SkyboxGenerator.createRenderable, "createRenderable", SkyGen.SkyboxGenerator)
        self.Overload_createRenderable.setGlobals(self.globals())
        self.TabWidget.addTab(self.Overload_createRenderable, "createRenderable")
        # buildStar
        self.Overload_buildStar = AGeIDE.OverloadWidget(self, SkyGen.SkyboxGenerator.buildStar, "buildStar", SkyGen.SkyboxGenerator)
        self.Overload_buildStar.setGlobals(self.globals())
        self.TabWidget.addTab(self.Overload_buildStar, "buildStar")
        # buildBox
        self.Overload_buildBox = AGeIDE.OverloadWidget(self, SkyGen.SkyboxGenerator.buildBox, "buildBox", SkyGen.SkyboxGenerator)
        self.Overload_buildBox.setGlobals(self.globals())
        self.TabWidget.addTab(self.Overload_buildBox, "buildBox")
        # makePointStars
        self.Overload_makePointStars = AGeIDE.OverloadWidget(self, SkyGen.SkyboxGenerator.makePointStars, "makePointStars", SkyGen.SkyboxGenerator)
        self.Overload_makePointStars.setGlobals(self.globals())
        self.TabWidget.addTab(self.Overload_makePointStars, "makePointStars")
        # makeBrightStars
        self.Overload_makeBrightStars = AGeIDE.OverloadWidget(self, SkyGen.SkyboxGenerator.makeBrightStars, "makeBrightStars", SkyGen.SkyboxGenerator)
        self.Overload_makeBrightStars.setGlobals(self.globals())
        self.TabWidget.addTab(self.Overload_makeBrightStars, "makeBrightStars")
        # makeNebulae
        self.Overload_makeNebulae = AGeIDE.OverloadWidget(self, SkyGen.SkyboxGenerator.makeNebulae, "makeNebulae", SkyGen.SkyboxGenerator)
        self.Overload_makeNebulae.setGlobals(self.globals())
        self.TabWidget.addTab(self.Overload_makeNebulae, "makeNebulae")
        # makeSun
        self.Overload_makeSun = AGeIDE.OverloadWidget(self, SkyGen.SkyboxGenerator.makeSun, "makeSun", SkyGen.SkyboxGenerator)
        self.Overload_makeSun.setGlobals(self.globals())
        self.TabWidget.addTab(self.Overload_makeSun, "makeSun")
        # cleanUp
        self.Overload_cleanUp = AGeIDE.OverloadWidget(self, SkyGen.SkyboxGenerator.cleanUp, "cleanUp", SkyGen.SkyboxGenerator)
        self.Overload_cleanUp.setGlobals(self.globals())
        self.TabWidget.addTab(self.Overload_cleanUp, "cleanUp")
        
        self.RunButton = AGeWidgets.Button(self, "Generate", lambda: self.gen())
        self.TopBar.layout().addWidget(self.RunButton, 0, 4, 1, 1,QtCore.Qt.AlignRight)
        
        self.Console1.setText(PARAMS_TEXT)
    
    def gen(self):
        self.Console1.executeCode()
        ape.engine().gen()

class PandaWidget(ape.PandaWidget):
    pass

PARAMS_TEXT = """
ape.engine().Params = {
    "seed": str(random.random()),
    "backgroundColor": [pow(random.random(),2)*32,pow(random.random(),2)*32,pow(random.random(),2)*32],
    "pointStars": True,
    "stars": 200,
    "sun": True,
    "sunFalloff": 100,
    "jpegQuality": 0.85,
    "nebulaColorBegin": [random.random()*255,random.random()*255,random.random()*255],
    "nebulaColorEnd": [random.random()*255,random.random()*255,random.random()*255],
    "nebulae": True,
    "resolution": 1024,
    "renderToTexture": True,
}
"""

def main():
    ape.start(WindowTitle, EngineClass, BaseClass, AppClass, MainWindowClass, PandaWidget, True, SupportsRenderPipeline)

if __name__ == '__main__':
    main()
