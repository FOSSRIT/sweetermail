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

import email.utils
import gtk
import logging
import pango
import thread

from email.mime.text import MIMEText
from gettext import gettext as _
from sugar.graphics.toolbutton import ToolButton
from sugar.graphics import style

from tracker import OutboundTracker, notify
import utility

class WriteCanvas(gtk.VBox):

    def __init__(self, activity):        
        gtk.VBox.__init__(self, False, 0)
        
        self._activity = activity

        self.set_border_width(5)
        self.set_spacing(0)

        table = gtk.Table(2, 2)
        
        to_label = gtk.Label('<i>%s</i>' % _('To'))
        to_label.set_use_markup(True)
        to_label.set_alignment(0.0, 0.5)
        self._to_entry = gtk.Entry()
        
        subj_label = gtk.Label('<i>%s</i>' % _('Subject'))
        subj_label.set_use_markup(True)
        subj_label.set_alignment(0.0, 0.5)
        self._subj_entry = gtk.Entry()
        
        padding = style.DEFAULT_PADDING
        table.attach(to_label, 0, 1, 0, 1, gtk.FILL, 0, padding, padding)
        table.attach(self._to_entry, 1, 2, 0, 1, gtk.EXPAND|gtk.FILL, 0, padding, padding)
        table.attach(subj_label, 0, 1, 1, 2, gtk.FILL, 0, padding, padding)
        table.attach(self._subj_entry, 1, 2, 1, 2, gtk.EXPAND|gtk.FILL, 0, padding, padding)
        
        self.pack_start(table, False, False, 0)

        scrolled = gtk.ScrolledWindow()
        scrolled.set_shadow_type(gtk.SHADOW_IN)
        
        self._textview = gtk.TextView()
        for prop in ('left_margin', 'right_margin', 'pixels_above_lines', 'pixels_below_lines'):
            setattr(self._textview.props, prop, style.DEFAULT_SPACING)
        self._textview.set_wrap_mode(gtk.WRAP_WORD)

        scrolled.add_with_viewport(self._textview)

        self.pack_start(scrolled, True, True, 0)
        
    def make_msg(self): # egh
        
        to = self._to_entry.get_text()
        subj = self._subj_entry.get_text()
        buf = self._textview.get_buffer()
        start, end = buf.get_bounds()
        body = buf.get_text(start, end)
        
        msg = MIMEText(body)
        msg['From'] = self._activity.config.from_hdr
        msg['To'] = to
        msg['Subject'] = subj
        msg['Date'] = email.utils.formatdate()
        msg['Message-ID'] = email.utils.make_msgid()
        return msg

class WriteToolbar(gtk.Toolbar):

    canvas = WriteCanvas

    def __init__(self, activity):        
        gtk.Toolbar.__init__(self)
        self._activity = activity
    
        self._send_button = ToolButton('send-email', tooltip=_('Send email'))
        self._send_button.connect('clicked', self.__send_email_cb)
        self.insert(self._send_button, -1)

        self._attach_button = ToolButton('add-attachment', tooltip=_('Add attachment'))
        self._attach_button.connect('clicked', self.__add_attachment_cb)
        self.insert(self._attach_button, -1)
        
        self.show_all()


    def __send_email_cb(self, *args):
        msg = self._activity.canvas.make_msg()
        if utility.check_online():
            func = self._activity.config.transport_account.send
            args = ([msg], OutboundTracker(self._activity))
            thread.start_new_thread(func, args)
        else:
            self._keep_as_outbound(msg)
        self._activity.toolbox.current_toolbar = 1  # egh

    def __add_attachment_cb(self, *args):
        pass

def keep_as_outbound(self, msg):
    ms = self._activity.ms
    key = ms.add_msg(msg)
    ms.flag(key, FLAGS['outbound'])
        notify(self._activity, _("<i>%s</i> kept as outbound" % msg['Subject']),
                       _('No network connection'))