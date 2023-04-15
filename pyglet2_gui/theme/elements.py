from abc import abstractmethod
import pyglet
from pyglet import gl
from ..core import Rectangle


class ThemeTextureGroup(pyglet.graphics.Group):
    """ThemeTextureGroup, in addition to setting the texture, also ensures that
    we map to the nearest texel instead of trying to interpolate from nearby
    texels. This prevents 'blooming' along the edges.
    """
    texture: pyglet.image.Texture
    program: pyglet.graphics.shader.ShaderProgram

    def __init__(self, texture: pyglet.image.Texture, order: int = 0, parent: pyglet.graphics.Group = None):
        """Create a ThemeTextureGroup.

        :Parameters:
            'texture' : '~pyglet.image.Texture'
                Texture to display
            'order' : int
                order of the group
            'parent' : '~pyglet.graphics.Group'
                parent group of this group
        """
        super().__init__(order=order, parent=parent)
        self.texture = texture
        self.program = pyglet.sprite.get_default_shader()

    def set_state(self):
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(self.texture.target, self.texture.id)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        self.program.use()

    def unset_state(self):
        gl.glDisable(gl.GL_BLEND)

    def __hash__(self):
        return hash((self.texture.target, self.texture.id, self.order, self.parent, self.program))

    def __eq__(self, other):
        return (self.__class__ is other.__class__ and
                self.texture.target == other.texture.target and
                self.texture.id == other.texture.id and
                self.order == other.order and
                self.program == other.program and
                self.parent == other.parent)


class GraphicElement(Rectangle):
    _color: tuple[int, int, int, int]
    _batch: pyglet.graphics.Batch
    _group: pyglet.graphics.Group | None
    _vertex_list: pyglet.graphics.vertexarray.VertexArray | pyglet.graphics.vertexdomain.IndexedVertexList | None = None

    def __init__(self, color: tuple[int, int, int, int], batch: pyglet.graphics.Batch, group: pyglet.graphics.Group,
                 width: int = 0, height: int = 0):
        """Create a GraphicElement.

        :Parameters:
            'color' : tuple[int, int, int, int]
                RGBA value
            'batch' : '~pyglet.graphics.Batch'
                the batch where the element is drawn
            'group' : '~pyglet.graphics.Group'
                the group of the element
            'width' : int
                width of the element
            'height' : int
                height of the element
        """
        super().__init__(width=width, height=height)
        self._color = color
        self._batch = batch
        self._group = group
        self._load()

    @abstractmethod
    def _load(self):
        assert self._vertex_list is None
        self._vertex_list = pyglet.sprite.get_default_shader().vertex_list(
            12, gl.GL_LINES, self._batch, self._group,
            position=('f', self._get_vertices()),
            colors=('Bn', self._color * 12),
            scale=('f', (1.0, 1.0) * 12)
        )

    @abstractmethod
    def _get_vertices(self, add_z: bool = False) -> tuple:
        x1, y1 = int(self.x), int(self.y)
        x2, y2 = x1 + int(self.width), y1 + int(self.height)
        if not add_z:
            return (x1, y1, x2, y1, x2, y1, x2, y2,
                    x2, y2, x1, y2, x1, y2, x1, y1,
                    x1, y1, x2, y2, x1, y2, x2, y1)
        if add_z:
            return (x1, y1, 0, x2, y1, 0, x2, y1, 0, x2, y2, 0,
                    x2, y2, 0, x1, y2, 0, x1, y2, 0, x1, y1, 0,
                    x1, y1, 0, x2, y2, 0, x1, y2, 0, x2, y1, 0)

    def unload(self):
        self._vertex_list.delete()
        self._vertex_list = None
        self._group = None

    def get_content_region(self) -> tuple[int, int, int, int]:
        return self.x, self.y, self.width, self.height

    def get_content_size(self, width, height) -> tuple[int, int]:
        return width, height

    def get_needed_size(self, content_width, content_height) -> tuple[int, int]:
        return content_width, content_height

    def update(self, x, y, width, height):
        self.set_position(x, y)
        self.width, self.height = width, height

        if self._vertex_list is not None:
            self._vertex_list.position[:] = self._get_vertices(True)


class TextureGraphicElement(GraphicElement):
    texture: pyglet.image.Texture

    def __init__(self, texture: pyglet.image.Texture, color: tuple[int, int, int, int],
                 batch: pyglet.graphics.Batch, group: pyglet.graphics.Group):
        """Create a TextureGraphicElement.

        :Parameters:
            'texture' : '~pyglet.image.Texture'
                texture of the image
            'color' : tuple[int, int, int, int]
                RGBA value
            'batch' : '~pyglet.graphics.Batch'
                the batch where the element is drawn
            'group' : '~pyglet.graphics.Group'
                the group of the element
            'width' : int
                width of the element
            'height' : int
                height of the element
        """
        self.texture = texture

        super().__init__(color,
                         batch,
                         ThemeTextureGroup(texture, group.order, group),
                         texture.width, texture.height)

    def _load(self):
        assert self._vertex_list is None
        self._vertex_list = pyglet.sprite.get_default_shader().vertex_list_indexed(
            4, gl.GL_TRIANGLES, (0, 1, 2, 0, 2, 3), self._batch, self._group,
            position=('f', self._get_vertices()),
            colors=('Bn', self._color * 4),
            tex_coords=('f', self.texture.tex_coords),
            scale=('f', (1.0, 1.0) * 4)
        )

    def _get_vertices(self, add_z=False) -> tuple:
        x1, y1 = int(self.x), int(self.y)
        x2, y2 = x1 + int(self.width), y1 + int(self.height)
        if not add_z:
            return x1, y1, x2, y1, x2, y2, x1, y2
        else:
            return x1, y1, 0, x2, y1, 0, x2, y2, 0, x1, y2, 0


class FrameTextureGraphicElement(GraphicElement):
    """FrameTextureGraphicElement is used to split the image in 9 regions, giving the image frame that isn't
    resized.

    """
    outer_texture: pyglet.image.Texture
    inner_texture: pyglet.image.TextureRegion
    margins: tuple[int, int, int, int]
    padding: list[int, int, int, int]

    def __init__(self, outer_texture: pyglet.image.Texture, inner_texture: pyglet.image.TextureRegion,
                 margins: list[int, int, int, int], padding: list[int, int, int, int],
                 color: tuple[int, int, int, int], batch: pyglet.graphics.Batch, group: pyglet.graphics.Group):
        """Create a FrameTextureGraphicElement.

        :Parameters:
            'outer_texture' : '~pyglet.image.Texture'
                the frame outline texture
            'inner_texture' : '~pyglet.image.TextureRegion'
                the inner texture
            'margins' : list[int, int, int, int]
                top, right, bottom, left margin of the image.
            'padding' : list[int, int, int, int]
                top, right, bottom, left padding of the element
            'color' : tuple[int, int, int, int]
                RGBA value
            'batch' : '~pyglet.graphics.Batch'
                the batch where the element is drawn
            'group' : '~pyglet.graphics.Group'
                the group of the element
            'width' : int
                width of the element
            'height' : int
                height of the element
        """
        self.outer_texture = outer_texture
        self.inner_texture = inner_texture
        self.margins = margins
        self.padding = padding

        super().__init__(color,
                         batch,
                         ThemeTextureGroup(outer_texture, group.order, group),
                         outer_texture.width,
                         outer_texture.height)

    def _load(self):
        assert self._vertex_list is None
        self._vertex_list = pyglet.sprite.get_default_shader().vertex_list_indexed(
            16, gl.GL_TRIANGLES, self._get_vertice_indexes(), self._batch, self._group,
            position=('f', self._get_vertices()),
            colors=('Bn', self._color * 16),
            tex_coords=('f', self._get_tex_coords()),
            scale=('f', (1.0, 1.0) * 16)
        )

    @staticmethod
    def _get_vertice_indexes() -> tuple:
        return (0, 1, 2, 2, 1, 3,  # bottom right
                1, 4, 3, 3, 4, 6,  # bottom
                4, 5, 6, 6, 5, 7,  # bottom right
                2, 3, 8, 8, 3, 9,  # left
                3, 6, 9, 9, 6, 12,  # center
                6, 7, 12, 12, 7, 13,  # right
                8, 9, 10, 10, 9, 11,  # top left
                9, 12, 11, 11, 12, 14,  # top
                12, 13, 14, 14, 13, 15  # top-right
                )

    def _get_tex_coords(self) -> tuple:
        x1, y1 = self.outer_texture.tex_coords[0:2]  # outer's lower left
        x4, y4 = self.outer_texture.tex_coords[6:8]  # outer's upper right
        x2, y2 = self.inner_texture.tex_coords[0:2]  # inner's lower left
        x3, y3 = self.inner_texture.tex_coords[6:8]  # inner's upper right
        return (x1, y1, 0, x2, y1, 0, x1, y2, 0, x2, y2, 0,  # bottom left
                x3, y1, 0, x4, y1, 0, x3, y2, 0, x4, y2, 0,  # bottom right
                x1, y3, 0, x2, y3, 0, x1, y4, 0, x2, y4, 0,  # top left
                x3, y3, 0, x4, y3, 0, x3, y4, 0, x4, y4, 0)  # top right

    def _get_vertices(self, add_z=False) -> tuple:
        top, right, bottom, left = self.margins  # left, right, top, bottom = self.margins
        x1, y1 = int(self.x), int(self.y)
        x2, y2 = x1 + left, y1 + bottom
        x3 = x1 + int(self.width) - right
        y3 = y1 + int(self.height) - top
        x4, y4 = x1 + int(self.width), y1 + int(self.height)
        if not add_z:
            return (x1, y1, x2, y1, x1, y2, x2, y2,  # bottom left
                    x3, y1, x4, y1, x3, y2, x4, y2,  # bottom right
                    x1, y3, x2, y3, x1, y4, x2, y4,  # top left
                    x3, y3, x4, y3, x3, y4, x4, y4)  # top right
        else:
            return (x1, y1, 0, x2, y1, 0, x1, y2, 0, x2, y2, 0,  # bottom left
                    x3, y1, 0, x4, y1, 0, x3, y2, 0, x4, y2, 0,  # bottom right
                    x1, y3, 0, x2, y3, 0, x1, y4, 0, x2, y4, 0,  # top left
                    x3, y3, 0, x4, y3, 0, x3, y4, 0, x4, y4, 0)  # top right

    def get_content_region(self) -> tuple[int, int, int, int]:
        top, right, bottom, left = self.padding  # left, right, bottom, top = self.padding
        return (self.x + left, self.y + bottom,
                self.width - left - right, self.height - top - bottom)

    def get_content_size(self, width: int, height: int) -> tuple[int, int]:
        top, right, bottom, left = self.padding
        return width - left - right, height - top - bottom

    def get_needed_size(self, content_width: int, content_height: int) -> tuple[int, int]:
        top, right, bottom, left = self.padding
        return (max(content_width + left + right, self.outer_texture.width),
                max(content_height + top + bottom, self.outer_texture.height))
