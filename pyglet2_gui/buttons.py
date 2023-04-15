import pyglet.window
from pyglet2_gui.override import Label
from pyglet2_gui.constants import HALIGN_LEFT, HALIGN_RIGHT, HALIGN_CENTER, VALIGN_BOTTOM, VALIGN_CENTER
from pyglet2_gui.controllers import TwoStateController
from pyglet2_gui.core import Viewer
from pyglet2_gui.mixins import FocusMixin, HighlightMixin
from pyglet2_gui.theme import templates
from pyglet2_gui.theme.theme import Theme
from typing import Any
from collections.abc import Callable


class Button(TwoStateController, Viewer):
    _width: int = 0
    _height: int = 0
    label: str = ""
    _label: Label | None = None
    _outline_graphic: templates.TextureGraphicElement | None = None
    _button: templates.TextureGraphicElement | None = None
    _path: list[str] | None = None  # path in the theme
    _alternative_theme: Theme | None = None
    font_size: int | None = None
    argument: Any = None  # argument passed to callable functions
    _outline_path: list[str] | str | tuple[str] | None = None
    disabled: bool = False
    _align: int = HALIGN_CENTER
    _font_color: tuple[int, int, int, int] | None = None
    _font_name: str | None
    _font_valign: int = VALIGN_CENTER
    on_right_press: Callable[[Any], Any] | None = None

    def __init__(self,
                 label: str = "",
                 is_pressed: bool = False,
                 on_press: Callable[[Any], Any] = None,
                 width: int = 0,
                 height: int = 0,
                 font_size: int = None,
                 path: str | list[str] | tuple[str] | None = None,
                 alternative_theme: Theme = None,
                 argument: Any = None,
                 outline_path: str = None,
                 disabled: bool = False,
                 align: int = HALIGN_CENTER,
                 font_color: tuple[int, int, int, int] | None = None,
                 texture: pyglet.image.Texture = None,
                 font_name: str | None = None,
                 font_valign: int = VALIGN_CENTER,
                 on_right_press: Callable[[Any], Any] = None):

        TwoStateController.__init__(self, is_pressed=is_pressed, on_press=on_press)
        Viewer.__init__(self, width=width, height=height)

        self._width = width
        self._height = height
        self.label = label

        # font stuff
        self._font_name = font_name
        self._font_size = font_size
        self._font_color = font_color
        self._font_valign = font_valign

        self._path = [path] if path is not None else ['button']
        self._alternative_theme = alternative_theme
        self.argument = argument
        self._outline_path = outline_path
        self.disabled = disabled
        self._align = align
        self._textureZ = texture
        self.on_right_press = on_right_press

    def change_state_without_fnc(self):
        self.is_pressed = not self.is_pressed
        self.reload()
        self.reset_size()

    def change_state(self):
        self.is_pressed = not self.is_pressed
        self.reload()
        self.reset_size()
        if self.argument is None:
            self.on_press(self.is_pressed)
        else:
            self.on_press(self.argument)

    def hit_test(self, x: int, y: int) -> bool:
        return self.is_inside(x, y)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        if not self.disabled:
            if self.on_right_press is None or button == 1:  # left click or no set right click
                self.change_state()
            elif self.on_right_press is not None and button == 4:  # right click
                self.on_right_press(self.argument)

    def get_path(self) -> list[str]:
        return [self._path[0], self.get_pressed_path()]

    def get_pressed_path(self) -> str:
        return 'down' if self.is_pressed else 'up'

    def load_graphics(self):
        theme = self._alternative_theme.get('button') if self._alternative_theme is not None \
            else self.theme.get(self.get_path())
        if self._textureZ is None:
            self._button = theme.get('image').generate(theme.get('gui_color', (255, 255, 255, 255)),
                                                       **self.get_batch('background'))

        else:
            self._button = templates.TextureTemplate(self._textureZ).generate((255, 255, 255, 255),
                                                                              **self.get_batch('background'))
        if self._outline_path is not None:
            outline_theme = self.theme.get(self._outline_path).get('normal')
            self._outline_graphic = outline_theme.get('image').generate((255, 255, 255, 255),
                                                                        **self.get_batch('foreground'))
        if self.label:
            _font_size = self._font_size or theme.get('font_size')
            _font_color = self._font_color or theme.get('font_color')
            _font_name = self._font_name or theme.get('font_name')
            self._label = Label(self.label,
                                font_name=_font_name,
                                font_size=_font_size,
                                color=_font_color,
                                **self.get_batch('foreground'))

    def unload_graphics(self):
        if self._outline_graphic is not None:
            self._outline_graphic.unload()
        self._button.unload()
        if self._label is not None:
            self._label.unload()

    def compute_size(self) -> tuple[int, int]:
        # Treat the height of the label as ascent + descent
        if self._label is not None:
            font = self._label.document.get_font()
            if not self._width and not self._height:
                height = font.ascent - font.descent
                return self._button.get_needed_size(self._label.content_width, height)
            elif self._width and not self._height:
                height = font.ascent - font.descent
                return self._button.get_needed_size(self._width, height)
            elif self._height and not self._width:
                return self._button.get_needed_size(self._label.content_width, self._height)
            else:
                return self._button.get_needed_size(self._width, self._height)
        else:
            return self._button.get_needed_size(self._width, self._height)

    def layout(self):
        self._button.update(self.x, self.y, self.width, self.height)

        if self._outline_graphic is not None:
            self._outline_graphic.update(self.x, self.y, self.width, self.height)

        if self._label is not None:
            # centers the label in the middle of the button
            x, y, width, height = self._button.get_content_region()
            font = self._label.document.get_font()
            if self._align == HALIGN_CENTER:
                _x = x + width / 2 - self._label.content_width / 2 + 1
            else:
                _x = x + 4
            if self._font_valign == VALIGN_BOTTOM:
                _y = y + font.ascent / 2 + font.descent + 2
            else:
                _y = y + height / 2 - font.ascent / 2 - font.descent - 2
            self._label.pos(_x, _y)

    def delete(self):
        TwoStateController.delete(self)
        Viewer.delete(self)


class GroupButton(Button):
    button_groups: dict
    group_id: str = ""

    def __init__(self, group_id: str = "", **kwargs):
        super().__init__(**kwargs)
        self.group_id = group_id
        self.button_groups = {}
        self.button_groups.setdefault(group_id, []).append(self)

    def change_state(self):
        for button in self.button_groups[self.group_id]:
            if button.is_pressed and button is not self:
                button.change_state()
        super().change_state()


class OneTimeButton(Button):
    on_release: Callable[[Any], Any] = None

    def __init__(self, label: str = "", on_release: Callable[[Any], Any] = None, **kwargs):
        super().__init__(label=label, **kwargs)
        self.on_release = on_release if on_release is not None else lambda x: x

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if self.is_pressed:
            self.change_state_without_fnc()

            # If mouse is still hovering us, signal on_release
            if self.hit_test(x, y) and not self.disabled:
                if self.argument is not None:
                    self.on_release(self.argument)
                else:
                    self.on_release(self.is_pressed)


class Checkbox(Button):
    align: int
    w: int = 0
    h: int = 0
    _padding: int

    def __init__(self, label: str = "", padding: int = 4, align=HALIGN_RIGHT, width: int = 24, height: int = 24, **kwargs):
        assert align in [HALIGN_LEFT, HALIGN_RIGHT]
        super().__init__(label=label, align=align, width=width, height=height, **kwargs)
        self.align = self._align
        self.w = self.width
        self.h = self.height
        self._padding = padding

    def get_path(self) -> list[str]:
        path = ['checkbox']
        if self.is_pressed:
            path.append('checked')
        else:
            path.append('unchecked')
        return path

    def layout(self):
        if self.align == HALIGN_RIGHT:  # label goes on right
            self._button.update(self.x,
                                self.y + self.height / 2 - self.h / 2,
                                self.w,
                                self.h)

        else:  # label goes on left
            self._button.update(self.x + self._label.content_width + self._padding,
                                self.y + self.height / 2 - self.h / 2,
                                self.w,
                                self.h)

        font = self._label.document.get_font()
        height = font.ascent - font.descent
        _x = self.x if self.align != HALIGN_RIGHT else self.x + self.w + self._padding
        _y = self.y + self.height / 2 - height / 2 - font.descent
        self._label.position = (_x, _y, 0)

    def compute_size(self) -> tuple[int, int]:
        if self._width is not None and self._height is not None:
            self.w = self._width
            self.h = self._height
        else:
            self.w = self._button.width
            self.h = self._button.height

        # Treat the height of the label as ascent + descent
        if self._label is not None:
            font = self._label.document.get_font()
            height = font.ascent - font.descent
            return self.w + self._padding + self._label.content_width, max(self.h, height)
        else:
            return self.w + self._padding, self.h


class FocusButton(Button, FocusMixin):
    """Button that is focusable and thus can be selected with TAB.
    """

    def __init__(self, label: str = "", **kwargs):
        Button.__init__(self, label=label, **kwargs)
        FocusMixin.__init__(self)

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == pyglet.window.key.ENTER:
            self.change_state()


class HighlightedButton(OneTimeButton, HighlightMixin):
    """An example of a Button that changes behavior when is mouse-hovered.
    We mix the behavior of button with HighlightMixin.
    """

    def __init__(self, label: str = "", outline_path: str = None, **kwargs):
        OneTimeButton.__init__(self, label=label, outline_path=outline_path, **kwargs)
        HighlightMixin.__init__(self, outline_path=outline_path)

    def load_graphics(self):
        OneTimeButton.load_graphics(self)
        HighlightMixin.load_graphics(self)

    def layout(self):
        OneTimeButton.layout(self)
        HighlightMixin.layout(self)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int):
        OneTimeButton.change_state(self)
        HighlightMixin.unload_graphics(self)

    def unload_graphics(self):
        OneTimeButton.unload_graphics(self)
        HighlightMixin.unload_graphics(self)
