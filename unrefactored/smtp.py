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

from gettext import gettext as _
from smtplib import SMTP

from accounts import TransportAccount
from pop import POPError
from utility import flatten

class SMTPTransportAccount(TransportAccount):

    def __init__(self, from_addr, host, port=25, auth_type=None, username=None, password=None, pop_account=None):
        TransportAccount.__init__(self, from_addr, host, port, auth_type, username, password)
        if auth_type=='POP_BEFORE_SMTP':
            self._pop_account = pop_account
    
    def _connect(self, tracker):
        server = SMTP()
        if self._auth_type=='POP_BEFORE_SMTP':
            tracker.update(_('Authenticating...'))
            try:
                self._pop_account.auth_and_quit()
            except POPError:
                tracker.error(_('Error authenticating using POP'))
                return None
        try:
            tracker.update(_('Connecting to server...'))
            server.connect(self._host, self._port)
        except:
            tracker.error(_('Error connecting to %s:%d' % (self._host, self._port)))
            return None
        if self._auth_type=='SSL':
            try:
                tracker.update(_('Authenticating...'))
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self._username, self._password)
            except:
                tracker.error(_('Error authenticating %s' % self._username))
                return None
        return server

    def __extract_addrs(self, msg):
        from email.utils import parseaddr
        frm = parseaddr(msg['From'])
        to = [split2.strip() for split1 in msg['To'].split(';') for split2 in split1.split(',') if not split2.strip()==''] # eh
        return frm, to

    def _deliver(self, server, msg, tracker):
        from_addr, to_addrs = self.__extract_addrs(msg)
        flattened_msg = flatten(msg)
        failures = {}
        try:
            tracker.update(_('Delivering %s' % msg['Subject']))
            failures = server.sendmail(from_addr, to_addrs, flattened_msg)
        except:
            tracker.error_delivering(msg)
            return None
        return failures

    def send(self, msgs, tracker):
        server = self._connect(tracker)
        if server is None:
            tracker.try_later(msgs)
            return
        for msg in msgs:
            failures = self._deliver(server, msg, tracker)
            if failures is not None:
                if failures=={}:
                    tracker.sent(msg)
                else:
                    tracker.some_rcpts_failed(msg, failures)
        try:
            server.quit()
        except:
            pass
        tracker.done()
