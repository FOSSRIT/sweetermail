# Copyright 2009 Shikhar Bhushan <shikhar@schmizz.net>
# 
# This file is part of the Sweetmail activity for Sugar.
#
# Sweetmail is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Sweetmail is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Sweetmail.  If not, see <http://www.gnu.org/licenses/>.
import logging

from gettext import gettext as _
from poplib import POP3, POP3_SSL
from email.parser import HeaderParser


_ok = lambda resp: True if resp.startswith('+OK') else False
class Account():
    
    def __init__(self, host, port, auth_type, username, password):
        self._host = host
        self._port = port
        self._auth_type = auth_type
        self._username = username
        self._password = password

class StoreAccount(Account):
    
    def __init__(self, host, port, auth_type, username, password, del_on_retr):
        Account.__init__(self, host, port, auth_type, username, password)
        self._del_on_retr = False

class POPStoreAccount(StoreAccount):

    def __init__(self, host, port, auth_type, username, password, del_on_retr=False):
        StoreAccount.__init__(self, host, port, auth_type, username, password, del_on_retr)

    def _connect(self):
        cls = POP3_SSL if self._auth_type=='SSL' else POP3
        return cls(self._host, self._port)

    def _authenticate(self, server):
        return ( _ok(server.user(self._username)) and _ok(server.pass_(self._password)) )

    def auth_and_quit(self):
        server = self._connect()
        if (server is None) or (not self._authenticate(server)):
            raise POPError
        server.quit()
        
    def retrieve_all(self, tracker):
        tracker.update(_('Connecting...'))
        logging.debug('Connecting...')
        try:
            server = self._connect()
        except:
            tracker.error(_('Error connecting to %s:%d' % (self._host, self._port)))
            return
        
        tracker.update(_('Authenticating...'))
        logging.debug('Authenticating...')
        if not self._authenticate(server):
            tracker.error(_('Error authenticating %s' % self._user))
            logging.debug("couldn't auth!")
            server.quit()
            return
        
        tracker.update(_('Checking for new mail...'))
        logging.debug("checking for new mail")
        (resp, msg_list, octets) = server.list()
        if not _ok(resp):
            tracker.error(_('Error getting message list.'))
            logging.debug("error getting message list")
            server.quit()
            return
        num_msgs = len(msg_list)
        if num_msgs==0:
            logging.debug("No mail!")
            tracker.done()
            server.quit()
            return

        for msg_info in msg_list:      
            
            (num, octets) = msg_info.split()
            tracker.update(_('Retrieving message %s of %d...' %(num, num_msgs)))
            logging.debug('Retrieving message %s of %d...' %(num, num_msgs))
            (resp, lines, octets) = server.retr(num)
            if not _ok(resp):
                tracker.error(_('Error retrieving message.')) # so?!
                server.quit()
                return
            
            tracker.dump_msg('\n'.join(lines))
        
            if (self._del_on_retr and
                 not _ok(server.dele(num))):
                tracker.error(_('Error deleting message.')) # so?!
                server.quit()
                return
        
        tracker.done()
        server.quit()

class TransportAccount(Account):
    
    def __init__(self, from_addr, host, port, auth_type, username, password):
        Account.__init__(self, host, port, auth_type, username, password)
        self._from_addr = from_addr
    
    def send(self, msgs, tracker):
        raise NotImplementedError

#why are these even here?
class DummyTransportAccount():
    
    def send(self, msgs, tracker):
        from tracker import notify
        notify(_('No transport account cofigured'))

class DummyStoreAccount():
    
    def retrieve_all(self, tracker):
        from tracker import notify
        notify(_('No store account cofigured'))

