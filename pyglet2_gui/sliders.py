from pyglet2_gui.controllers import ContinuousStateController
from pyglet2_gui.core import Viewer
from pyglet2_gui.theme.elements import FrameTextureGraphicElement
from collections.abc import Callable
from typing import Any


class Slider(ContinuousStateController, Viewer):
    PATH: str = 'slider'
    IMAGE_BAR: str = 'bar'
    IMAGE_KNOB: str = 'knob'
    IMAGE_STEP: str = 'step'
    _bar: FrameTextureGraphicElement | None = None  # a bar where the knob slides.
    _knob: FrameTextureGraphicElement | None = None  # the knob that moves along the bar.
    _offset: tuple[int, int]  # offset of the knob image to its central position
    _padding: tuple[int, int, int, int]  # padding of the bar image to its central position
    _markers: list[FrameTextureGraphicElement]
    _step_offset: tuple[int, int]  # markers in case of discrete steps.
    steps: int

    def __init__(self, value: float = 0.0,
                 min_value: float = 0.0,
                 max_value: float = 1.0,
                 on_set: Callable[[Any], Any] | None = None,
                 steps: int = None,
                 width: int = 0,
                 height: int = 0):
        ContinuousStateController.__init__(self,
                                           value=value,
                                           min_value=min_value,
                                           max_value=max_value,
                                           on_set=on_set
                                           )
        Viewer.__init__(self, width=width, height=height)
        self._offset = (0, 0)  # offset of the knob image to its central position
        self._padding = (0, 0, 0, 0)  # padding of the bar image to its central position

        self.steps = steps
        self._markers = []  # markers in case of discrete steps.
        self._step_offset = (0, 0)

    def get_path(self) -> str:
        return self.PATH

    def load_graphics(self):
        theme = self.theme.get(self.get_path())
        color = theme.get('gui_color', (255, 255, 255, 255))

        self._bar = theme.get(self.IMAGE_BAR).get('image').generate(color, **self.get_batch('background'))
        self._padding = theme.get(self.IMAGE_BAR).get('padding', (0, 0, 0, 0))

        self._knob = theme.get(self.IMAGE_KNOB).get('image').generate(color, **self.get_batch('foreground'))
        self._offset = theme.get(self.IMAGE_KNOB).get('offset', (0, 0))

        if self.steps is not None:
            image_path = self.IMAGE_STEP
            for n in range(0, self.steps + 1):
                self._markers.append(theme.get(image_path).get('image').generate(
                    theme.get(image_path).get('gui_color', (255, 255, 255, 255)), **self.get_batch('highlight')))
            self._step_offset = theme.get(image_path).get('offset', (0, 0))

    def unload_graphics(self):
        self._knob.unload()
        self._bar.unload()
        for marker in self._markers:
            marker.unload()
        self._markers.clear()

    def hit_test(self, x: int, y: int) -> bool:
        return self.is_inside(x, y)

    def set_knob_pos(self, pos: float):
        """A setter for value, but using normalized values.
        """
        pos = max(min(pos, 1.0), 0.0)

        self.set_value(self.min_value + (self.max_value - self.min_value) * pos)
        if self._bar is not None and self._knob is not None:
            x, y, width, height = self._bar.get_content_region()
            offset_x, offset_y = self._offset
            self._knob.update(x + int(width * pos) + offset_x,
                              y + offset_y,
                              self._knob.width, self._knob.height)

    def _knob_pos(self) -> float:
        """The position of the knob in the bar computed by our value.
        """
        return max(min(float(self.value - self.min_value) / (self.max_value - self.min_value), 1.0), 0.0)

    def _snap_to_nearest(self):
        """Snaps the knob and value to a discrete value dictated by steps.
        """
        assert self.steps is not None
        pos = float(int(self._knob_pos() * self.steps + 0.5)) / self.steps

        self.set_knob_pos(pos)

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int) -> Any:
        raise NotImplementedError

    def on_mouse_press(self, x: int, y: int, button: int, modifiers: int) -> Any:
        return self.on_mouse_drag(x, y, 0, 0, button, modifiers)

    def on_mouse_release(self, x: int, y: int, button: int, modifiers: int):
        if self.steps is not None:
            self._snap_to_nearest()

    def delete(self):
        ContinuousStateController.delete(self)
        Viewer.delete(self)


class HorizontalSlider(Slider):
    min_width: int

    def __init__(self, width: int = 100, **kwargs):
        super().__init__(**kwargs)
        self.min_width = width

    def layout(self):
        left, right, top, bottom = self._padding
        self._bar.update(self.x + left, self.y + bottom,
                         self.width - left - right,
                         self.height - top - bottom)

        x, y, width, height = self._bar.get_content_region()

        # knob is positioned with an (x,y) offset
        # since its graphics are on its bottom-left corner.
        offset_x, offset_y = self._offset
        self._knob.update(x + int(width * self._knob_pos()) + offset_x,
                          y + offset_y,
                          self._knob.width, self._knob.height)

        if self.steps is not None:
            step = float(width) / self.steps
            offset_x, offset_y = self._step_offset
            for n in range(0, self.steps + 1):
                self._markers[n].update(int(x + step * n) + offset_x,
                                        y + offset_y,
                                        self._markers[n].width,
                                        self._markers[n].height)

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int) -> True:
        bar_x, bar_y, bar_width, bar_height = self._bar.get_content_region()
        self.set_knob_pos(float(x - bar_x) / bar_width)
        return True

    def compute_size(self) -> tuple[int, int]:
        width, height = self._bar.get_needed_size(self.min_width, 0)
        left, right, top, bottom = self._padding

        return width + left + right, height + top + bottom
