from pyglet2_gui.buttons import HighlightedButton
from pyglet2_gui.gui import Label, Frame
from pyglet2_gui.containers import HorizontalContainer, VerticalContainer
from pyglet2_gui.manager import Manager
from pyglet2_gui.text_input import TextInput
from collections.abc import Callable
from typing import Any


class PopupInput(Manager):
    input: TextInput

    def __init__(self, text: str = "", ok: str = "Ok", cancel: str = "Cancel",
                 on_ok: Callable[[str], Any] = None,
                 on_cancel: Callable[[Any], Any] = None,
                 font_color: tuple[int, int, int, int] = None, bold: bool = False,
                 max_length: int = 44, placeholder: str = "", **kwargs):

        self.input = TextInput(placeholder=placeholder, padding=4, length=24, max_length=max_length)

        def on_ok_click(_):
            if on_ok is not None:
                on_ok(self.input.get_text())
            self.delete()

        def on_cancel_click(_):
            if on_cancel is not None:
                on_cancel(self)
            self.delete()

        super().__init__(content=Frame(
            VerticalContainer([
                Label(text, color=font_color, bold=bold),
                self.input,
                HorizontalContainer([HighlightedButton(ok, on_release=on_ok_click),
                                     None,
                                     HighlightedButton(cancel, on_release=on_cancel_click)]
                                    )])
        ), is_movable=True, **kwargs)


class PopupMessage(Manager):
    """A simple fire-and-forget manager."""

    def __init__(self, text: str = "",
                 font_color: tuple[int, int, int, int] = None,
                 width: int = None,
                 on_escape: Callable[[Any], Any] = None,
                 has_focus: bool = False, font_size: int = None,
                 multiline: bool = False, **kwargs):
        def on_ok(_):
            if on_escape is not None:
                on_escape(self)
            self.delete()

        button = HighlightedButton("Ok", on_release=on_ok)
        super().__init__(content=Frame(
            VerticalContainer(
                [
                    Label(text, color=font_color, font_size=font_size, width=width, multiline=multiline),
                    button
                ])
        ), is_movable=True, **kwargs)
        Manager.set_next_focus(self, 1 if has_focus else -1)


class PopupConfirm(Manager):
    """An ok/cancel-style dialog.  Escape defaults to cancel."""
    argument: Any

    def __init__(self, text: str = "", ok: str = "Ok", cancel: str = "Cancel",
                 on_ok: Callable[[Any], Any] = None, on_cancel: Callable[[Any], Any] = None,
                 argument: Any = None, **kwargs):
        self.argument = argument

        def on_ok_click(_):
            if on_ok is not None:
                on_ok(self.argument if self.argument is not None else True)
            self.delete()

        def on_cancel_click(_):
            if on_cancel is not None:
                on_cancel(self.argument if self.argument is not None else False)
            self.delete()

        super().__init__(content=Frame(
            VerticalContainer([
                Label(text),
                HorizontalContainer([HighlightedButton(ok, on_release=on_ok_click),
                                     None,
                                     HighlightedButton(cancel, on_release=on_cancel_click)]
                                    )])
        ), **kwargs)
