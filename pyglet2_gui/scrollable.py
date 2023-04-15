import pyglet
from pyglet import gl
from pyglet2_gui.core import Managed, Viewer
from pyglet2_gui.manager import ControllerManager, Manager

from pyglet2_gui.controllers import Controller
from pyglet2_gui.containers import Wrapper
from pyglet2_gui.scrollbars import HScrollbar, VScrollbar
from pyglet2_gui.theme.theme import Theme
from typing import Any


class ScrollableGroup(pyglet.graphics.Group):
    """We restrict what's shown within a Scrollable by performing a scissor
    test.
    """
    x: int
    y: int
    width: int
    height: int
    was_scissor_enabled: bool = False

    def __init__(self, x: int, y: int, width: int, height: int, parent: Any = None):
        super().__init__(parent=parent)
        self.x, self.y, self.width, self.height = x, y, width, height

    def set_state(self):
        """Enables a scissor test on our region
        """
        # gl.glPushAttrib(gl.GL_ENABLE_BIT | gl.GL_TRANSFORM_BIT | gl.GL_CURRENT_BIT)
        self.was_scissor_enabled = gl.glIsEnabled(gl.GL_SCISSOR_TEST)
        gl.glEnable(gl.GL_SCISSOR_TEST)
        gl.glScissor(int(self.x), int(self.y), int(self.width), int(self.height))

    def unset_state(self):
        """Disables the scissor test
        """
        if not self.was_scissor_enabled:
            gl.glDisable(gl.GL_SCISSOR_TEST)


class Scrollable(Wrapper, Controller, ControllerManager):
    max_width: int
    max_height: int
    is_fixed_size: bool
    _hscrollbar: HScrollbar | None = None
    _vscrollbar: VScrollbar | None = None
    _content_width: int = 0
    _content_height: int = 0
    _content_x: int = 0
    _content_y: int = 0
    _content_length: int  # the number of contents  todo fix
    _theme: Theme | None = None
    batch: pyglet.graphics.Batch | None = None
    root_group: ScrollableGroup | None = None
    group: dict

    def __init__(self, content: Viewer = None, width: int = None, height: int = None, is_fixed_size: bool = False,
                 content_length: int = None):
        if is_fixed_size:
            assert width is not None and height is not None
        Wrapper.__init__(self, content=content)
        ControllerManager.__init__(self)
        self.max_width = width
        self.max_height = height
        self.is_fixed_size = is_fixed_size
        self._content_length = content_length
        self.group = {'panel': None, 'background': None, 'foreground': None, 'highlight': None}

    @Managed.theme.getter
    def theme(self) -> Theme:
        return self._theme

    def set_manager(self, manager: Manager):
        Controller.set_manager(self, manager)
        self._theme = manager.theme
        self.batch = manager.batch
        self.root_group = ScrollableGroup(0, 0, self.width, self.height, parent=manager.group.get('foreground'))
        self.group.update({
            'panel': pyglet.graphics.Group(order=10, parent=self.root_group),
            'background': pyglet.graphics.Group(order=20, parent=self.root_group),
            'foreground': pyglet.graphics.Group(order=30, parent=self.root_group),
            'highlight': pyglet.graphics.Group(order=20, parent=self.root_group)
        })
        self.content.set_manager(self)
        self.content.parent = self

    def unload_graphics(self):
        Wrapper.unload_graphics(self)
        if self._hscrollbar is not None:
            self._hscrollbar.unload()
            self._hscrollbar = None
        if self._vscrollbar is not None:
            self._vscrollbar.unload()
            self._vscrollbar = None

    def expand(self, width: int, height: int):
        if self.content.is_expandable():
            if self._vscrollbar is not None:
                self._content_width = width
            else:
                self._content_width = width
            if self._hscrollbar is not None:
                self._content_height = height
            else:
                self._content_height = height
            self.content.expand(max(self._content_width, self.content.width),
                                max(self._content_height, self.content.height))
        self.width, self.height = width, height

    def hit_test(self, x: int, y: int) -> bool:
        # We only intercept events for the content region, not for
        # the scrollbars. They can handle themselves.
        return y >= self._content_y < self._content_y + self._content_height and \
            self._content_x <= x < self._content_x + self._content_width

    def is_expandable(self) -> True:
        return True

    def _load_scrollbars(self, width: int, height: int):
        # if content size bigger than our size,
        # we load a scrollbar
        if self.content.width > width:
            if self._hscrollbar is None:
                self._hscrollbar = HScrollbar(width)
                self._hscrollbar.set_manager(self.manager)
                self._hscrollbar.parent = self
                self._hscrollbar.load()
        # if smaller, we unload it if it is loaded
        elif self._hscrollbar is not None:
            self._hscrollbar.delete()
            self._hscrollbar = None

        if self.content.height > height:
            if self._vscrollbar is None:
                self._vscrollbar = VScrollbar(height, content_length=self._content_length)
                self._vscrollbar.set_manager(self.manager)
                self._vscrollbar.parent = self
                self._vscrollbar.load()
        elif self._vscrollbar is not None:
            self._vscrollbar.delete()
            self._vscrollbar = None
            self.manager.set_wheel_target(None)

    def layout(self, load_wrapper: bool = True):
        if load_wrapper:
            Wrapper.layout(self)

        # Work out the adjusted content width and height
        y = self.y + (self.height - self._content_height)
        if self._hscrollbar is not None:
            self._hscrollbar.set_position(self.x, self.y)
        if self._vscrollbar is not None:
            self._vscrollbar.set_position(self.x + self._content_width, y)

        # Set the scissor group
        self.root_group.x, self.root_group.y = self.x - 1, y - 1
        self.root_group.width = self._content_width + 1
        self.root_group.height = self._content_height + 1

        # Work out the content layout
        self._content_x, self._content_y = self.x, y
        left = self.x
        top = y + self._content_height - self.content.height

        if self._hscrollbar:
            left -= self._hscrollbar.get_knob_pos()
        if self._vscrollbar:
            top += self._vscrollbar.get_knob_pos()

        self.content.set_position(left, top)

    def on_gain_highlight(self):
        if self._hscrollbar is not None:
            self.manager.set_wheel_hint(self._hscrollbar)
        if self._vscrollbar is not None:
            self.manager.set_wheel_target(self._vscrollbar)

    def on_lose_highlight(self):
        ControllerManager.set_hover(self, None)
        self.manager.set_wheel_target(None)
        self.manager.set_wheel_hint(None)

    def compute_size(self) -> tuple[int, int]:
        content_width, content_height = self.content.compute_size()

        width = min(self.max_width or content_width, content_width)
        height = min(self.max_height or content_height, content_height)

        self._content_width = width
        self._content_height = height

        # we have to load the scrolls here because they require knowing content size
        self._load_scrollbars(width, height)
        if self._hscrollbar is not None:
            self._hscrollbar.set_knob_size(self._content_width, content_width)
            _, scroll_height = self._hscrollbar.compute_size()
            height += scroll_height

        if self._vscrollbar is not None:
            self._vscrollbar.set_knob_size(self._content_height, content_height)
            scroll_width, _ = self._vscrollbar.compute_size()
            width += scroll_width
        return width, height

    def reset_size(self, reset_parent: bool = True):
        Wrapper.reset_size(self, reset_parent)
        if self._hscrollbar is not None:
            self._hscrollbar.reset_size(reset_parent=False)
        if self._vscrollbar is not None:
            self._vscrollbar.reset_size(reset_parent=False)

    def delete(self):
        Wrapper.delete(self)
        ControllerManager.delete(self)
