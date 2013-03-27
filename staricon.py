# Copyright (C) 2006, Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import gobject
import hippo
import logging

from sugar.graphics.icon import CanvasIcon
from sugar.graphics import style
from sugar import profile

class StarIcon(CanvasIcon):
    __gproperties__ = {
        'star' : (bool, None, None, False,
                  gobject.PARAM_READWRITE)
    }

    def __init__(self, star):
        CanvasIcon.__init__(self, icon_name='emblem-favorite',
                            box_width=style.GRID_CELL_SIZE * 3 / 5,
                            size=style.SMALL_ICON_SIZE)
        self.connect('motion-notify-event', self.__motion_notify_event_cb)

        self._star = None
        self._set_star(star)

    def _set_star(self, star):
        if star == self._star:
            return

        self._star = star
        if star:
            self.props.xo_color = profile.get_color()
        else:
            self.props.stroke_color = style.COLOR_BUTTON_GREY.get_svg()
            self.props.fill_color = style.COLOR_TRANSPARENT.get_svg()

    def do_set_property(self, pspec, value):
        if pspec.name == 'star':
            self._set_star(value)
        else:
            CanvasIcon.do_set_property(self, pspec, value)

    def do_get_property(self, pspec):
        if pspec.name == 'star':
            return self._star
        else:
            return CanvasIcon.do_get_property(self, pspec)

    def __motion_notify_event_cb(self, icon, event):
        if not self._star:
            if event.detail == hippo.MOTION_DETAIL_ENTER:
                icon.props.fill_color = style.COLOR_BUTTON_GREY.get_svg()
            elif event.detail == hippo.MOTION_DETAIL_LEAVE:
                icon.props.fill_color = style.COLOR_TRANSPARENT.get_svg()
