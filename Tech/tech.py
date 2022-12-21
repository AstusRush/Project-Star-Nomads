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

#NOTE: Here are the notes:
"""
General notes:
- Almost all stats you can add or change for modules and some modules themselves as well as the max value of those stats should be unlocked/(increased) via research.
    Game mechanics should constantly evolve and unlock. The game should always evolve but it should always be fun and playable.
    It should not be mandatory to increase the max weapon range from 1 to 3 in order to make the game fun.

How do we implement the internal structure? Ideas:
- In order for all modules to have information about the tech tree:
    - we want to have a dictionary like structure that contains information about all modules, their stats, and how to research all of that
    -vs- it might be advantageous to simply have a class method that provides all information about the module class
    -vs- it might be advantageous to simply have an extra file with a dictionary with all the tech information and we just need to make a central dict and update it with the information from all other dicts

How do we implement the UI? Ideas:
    - This is gonna be complicated, isn't it...
    - Maybe start with a simple list of all the technologies and implement a good solution later?

How do we implement research in the game? Ideas:
    - Maybe there is simply a research module which contributes X research points per turn to the current research project?
    - But we could also make it much much more complicated:
        - research modules having tiers and each tier can only research up that that tier in terms of tech tier
        - different categories like military and economic and the research modules can only research techs from their category
        - researching a new technology unlocks a module prototype which first must be used a certain number of times before it fully unlocks the technology
        - survey modules that can be used on anomalies to generate more research points than a normal lab module but this would make the fleet immobile while surveying the anomaly
        - using modules generates research points. I.e. using many beam weapons generates beam weapon research points because the understanding of how they work increases
        - researching wrecks from defeated enemies
        - events like investigating derelict ships (could be tied into the aforementioned survey modules)
        - research staff and an education system for the civilian population of the fleet

"""
