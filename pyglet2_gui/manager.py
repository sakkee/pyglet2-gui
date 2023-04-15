from __future__ import annotations
import pyglet
from pyglet import gl

from pyglet2_gui.constants import ANCHOR_CENTER, get_relative_point
from pyglet2_gui.core import Rectangle, Controller, Viewer
from pyglet2_gui.containers import Wrapper
from pyglet2_gui.theme.theme import Theme
from typing import Any
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .gui import Frame


class ViewerManagerGroup(pyglet.graphics.Group):
    """Ensure that Viewers inside Manager can be drawn with
    blending enabled, and that Managers are drawn in a particular
    order.
    """
    _top_manager_order: int = 0
    own_order: int

    @classmethod
    def _get_next_top_order(cls):
        cls._top_manager_order += 1
        return cls._top_manager_order

    def __init__(self, parent: pyglet.graphics.Group = None):
        """Creates a new ViewerManagerGroup. By default, it is on top.
        """
        super().__init__(order=self._get_next_top_order(), parent=parent)
        self.own_order = self.order

    def __eq__(self, other: ViewerManagerGroup) -> bool:
        """When compared with other ViewerManagerGroups, we'll return the own_order
        compared against theirs; otherwise use the OrderedGroup comparison.
        """
        if isinstance(other, ViewerManagerGroup):
            return self.own_order == other.own_order
        else:
            return super().__eq__(other)

    def __lt__(self, other: ViewerManagerGroup) -> bool:
        if isinstance(other, ViewerManagerGroup):
            return self.own_order < other.own_order
        else:
            return super().__lt__(other)

    def __hash__(self) -> int:
        return hash((self.order, self.parent))

    def is_on_top(self) -> bool:
        """Are we the top manager group?
        """
        return self.own_order == self._top_manager_order

    def pop_to_top(self):
        """Put us on top of other manager groups.
        """
        self.own_order = self._get_next_top_order()

    def set_state(self):
        """Ensure that blending is set.
        """
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    def unset_state(self):
        """Restore previous blending state.
        """
        gl.glDisable(gl.GL_BLEND)


class ViewerManager(Wrapper):
    _theme: Theme
    _offset: tuple[int, int]
    _batch: pyglet.graphics.Batch
    _has_own_batch: bool
    _root_group: ViewerManagerGroup
    group: dict[str, pyglet.graphics.Group]
    screen: Rectangle
    _window: pyglet.window.Window | None

    def __init__(self, content: Viewer | Frame,
                 theme: Theme,
                 window: pyglet.window.Window = None,
                 batch: pyglet.graphics.Batch = None,
                 group: pyglet.graphics.Group = None,
                 anchor: tuple[int, int] = ANCHOR_CENTER,
                 offset: tuple[int, int] = (0, 0)):
        super().__init__(content=content, anchor=anchor)
        assert isinstance(theme, dict)
        self._theme = theme
        self._manager = self
        self._offset = offset

        if batch is None:
            self._batch = pyglet.graphics.Batch()
            self._has_own_batch = True
        else:
            self._batch = batch
            self._has_own_batch = False

        self._root_group = ViewerManagerGroup(parent=group)
        self.group = {'panel': pyglet.graphics.Group(order=10, parent=self.root_group),
                      'background': pyglet.graphics.Group(order=20, parent=self.root_group),
                      'highlight': pyglet.graphics.Group(order=25, parent=self.root_group),
                      'foreground': pyglet.graphics.Group(order=30, parent=self.root_group)}

        self.content.set_manager(self)
        self.content.parent = self

        self.screen = Rectangle()
        self.load()
        self._window = None
        self.window = window

    @property
    def root_group(self) -> ViewerManagerGroup:
        return self._root_group

    @property
    def batch(self) -> pyglet.graphics.Batch:
        return self._batch

    @property
    def window(self) -> pyglet.window.Window:
        return self._window

    @window.setter
    def window(self, window: pyglet.window.Window):
        if self._window is not None:
            self._window.remove_handlers(self)
        self._window = window

        if self._window is None:
            self.unload()
            self.screen = Rectangle()
        else:
            width, height = window.get_size()
            self.screen = Rectangle(width=width, height=height)
            self._window.push_handlers(self)

        # make a top-down reset_size.
        self.reset_size(reset_parent=False)

        # and set the new position.
        self.set_position(*self.get_position())

    @property
    def offset(self) -> tuple[int, int]:
        return self._offset

    @offset.setter
    def offset(self, offset: tuple[int, int]):
        assert isinstance(offset, tuple)
        assert len(offset) == 2
        self._offset = offset
        self.set_position(*self.get_position())

    @Wrapper.theme.getter
    def theme(self) -> Wrapper.theme:
        return self._theme

    def update_theme(self, new_theme: Theme):
        self._theme = new_theme
        self.refresh()

    @Wrapper.anchor.setter
    def anchor(self, anchor: Wrapper.anchor):
        self._anchor = anchor
        self.set_position(*self.get_position())

    def get_position(self) -> tuple[int, int]:
        # Calculate our position relative to our containing window,
        # making sure that we fit completely on the window.  If our offset
        # sends us off the screen, constrain it.
        x, y = get_relative_point(self.screen, self.anchor, self, None, (0, 0))
        max_offset_x = self.screen.width - int(self.width) - int(x)
        max_offset_y = self.screen.height - int(self.height) - int(y)
        offset_x, offset_y = self._offset
        offset_x = max(min(offset_x, max_offset_x), -x)
        offset_y = max(min(offset_y, max_offset_y), -y)
        self._offset = (offset_x, offset_y)
        x += offset_x
        y += offset_y

        return x, y

    def reset_size(self, reset_parent: bool = True):
        # Manager never has parent and thus never reset_parent.
        super().reset_size(reset_parent=False)

        # if is a bottom-up, we have to reposition ourselves.
        if reset_parent:
            self.set_position(*self.get_position())

    def draw(self):
        assert self._has_own_batch
        self._batch.draw()

    def pop_to_top(self):
        """Puts the manager on top of the other dialogs on the same batch (and window).
        - Pops the manager group to the top
        - Puts the event handler on top of the event handler's stack of the window.
        """
        self._root_group.pop_to_top()
        self._batch._draw_list_dirty = True  # forces resorting groups
        if self._window is not None:
            self._window.remove_handlers(self)
            self._window.push_handlers(self)

    def delete(self):
        Wrapper.delete(self)
        if self._window is not None:
            self._window.remove_handlers(self)
            self._window = None
        self._batch._draw_list_dirty = True  # forces resorting groups


class ControllerManager:
    _controllers: list[Controller]  # list of controllers
    _hover: Controller | None = None  # the control that is being hovered (mouse inside)
    _focus: Controller | None = None  # the control that has the focus (accepts key strokes)
    wheel_target: Controller | None = None  # the primary control to receive wheel events.
    wheel_hint: Controller | None = None  # the secondary control to receive wheel events.

    def __init__(self):
        self._controllers = []

    @property
    def controllers(self) -> list[Controller]:
        return self._controllers

    def add_controller(self, controller: Controller):
        assert controller not in self._controllers
        self._controllers.append(controller)

    def remove_controller(self, controller: Controller):
        assert controller in self._controllers
        self._controllers.remove(controller)
        if self._hover == controller:
            self.set_hover(None)
        if self._focus == controller:
            self.set_focus(None)

    def set_next_focus(self, direction: int):
        assert direction in [-1, 1]

        # all the focusable controllers
        focusable = [x for x in self._controllers if hasattr(x, 'on_gain_focus')]
        if not focusable:
            return
        if len(focusable) == 1:
            focusable.append(None)

        if self._focus is not None and self._focus in focusable:
            index = focusable.index(self._focus)
        else:
            index = 0 - direction

        new_focus = focusable[(index + direction) % len(focusable)]
        self.set_focus(new_focus)

    def on_key_press(self, symbol: int, modifiers: int) -> Any:
        # move between focusable controllers.
        if symbol == pyglet.window.key.TAB:
            if modifiers & pyglet.window.key.MOD_SHIFT:
                direction = -1
            else:
                direction = 1

            self.set_next_focus(direction)
            return True  # we only change focus on the manager we are in.

        if self._focus is not None and hasattr(self._focus, 'on_key_press'):
            return self._focus.on_key_press(symbol, modifiers)

    def on_key_release(self, symbol: int, modifiers: int) -> Any:
        if self._focus is not None and hasattr(self._focus, 'on_key_release'):
            return self._focus.on_key_release(symbol, modifiers)

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int) -> Any:
        if self._focus is not None and hasattr(self._focus, 'on_mouse_drag'):
            return self._focus.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int) -> Any:
        new_hover = None
        for control in self._controllers:
            if control.hit_test(x, y):
                new_hover = control
                break
        self.set_hover(new_hover)

        if self._hover is not None and hasattr(self._hover, 'on_mouse_motion'):
            return self._hover.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> Any:
        self.set_focus(self._hover)
        if self._focus and hasattr(self._focus, 'on_mouse_press'):
            return self._focus.on_mouse_press(x, y, button, modifiers)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> Any:
        if self._focus is not None and hasattr(self._focus, 'on_mouse_release'):
            return self._focus.on_mouse_release(x, y, button, modifiers)

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> Any:
        if self.wheel_target in self._controllers:
            return self.wheel_target.on_mouse_scroll(x, y, scroll_x, scroll_y)
        elif self.wheel_hint in self._controllers:
            return self.wheel_hint.on_mouse_scroll(x, y, scroll_x, scroll_y)
        else:
            return False

    def on_text(self, text: str) -> Any:
        if self._focus and text != '\r' and hasattr(self._focus, 'on_text'):
            return self._focus.on_text(text)

    def on_text_motion(self, motion: int) -> Any:
        if self._focus and hasattr(self._focus, 'on_text_motion'):
            return self._focus.on_text_motion(motion)

    def on_text_motion_select(self, motion: int) -> Any:
        if self._focus and hasattr(self._focus, 'on_text_motion_select'):
            return self._focus.on_text_motion_select(motion)

    def set_focus(self, focus: Controller | None):
        if self._focus == focus:
            return
        if self._focus is not None and hasattr(self._focus, 'on_lose_focus'):
            self._focus.on_lose_focus()
        self._focus = focus
        if focus is not None and hasattr(self._focus, 'on_gain_focus'):
            self._focus.on_gain_focus()

    def set_hover(self, hover: Controller | None):
        if self._hover == hover:
            return

        if self._hover is not None and hasattr(self._hover, 'on_lose_highlight'):
            self._hover.on_lose_highlight()
        self._hover = hover
        if hover is not None and hasattr(self._hover, 'on_gain_highlight'):
            hover.on_gain_highlight()

    def set_wheel_hint(self, control: Controller | None):
        self.wheel_hint = control

    def set_wheel_target(self, control: Controller | None):
        self.wheel_target = control

    def delete(self):
        self._controllers.clear()
        self._focus = None
        self._hover = None
        self.wheel_hint = None
        self.wheel_target = None


class Manager(ViewerManager, ControllerManager):
    is_movable: bool
    _is_dragging: bool = False
    on_mouse_click: Callable[[int, int, int, int, bool], Any] | None
    on_mouse_unclick: Callable[[int, int, int, int, bool], Any] | None

    def __init__(self,
                 content: Viewer | Frame,
                 theme: Theme,
                 window: pyglet.window.Window = None,
                 batch: pyglet.graphics.Batch = None,
                 group: pyglet.graphics.Group = None,
                 is_movable: bool = True,
                 anchor: tuple[int, int] = ANCHOR_CENTER,
                 offset: tuple[int, int] = (0, 0),
                 on_mouse_click: Callable[[int, int, int, int, bool], Any] | None = None,
                 on_mouse_unclick: Callable[[int, int, int, int, bool], Any] | None = None):
        ControllerManager.__init__(self)
        ViewerManager.__init__(self, content=content, theme=theme, window=window, batch=batch,
                               group=group, anchor=anchor, offset=offset)

        self.is_movable = is_movable
        self.on_mouse_click = on_mouse_click
        self.on_mouse_unclick = on_mouse_unclick

    def hit_test(self, x: int, y: int) -> bool:
        return self.is_inside(x, y)

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int) -> bool:
        if not ControllerManager.on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
            if self.is_movable and self._is_dragging:
                x, y = self._offset
                self._offset = (int(x + dx), int(y + dy))
                self.set_position(*self.get_position())
                return True

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        ControllerManager.on_mouse_motion(self, x, y, dx, dy)
        if self.hit_test(x, y):
            return True

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> Any:
        for controller in self._controllers:
            if controller.opened:
                controller.close()
        retval = ControllerManager.on_mouse_press(self, x, y, button, modifiers)
        if self.hit_test(x, y):
            if not retval:
                self._is_dragging = True
                retval = True
                if self.on_mouse_click:
                    self.on_mouse_click(x, y, button, modifiers, True)

        return retval

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int) -> Any:
        self._is_dragging = False
        if self.on_mouse_unclick:
            self.on_mouse_unclick(x, y, button, modifiers, True)
        return ControllerManager.on_mouse_release(self, x, y, button, modifiers)

    def on_resize(self, width: int, height: int):
        """Update our knowledge of the window's width and height.
        """
        if self.screen.width != width or self.screen.height != height:
            self.screen.width, self.screen.height = width, height
            self.set_position(*self.get_position())

    def delete(self):
        ViewerManager.delete(self)
        ControllerManager.delete(self)
