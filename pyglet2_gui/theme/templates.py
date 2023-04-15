import pyglet

from abc import abstractmethod
from typing import Any
from .elements import GraphicElement, TextureGraphicElement, FrameTextureGraphicElement


class Template:
    @abstractmethod
    def generate(self, color: tuple[int, int, int, int], batch: pyglet.graphics.Batch, group: pyglet.graphics.Group) \
            -> GraphicElement:
        return GraphicElement(color, batch, group)


class TextureTemplate(Template):
    texture: pyglet.image.Texture
    width: int
    height: int

    def __init__(self, texture: pyglet.image.Texture, width: int = None, height: int = None):
        """Creates a TextureTemplate

        :Parameters:
            'texture' : '~pyglet.image.Texture'
                the texture
            'width' : int
                width of the element
            'height' : int
                height of the element
        """
        super().__init__()
        self.texture = texture
        self.width = width or texture.width
        self.height = height or texture.height

    def generate(self, color: tuple[int, int, int, int], batch: pyglet.graphics.Batch, group: pyglet.graphics.Group) \
            -> TextureGraphicElement:
        return TextureGraphicElement(self.texture, color, batch, group)


class FrameTextureTemplate(TextureTemplate):
    _margins: list[int, int, int, int]  # left, bottom, right, top
    _padding: list[int, int, int, int]
    _inner_texture = pyglet.image.TextureRegion

    def __init__(self, texture: pyglet.image.Texture, frame: list[int, int, int, int], padding: list[int, int, int, int],
                 width: int = None, height: int = None):
        super().__init__(texture, width=width, height=height)
        self._margins = frame  # top, right, bottom, left
        region_frame = (self._margins[3], self._margins[2],  # x, y
                        texture.width - self._margins[3] - self._margins[1],
                        texture.height - self._margins[2] - self._margins[0])  # width, height
        self._padding = padding
        self._inner_texture = texture.get_region(*region_frame).get_texture()

    def generate(self, color: tuple[int, int, int, int], batch: pyglet.graphics.Batch, group: pyglet.graphics.Group) \
            -> FrameTextureGraphicElement:
        return FrameTextureGraphicElement(
            self.texture, self._inner_texture,
            self._margins, self._padding, color, batch, group)
