import pyglet
from pyglet2_gui.mixins import FocusMixin
from pyglet2_gui.override import InputLabel
from pyglet2_gui.core import Viewer
from pyglet2_gui.theme.elements import FrameTextureGraphicElement
from pyglet2_gui.theme.theme import Theme
from typing import Any
from collections.abc import Callable


class TextInput(FocusMixin, Viewer):
    """This class works in two states defined by is_focus():
       True: "writing"
       False: "label
   """
    _document: pyglet.text.document.UnformattedDocument
    _document_style_set: bool = False  # check if style of document was set.
    _length: int  # the length of the box in characters
    _max_length: int  # the max length allowed for writing.
    _on_input: Callable[[Any], Any] | None
    focused: bool = False
    _padding: int
    _field: FrameTextureGraphicElement | None = None
    w1: int  # width
    h1: int  # height
    _text_layout: pyglet.text.layout.IncrementalTextLayout | None = None
    _caret: pyglet.text.caret.Caret | None = None
    _label: InputLabel | None = None
    _caret_height: int = 0
    _font_size: float | None
    _font_name: str | list[str] | None
    _font_color: tuple[int, int, int, int] | None
    multiline: bool
    placeholder: str

    def __init__(self, text: str = "", length: int = 20, max_length: int = None,
                 font_name: str | list[str] | None = None, padding: int = 4,
                 on_input: Callable[[Any], Any] = None, width: int = None, height: int = None, font_size: float = None,
                 font_color: tuple[int, int, int, int] = None, multiline: bool = False, placeholder: str = ""):
        Viewer.__init__(self)
        FocusMixin.__init__(self)

        self.placeholder = placeholder
        self._document = pyglet.text.document.UnformattedDocument(text if text else placeholder)
        self._length = length
        self._max_length = max_length
        self._on_input = on_input
        self._padding = 4 + padding
        self.w1 = width
        self.h1 = height
        self._font_size = font_size
        self._font_name = font_name
        self._font_color = font_color
        self.multiline = multiline

    def get_path(self) -> str:
        return 'input'

    def _load_label(self, theme: Theme):
        font_name = self._font_name if self._font_name else theme.get('font_name', 'Arial')
        font_size = self._font_size if self._font_size else theme.get('font_size', 12)
        if not self._font_color:
            self._font_color = theme.get('font_color', (0, 0, 0, 255))
        color = self._font_color[:3] + (self._font_color[3] // 2,) if self.placeholder else self._font_color
        anchor_y = 'top' if self.multiline else 'baseline'

        self._label = InputLabel(text=self._document.text,
                                 width=self.width - self._padding * 2,
                                 color=color,
                                 font_name=font_name,
                                 font_size=font_size,
                                 multiline=self.multiline,
                                 anchor_y=anchor_y,
                                 **self.get_batch('foreground'))

    def _load_writing(self, theme: Theme):
        needed_width, needed_height = self._compute_needed_size()
        self._text_layout = pyglet.text.layout.IncrementalTextLayout(
            self._document, needed_width - self._padding * 2, needed_height,
            multiline=self.multiline, **self.get_batch('foreground'))

        self._caret = pyglet.text.caret.Caret(self._text_layout, color=self._font_color[0:3])
        self._caret.visible = True
        self._caret.mark = 0
        self._caret.position = len(self._document.text)
        self._caret_height = self._caret._layout._height

    def load_graphics(self):
        theme = self.theme.get(self.get_path())

        # We set the style once. We shouldn't have to do so again because
        # it's an UnformattedDocument.
        if not self._document_style_set:
            font_name = self._font_name if self._font_name else theme.get('font_name', 'Arial')
            font_size = self._font_size if self._font_size else theme.get('font_size', 12.0)
            if not self._font_color:
                self._font_color = theme.get('font_color', (0, 0, 0, 255))
            self._document.set_style(0, 0,  # parameters not used in set_style
                                     dict(color=self._font_color,
                                          font_name=font_name,
                                          font_size=font_size))
            self._document_style_set = True

        self._field = theme.get('image').generate(color=theme.get('gui_color'), **self.get_batch('background'))
        if self.is_focus():
            self._load_writing(theme)
        else:
            self._load_label(theme)

    def _unload_writing(self):
        self._caret.delete()  # it should be .unload(), but Caret does not have it.
        self._document.remove_handlers(self._text_layout)
        self._text_layout.delete()  # it should also be .unload().
        self._caret = self._text_layout = None

    def _unload_label(self):
        self._label.delete()
        self._label = None

    def unload_graphics(self):
        if self.is_focus():
            self._unload_writing()
        else:
            self._unload_label()

        self._field.unload()

    def _compute_needed_size(self) -> tuple[int, int]:
        # Calculate the needed size based on the font size
        font = self._document.get_font(0)

        if self.w1 is None:
            glyphs = font.get_glyphs('A_')
            width = max([x.width for x in glyphs])
            needed_width = self._length * width - 2 * self._padding
        else:
            needed_width = self.w1
        if self.h1 is None:
            height = font.ascent - font.descent
            needed_height = height + 2 * self._padding
        else:
            needed_height = self.h1
        return needed_width, needed_height

    def get_text(self) -> str:
        return self._document.text if not self.placeholder else ""

    def layout(self):
        Viewer.layout(self)
        self._field.update(self.x, self.y, self.width, self.height)

        x, y, width, height = self._field.get_content_region()
        if self.is_focus():
            self._text_layout.begin_update()
            self._text_layout.x = self.x + self._padding
            self._text_layout.y = self.y - self._padding
            self._text_layout.end_update()
        else:
            # Adjust the text for font's descent
            descent = self._document.get_font().descent
            self._label.begin_update()
            self._label.x = self.x + self._padding
            self._label.y = self.y + self._padding - descent
            if self.multiline:
                self._label.y += self._caret_height - self._padding * 2 + descent
            self._label.width = width - self._padding * 2
            self._label.end_update()

    def on_gain_focus(self):
        if self.placeholder != "":
            self._document.text = ""
            self.placeholder = ""
        self.unload()
        self.focused = True
        FocusMixin.on_gain_focus(self)  # changes is_focus()
        self.load()

        self.reset_size()
        self.layout()

    def on_lose_focus(self):
        # send text to callback _on_input
        if self._on_input is not None:
            self._on_input(self.get_text())

        self.unload()
        self.focused = False
        FocusMixin.on_lose_focus(self)  # changes is_focus()
        self.load()

        self.reset_size()
        self.layout()

    def hit_test(self, x: int, y: int) -> bool:
        return self.is_inside(x, y)

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int) -> Any:
        if self.is_focus():
            return self._caret.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> Any:
        if self.is_focus():
            return self._caret.on_mouse_press(x, y, button, modifiers)

    def on_text(self, text: str) -> True:
        assert self.is_focus()
        self._caret.on_text(text)
        if self._max_length and len(self._document.text) > self._max_length:
            self._document.text = self._document.text[:self._max_length]
            self._caret.mark = self._caret.position = self._max_length
        return pyglet.event.EVENT_HANDLED

    def on_text_motion(self, motion: int) -> Any:
        assert self.is_focus()
        return self._caret.on_text_motion(motion)

    def on_text_motion_select(self, motion: int) -> Any:
        assert self.is_focus()
        return self._caret.on_text_motion_select(motion)

    def set_text(self, text: str):
        self._document.text = text
        if self.is_focus():
            self._caret.mark = self._caret.position = len(self._document.text)
        else:
            self._label.text = text

    def compute_size(self) -> tuple[int, int]:
        needed_width, needed_height = self._compute_needed_size()
        return self._field.get_needed_size(needed_width, needed_height)

    def delete(self):
        FocusMixin.delete(self)
        Viewer.delete(self)
