import types

class Singleton:
    """
    Decorator to convert class to a Singleton.
    """
    def __new__(cls,*args, **kwargs):
        if isinstance(args[0], type):
            cls_t = args[0]
            cls_t.__instance = cls_t()
            cls_t.__new__ = cls.__extend__
            def get_instance(cls):
                return cls.__instance
            cls_t.__call__ = get_instance
            return cls_t.__instance
        else:
            raise RuntimeError(f"Unsupported type {cls=} {args=} {kwargs=}")

    def __extend__(cls, name, cls_ext, info, **kwargs):
        if cls.__instance is not None:
            if "__init__" in info:
                info["__init__"](cls.__instance)
            for key in info:
                val = info[key]
                if isinstance(val, types.FunctionType):
                    if not key.startswith("__"):
                        if key in dir(cls):
                            raise KeyError(f"Duplicated attr{key}")
                        setattr(cls, key, val)
        return cls.__instance

