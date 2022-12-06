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
    from GUI.Windows import MainWindowClass
    #from Main_temp import * #TODO: This is temporary
    from BaseClasses import UnitManagerBase
    from BaseClasses import HexBase
    from BaseClasses import BaseModules
    from BaseClasses import ShipBase
    from BaseClasses import ModelBase
    from ApplicationClasses import MainAppClass

def addStatCustomizer(d:'dict', module:'BaseModules.Module', statName:str, type:'type[AGeInput._TypeWidget]', dplName:str=None):
    if dplName is None: dplName = statName
    if issubclass(type,(AGeInput.Int, AGeInput.Float,)):
        if statCustomisationUnlocked(module, statName): d[statName] = lambda: type(None,dplName,getattr(module,statName),moduleStatMin(module,statName),moduleStatMax(module,statName))
    elif issubclass(type,(AGeInput.Bool,AGeInput.Str)):
        if statCustomisationUnlocked(module, statName): d[statName] = lambda: type(None,dplName,getattr(module,statName))

def statCustomisationUnlocked(moduleClass:'type[BaseModules.Module]', statName:str) -> bool:
    #TODO: This should query the research tree and get whether the stat is customisable.
    #       If the module class does not support this request query up through the inheritance line
    return True

def moduleStatMin(moduleClass:'type[BaseModules.Module]', statName:str) -> float:
    #TODO: This should query the research tree and get the min/max value.
    #       If the module class does not support this request query up through the inheritance line
    return 0

def moduleStatMax(moduleClass:'type[BaseModules.Module]', statName:str) -> float:
    #TODO: This should query the research tree and get the min/max value.
    #       If the module class does not support this request query up through the inheritance line
    return 10000
