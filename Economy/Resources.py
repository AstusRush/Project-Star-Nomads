"""
TODO
"""
"""
    Copyright (C) 2021  Robin Albers
"""

import typing as _typing
from AGeLib import AGeAux as _AGeAux

class _InvalidCapacityChangeException(Exception):
    pass

class _InvalidResourceTypeException(Exception):
    pass

class _InsufficientCapacityException(Exception):
    pass

class _InsufficientResourcesException(Exception):
    pass

#region AGeToCode
_IMP_RESOURCES = [("PSN Resources","from Economy import Resources"),]
#endregion AGeToCode

#region Resource Base Class
class _Resource_Metaclass(type):
    #TODO: There should be a mechanism that prevents the creation of any resource that ends with an underscore!
    def __repr__(self): #MAYBE: This might be temporary until the Storage dict has the text method...
        return self._Name
    
    def __str__(self):
        return self._Name
    
    def __hash__(self) -> int:
        return hash(self._Name)

class Resource_(metaclass=_Resource_Metaclass):
    _Name = "Undefined Resource"
    _Description = "#TODO: It would be neat to have a description for each resource"
    Quantity = 0
    
    def __init__(self, quantity:float=0) -> None:
        self.Quantity = float(quantity)
    
    def __call__(self, quantity:float=0) -> 'Resource_':
        return self.new(quantity)
    
    @property
    def Name(self) -> str:
        return self._Name
    
    @property
    def S(self) -> str:
        "A simple string containing the name and amount of this resource"
        return f"{self.Name}: {self.Quantity}"
    
    @property
    def Q(self) -> float:
        "The amount of resources. Equivalent to .Quantity but shorter"
        return self.Quantity
    
    @Q.setter
    def Q(self, value:float):
        self.Quantity = float(value)
    
    def __str__(self) -> str:
        return self.Name #MAYBE: This probably should also display the amount if it is not 0? Or would that make it too unpredictable for formatting?
    
    def __float__(self) -> float:
        return float(self.Quantity)
    
    #def __hash__(self) -> int: #NOTE: Do not do this since a==b must imply hash(a)==hash(b) . Therefore we only support hash for the Class and == for instances
    #    return hash(self.Name)
    
    @classmethod
    def __hash__(cls) -> int:
        return hash(cls._Name)
    
    def new(self, qnt:float) -> 'Resource_':
        return type(self)(qnt)
    
    @classmethod
    def new(cls, qnt:float) -> 'Resource_':
        return cls(qnt)
    
    def _mathPrepare(self, a):
        if isinstance(a, Resource_):
            a = a.Quantity
        return a
    
    def __add__(self, a) -> 'Resource_':
        return self.new(self.Quantity + self._mathPrepare(a))
    def __radd__(self, a) -> 'Resource_':
        return self.new(self.Quantity + self._mathPrepare(a))
    def __sub__(self, a) -> 'Resource_':
        return self.new(self.Quantity - self._mathPrepare(a))
    def __rsub__(self, a) -> 'Resource_':
        return self.new(self._mathPrepare(a) - self.Quantity)
    def __mul__(self, a) -> 'Resource_':
        return self.new(self.Quantity * self._mathPrepare(a))
    def __rmul__(self, a) -> 'Resource_':
        return self.new(self.Quantity * self._mathPrepare(a))
    def __div__(self, a) -> 'Resource_':
        return self.new(self.Quantity / self._mathPrepare(a))
    def __rdiv__(self, a) -> 'Resource_':
        return self.new(self._mathPrepare(a) / self.Quantity)
    def __truediv__(self, a) -> 'Resource_':
        return self.new(self.Quantity / self._mathPrepare(a))
    def __rtruediv__(self, a) -> 'Resource_':
        return self.new(self._mathPrepare(a) / self.Quantity)
    def __mod__(self, a) -> 'Resource_':
        return self.new(self.Quantity % self._mathPrepare(a))
    def __rmod__(self, a) -> 'Resource_':
        return self.new(self._mathPrepare(a) % self.Quantity)
    def __pow__(self, a) -> 'Resource_':
        return self.new(pow(self.Quantity, self._mathPrepare(a)))
    def __rpow__(self, a) -> 'Resource_':
        return self.new(pow(self._mathPrepare(a), self.Quantity))
    
    def __lt__(self, a) -> bool:
        return self.Quantity < self._mathPrepare(a)
    def __gt__(self, a) -> bool:
        return self.Quantity > self._mathPrepare(a)
    def __eq__(self, a) -> bool:
        return self.Quantity == self._mathPrepare(a)
    def __le__(self, a) -> bool:
        return self.Quantity <= self._mathPrepare(a)
    def __ge__(self, a) -> bool:
        return self.Quantity >= self._mathPrepare(a)
    def __ne__(self, a) -> bool:
        return self.Quantity != self._mathPrepare(a)
    
    def __round__(self, n) -> 'Resource_':
        return round(self.Quantity, n)
    def __pos__(self) -> 'Resource_':
        return self.new(self.Quantity)
    def __neg__(self) -> 'Resource_':
        return self.new(-self.Quantity)
    def __abs__(self) -> 'Resource_':
        return self.new(abs(self.Quantity))
    def __nonzero__(self) -> bool:
        return bool(self.Quantity)
    
    def tocode_AGeLib(self, name="", indent=0, indentstr="    ", ignoreNotImplemented = False) -> _typing.Tuple[str,dict]:
        ret, imp = "", {}
        # ret is the ship data that calls a function which is stored as an entry in imp which constructs the ship
        # Thus, ret, when executed, will be this ship. This can then be nested in a list so that we can reproduce entire fleets.
        from AGeLib import AGeToPy
        imp.update(_IMP_RESOURCES)
        ret = indentstr*indent
        if name:
            ret += name + " = "
        ret += f"Resources.{self.__class__.__name__}({float(self.Quantity)})"
        return ret, imp
#endregion Resource Base Class

#region Raw Resources
class RawResource_(Resource_):
    _Name = "Undefined Raw Resource"

class Salvage(RawResource_):
    _Name = "Salvage"

class Ore(RawResource_):
    _Name = "Ore"

class RareOre(RawResource_):
    _Name = "Rare Ore"
#endregion Raw Resources

#region Construction Materials
class Material_(Resource_):
    _Name = "Undefined Construction Material"

class Metals(Material_):
    _Name = "Metals"

class RareMetals(Material_):
    _Name = "Rare Metals"

class Crystals(Material_):
    _Name = "Crystals"

class AdvancedComponents(Material_):
    _Name = "Advanced Components"
#endregion Construction Materials

#region _ResourceDict
class _ResourceDict(_typing.Dict['Resource_','Resource_']):
    Capacity:float = float("inf")
    ValidResourceTypes:'tuple[type[Resource_]]' = (Resource_,)
    def setCapacity(self, cap:float):
        if self.UsedCapacity <= cap:
            self.Capacity = cap
        else:
            raise _InvalidCapacityChangeException("This would result in resource loss!") #TODO: More error info
    
    @classmethod
    def new(cls, *args:Resource_, cap=float("inf"), validResourceTypes:'tuple[type[Resource_]]'=(Resource_,)):
        d = _ResourceDict()
        d.Capacity = cap
        for i in args:
            d.add(i)
        d.ValidResourceTypes = validResourceTypes
        return d
    
    @classmethod
    def fromList(cls, l:'list[Resource_]', cap=float("inf"), validResourceTypes:'tuple[type[Resource_]]'=(Resource_,)):
        d = _ResourceDict()
        d.Capacity = cap
        d.ValidResourceTypes = validResourceTypes
        for i in l:
            d.add(i)
        return d
    
    @property
    def UsedCapacity(self) -> float:
        return sum(list(self.values()))
    
    @property
    def FreeCapacity(self) -> float:
        return self.Capacity - self.UsedCapacity
    
    def __getitem__(self, __key: 'Resource_') -> 'Resource_':
        __key = self._prepareKey(__key)
        if __key in self:
            return __key.new(super().__getitem__(__key))
        else:
            return __key.new(0)
    
    def __setitem__(self, __key: 'Resource_', __value: '_typing.Union[float,Resource_]') -> None:
        __key = self._prepareKey(__key)
        if not _AGeAux.isInstanceOrSubclass(__key,self.ValidResourceTypes):
            raise _InvalidResourceTypeException()
        if isinstance(__value, Resource_):
            __value = __value.Quantity
        if __key in self:
            prev = super().__getitem__(__key)
        else:
            prev = 0
        super().__setitem__(__key, __value)
        if self.isOverCapacity():
            f = self.FreeCapacity
            super().__setitem__(__key, prev)
            raise _InsufficientCapacityException(f"Can not store that many resources. {self.Capacity = } , {self.UsedCapacity = } , {self.FreeCapacity = } , {prev = } , {__value = } , {__value-prev = } , Free Capacity if added = {f}")
    
    def _prepareKey(self, key):
        if not _AGeAux.isInstanceOrSubclass(key,Resource_):
            raise _InvalidResourceTypeException()
        if isinstance(key, type):
            return key
        elif isinstance(key, Resource_):
            return type(key)
    
    def list(self) -> 'list[Resource_]':
        return [k(v) for k,v in self.items()]
    
    #MAYBE: Implement __iter__ to directly iterate over a list
    
    def isOverCapacity(self) -> bool:
        return self.FreeCapacity < 0
    
    def anyNegative(self) -> bool:
        for i in self.values():
            if i < 0:
                return True
        return False
    
    def isValid(self) -> bool:
        return (not self.isOverCapacity()) and (not self.anyNegative())
    
    def add(self, r:'Resource_'):
        self[r] += r
    
    def subtract(self, r:'Resource_'):
        return self.add(-r)
    
    def set(self, r:'Resource_'):
        self[r] = r
    
    def fillFrom(self, other:'_ResourceDict', _recursive:bool=True) -> '_ResourceDict':
        """
        Try to put as many resources from `other` into this _ResourceDict and returns everything that did not fit as a new _ResourceDict\n
        `other` is not altered!
        """
        # the -1e-13 and 1e-10 are used instead of 0 to avoid errors due to floating point imprecision
        r = other.copy(keepRestrictions=False)
        for k,v in r.items():
            if not r: return r # When the r is empty we just return it
            if v > 0:
                amount = v if v < self.FreeCapacity-1e-13 else self.FreeCapacity-1e-13
            else:
                amount = v if -v < self[k] else -self[k]
            self.add(k(amount))
            r.subtract(k(amount))
        if self.FreeCapacity > 1e-10 and r.UsedCapacity > 0 and _recursive:
            r = self.fillFrom(r, _recursive=False)
        return r
    
    def transferMax(self, other:'_ResourceDict', _recursive:bool=True) -> '_ResourceDict':
        """
        Try to take as many resources out of `other` and put them into self as the capacity of self allows.
        """
        # the -1e-13 and 1e-10 are used instead of 0 to avoid errors due to floating point imprecision
        for k,v in other.items():
            if not other: return other # When the other dict is empty we just return it
            if v > 0:
                amount = v if v < self.FreeCapacity-1e-13 else self.FreeCapacity-1e-13
            else:
                amount = v if -v < self[k] else -self[k]
            self.add(k(amount))
            other.subtract(k(amount))
        if self.FreeCapacity > 1e-10 and other.UsedCapacity > 0 and _recursive:
            other = self.transferMax(other, _recursive=False)
        return other
    
    def __add__(self, a:'_ResourceDict') -> '_ResourceDict':
        return self._add_sub(a, 1)
    def __radd__(self, a:'_ResourceDict') -> '_ResourceDict': # Required to sum of a list of ResourceDicts as the sum is initialized with a 0
        return self._add_sub(a, 1)
    def __sub__(self, a:'_ResourceDict') -> '_ResourceDict':
        return self._add_sub(a,-1)
    def _add_sub(self, other:'_ResourceDict', sign:'int') -> '_ResourceDict':
        if other == 0: return self.copy() # Required to sum of a list of ResourceDicts as the sum is initialized with a 0
        if not isinstance(other, _ResourceDict): raise TypeError(f"Only a ResourceStorageDict can be added to or subtracted from a ResourceStorageDict, not a {type(other)} ({other})")
        d = self.copy()
        for k,v in other.items():
            d[k] += sign*v
        return d
    
    def __neg__(self) -> '_ResourceDict':
        return self.copy(_negate=True)
    def __nonzero__(self) -> bool:
        return bool(len(self))
    
    def __len__(self) -> int:
        return len([i for i in self.values() if round(i,15)])
    
    def copy(self, keepRestrictions=True, _negate=False) -> '_ResourceDict':
        d = _ResourceDict()
        if _negate:
            for k,v in self.items():
                d[k] = -v
        else:
            for k,v in self.items():
                d[k] = v
        if keepRestrictions:
            d.Capacity = self.Capacity
            d.ValidResourceTypes = self.ValidResourceTypes
        return d
    
    def text(self, headline:str="", indent:bool=None, inverseSigns:bool=False, digits:int=5) -> str:
        """
        Returns a formatted text that describes this storage dict and its content.
        """
        if indent is None: indent = bool(headline)
        if self.Capacity != float("inf"):
            text = f"{headline} (Cap" if headline else "Capacity"
            text += f": {round(self.UsedCapacity,5)} / {round(self.Capacity,5)}"
            if headline: text += ")"
            text += "\n"
        else:
            text = f"{headline}\n" if headline else ""
        if not self:
            if indent: text += "\t"
            text += "None"
        else:
            for k,v in self.items():
                if indent: text += "\t"
                if inverseSigns: text += f"{k}: {round(-v,digits)}\n"
                else:            text += f"{k}: {round( v,digits)}\n"
        text = text.rstrip("\n")
        return text
    
    def tocode_AGeLib(self, name="", indent=0, indentstr="    ", ignoreNotImplemented = False) -> _typing.Tuple[str,dict]:
        ret, imp = "", {}
        # ret is the ship data that calls a function which is stored as an entry in imp which constructs the ship
        # Thus, ret, when executed, will be this ship. This can then be nested in a list so that we can reproduce entire fleets.
        from AGeLib import AGeToPy
        imp.update(_IMP_RESOURCES)
        ret = indentstr*indent
        if name:
            ret += name + " = "
        ret += f"Resources._ResourceDict.fromList(\n"
        r,i = AGeToPy._topy(self.list(), indent=indent+2, indentstr=indentstr, ignoreNotImplemented=ignoreNotImplemented)
        ret += f"{r},\n{indentstr*(indent+1)}cap="+AGeToPy._topy(self.Capacity)[0]+")" #TODO: Save ValidResourceTypes
        imp.update(i)
        imp.update(AGeToPy._topy(self.Capacity)[1])
        return ret, imp
#endregion _ResourceDict

#NOTE: Here are some Notes
"""
Survey ships are needed to identify resource deposits
    This also gives a reason to build ships with a higher FTL speed than the rest of the fleet
Ore >--Refinery--> 95% Metal + 5% Rare Metal
RareOre >--Refinery--> 75% Metal + 25% Rare Metal
Crystal an Metal are the basic resources
Rare Metals and Advanced Components are only really needed for advanced modules (though little amounts of rare metals might be needed for some basic modules)
Value Thresholds: Example: Beam with range 1 or 2 need only crystals and Metals but at range 3 they also need Rare Metals and at range 5 Advanced Components (and all costs increase as the range and the other stats increase)
Diverse Gameplay:
    Salvaging should be viable as a strategy with easier economics (only need salvaging modules and recycling modules that turn salvage into Metals, Rare Metals, and Crystals (not Adv.Comp.)) and gives a nice mix
        but also requires battles which pose the risc of loosing ships.
    Meanwhile mining requires survey ships and involves sector generation RNG but is less risky and allows to focus on the specific resources that are currently needed the most
        and also requires mining modules and ore refineries but asteroids and planets have more resources than battle-sites and therefore allow for better scaling
            (increasing the number and size of miners will pretty much always result in faster gathering while a given battle-site is far more limited in resources
            and it is not hard to get to a salvage module that is big enough to salvage the entire battle-site in one turn after which increasing the module size has no effect)
        Mining, however, also requires the player to stay at a location for longer which makes the mining ships easy prey if not protected

Ideas for later:
    More late game resources
    food and other resources for the population of the fleet
    ammunition for some weapons
    ?Fuel?
    ?Maybe some generic trade goods to be bought in a sector and sold for a profit later (with random prices in each sector for the different generic trade good types)?
"""

#TODO: This is actually something where automated testing might be appropriate
#NOTE: To test use:
"""
display()
from Economy import Resources
from Economy import EconomyManager

c = Resources._ResourceDict()

c[Resources.Metals] = 4

r = c[Resources.Metals]
dpl(r, r.Quantity)
dpl(r, float(r))
dpl(r.S)
dpl(c)

c[Resources.Metals] -= 3
dpl(c)

r = c[Resources.Metals]
dpl(r.S)

c[Resources.RareMetals()] = 4
dpl(c)
dpl()

c[Resources.RareMetals] += 4
dpl(c)
dpl()
c[Resources.RareMetals()] -= 3
dpl(c)
dpl()
c[Resources.RareMetals()] /= 3
dpl(c)
dpl()
c[Resources.RareMetals()] *= 3
dpl(c)

c[Resources.RareMetals()] = 1
dpl(c[Resources.RareMetals] <= c[Resources.Metals])

dpl("\n=========\n")

dpl(c)
dpl(c[Resources.Crystals].S)
dpl(c)
c[Resources.Crystals] += 3
dpl(c)

dpl("\n=========\n")
dpl(Resources.Metals)
r = Resources.Metals(4)
dpl(r.S)
r = 4 + r
dpl(r.S)

"""

#NOTE: More Tests
"""
display()
from Economy import Resources
from Economy import EconomyManager

c = Resources._ResourceDict()
c[Resources.Crystals] = 4
d = Resources._ResourceDict()
d[Resources.Crystals] = 3
dpl(c+d)
dpl(c-d)
d[Resources.Metals] = 3
dpl(c+d)
dpl(c-d)
dpl(d+c)
dpl(d-c)
dpl()
dpl(sum([c,d]))

"""
