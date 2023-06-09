import pyglet


class Label(pyglet.text.Label):
    def update(self):
        pyglet.text.Label._update(self)

    def unload(self):
        self.delete()

    def pos(self, x: float | int, y: float | int):
        if isinstance(x, float):
            x = round(x)
        if isinstance(y, float):
            y = round(y)
        self.position = (x, y, 0)


class InputLabel(Label):
    def _get_left(self) -> int:
        if self._multiline:
            width = self._width
        else:
            width = self.content_width
            if self.width and width > self.width:
                # align to right edge, clip left
                return self._x + self.width - width

        if self._anchor_x == 'left':
            return self._x
        elif self._anchor_x == 'center':
            return self._x - width // 2
        elif self._anchor_x == 'right':
            return self._x - width
        else:
            assert False, 'Invalid anchor_x'

    def _update(self):
        Label.update(self)
        # Iterate through our vertex lists and break if we need to clip
        remove = []
        if self.width and not self._multiline:
            for vlist in self._vertex_lists:
                num_quads = len(vlist.position) // 12

                remove_quads = 0
                for n in range(0, num_quads):
                    x1, y1, z1, x2, y2, z2, x3, y3, z3, x4, y4, z4 = vlist.position[n * 12: n * 12 + 12]
                    tx1, ty1, tz1, tx2, ty2, tz2, tx3, ty3, tz3, tx4, ty4, tz4 = vlist.tex_coords[n * 12: n * 12 + 12]
                    if x2 >= self._x:
                        m = n - remove_quads  # shift quads left
                        if x1 < self._x:  # clip on left side
                            percent = (float(self._x) - float(x1)) / \
                                      (float(x2) - float(x1))
                            x1 = x4 = max(self._x, x1)
                            tx1 = tx4 = (tx2 - tx1) * percent + tx1
                        vlist.position[m * 12: m * 12 + 12] = \
                            [x1, y1, z4, x2, y2, z4, x3, y3, z4, x4, y4, z4]
                        vlist.tex_coords[m * 12: m * 12 + 12] = \
                            [tx1, ty1, tz1, tx2, ty2, tz2,
                             tx3, ty3, tz3, tx4, ty4, tz4]
                    else:
                        # We'll unload quads entirely not visible
                        remove_quads += 1
                if remove_quads == num_quads:
                    remove.append(vlist)
                elif remove_quads > 0:
                    vlist.resize((num_quads - remove_quads) * 6, (num_quads - remove_quads) * 6)
        for vlist in remove:
            vlist.delete()
            self._vertex_lists.remove(vlist)
