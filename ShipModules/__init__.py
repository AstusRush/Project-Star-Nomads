import typing
if typing.TYPE_CHECKING:
    import TestModules
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
