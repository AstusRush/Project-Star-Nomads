import typing
from BaseClasses import ListLoader
if typing.TYPE_CHECKING:
    from BaseClasses import ShipBase
    from BaseClasses import ModelBase
    #
    import TestShips
    import AI_faction_ships
else:
    """Import all modules that exist in the current directory."""
    # Ref https://stackoverflow.com/a/60861023/
    from importlib import import_module
    from pathlib import Path
    
    for f in Path(__file__).parent.glob("*.py"):
        module_name = f.stem
        if (not module_name.startswith("_")) and (module_name not in globals()):
            import_module(f".{module_name}", __package__)
        del f, module_name
    del import_module, Path

def getShips() -> 'typing.Dict[str,type[ShipBase.ShipBase]]':
    from BaseClasses import ShipBase
    Ships:'typing.Dict[str,type[ShipBase.ShipBase]]' = {}
    ListLoader.fillWithType(Ships, globals(), ShipBase.ShipBase)
    #for m in globals().values():
    #    if hasattr(m,"__dict__"):
    #        for k,v in m.__dict__.items():
    #            if isinstance(v, type) and issubclass(v, ShipBase.ShipBase):
    #                Ships[k] = v
    return Ships

def getShipModels() -> 'typing.Dict[str,type[ModelBase.ShipModel]]':
    from BaseClasses import ModelBase
    from ProceduralGeneration import ProceduralShips
    ShipModels:'typing.Dict[str,type[ModelBase.ShipModel]]' = {"Procedural":None}
    ListLoader.fillWithType(ShipModels, globals(), (ModelBase.ShipModel, ProceduralShips.ProceduralShip))
    #for k,v in globals().items():
    #    if isinstance(v, type) and issubclass(v, ModelBase.ShipModel):
    #        ShipModels[k] = v
    return ShipModels
