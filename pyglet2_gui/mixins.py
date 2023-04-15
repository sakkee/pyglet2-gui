from pyglet2_gui.core import Controller
from pyglet2_gui.core import Viewer
from pyglet2_gui.theme.elements import FrameTextureGraphicElement


class HighlightMixin(Controller, Viewer):
    _highlight: FrameTextureGraphicElement | None = None
    _highlight_outline: FrameTextureGraphicElement | None = None
    _highlight_flag: bool = False
    outline_path: str = None

    def __init__(self, outline_path: str = None):
        self.outline_path = outline_path
        Controller.__init__(self)
        Viewer.__init__(self)

    def on_gain_highlight(self):
        self._highlight_flag = True
        HighlightMixin.load_graphics(self)
        HighlightMixin.layout(self)

    def on_lose_highlight(self):
        self._highlight_flag = False
        HighlightMixin.unload_graphics(self)

    def is_highlighted(self) -> bool:
        return self._highlight_flag

    def load_graphics(self):
        theme = self.theme.get(self.get_path())
        if self._highlight is None and self._highlight_flag:
            if self.outline_path:
                hlight_theme = self.theme.get([self.outline_path, 'highlight'])
                if hlight_theme:
                    self._highlight_outline = hlight_theme.get('image').generate(
                        hlight_theme.get('highlight_color', (255, 255, 255, 128)), **self.get_batch('highlight'))
            else:
                self._highlight = theme.get('highlight').get('image').generate(
                    theme.get('highlight_color', (255, 255, 255, 255)), **self.get_batch('highlight'))

    def unload_graphics(self):
        if self._highlight is not None:
            self._highlight.unload()
            self._highlight = None
        if self._highlight_outline is not None:
            self._highlight_outline.unload()
            self._highlight_outline = None

    def layout(self):
        if self._highlight is not None:
            self._highlight.update(self.x, self.y, self.width, self.height)
        if self._highlight_outline is not None:
            self._highlight_outline.update(self.x, self.y, self.width, self.height)

    def delete(self):
        HighlightMixin.unload_graphics(self)


class FocusMixin(Controller, Viewer):
    _focus: FrameTextureGraphicElement | None = None
    _focus_flag: bool = False

    def on_gain_focus(self) -> True:
        self._focus_flag = True
        FocusMixin.load_graphics(self)
        FocusMixin.layout(self)
        return True

    def on_lose_focus(self) -> True:
        self._focus_flag = False
        FocusMixin.unload_graphics(self)
        return True

    def is_focus(self) -> bool:
        return self._focus_flag

    def load_graphics(self):
        theme = self.theme[self.get_path()]
        self._focus = theme.get('highlight').get('image').generate(theme.get('highlight_color'),
                                                                   **self.get_batch('highlight'))

    def unload_graphics(self):
        self._focus.unload()
        self._focus = None

    def layout(self):
        if self._focus is not None:
            self._focus.update(self.x, self.y, self.width, self.height)

    def delete(self):
        if self._focus is not None:
            FocusMixin.unload_graphics(self)
