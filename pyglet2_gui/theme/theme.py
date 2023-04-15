from __future__ import annotations
import json
from typing import Any
import pyglet
from .parsers import TextureParser


class ScopedDict(dict):
    """ScopedDict is a special type of dict with two additional features:
    - It is 'scoped' - if a key exists in a parent ScopedDict but
    not in the child ScopedDict, it returns the parent value.
    -  keys can be a list such that:
        sdict.get(['button', 'down', 'highlight']) is equivalent
        to sdict.get('button').get('down').get('highlight').
    """
    parent: ScopedDict

    def __init__(self, arg: dict = None, parent: ScopedDict = None):
        arg = {} if arg is None else arg
        super().__init__()
        self.parent = parent
        for k, v in arg.items():
            if isinstance(v, dict):
                self[k] = ScopedDict(v, self)
            else:
                self[k] = v

    def __getitem__(self, key: str | None | tuple | list) -> Any:
        if key is None:
            return self
        elif isinstance(key, list) or isinstance(key, tuple):
            if len(key) > 1:
                return self.__getitem__(key[0]).__getitem__(key[1:])  # start a recursion
            elif len(key) == 1:
                return self.__getitem__(key[0])
            else:
                return self  # theme[][key] returns theme[key]
        else:
            try:
                return dict.__getitem__(self, key)
            except KeyError:
                if self.parent is not None:
                    return self.parent.__getitem__(key)
                else:
                    raise

    def __setitem__(self, key: str | dict, value: Any):
        if isinstance(value, dict):
            dict.__setitem__(self, key, ScopedDict(value, self))
        else:
            dict.__setitem__(self, key, value)

    def get(self, key: str | list[str] | tuple[str] | None, default: Any = None) -> Any:
        if isinstance(key, list) or isinstance(key, tuple):
            if len(key) > 1:
                return self.__getitem__(key[0]).get(key[1:], default)
            elif len(key) == 1:
                return self.get(key[0], default)
            else:
                raise KeyError(key)  # empty list

        if key is None:
            return self
        elif key in self:
            return dict.get(self, key)
        elif self.parent:
            return self.parent.get(key, default)
        else:
            return default

    def get_path(self, path: list[str] | tuple[str], default: None | tuple = None) -> Any:
        assert isinstance(path, list) or isinstance(path, tuple)
        if len(path) == 1:
            return self.get(path[0], default)
        else:
            return self.__getitem__(path[0]).get_path(path[1:], default)

    def set_path(self, path: list[str] | tuple[str], value: Any):
        assert isinstance(path, list) or isinstance(path, tuple)
        if len(path) == 1:
            return self.__setitem__(path[0], value)
        else:
            return self.__getitem__(path[0]).set_path(path[1:], value)


class Theme(ScopedDict):
    """A theme is a scoped dictionary that
    maps specific keys to specific templates.
    It is initialized by a dictionary (json-like) and by a resource path.
    It maps resources in the dictionary to resources in the path,
    initializing the correct template accordingly.
    """
    _parsers: list

    def __init__(self, dictionary: dict, resources_path: str):
        """Create a Theme.

        :Parameters:
            'dictionary' : dict
                the dict object of the theme, e.g. {'font_name': 'Arial', 'font_size': 14}
            'resources_path' : str
                directory path where the resources are found
        """
        super().__init__(dictionary, None)
        self._parsers = [TextureParser(resources_path)]
        self.build(self, dictionary)

    def update(self, e: Any = None, **f: Any):
        super().update(e, **f)
        self.build(self, e)

    def build_element(self, key: str, value: Any, target: ScopedDict):
        if isinstance(value, list):
            value = tuple(value)
        for parser in self._parsers:
            if parser.condition_fulfilled(key):
                target[key] = parser.parse_element(value)
                # we only parse one element by parser.
                # if it is parsed, we are done.
                return

        # if value is a non-parsed dict, we add a new depth
        # and build against the new depth.
        if isinstance(value, dict):
            target[key] = ScopedDict(parent=target)
            self.build(target[key], value)
        else:
            target[key] = value

    def build(self, target: ScopedDict, input_dict: dict):
        """
        The main function of theme. Called during initialization,
        it crawls the input_dict and populates
        'target' with templates built from the dict.
        """
        for key, value in input_dict.items():
            self.build_element(key, value, target)


class ThemeFromPath(Theme):
    """A theme that is loaded from a json in a path.
    The convention is that the json file is called 'theme.json' and lives
    inside the resources_path given.
    """

    def __init__(self, resources_path: str, theme_name: str = "theme.json"):
        """Create a Theme from path.

        :Parameters:
            'resources_path' : str
                directory path where the resources are found
            'theme_name' : str
                the filename of the theme json
        """
        print(resources_path, theme_name)
        theme_file = pyglet.resource.Loader(resources_path).file(theme_name)
        try:
            dictionary = json.loads(theme_file.read().decode("utf-8"))  # TODO CHANGE THIS
        finally:
            theme_file.close()
        super().__init__(dictionary, resources_path)
