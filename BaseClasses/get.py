"""
TODO
"""
"""
    Copyright (C) 2021  Robin Albers
"""
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

if TYPE_CHECKING:
    # These imports make the IDE happy
    from GUI.Windows import MainWindowClass
    #from Main_temp import * #TODO: This is temporary
    from BaseClasses import UnitManagerBase
    from ApplicationClasses import MainAppClass

def window():
    # type: () -> MainWindowClass
    #w:MainWindowClass = _window()
    return _window()#w

def engine() -> 'MainAppClass.EngineClass':
    return _engine()

def unitManager(campaign = None) -> 'UnitManagerBase.UnitManager':
    return engine().getUnitManager(campaign)


__all__ = ["window",
           "unitManager",
           ]
