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
import textwrap
import math

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

# Game Imports
if TYPE_CHECKING:
    from BaseClasses import ShipBase
    from BaseClasses import FleetBase
    from BaseClasses import UnitManagerBase
from BaseClasses import get
from BaseClasses import HexBase

class AI_Base():
    def __init__(self) -> None:
        pass

class Orders(dict):
    """
    This class is used to store orders. \n
    If a key does not have a value it returns `None`.
    Only `__getitem__` is overwritten thus `.get` can still be used to detect if an key was actually filled with `None` intentionally if that would make a difference at some point.
    """
    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except:
            return None
    
    def copyFromDict(self, dict:dict):
        for i,v in dict.items():
            self[i] = v
