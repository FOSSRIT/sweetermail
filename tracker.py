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

import email
import email.utils
import gtk

from gettext import gettext as _
from sugar.graphics.icon import Icon
from sugar.graphics import alert

from tags import FLAGS, HARDCODED

def ugly_hack(self, papa, pspec, value):
    if pspec.name=='msg':
        if self._msg != value:
            self._msg = value
            self._msg_label.set_markup(self._msg)
    else:
        papa.do_set_property(self, pspec, value)

class ProgressAlert(alert.Alert):
    
    def __init__(self, *args, **kwds):
        alert.Alert.__init__(self, *args, **kwds)
        icon = Icon(icon_name='emblem-busy')
        self.props.icon = icon
        icon.show()
    
    do_set_property = lambda self, pspec, value: ugly_hack(self, alert.Alert, pspec, value)

class ErrorAlert(alert.NotifyAlert):
    
    def __init__(self, *args, **kwds):
        alert.NotifyAlert.__init__(self, *args, **kwds)
        icon = Icon(icon_name='emblem-notification')
        self.props.icon = icon
        icon.show()
    
    do_set_property = lambda self, pspec, value: ugly_hack(self, alert.NotifyAlert, pspec, value)

class ProgressTracker(object):

    def __init__(self, activity, title):
        self._activity = activity
        self._title = title
        self._alert = ProgressAlert()

        self._alert.props.title = title
        self._activity.add_alert(self._alert)
        
    def _remove_alert(self, *args):
        gtk.gdk.threads_enter()
        self._activity.remove_alert(self._alert)
        gtk.gdk.threads_leave()

    def done(self):
        self._remove_alert()

    def update(self, msg):
        gtk.gdk.threads_enter()
        self._alert.props.msg = msg
        gtk.gdk.threads_leave()

    def error(self, msg, remove_old=True):
        if remove_old: self._remove_alert()
        gtk.gdk.threads_enter()
        notify(self._activity, self._title, msg)
        gtk.gdk.threads_leave()

class InboundTracker(ProgressTracker):
    
    def __init__(self, activity):
        ProgressTracker.__init__(self, activity, _('Checking email'))
    
    def dump_msg(self, msg_str):
        # TODO setting of FLAGS{'has_attachment'], filtering(!)
        msg = email.message_from_string(msg_str)
        ms = self._activity.ms
        key = ms.add_msg(msg)
        # gmail sent emails hack
        if email.utils.parseaddr(msg['From'])[1]==self._activity.config.transport_account._from_addr:
            ms.flag(key, FLAGS['sent'])
        else:
            ms.associate(HARDCODED['inbox'], key)

class OutboundTracker(ProgressTracker):
    
    def __init__(self, activity):
        ProgressTracker.__init__(self, activity, _('Sending email'))

    def _add_and_flag(self, msg, flag):
        ms = self._activity.ms
        key = ms.add_msg(msg)
        ms.flag(key, flag)

    def try_later(self, msgs):
        for msg in msgs:
            self._add_and_flag(msg, FLAGS['outbound'])
    
    def error_delivering(self, msg):
        self._add_and_flag(msg, FLAGS['draft'])
        ProgressTracker.error(self, _('Error delivering <i>%s</i>, message saved as draft.' % msg['Subject']), remove_old=False)
        
    def some_rcpts_failed(self, msg, who):
        msg['To'] = '; '.join(who)
        self._add_and_flag(msg, FLAGS['draft'])
        ProgressTracker.error(self, _('Error delivering <i></i> to %s; saved as draft.' % ', '.join(who)), remove_old=False)
    
    def sent(self, msg):
        self._add_and_flag(msg, FLAGS['sent'])

def notify(activity, title, msg, timeout=5):
    alert = ErrorAlert(timeout)
    alert.props.title = title
    alert.props.msg = msg
    activity.add_alert(alert)
    alert.connect('response', lambda x,y: activity.remove_alert(alert))
