from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .theme.theme import Theme
    from .manager import Manager, ViewerManager


class Managed:
    manager: Manager | None = None

    def set_manager(self, manager: Manager | ViewerManager | None):
        self.manager = manager

    def has_manager(self) -> bool:
        return self.manager is not None

    def get_batch(self, group_name: str) -> dict:
        return {'batch': self.manager.batch, 'group': self.manager.group[group_name]}

    @property
    def theme(self) -> Theme:
        assert self.manager is not None
        return self.manager.theme

    def delete(self):
        self.manager = None


class Rectangle:
    x: int
    y: int
    width: int
    height: int

    def __init__(self, x: int = 0, y: int = 0, width: int = 0, height: int = 0):
        assert width >= 0 and height >= 0
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def set_position(self, x: int, y: int):
        self.x = x
        self.y = y

    def is_inside(self, x: int, y: int) -> bool:
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height


class Viewer(Rectangle, Managed):
    _is_loaded: bool = False
    parent: Viewer | None = None

    def __init__(self, **kwargs):
        Managed.__init__(self)
        Rectangle.__init__(self, **kwargs)

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    def is_expandable(self) -> False:
        return False

    def set_position(self, x: int, y: int):
        Rectangle.set_position(self, x, y)
        self.layout()

    def get_path(self) -> str | dict[str] | tuple[str]:
        raise NotImplementedError

    def load(self):
        assert not self._is_loaded
        self._is_loaded = True
        self.load_graphics()

    def unload(self):
        assert self._is_loaded
        self._is_loaded = False
        self.unload_graphics()

    def reload(self):
        self.unload()
        self.load()

    def refresh(self):
        self.reload()
        self.reset_size()

    def load_graphics(self):
        pass

    def unload_graphics(self):
        pass

    def layout(self):
        pass

    def compute_size(self) -> tuple[int, int]:
        return self.width, self.height

    def reset_size(self, reset_parent: bool = True):
        width, height = self.compute_size()

        # if out size changes
        if self.width != width or self.height != height:
            self.width, self.height = int(width), int(height)

            # This will eventually call our layout
            if reset_parent:
                self.parent.reset_size(reset_parent)

        # else, the parent is never affected thus we do a layout.
        else:
            self.layout()

    def delete(self):
        if self.is_loaded:
            self.unload()
        self.parent = None
        Managed.delete(self)

    def close(self):
        pass

    def expand(self, width: int, height: int):
        pass


class Controller(Managed):
    opened: bool = False

    def set_manager(self, manager: Manager):
        Managed.set_manager(self, manager)
        manager.add_controller(self)

    def delete(self):
        self.manager.remove_controller(self)
        super().delete()

    def close(self):
        pass

