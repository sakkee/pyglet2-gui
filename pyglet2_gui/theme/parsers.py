from abc import abstractmethod
import pyglet.resource
from .templates import TextureTemplate, FrameTextureTemplate


class Parser:
    @abstractmethod
    def condition_fulfilled(self, key):
        return False

    @abstractmethod
    def parse_element(self, element):
        pass


class TextureParser(Parser):
    """Texture Parser.

    Parses texture and returns a 'TextureTemplate' or 'FrameTextureTemplate'
    """
    _textures: dict
    _loader: pyglet.resource.Loader

    def __init__(self, resources_path: str):
        """Creates a TextureParser

        :Parameters:
            'resources_path' : str
                the directory path to the resource of the textures
        """
        pyglet.resource.path.append(resources_path)
        self._textures = {}
        self._loader = pyglet.resource.Loader(resources_path)

    def condition_fulfilled(self, key: str) -> bool:
        return key.startswith('image')

    def _get_texture(self, filename: str) -> pyglet.image.Texture:
        """Returns the texture associated with the filename. Loads it from
        resources if it hasn't done before.
        """
        if filename not in self._textures:
            texture = self._loader.texture(filename)
            self._textures[filename] = texture
        return self._textures[filename]

    def _get_texture_region(self, filename: str, x: int, y: int, width: int, height: int) -> pyglet.image.TextureRegion:
        """Same as _get_texture, but limits the texture for a region
        x, y, width, height.
        """
        texture = self._get_texture(filename)
        retval = texture.get_region(x, y, width, height).get_texture()
        return retval

    def parse_element(self, element: dict | str) -> TextureTemplate | FrameTextureTemplate:
        if isinstance(element, dict):
            # if it has a region, we create a texture from that region.
            # else, we use a full texture.
            texture = self._get_texture_region(element.get('source'), *element.get('region')) if 'region' in element \
                else self._get_texture(element.get('source'))

            # if it has frame, it is a FrameTexture
            # else, it is a simple texture.
            return FrameTextureTemplate(
                texture,
                element.get('frame'),
                element.get('padding', [0, 0, 0, 0])  # if padding, else 0.
            ) if 'frame' in element else TextureTemplate(texture)

        # if it is of the form {'image': 'test.png'}
        else:
            texture = self._get_texture(element)
            return TextureTemplate(texture)
