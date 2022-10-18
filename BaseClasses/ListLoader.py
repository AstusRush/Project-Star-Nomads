
def fillWithType(_dict:dict, _globals:dict, _type:type):
    """
    Fills _dict with all types that are a subclass of _type that are in the imported modules in _globals.
    """
    for mName,module in _globals.items():
        if hasattr(module,"__dict__"):
            for k,v in module.__dict__.items():
                if isinstance(v, type) and issubclass(v, _type):
                    intName = f"{mName}: {k}"
                    v.INTERNAL_NAME = intName
                    _dict[intName] = v
