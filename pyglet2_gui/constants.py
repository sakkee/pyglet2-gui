from .core import Rectangle

VALIGN_TOP: int = 1
VALIGN_CENTER: int = 0
VALIGN_BOTTOM: int = -1

HALIGN_LEFT: int = -1
HALIGN_CENTER: int = 0
HALIGN_RIGHT: int = 1

ANCHOR_TOP_LEFT: tuple[int, int] = (VALIGN_TOP, HALIGN_LEFT)
ANCHOR_TOP: tuple[int, int] = (VALIGN_TOP, HALIGN_CENTER)
ANCHOR_TOP_RIGHT: tuple[int, int] = (VALIGN_TOP, HALIGN_RIGHT)
ANCHOR_LEFT: tuple[int, int] = (VALIGN_CENTER, HALIGN_LEFT)
ANCHOR_CENTER: tuple[int, int] = (VALIGN_CENTER, HALIGN_CENTER)
ANCHOR_RIGHT: tuple[int, int] = (VALIGN_CENTER, HALIGN_RIGHT)
ANCHOR_BOTTOM_LEFT: tuple[int, int] = (VALIGN_BOTTOM, HALIGN_LEFT)
ANCHOR_BOTTOM: tuple[int, int] = (VALIGN_BOTTOM, HALIGN_CENTER)
ANCHOR_BOTTOM_RIGHT: tuple[int, int] = (VALIGN_BOTTOM, HALIGN_RIGHT)


def get_relative_point(parent: Rectangle, parent_anchor: tuple[int, int], child: Rectangle,
                       child_anchor: tuple[int, int] | None, offset: tuple[int, int]) -> tuple[int, int]:
    valign, halign = parent_anchor or ANCHOR_CENTER

    if valign == VALIGN_TOP:
        y = parent.y + parent.height
    elif valign == VALIGN_CENTER:
        y = parent.y + parent.height // 2
    else:  # VALIGN_BOTTOM
        y = parent.y

    if halign == HALIGN_LEFT:
        x = parent.x
    elif halign == HALIGN_CENTER:
        x = parent.x + parent.width // 2
    else:  # HALIGN_RIGHT
        x = parent.x + parent.width

    valign, halign = child_anchor or (valign, halign)
    offset_x, offset_y = offset

    if valign == VALIGN_TOP:
        y += offset_y - child.height
    elif valign == VALIGN_CENTER:
        y += offset_y - child.height // 2
    else:  # VALIGN_BOTTOM
        y += offset_y

    if halign == HALIGN_LEFT:
        x += offset_x
    elif halign == HALIGN_CENTER:
        x += offset_x - child.width // 2
    else:  # HALIGN_RIGHT
        x += offset_x - child.width

    return x, y
