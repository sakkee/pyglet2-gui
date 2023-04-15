import pyglet
from typing import Any
from pyglet2_gui.scrollbars import VScrollbar
from pyglet2_gui.core import Viewer, Rectangle
from pyglet2_gui.theme.elements import TextureGraphicElement
from pyglet2_gui.controllers import Controller
from pyglet2_gui.manager import Manager


class Document(Controller, Viewer):
    """Allows you to embed a document within the GUI, which includes a
    vertical scrollbar.
    """
    _document: pyglet.text.document.AbstractDocument
    chat: bool
    max_height: int
    h1: int
    w1: int
    font_size: int
    font_name: str
    font_color: tuple[int, int, int, int] | None
    _bgcolor: bool
    _content: pyglet.text.layout.IncrementalTextLayout | None = None
    _bg: TextureGraphicElement = None
    _scrollbar: VScrollbar | None = None
    set_document_style: bool = False
    first_time_load: bool = True
    is_fixed_size: bool

    def __init__(self, document: pyglet.text.document.FormattedDocument | pyglet.text.document.AbstractDocument | str,
                 width: int = 0,
                 height: int = 0,
                 is_fixed_size: bool = False,
                 background: bool = False,
                 font_size: int = 13,
                 font_name: str = "Segoe UI",
                 font_color: tuple[int, int, int, int] | None = None,
                 chat: bool = False):
        Viewer.__init__(self, width=width, height=height)
        Controller.__init__(self)

        self.max_height = height
        self._document = pyglet.text.document.UnformattedDocument(document) if isinstance(document, str) else document
        self.h1 = height
        self.w1 = width
        self.chat = chat
        self.font_size = font_size
        self.font_name = font_name
        self.font_color = font_color
        self._bgcolor = background
        self.content_width = width
        self.is_fixed_size = is_fixed_size

    def hit_test(self, x: int, y: int) -> bool:
        if self._content is not None:
            return Rectangle(x=self._content.x,
                             y=self._content.y,
                             width=self._content.width,
                             height=self._content.height).is_inside(x, y)
        else:
            return False

    def _load_scrollbar(self, height: int):
        if self._content.content_height > height:
            if self._scrollbar is None:
                self._scrollbar = VScrollbar(self.max_height)
                self._scrollbar.set_manager(self.manager)
                self._scrollbar.parent = self
                self._scrollbar.load()
                self._scrollbar.set_knob_size(self.height, self._content.content_height)
        # if smaller, we unload it if it is loaded
        elif self._scrollbar is not None:
            self._scrollbar.unload()
            self._scrollbar = None

    def load_graphics(self):
        if self._bgcolor is True:
            self._bg = self.theme.get('document').get('image').generate(self.theme.get('document').get('gui_color'),
                                                                        **self.get_batch('background'))

        if not self.set_document_style and not self.chat:
            self.do_set_document_style(self.manager)
        self._content = pyglet.text.layout.IncrementalTextLayout(self._document,
                                                                 self.content_width, self.max_height,
                                                                 multiline=True, **self.get_batch('foreground'))

    def unload_graphics(self):
        if self._bg is not None:
            self._bg.unload()
        self._content.delete()
        if self._scrollbar is not None:
            self._scrollbar.unload()
            self._scrollbar = None

    def do_set_document_style(self, dialog: Manager):
        self.set_document_style = True
        # Check the style runs to make sure we don't stamp on anything
        # set by the user
        self._do_set_document_style('color', dialog.theme.get('font_color'))
        self._do_set_document_style('font_name', dialog.theme.get('font_name'))
        self._do_set_document_style('font_size', dialog.theme.get('font_size'))

    def _do_set_document_style(self, attr: str, value: Any):
        length = len(self._document.text)
        runs = [(start, end, doc_value) for start, end, doc_value in
                self._document.get_style_runs(attr).ranges(0, length)
                if doc_value is not None]
        if not runs:
            terminator = len(self._document.text)
        else:
            terminator = runs[0][0]
        self._document.set_style(0, terminator, {attr: value})

    def get_text(self) -> str:
        return self._document.text

    def layout(self):
        if self._bgcolor is True:
            self._bg.update(self.x, self.y, self.w1 + 2, self.h1)
        if self._scrollbar is not None:
            self._scrollbar.set_position(self.x + self._content.content_width + 2, self.y)
            pos = self._scrollbar.get_knob_pos()
            if pos != -self._content.view_y:
                self._content.view_y = -pos

        self._content.begin_update()
        self._content.x = self.x + 2
        self._content.y = self.y
        self._content.end_update()
        if self._scrollbar is not None:
            self._scrollbar.set_position(self.x + self.content_width + 2, self.y)

    def on_gain_highlight(self):
        if self._scrollbar is not None:
            self.manager.set_wheel_target(self._scrollbar)

    def on_lose_highlight(self):
        self.manager.set_wheel_target(None)

    def compute_size(self) -> tuple[int, int]:
        if self.is_fixed_size or (self.max_height and self._content.content_height > self.max_height):
            height = self.max_height
        else:
            height = self._content.content_height
        self._content.height = height
        self._load_scrollbar(height)
        if self._scrollbar is not None:
            self._scrollbar.set_knob_size(height, self._content.content_height)
            if self.first_time_load:
                self._scrollbar.set_knob_pos(0)
                self.first_time_load = False
            else:
                self._scrollbar.set_knob_pos(1)
            self._scrollbar.compute_size()

            width = self.content_width + self._scrollbar.width
        else:
            width = self.content_width
        return width, height

    def set_text(self, text: str):
        self._document.text = text
        self.compute_size()
        self.layout()

    def delete(self):
        Controller.delete(self)
        Viewer.delete(self)
