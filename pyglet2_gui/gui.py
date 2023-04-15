import pyglet.text
from pyglet2_gui.constants import VALIGN_BOTTOM, ANCHOR_CENTER, get_relative_point
from pyglet2_gui.core import Rectangle, Viewer
from pyglet2_gui.containers import HorizontalContainer, VerticalContainer, Wrapper
from pyglet2_gui.theme.elements import TextureGraphicElement
from pyglet2_gui.theme.theme import Theme
from pyglet2_gui.theme.templates import TextureTemplate, FrameTextureGraphicElement
from pyglet2_gui.override import Label as LabelOverride


class Graphic(Viewer):
    _path: str | list[str] | tuple[str]
    _expandable: bool
    _graphic: TextureGraphicElement | None = None
    _outline_graphic: TextureGraphicElement | None = None
    texture_tmp: pyglet.image.Texture | None
    _alt_theme: Theme | None
    _outline_path: str | list[str] | tuple[str] | None
    _min_width: int = 0
    _min_height: int = 0
    w1: int
    h1: int
    bg_width: int

    def __init__(self,
                 path: str | list[str] | tuple[str] | None = None,
                 is_expandable: bool = False,
                 alternative_theme: Theme | None = None,
                 outline_path: str | list[str] | tuple[str] | None = None,
                 width: int = None,
                 height: int = None,
                 bg_width: int = None,
                 texture=None):
        super().__init__()
        self._path = path
        self._expandable = is_expandable
        self.texture_tmp = texture
        self._alt_theme = alternative_theme
        self._outline_path = outline_path
        self.w1 = width
        self.h1 = height
        self.bg_width = bg_width

    def get_path(self) -> str | list[str] | tuple[str]:
        return self._path

    def change_path(self, path: str | list[str] | tuple[str]):
        self._path = path

    def load_graphics(self):
        if self._alt_theme is not None:
            theme = self._alt_theme.get(self.get_path())
            self._graphic = theme.get('image').generate(
                theme.get(self._path).get('gui_color'),
                **self.get_batch('background')
            )
        elif self.texture_tmp is not None:
            self._graphic = TextureTemplate(self.texture_tmp).generate((255, 255, 255, 255),
                                                                       **self.get_batch('background'))
        else:
            theme = self.theme.get(self.get_path())
            self._graphic = theme.get('image').generate(
                theme.get(self._path).get('gui_color'),
                **self.get_batch('background')
            )
        if self._outline_path is not None:
            outline = self.theme.get(self._outline_path, None)

            if outline is not None:
                print(outline, self._outline_path)
                self._outline_graphic = outline.get('image').generate(
                    (255, 255, 255, 255),
                    **self.get_batch('foreground')
                )
        self._min_width = self._graphic.width
        self._min_height = self._graphic.height

    def unload_graphics(self):
        if self._outline_graphic is not None:
            self._outline_graphic.unload()
        self._graphic.unload()

    def expand(self, width: int, height: int):
        assert self.is_expandable()
        self.width, self.height = width, height
        self._graphic.update(self.x, self.y, self.width, self.height)
        if self._outline_graphic is not None:
            self._outline_graphic.update(self.x, self.y, self.width, self.height)

    def is_expandable(self) -> bool:
        return self._expandable

    def layout(self):
        if self.bg_width is not None:
            self._graphic.update(self.x, self.y, int(self.width * self.bg_width / 100), self.height)
        else:
            self._graphic.update(self.x, self.y, self.width, self.height)

        if self._outline_graphic is not None:
            self._outline_graphic.update(self.x, self.y, self.width, self.height)

    def compute_size(self) -> tuple[int, int]:
        if self.w1 is not None and self.h1 is not None:
            return self.w1, self.h1
        else:
            return self._min_width, self._min_height


class Label(Viewer):
    text: str
    bold: bool
    italic: bool
    font_name: str | None
    font_size: int | None
    color: tuple[int, int, int, int]
    alpha: int  # overrides color alpha channel if necessary
    _opacity: float
    path: str | list[str] | tuple[str]
    label: LabelOverride | None = None
    multiline: bool
    w: int
    updated: bool = False

    def __init__(self, text: str = "", bold: bool = False, italic: bool = False,
                 font_name: str = None, font_size: int = None, color: tuple[int, int, int, int] = None,
                 path: str | list[str] | tuple[str] | None = None, width: int = None, multiline: bool = False,
                 opacity: float = 1.0):
        super().__init__()
        self.text = text
        self.bold = bold
        self.italic = italic
        self.font_name = font_name
        self.font_size = font_size
        self.color = color
        self.opacity = opacity
        self.path = path
        self.multiline = multiline
        self.w = width

    @property
    def opacity(self) -> float:
        return self._opacity

    @opacity.setter
    def opacity(self, value: float = 1.0):
        value = 0.0 if value < 0.0 else value
        value = 1.0 if value > 1.0 else value
        self.alpha = int(round(value * 255))
        self._opacity = value

    def get_path(self) -> str:
        return self.path

    def load_graphics(self):
        theme = self.theme.get(self.get_path())
        color = self.color or theme.get('font_color')
        if self.alpha != 255:
            color = color[:3] + (self.alpha,)
        self.font_size = self.font_size or theme.get('font_size')

        self.label = LabelOverride(self.text,
                                   bold=self.bold,
                                   multiline=self.multiline,
                                   italic=self.italic,
                                   width=self.w,
                                   anchor_y='bottom',
                                   color=color,
                                   font_name=self.font_name or theme.get('font_name'),
                                   font_size=self.font_size,
                                   **self.get_batch('background'))

    def unload_graphics(self):
        self.label.delete()

    def layout(self):
        self.label.pos(self.x, self.y)

    def set_text(self, text: str):
        self.text = text
        self.refresh()

    def compute_size(self) -> tuple[int, int]:
        return self.label.content_width, self.label.content_height


class Frame(Wrapper):
    """A Viewer that wraps another widget with a frame.
    """
    _frame: FrameTextureGraphicElement | None = None
    _image_name: str  # image name in the theme
    _path: list[str]  # path in the theme

    def __init__(self, content: Viewer, path: str | list[str] | tuple[str] | None = None, image_name: str = 'image',
                 is_expandable: bool = False, anchor: tuple[int, int] = ANCHOR_CENTER):

        super().__init__(content=content, is_expandable=is_expandable, anchor=anchor)
        self._path = [path] if path is not None else ['frame']
        self._image_name = image_name

    def get_path(self) -> list[str]:
        return self._path

    def load_graphics(self):
        super().load_graphics()
        theme = self.theme.get(self.get_path())
        if self._frame is None:
            template = theme.get(self._image_name)
            self._frame = template.generate(theme.get('gui_color'), **self.get_batch('panel'))

    def unload_graphics(self):
        if self._frame is not None:
            self._frame.unload()
            self._frame = None
        super().unload_graphics()

    def expand(self, width: int, height: int):
        height_change = height - self.content.height
        if self.content.is_expandable():
            content_width, content_height = self._frame.get_content_size(width, height)
            self.content.expand(content_width, content_height)
        self.width = width
        self.height += height_change

    def layout(self):
        self._frame.update(self.x, self.y, self.width, self.height)

        # we create a rectangle with the interior for using in get_relative_point
        x, y, width, height = self._frame.get_content_region()
        interior = Rectangle(x=x, y=y, width=width, height=height)
        x, y = get_relative_point(interior, self.anchor, self.content, self.anchor, self.content_offset)
        self.content.set_position(x, y)

    def compute_size(self) -> tuple[int, int]:
        self.content.compute_size()
        return self._frame.get_needed_size(self.content.width, self.content.height)


class TitleFrame(VerticalContainer):
    def __init__(self, title: str, content: Viewer):
        super().__init__(content=[
            HorizontalContainer([Graphic(path=["titlebar", "left"], is_expandable=True),
                                 Frame(Label(text=title, path=["titlebar"]),
                                       path=["titlebar", "center"]),
                                 Graphic(path=["titlebar", "right"], is_expandable=True),
                                 ], align=VALIGN_BOTTOM, padding=0),
            Frame(content=content, path=["titlebar", "frame"], is_expandable=True),
        ], padding=0)
