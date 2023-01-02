import typing
from BaseClasses import ListLoader
from BaseClasses import BaseModules
from Economy import BaseEconomicModules
if typing.TYPE_CHECKING:
    import TestModules
    import AI_faction_modules
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

def getModules() -> 'typing.Dict[str, type[BaseModules.Module]]':
    Modules:'typing.Dict[str, type[BaseModules.Module]]' = {}
    ListLoader.fillWithType(Modules, globals(), BaseModules.Module)
    return Modules
