from __future__ import annotations
from collections import OrderedDict
from typing import Any
from collections.abc import Callable
from pyglet2_gui.core import Controller

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .option_selectors import OptionButton


class TwoStateController(Controller):
    is_pressed: bool
    on_press: Callable[[Any], Any]

    def __init__(self, is_pressed: bool = False, on_press: Callable[[Any], Any] = None):
        super().__init__()
        self.is_pressed = is_pressed
        self.on_press = on_press if on_press is not None else lambda y: y

    def change_state(self):
        self.is_pressed = not self.is_pressed
        self.on_press(self.is_pressed)


class ContinuousStateController(Controller):
    min_value: float
    max_value: float
    value: float
    on_set: Callable[[Any], Any]

    def __init__(self, value: float = 0.0, min_value: float = 0.0, max_value: float = 1.0,
                 on_set: Callable[[Any], Any] | None = None):
        assert min_value <= value <= max_value
        super().__init__()
        self.min_value = min_value
        self.max_value = max_value
        self.value = value
        self.on_set = on_set if on_set is not None else lambda x: x

    def set_value(self, value: float):
        assert self.min_value <= value <= self.max_value
        self.value = value
        self.on_set(value)


class Option(Controller):
    _option_name: str
    _selector: Any

    def __init__(self, name: str, parent: Selector):
        super().__init__()
        self._option_name = name
        self._selector = parent

    def select(self):
        self._selector.deselect()
        self._selector.select(self._option_name)


class Selector:
    _selected: str | None
    _options: OrderedDict[str, OptionButton]
    _on_select: Callable[[Any], Any]
    opened: bool = False

    def __init__(self, options: list[str], labels: list[str] = None, on_select: Callable[[Any], Any] = None,
                 selected: str = None):
        assert len(options) > 0
        assert None not in options
        assert labels is None or len(options) == len(labels)
        assert selected is None or selected in options

        if labels is None:
            labels = options
        self._selected = selected
        widget_options = self._make_options(options, labels)
        self._options = OrderedDict(list(zip(options, widget_options)))
        self._on_select = on_select if on_select else lambda x: x

    def _make_options(self, options: list[str], labels: list[str]):
        # todo has to be implemented.
        raise NotImplementedError

    def select(self, option_name: str):
        if self._selected is not None:
            self._options[self._selected].change_state()
        self._selected = option_name
        self._options[option_name].change_state()
        self._on_select(option_name)

    def deselect(self):
        if self._selected is not None:
            self._options[self._selected].change_state()
        self._selected = None
