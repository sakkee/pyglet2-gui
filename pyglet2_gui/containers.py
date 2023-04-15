from __future__ import annotations
from functools import reduce
from pyglet2_gui.constants import HALIGN_CENTER, HALIGN_LEFT, HALIGN_RIGHT, \
    VALIGN_TOP, VALIGN_CENTER, ANCHOR_CENTER, get_relative_point
from pyglet2_gui.core import Viewer, Rectangle
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .manager import Manager


class Spacer(Viewer):
    _min_width: int
    _min_height: int

    def __init__(self, min_width: int = 0, min_height: int = 0):
        super().__init__()
        self._min_width = min_width
        self._min_height = min_height

    def expand(self, width: int, height: int):
        self.width, self.height = width, height

    def is_expandable(self) -> True:
        return True

    def compute_size(self) -> tuple[int, int]:
        return self._min_width, self._min_height


class Container(Viewer):
    _content: list

    def __init__(self, content: list, **kwargs):
        assert isinstance(content, list)
        super().__init__(**kwargs)
        self._content = [x or Spacer() for x in content]

    @property
    def content(self) -> list:
        return self._content

    def set_manager(self, manager: Manager):
        Viewer.set_manager(self, manager)
        for item in self._content:
            item.set_manager(self.manager)
            item.parent = self

    def load_content(self):
        for item in self._content:
            item.load()

    def load(self):
        super().load()
        self.load_content()

    def unload_content(self):
        for item in self._content:
            item.unload()

    def unload(self):
        super().unload()
        self.unload_content()

    def add(self, item: Viewer, position: int = 0):
        item = item or Spacer()
        assert isinstance(item, Viewer)

        item.set_manager(self.manager)
        item.parent = self

        item.load()
        item.reset_size()
        self._content.insert(len(self._content) - position, item)
        self.reset_size()

    def remove(self, item):
        assert isinstance(item, Viewer)
        self._content.remove(item)
        item.delete()
        self.reset_size()

    def delete(self):
        for item in self._content:
            item.delete()
        self._content.clear()
        Viewer.delete(self)

    def delete_contents(self):
        for item in self._content:
            item.delete()
        self._content.clear()
        self.reset_size()

    def reset_size(self, reset_parent=True):
        if not reset_parent:
            for item in self._content:
                item.reset_size(reset_parent=False)
        super().reset_size(reset_parent)


class VerticalContainer(Container):
    align: int = HALIGN_CENTER
    padding: int = 5
    _expandable: list

    def __init__(self, content: list, align: int = HALIGN_CENTER, padding: int = 5, width: int = 0, height: int = 0):
        assert align in (HALIGN_CENTER, HALIGN_LEFT, HALIGN_RIGHT)
        if width and height:
            super().__init__(content=content, width=width, height=height)
        else:
            super().__init__(content=content)
        self.align = align
        self.padding = padding
        self._expandable = []

    def expand(self, width: int, height: int):
        """Expands to fill available vertical space.  We split available space
        equally between all spacers.
        """
        available = int((height - self.height) / len(self._expandable))
        remainder = height - self.height - len(self._expandable) * available
        for item in self._expandable:
            if remainder > 0:
                item.expand(item.width, item.height + available + 1)
                remainder -= 1
            else:
                item.expand(item.width, item.height + available)
        self.height = height
        self.width = width

    def is_expandable(self) -> bool:
        # True if we contain an expandable content.
        return len(self._expandable) > 0

    def layout(self, position_set: bool = False):
        # Expand any expandable content to our width
        for item in self._content:
            if item.is_expandable() and item.width < self.width:
                item.expand(self.width, item.height)

        top = self.y + self.height
        if self.align == HALIGN_RIGHT:
            for item in self._content:
                item.set_position(self.x + self.width - item.width, top - item.height)
                top -= item.height + self.padding
        elif self.align == HALIGN_CENTER:
            for item in self._content:
                item.set_position(self.x + self.width / 2 - item.width / 2, top - item.height)
                top -= item.height + self.padding
        else:  # HALIGN_LEFT
            for item in self._content:
                item.set_position(self.x, top - item.height)
                top -= item.height + self.padding

    def compute_size(self) -> tuple[int, int]:
        if len(self._content) < 2:
            height = 0
        else:
            height = -self.padding
        width = 0
        for item in self._content:
            height += item.height + self.padding
            width = max(width, item.width)
        self._expandable = [x for x in self._content if x.is_expandable()]

        return width, height


class HorizontalContainer(Container):
    align: int = HALIGN_CENTER
    padding: int = 5
    _expandable: list

    def __init__(self, content: list, align: int = VALIGN_CENTER, padding: int = 5,
                 width: int = 0, height: int = 0):
        assert align in (HALIGN_CENTER, HALIGN_LEFT, HALIGN_RIGHT)
        if width and height:
            super().__init__(content=content, width=width, height=height)
        else:
            super().__init__(content=content)
        self.align = align
        self.padding = padding
        self._expandable = []

    def is_expandable(self) -> bool:
        # True if we contain expandable content.
        return len(self._expandable) > 0

    def expand(self, width: int, height: int):
        """Expands to fill available horizontal space.  We split available space
        equally between all spacers.
        """
        available = int((width - self.width) / len(self._expandable))
        remainder = width - self.width - len(self._expandable) * available
        for item in self._expandable:
            if remainder > 0:
                item.expand(item.width + available + 1, item.height)
                remainder -= 1
            else:
                item.expand(item.width + available, item.height)
        self.width = width
        self.height = height

    def layout(self):
        # Expand any expandable content to our height
        for item in self._content:
            if item.is_expandable() and item.height < self.height:
                item.expand(item.width, self.height)

        left = self.x
        if self.align == VALIGN_TOP:
            for item in self._content:
                item.set_position(left, self.y + self.height - item.height)
                left += item.width + self.padding
        elif self.align == VALIGN_CENTER:
            for item in self._content:
                item.set_position(left, self.y + self.height / 2 - item.height / 2)
                left += item.width + self.padding
        else:  # VALIGN_BOTTOM
            for item in self._content:
                item.set_position(left, self.y)
                left += item.width + self.padding

    def compute_size(self) -> tuple[int, int]:
        height = 0
        if len(self._content) < 2:
            width = 0
        else:
            width = -self.padding
        for item in self._content:
            height = max(height, item.height)
            width += item.width + self.padding
        self._expandable = [x for x in self._content if x.is_expandable()]
        return width, height


class GridContainer(Container):
    """Arranges Widgets in a table.  Each cell's height and width are set to
    the maximum width of any Viewer in its column, or the maximum height of
    any Viewer in its row.
    """
    _matrix: list
    anchor: tuple[int, int]
    padding: int
    offset: tuple[int, int]
    _max_heights: list
    _max_widths: list

    def __init__(self, content: list, anchor: tuple[int, int] = ANCHOR_CENTER, padding: int = 5,
                 offset: tuple[int, int] = (0, 0)):
        assert isinstance(content, list) and len(content) != 0

        # we set _content to be a flatten list of content.
        super().__init__([item for sub_list in content for item in sub_list])

        # and we set _matrix to be the matrix-like list [[]].
        self._matrix = content
        self.anchor = anchor
        self.padding = padding
        self.offset = offset

        self._max_heights = []
        self._max_widths = []
        self._update_max_vectors()

    @property
    def content(self) -> list:
        return self._matrix

    def _update_max_vectors(self):
        """Updates the sizes of vectors _max_widths and _max_heights.

        Must be called when _matrix changes number of elements.
        """
        # re-compute length of vector _max_widths
        self._max_heights = [0] * len(self._matrix)
        width = 0
        for row in self._matrix:
            width = max(width, len(row))
        self._max_widths = [0] * width

    def add_row(self, row: list):
        """Adds a new row to the layout.
        """
        assert isinstance(row, list)
        for item in row:
            item = item or Spacer()
            item.set_manager(self.manager)
            item.parent = self
            item.load()
            self._content.append(item)
        self._matrix.append(row)

        self._update_max_vectors()

        self.reset_size()

    def add_column(self, column: list):
        """Adds a new column to the layout.
        """
        assert isinstance(column, list)

        # assign items parents and managers
        for item in column:
            if item is not None:
                item = item or Spacer()
                item.set_manager(self.manager)
                item.parent = self
                item.load()
                self._content.append(item)

        # add items to the matrix, extending the grid if needed.
        for i in range(len(column)):
            try:
                self._matrix[i].append(column[i])
            except IndexError:
                self._matrix.append([] * len(column) + [column[i]])

        self._update_max_vectors()

        # update sizes
        self.reset_size()

    def get(self, column: int, row: int) -> Viewer:
        """Gets the content of a cell within the grid.
        If invalid, it raises an IndexError.
        """
        return self._matrix[row][column]

    def set(self, column: int, row: int, item: Viewer):
        """Set the content of a cell within the grid,
        substituting existing content.
        """
        item = item or Spacer()
        assert isinstance(item, Viewer)

        self._content.remove(self._matrix[row][column])
        self._matrix[row][column].delete()
        self._matrix[row][column] = item
        self._content.append(item)

        item.set_manager(self.manager)
        item.parent = self
        item.load()
        self.reset_size()

    def layout(self):
        row_index = 0
        placement = Rectangle()
        placement.y = self.y + self.height
        for row in self._matrix:
            col_index = 0
            placement.x = self.x
            placement.height = self._max_heights[row_index]
            placement.y -= placement.height
            for item in row:
                placement.width = self._max_widths[col_index]
                if item is not None:
                    if item.is_expandable():
                        item.expand(placement.width, placement.height)
                    item.set_position(*get_relative_point(placement, self.anchor, item, self.anchor, self.offset))
                placement.x += placement.width
                col_index += 1
            row_index += 1

    def compute_size(self) -> tuple[int, int]:
        # calculates the size and the maximum widths and heights of
        # each row and column.
        row_index = 0
        for row in self._matrix:
            max_height = self.padding
            col_index = 0
            for item in row:
                if item is not None:
                    item.compute_size()
                    width, height = item.width, item.height
                else:
                    width = height = 0
                max_height = max(max_height, height + self.padding)
                max_width = self._max_widths[col_index]
                max_width = max(max_width, width + self.padding)
                self._max_widths[col_index] = max_width
                col_index += 1
            self._max_heights[row_index] = max_height
            row_index += 1

        if self._max_widths:
            width = reduce(lambda x, y: x + y, self._max_widths) - self.padding
        else:
            width = 0
        if self._max_heights:
            height = reduce(lambda x, y: x + y, self._max_heights) - self.padding
        else:
            height = 0

        return width, height

    def delete(self):
        super().delete()
        self._matrix.clear()


class Wrapper(Container):
    """A Viewer that wraps another widget.
    """
    expandable: bool = False
    _anchor: tuple[int, int]
    content_offset: tuple[int, int]

    def __init__(self, content: Viewer, is_expandable: bool = False, anchor: tuple[int, int] = ANCHOR_CENTER,
                 offset: tuple[int, int] = (0, 0)):
        assert isinstance(content, Viewer)
        super().__init__(content=[content])
        self.expandable = is_expandable
        self._anchor = anchor
        self.content_offset = offset

    @property
    def anchor(self) -> tuple[int, int]:
        return self._anchor

    @anchor.setter
    def anchor(self, anchor: tuple[int, int]):
        self._anchor = anchor

    @property
    def content(self) -> Viewer:
        return self._content[0]

    @content.setter
    def content(self, content: Viewer):
        assert isinstance(content, Viewer)
        self.content.delete()

        self._content[0] = content
        self.content.set_manager(self.manager)
        self.content.parent = self
        self.content.load()
        self.reset_size()

    def expand(self, width: int, height: int):
        if self.content.is_expandable():
            self.content.expand(width, height)
        self.width = width
        self.height = height

    def is_expandable(self) -> bool:
        return self.expandable

    def compute_size(self) -> tuple[int, int]:
        return self.content.width, self.content.height

    def layout(self):
        x, y = get_relative_point(self, self.anchor, self.content, self.anchor, self.content_offset)
        self.content.set_position(x, y)
