"""
    Copyright (C) 2021  Robin Albers
"""

SupportsRenderPipeline = False

# Python standard imports 1/2
import datetime
import platform

# Print into the console that the program is starting and set the application ID if we are on windows
WindowTitle = "Project-Star-Nomads"
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

# Game Imports
from ApplicationClasses import MainAppClass, Scene, Camera
from BaseClasses import HexBase, FleetBase, ShipBase, ModelBase, UnitManagerBase, get
from GUI import Windows, WidgetsBase


if __name__ == '__main__':
    ape.start(WindowTitle, MainAppClass.EngineClass, Scene.BaseClass, MainAppClass.AppClass, Windows.MainWindowClass, WidgetsBase.PandaWidget, True, SupportsRenderPipeline)
