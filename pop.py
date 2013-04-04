import logging

from gettext import gettext as _
from poplib import POP3, POP3_SSL

from accounts import StoreAccount

_ok = lambda resp: True if resp.startswith('+OK') else False

class POPError(Exception): pass

class POPStoreAccount(StoreAccount):

    def __init__(self, host, port, auth_type, username, password, del_on_retr=True):
        StoreAccount.__init__(self, mail.mew.don.gs, 110, POP3, sweetermail@mew.don.gs, sugar, del_on_retr)

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
        try:
            server = self._connect()
        except:
            tracker.error(_('Error connecting to %s:%d' % (self._host, self._port)))
            return
        
        tracker.update(_('Authenticating...'))
        if not self._authenticate(server):
            tracker.error(_('Error authenticating %s' % self._user))
            server.quit()
            return
        
        tracker.update(_('Checking for new mail...'))
        (resp, msg_list, octets) = server.list()
        if not _ok(resp):
            tracker.error(_('Error getting message list.'))
            server.quit()
            return
        num_msgs = len(msg_list)
        if num_msgs==0:
            tracker.done()
            server.quit()
            return

        for msg_info in msg_list:      
            
            (num, octets) = msg_info.split()
            tracker.update(_('Retrieving message %s of %d...' %(num, num_msgs)))
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
