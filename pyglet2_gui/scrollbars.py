from pyglet2_gui.sliders import Slider


class ScrollBar(Slider):
    """An abstract scrollbar with a specific knob size to be set.
    """
    _knob_size: float = 0.0  # the size of the knob. Value runs from [_knob_size/2, 1 - _knob_size/2]
    _scrolled: int = 0  # a cumulative value of scroll to avoid re-layout on every scroll event

    def set_size(self, width: int, height: int):
        self.width = width
        self.height = height

    def re_layout(self):
        self.layout()
        # when we do layout, we ask the parent also re_layout since
        # a scrollbar defines the content region.
        if self._scrolled > 4:
            try:
                self.parent.layout(load_wrapper=False)
            except:
                self.parent.layout()
            self._scrolled = 0

    def _get_bar_region(self) -> tuple[int, int, int, int]:
        """Returns the area of the space where the knob moves (x, y, width, height)
        """
        return self.x, self.y, self.width, self.height

    def _get_knob_region(self):
        """Returns the area of the knob (x, y, width, height). To be subclassed.
        """
        raise NotImplementedError

    def get_knob_pos(self) -> float:
        """Returns the position of the relative position of the knob
        in the bar.
        """
        raise NotImplementedError

    def set_knob_pos(self, pos: float):
        pos = max(min(pos, 1 - self._knob_size / 2), self._knob_size / 2)
        self.value = self.min_value + (self.max_value - self.min_value) * pos

    def layout(self):
        self._knob.update(*self._get_knob_region())
        self._bar.update(*self._get_bar_region())

    def on_gain_focus(self):
        if self.manager is not None:
            self.manager.set_wheel_target(self)

    def on_lose_focus(self):
        self._scrolled = 0
        if self.manager is not None:
            self.manager.set_wheel_target(None)


class HScrollbar(ScrollBar):
    PATH: str = 'hscrollbar'

    def __init__(self, width: int):
        super().__init__(width=width, height=0)

    def _get_knob_region(self) -> tuple[int, int, int, int]:
        return int(self.x + (self._knob_pos() - self._knob_size / 2) * self.width), \
            self.y, int(self._knob_size * self.width), self.height

    def get_knob_pos(self) -> int:
        return int((self._knob_pos() - self._knob_size / 2) * self.width / self._knob_size)

    def load_graphics(self):
        super().load_graphics()
        self.height = self._bar.height

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, buttons: int, modifiers: int) -> True:
        bar_x, _, bar_width, _ = self._bar.get_content_region()

        absolute_distance = float(x - bar_x)
        relative_distance = absolute_distance / bar_width

        self.set_knob_pos(relative_distance)
        self._scrolled = 10
        self.re_layout()
        return True

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> True:
        self._scrolled += abs(scroll_x)
        self.set_knob_pos(self._knob_pos() - float(scroll_x) / self.width)
        self.re_layout()
        return True

    def set_knob_size(self, width: int, max_width: int):
        self._knob_size = min(float(width) / max_width, 1.0)

        # update the knob position given the new knob size.
        self.set_knob_pos(self._knob_pos())

    def compute_size(self) -> tuple[int, int]:
        return self.width, self._bar.height


class VScrollbar(ScrollBar):
    PATH: str = 'vscrollbar'
    _last: int = 0
    _content_length: int | None  # the number of contents

    def __init__(self, height: int, content_length: int = None):
        super().__init__(width=0, height=height)
        self._content_length = content_length

    def _get_knob_region(self) -> tuple[int, int, int, int]:
        top = self.y + self.height
        return (self.x, int(top - (self._knob_pos() + self._knob_size / 2) * self.height),
                self.width, int(self._knob_size * self.height))

    def get_knob_pos(self) -> int:
        # we remove half the knob size to pick the center of the knob.
        # height/_knob_size = max_height by "set_knob_size()".
        return int((self._knob_pos() - self._knob_size / 2) * self.height / self._knob_size)

    def load_graphics(self):
        super().load_graphics()
        self.width = self._bar.width

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, button: int, modifiers: int) -> True:
        bar_x, bar_y, bar_width, bar_height = self._bar.get_content_region()
        absolute_distance = float(y - bar_y)
        relative_distance = absolute_distance / bar_height
        # print relative_distance
        if self._content_length is not None:
            if int(absolute_distance // self._content_length) != self._last:
                self.set_knob_pos(1 - relative_distance)
                self._scrolled += abs(dy)
                self.re_layout()
                self._last = int(absolute_distance // self._content_length)
        else:
            self.set_knob_pos(1 - relative_distance)
            self._scrolled += abs(dy)
            self.re_layout()
        return True

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> True:
        scroll_y = -scroll_y * 15
        self._scrolled += abs(scroll_y)
        self.set_knob_pos(self._knob_pos() + float(scroll_y) / self.height)
        self.re_layout()
        return True

    def set_knob_size(self, height: int, max_height: int):
        self._knob_size = float(height) / max_height
        # update the knob position given the new knob size.
        self.set_knob_pos(self._knob_pos())

    def compute_size(self) -> tuple[int, int]:
        return self._bar.width, self.height
