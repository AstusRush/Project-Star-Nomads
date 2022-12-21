"""
TODO
"""
"""
    Copyright (C) 2021  Robin Albers
"""
# # Python standard imports
# import datetime
# import platform
# import os
# import sys
# import time
# import random
# import typing
# import weakref
# import inspect
# import importlib
# from heapq import heappush, heappop
# 
# # External imports
# import numpy as np
# 
# # Panda imports
# import panda3d as p3d
# import panda3d.core as p3dc
# import direct as p3dd
# from direct.interval.IntervalGlobal import Sequence as p3ddSequence
# from direct.showbase.DirectObject import DirectObject
# from direct.gui.OnscreenText import OnscreenText
# from direct.task.Task import Task

# AGe and APE imports
import typing
if typing.TYPE_CHECKING:
    # These imports make the IDE happy
    from ...AstusPandaEngine.AGeLib import *
    from ...AstusPandaEngine import AstusPandaEngine as ape
    from ...AstusPandaEngine.AstusPandaEngine import base, render, loader
    from ...AstusPandaEngine.AstusPandaEngine import window as _window
    from ...AstusPandaEngine.AstusPandaEngine import engine as _engine
else:
    # These imports make Python happy
    #sys.path.append('../AstusPandaEngine')
    from AGeLib import *
    import AstusPandaEngine as ape
    from AstusPandaEngine import base, render, loader
    from AstusPandaEngine import window as _window
    from AstusPandaEngine import engine as _engine

if typing.TYPE_CHECKING:
    # These imports make the IDE happy
    #from Main_temp import * #TODO: This is temporary
    from BaseClasses import UnitManagerBase
    from BaseClasses import HexBase
    from BaseClasses import BaseModules
    from BaseClasses import ShipBase
    from BaseClasses import ModelBase
    from ApplicationClasses import Scene
    from ApplicationClasses import Camera
    from ApplicationClasses import MainAppClass
    from GUI import Windows
    from GUI import BaseInfoWidgets
    from GUI import Menu

def window() -> 'Windows.MainWindowClass':
    return _window()

def menu() -> 'Menu.Menu':
    return window().Menu

def engine() -> 'MainAppClass.EngineClass':
    return _engine()

def unitManager(campaign = None) -> 'UnitManagerBase.UnitManager':
    return engine().getUnitManager(campaign)

def hexGrid(campaign = None) -> 'HexBase.HexGrid':
    return engine().getHexGrid(campaign)

def scene(campaign = None) -> 'Scene.BaseScene':
    return engine().getScene(campaign)

def camera(campaign = None) -> 'Camera.StrategyCamera':
    return engine().getScene(campaign).Camera

def shipClasses() -> 'typing.Dict[str, type[ShipBase.ShipBase]]':
    import Ships
    return Ships.getShips()

def shipModels() -> 'typing.Dict[str, type[ModelBase.ShipModel]]':
    import Ships
    return Ships.getShipModels()

def modules() -> 'typing.Dict[str, type[BaseModules.Module]]':
    import ShipModules
    return ShipModules.getModules()
