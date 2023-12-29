from typing import Any
import util.singleton as singleton
import importlib
import re
import json

@singleton.Singleton
class Config:
    def __init__(self) -> None:
        self._class_list = {}
        self._refs = {}
        self._str_cap = {}
        self._instances = set()

    def register(self, cls, **kwargs):
        name = kwargs.get('name', cls.__qualname__)
        if name in self._class_list:
            obj = self._class_list[name]
            raise KeyError(f"Key {name} already exist with value {obj}. Failed to register {cls}")

        def cls_builder(**kwargs):
            obj = cls(**kwargs)
            if obj not in self._instances:
                self._instances.add(obj)
            return obj

        str_cap = kwargs.get('str_cap')
        if str_cap is not None:
            self._str_cap[name] = (re.compile(str_cap), cls_builder)
        self._class_list[name] = cls_builder

    def load_from_filename(self, filename, reset_refs=False):
        with open(filename, 'r') as file:
            return self.load_from_file(file, reset_refs)

    def load_from_file(self, file, reset_refs=False):
        config = json.load(file)
        return self.load_from_json(config, reset_refs)

    def load_from_str(self, txt, reset_refs=False):
        config = json.loads(txt)
        return self.load_from_json(config, reset_refs)

    def load_from_json(self, json_obj, reset_refs=False):
        if reset_refs:
            self.reset_refs()
        return self.__porcess_config(json_obj)

    def reset_refs(self):
        self._refs = {}

    def get_refs(self):
        return self._refs

    def get_instance(self, name):
        return self._refs.get(name,None)

    def parse_string(self, txt):
        for exp,cls in self._str_cap.values():
            found = exp.match(txt)
            if found:
                return cls(**found.groupdict())
        return txt
    
    def get_all_objects(self):
        return list(self._instances)

    def __load_class(self, config):
        cls_name = config["class"]
        name = config.get("name",None)

        for k in config:
            config[k] = self.__porcess_config(config[k])

        obj = None
        if cls_name in self._class_list:
            obj = self._class_list[cls_name](**config)
        else:
            raise KeyError(f"Class '{cls_name}' not found")
        ret_val = config
        if obj is not None:
            if name is not None:
                obj.name = name
            ret_val = obj
        if name is not None:
            self._refs[name] = ret_val
        return ret_val

    def __porcess_config(self, config):
        if isinstance(config, str):
            return self.parse_string(config)
        elif isinstance(config, list):
            tmp = config
            config = []
            for n in tmp:
                config.append(self.__porcess_config(n))
        elif isinstance(config, dict):
            if "class" in config:
                return self.__load_class(config)
            else:
                temp = config
                config = {}
                for k in temp:
                    config[k] = self.__porcess_config(temp[k])
        return config


class DataClass:
    def __new__(cls=None, **kwargs):
        def Wrap(_cls):
            Config.register(_cls, **kwargs)
            return _cls
        if cls is not None:
            return Wrap
        return Wrap(cls)

@DataClass(name="ref", str_cap=r"@ref:(?P<name>.+)")
def get_refs(name, **kwargs):
    return Config.get_instance(name)

@DataClass(name="import", str_cap=r"@import:(?P<imports>.+)")
def get_import(imports, **kwargs):
    if isinstance(imports, list):
        vals = []
        for n in imports:
            vals.append(importlib.import_module(n))
        return vals
    return importlib.import_module(imports)