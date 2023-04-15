from __future__ import annotations
import pyglet

from pyglet2_gui.controllers import Option, Selector
from pyglet2_gui.gui import Frame
from pyglet2_gui.containers import VerticalContainer
from pyglet2_gui.constants import ANCHOR_TOP_LEFT, ANCHOR_BOTTOM_LEFT, HALIGN_CENTER, VALIGN_TOP
from pyglet2_gui.manager import Manager
from pyglet2_gui.scrollable import Scrollable
from pyglet2_gui.buttons import OneTimeButton, HighlightedButton
from typing import Any
from collections.abc import Callable


class OptionButton(Option, HighlightedButton):
    def __init__(self, option_name: str, button_text: str = "", is_selected: bool = False, parent: Any = None):
        Option.__init__(self, name=option_name, parent=parent)
        HighlightedButton.__init__(self, label=button_text, is_pressed=is_selected)

    def expand(self, width: int, height: int):
        self.width = width
        self.height = height

    def is_expandable(self) -> True:
        return True

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> True:
        self.select()
        try:
            self.parent.layout()
        except:
            pass
        return True

    def on_key_press(self, symbol: int, modifiers: int) -> bool:
        if symbol == pyglet.window.key.ENTER:
            self.select()
            self.parent.layout()
            return True


class VerticalButtonSelector(VerticalContainer, Selector):
    def __init__(self, options: list[str], labels: list[str] | None = None,
                 align: int = HALIGN_CENTER, padding: int = 4, on_select: Callable[[Any], Any] | None = None):
        Selector.__init__(self, options=options, labels=labels, on_select=on_select)
        VerticalContainer.__init__(self, content=list(self._options.values()), align=align, padding=padding)

    def _make_options(self, options: list[str], labels: list[str]) -> list[OptionButton]:
        widget_options = []
        for option, label in zip(options, labels):
            widget_options.append(OptionButton(option, label, is_selected=(option == self._selected), parent=self))
        return widget_options


class Dropdown(Selector, HighlightedButton):
    max_height: int
    align: int
    _pulldown_menu: Manager | None = None

    def __init__(self, options: list[str], labels: list[str] | None = None, max_height: int = 400,
                 align: int = VALIGN_TOP, on_select: Callable[[Any], Any] = None):
        Selector.__init__(self, options=options, labels=labels, on_select=on_select, selected=options[0])
        HighlightedButton.__init__(self)
        self.max_height = max_height
        self.align = align

    def _make_options(self, options: list[str], labels: list[str]):
        widget_options = []
        for option, label in zip(options, labels):
            widget_options.append(OptionButton(option_name=option, button_text=label,
                                               is_selected=(option == self._selected),
                                               parent=self))
        return widget_options

    def close(self):
        if self._pulldown_menu is not None:
            self.opened = False
            self._pulldown_menu.delete()
            self._pulldown_menu = None

    def get_path(self) -> str:
        return 'dropdown'

    def load_graphics(self):
        self.label = self._options.get(self._selected).label
        OneTimeButton.load_graphics(self)

    def unload_graphics(self):
        OneTimeButton.unload_graphics(self)
        self.close()

    def select(self, option_name: str):
        Selector.select(self, option_name)
        self.close()
        self.reload()
        self.reset_size()
        self.layout()
        self.manager.set_focus(None)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        """A mouse press is going to create a manager with the options.
        """
        # if it's already opened, we just close it.
        if self._pulldown_menu is not None:
            self.close()
            return

        # Compute the anchor point and location for the manager
        width, height = self.manager.window.get_size()
        if self.align == VALIGN_TOP:
            # Dropdown is at the top, pulldown appears below it
            anchor = ANCHOR_TOP_LEFT
            x = self.x
            y = -(height - self.y - 1)
        else:
            # Dropdown is at the bottom, pulldown appears above it
            anchor = ANCHOR_BOTTOM_LEFT
            x = self.x
            y = self.y + self.height + 1

        # we set the manager
        self.opened = True
        self._pulldown_menu = \
            Manager(
                Frame(
                    Scrollable(
                        VerticalContainer(list(self._options.values())),
                        height=self.max_height, content_length=len(self._options)
                    ),
                    path=['dropdown', 'pulldown']
                ),
                window=self.manager.window, batch=self.manager.batch,
                group=self.manager.root_group.parent, theme=self.manager.theme,
                is_movable=False, anchor=anchor, offset=(x, y)
            )

    def delete(self):
        self.close()
        OneTimeButton.delete(self)
