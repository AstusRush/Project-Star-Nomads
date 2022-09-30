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

# Game Imports
from BaseClasses import get
if TYPE_CHECKING:
    from BaseClasses import FleetBase
    from BaseClasses import ShipBase
    from BaseClasses import ModelBase
from BaseClasses import HexBase

class Module():
    # Should at least implement:
    #   size (hull and some augments have negative values)
    #   resource costs
    #   module hp (if <=0 the module is inoperable until repaired) (some modules may have infinite HP but only if they are not targetable)
    #   exposure of the module (which means "how likely is the module to be hit" (a construction module is big and can be easily hit but weapons are much smaller))
    #       (Some modules like the hull should not be attackable since the ships hull-HP takes that role)
    #       (This is used to determine random module damage. Targeted attacks by fighters on for example weapon systems are effected by this but far more likely to hit)
    #   required staff (#MAYBE: make a distinction between staff on the strategic map and staff on the tactical map since the crew that usually operates refineries can operate guns during combat)
    #   (Slot type is basically the type of the subclass but maybe it would be helpful to implement it here)
    def __init__(self, ship:'ShipBase.ShipBase') -> None:
        self.ship = weakref.ref(ship)
    
    def handleNewTurn(self):
        pass

class Hull(Module):
    # The hull of a ship (can be tied to a ship model)
    # Determins the size of the ship (and maybe available slots for module types)
    # Also influences the HP of the ship and the required engine size
    def __init__(self, ship:'ShipBase.ShipBase') -> None:
        super().__init__(ship)
        self.Evasion = 0.1
        self.HP_Hull_max = 100
        self.HP_Hull = self.HP_Hull_max
        self.HP_Hull_Regeneration = self.HP_Hull_max / 20
        self.NoticeableDamage = self.HP_Hull_max / 10

class HullPlating(Module):
    pass

#class PowerGenerator(Module): #MAYBE: I don't see how a power system would help
#    pass

class Engine(Module):
    pass

class Shield(Module):
    pass

class Weapon(Module):
    pass

class Quaters(Module):
    # Houses crew and civilians
    # Crew is used to staff other modules and repair things. Crew is also used to pilot fighters and board enemies
    # Crew is recruited from the civilian population of the fleet.
    #MAYBE: Make variants to separate crew and civilians. I currently see no advantage of making a distinction. After all the crew is part of the population and shares all needs...
    #       It would only make sense to make a distinction between people who can operate a specific module and those that can not and in that case there would need to be a complex education system...
    #       Therefore a distinction is (at least until version 1.0 of the game) not useful
    pass

class Cargo(Module):
    # Used to store resources
    pass

class Hangar(Module):
    pass

class ConstructionModule(Module):
    # Modules to construct new ships.
    #TODO: Make 2 variants: Enclosed (can move while constructing) and open (can not move while constructing)
    pass

class Sensor(Module):
    # Includes sensors that increase weapon accuracy
    pass

class Economic(Module):
    # Modules for economic purposes like educating and entertaining people (civilians and crew), harvesting or processing resources, growing food, and researching stuff.
    #MAYBE: Researching could be tied to other modules like sensors to scan stuff or special experimental weapons to test stuff or experimental shields to test stuff or... you get the idea
    pass

class Augment(Module):
    # All augmentations that enhance/modify the statistics of other modules like +dmg% , +movementpoints , or +shieldRegeneration
    pass

class Support(Module): #MAYBE: inherit from Augment
    # like Augment but with an area of effect to buff allies or debuff enemies
    pass

class Special(Module):
    # Modules that add new special functions to ships that can be used via buttons in the gui like:
    #   hacking the enemy, cloaking, extending shields around allies, repairing allies, sensor pings, boarding
    pass
