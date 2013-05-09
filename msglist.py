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
import gtk
import hippo
import logging
import traceback
import sys

from gettext import gettext as _
from sugar import profile
from sugar.graphics import style
from sugar.graphics.icon import CanvasIcon
import sugar

import query

from msgentry import MessageEntry

UPDATE_INTERVAL = 300000
NO_MATCHES = _('No matching messages')
NOTHING_TO_SHOW = _('Select a tag')

class MsgList(gtk.HBox):
    
    def __init__(self, store, activity):
        self._store = store
        self._query = {}
        self._result_set = None
        self._entries = []
        self._page_size = 10
        self._last_value = -1
        self._reflow_sid = 0
	self.activity = activity;
        
        gtk.HBox.__init__(self)
        self.set_flags(gtk.HAS_FOCUS | gtk.CAN_FOCUS)
        self.connect('key-press-event', self._key_press_event_cb)

        self._box = hippo.CanvasBox(orientation=hippo.ORIENTATION_VERTICAL,
                                    background_color=style.COLOR_WHITE.get_int())
        self._canvas = hippo.Canvas()
        self._canvas.set_root(self._box)

        self.pack_start(self._canvas)
        self._canvas.show()
        
        self._vadjustment = gtk.Adjustment(value=0, lower=0, upper=0,
                                           step_incr=1, page_incr=0, page_size=0)
        self._vadjustment.connect('value-changed', self._vadjustment_value_changed_cb)
        self._vadjustment.connect('changed', self._vadjustment_changed_cb)
        
        self._vscrollbar = gtk.VScrollbar(self._vadjustment)
        self.pack_end(self._vscrollbar, expand=False, fill=False)
        self._vscrollbar.show()
        
        self.connect('scroll-event', self._scroll_event_cb)
        self.connect('destroy', self.__destroy_cb)
        
        self._fully_obscured = True
        self._dirty = False
        self._refresh_idle_handler = None
        self._update_dates_timer = None
        
    def __destroy_cb(self, widget):
        if self._result_set:
            self._result_set.destroy()
    
    def _vadjustment_changed_cb(self, vadjustment):
        logging.debug('_vadjustment_changed_cb:\n \t%r\n \t%r\n \t%r\n \t%r\n \t%r\n' % \
              (vadjustment.props.lower, vadjustment.props.page_increment, 
              vadjustment.props.page_size, vadjustment.props.step_increment,
              vadjustment.props.upper))
        if vadjustment.props.upper > self._page_size:
            self._vscrollbar.show()
        else:
            self._vscrollbar.hide()
    
    def _vadjustment_value_changed_cb(self, vadjustment):
        gobject.idle_add(self._do_scroll)
        
    def _do_scroll(self, force=False):
        import time
        t = time.time()
        
        value = int(self._vadjustment.props.value)
        
        if value == self._last_value and not force:
            return
        self._last_value = value
        
        self._result_set.seek(value)
        mobjects = self._result_set.read(self._page_size)
        
        if self._result_set.length != self._vadjustment.props.upper:
            self._vadjustment.props.upper = self._result_set.length
            self._vadjustment_changed()
        
        self._refresh_view(mobjects)
        self._dirty = False
        
        logging.debug('_do_scroll %r %r\n' % (value, (time.time() - t)))

        return False
    
    def _refresh_view(self, mobjects):
        logging.debug('ListView %r' % self)
        # no mail to show
        if len(mobjects) == 0:
            self._show_message(NOTHING_TO_SHOW)
            return
        # refresh view and create the entries if they don't exist
        for i in range(0, self._page_size):
            try:
                if i < len(mobjects):
                    if i >= len(self._entries):
                        entry = self.create_entry()
                        self._box.append(entry)
                        self._entries.append(entry)
                        entry.mobject = mobjects[i]
                    else:
                        entry = self._entries[i]
                        entry.mobject = mobjects[i]
                        entry.set_visible(True)
                elif i < len(self._entries):
                    entry = self._entries[i]
                    entry.set_visible(False)
            except Exception:
                logging.error('Exception while displaying entry:\n' + \
                    ''.join(traceback.format_exception(*sys.exc_info())))


    def create_entry(self):
        return MessageEntry(self.activity)
    
    def update_with_query(self, query):
        logging.debug('update_with_query, page_size = %d' % self._page_size)
        self._query = query
        if self._page_size > 0:
            self.refresh()
    
    def refresh(self, message_mode=False, message=None):
        if self._result_set:
            self._result_set.destroy()
        self._result_set = query.find(self._store, self._query)
        self._vadjustment.props.upper = self._result_set.length
        self._vadjustment.changed()
        
        self._vadjustment.props.value = min(self._vadjustment.props.value,
                                           self._result_set.length -self._page_size)
        
        if self._result_set.length == 0:
            if self._query.get('query', ''):
                self._show_message(NO_MATCH)
            else:
                self._show_message(NOTHING_TO_SHOW)
        elif message_mode:
            self._show_mobject(message)
        else:
            self._clear_message()
            self._do_scroll(force=True)
    
    def _scroll_event_cb(self, hbox, event):
        if event.direction == gtk.gdk.SCROLL_UP:
            if self._vadjustment.props.value > self._vadjustment.props.lower:
                self._vadjustment.props.value -= 1
            elif event.direction == gtk.gdk.SCROLL_DOWN:
                max_value = self._result_set.length - self._page_size
                if self._vadjustment.props.value < max_value:
                    self._vadjustment.props.value += 1
    
    def do_focus(self, direction):
        if not self.is_focus():
            self.grab_focus()
            return True
        return False
    
    def _key_press_event_cb(self, widget, event):
        keyname = gtk.gdk.keyval_name(event.keyval)

        if keyname == 'Up':
            if self._vadjustment.props.value > self._vadjustment.props.lower:
                self._vadjustment.props.value -= 1
        elif keyname == 'Down':
            max_value = self._result_set.length - self._page_size
            if self._vadjustment.props.value < max_value:
                self._vadjustment.props.value += 1
        elif keyname == 'Page_Up' or keyname == 'KP_Page_Up':
            new_position = max(0, self._vadjustment.props.value - self._page_size)
            if new_position != self._vadjustment.props.value:
                self._vadjustment.props.value = new_position
        elif keyname == 'Page_Down' or keyname == 'KP_Page_Down':
            new_position = min(self._result_set.length - self._page_size,
                               self._vadjustment.props.value + self._page_size)
            if new_position != self._vadjustment.props.value:
                self._vadjustment.props.value = new_position
        elif keyname == 'Home' or keyname == 'KP_Home':
            new_position = 0
            if new_position != self._vadjustment.props.value:
                self._vadjustment.props.value = new_position
        elif keyname == 'End' or keyname == 'KP_End':
            new_position = max(0, self._result_set.length - self._page_size)
            if new_position != self._vadjustment.props.value:
                self._vadjustment.props.value = new_position
        else:
            return False

        return True

    def do_size_allocate(self, allocation):
        gtk.HBox.do_size_allocate(self, allocation)
        new_page_size = int(allocation.height / style.GRID_CELL_SIZE)

        logging.debug("do_size_allocate: %r" % new_page_size)
        
        if new_page_size != self._page_size:
            self._page_size = new_page_size
            self._queue_reflow()
    
    def _queue_reflow(self):
        if not self._reflow_sid:
            self._reflow_sid = gobject.idle_add(self._reflow_idle_cb)
            
    def _reflow_idle_cb(self):
        self._box.clear()
        self._entries = []
        
        self._vadjustment.props.page_size = self._page_size
        self._vadjustment.props.page_increment = self._page_size
        self._vadjustment_changed()
        
        if self._result_set is None:
            self._result_set = query.find(self._store, self._query)
        
        max_value = max(0, self._result_set.length - self._page_size)
        if self._vadjustment.props.value > max_value:
            self._vadjustment.props.value = max_value
        else:
            self._do_scroll(force=True)
            
        self._reflow_sid = 0
        
    def _show_message(self, message):
        box = hippo.CanvasBox(orientation=hippo.ORIENTATION_VERTICAL,
                              background_color=style.COLOR_WHITE.get_int(),
                              yalign=hippo.ALIGNMENT_CENTER)
        icon = CanvasIcon(size=style.LARGE_ICON_SIZE,
                          file_name='activity/activity-mail.svg',
                          stroke_color=style.COLOR_BUTTON_GREY.get_svg(),
                          fill_color=style.COLOR_TRANSPARENT.get_svg())
        text = hippo.CanvasText(text=message,
                                xalign=hippo.ALIGNMENT_CENTER,
                                font_desc=style.FONT_NORMAL.get_pango_desc(),
                                color=style.COLOR_BUTTON_GREY.get_int())
        
        box.append(icon)
        box.append(text)
        self._canvas.set_root(box)

    def _show_mobject(self, mobject):
	black = sugar.graphics.style.Color('#000000')
        box = hippo.CanvasBox(orientation=hippo.ORIENTATION_VERTICAL,
                              background_color=style.COLOR_WHITE.get_int(),
                              yalign=hippo.ALIGNMENT_CENTER)
        icon = CanvasIcon(size=style.LARGE_ICON_SIZE,
                          file_name='icons/back.svg',
                          stroke_color=style.COLOR_WHITE.get_svg(),
                          fill_color=style.COLOR_TRANSPARENT.get_svg())
        who = hippo.CanvasText(text="From: "+mobject.who,
                                xalign=hippo.ALIGNMENT_CENTER,
                                font_desc=style.FONT_NORMAL.get_pango_desc(),
                                color=black.get_int())

        what = hippo.CanvasText(text="Subject: "+mobject.what,
                                xalign=hippo.ALIGNMENT_CENTER,
                                font_desc=style.FONT_NORMAL.get_pango_desc(),
                                color=black.get_int())

        when = hippo.CanvasText(text="Date: "+mobject.when,
                                xalign=hippo.ALIGNMENT_CENTER,
                                font_desc=style.FONT_NORMAL.get_pango_desc(),
                                color=black.get_int())

        contents = hippo.CanvasText(text="Message: "+self._store.get_msg(mobject.key),
                                xalign=hippo.ALIGNMENT_CENTER,
                                font_desc=style.FONT_NORMAL.get_pango_desc(),
                                color=black.get_int())

	
        
        #box.append(icon)
        box.append(who)
        box.append(what)
        box.append(when)
	box.append(contents)
        self._canvas.set_root(box)
        
    def _clear_message(self):
        self._canvas.set_root(self._box)
        
    def update_dates(self):
        logging.debug('MessageList.update_dates')
        for entry in self._entries:
            entry.update_date()
            
    def _set_dirty(self):
        if self._fully_obscured:
            self._dirty = True
        else:
            self._schedule_refresh()
            
    def _schedule_refresh(self):
        if self._refresh_idle_handler is None:
            logging.debug('Add refresh idle callback')
            self._refresh_idle_handler = gobject.idle_add(self.__refresh_idle_cb)
        
    def __refresh_idle_cb(self):
        self.refresh()
        if self._refresh_idle_handler is not None:
            logging.debug('Remove refresh idle callback')
            gobject.source_remove(self._refresh_idle_handler)
            self._refresh_idle_handler = None
        return False
    
    def set_is_visible(self, visible):
        logging.debug('canvas_visibility_notify_event_cb %r' % visible)
        if visible:
            self._fully_obscured = False
            if self._dirty:
                self._schedule_refresh()
            if self._update_dates_timer is None:
                logging.debug('Adding date updating timer')
                self._update_dates_timer = gobject.timeout_add(UPDATE_INTERVAL, self.__update_dates_timer_cb)
        else:
            self._fully_obscured = True
            if self._update_dates_timer is not None:
                logging.debug('Remove date updating timer')
                gobject.source_remove(self._update_dates_timer)
                self._update_dates_timer = None
    
    def __update_dates_timer_cb(self):
        self.update_dates()
        return True
