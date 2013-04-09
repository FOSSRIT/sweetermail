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

from ConfigParser import SafeConfigParser as ConfigParser, NoOptionError
import os
import gtk

from sugar.profile import get_nick_name

import accounts

class ConfigureCanvas(gtk.Button):
    def __init__(self, mailactivity):
        gtk.Button.__init__(self, 'CONFIGURE')

class ConfigureToolbar(gtk.Toolbar):

    def __init__(self, mailactivity):
        gtk.Toolbar.__init__(self)        
        self.mailactivity = mailactivity
        self.canvas = ConfigureCanvas
        
class Configuration:
    
    def __init__(self, cfg_file):        
        self._cfg_file = cfg_file
        
        if not os.path.exists(self._cfg_file): # create it
            open(self._cfg_file, 'w')
        
        self._cp = ConfigParser()
        if not self._cp.read([self._cfg_file]):
            logging.error('ConfigParser: error parsing %s', self._cfg_file)
        
        ### public options ###
        
        # defaults
        self.name = get_nick_name()
        self.sync_every = 1 # minutes
        self.del_on_retr = True
        self.store_account = accounts.DummyStoreAccount()
        self.transport_account = accounts.DummyTransportAccount()
        
        # now parse
        self._parse_profile()
        self._parse_store()
        self._parse_transport()

    def __del__(self):
        fp = open(self._cfg_file, 'w')
        self._cp.write(fp)
        fp.close()

    def _account_dict(self, sec):
        kwds = {}
        fields = ('host', 'port', 'auth_type', 'username', 'password')
        for field in fields:
            try:
                kwds[field] = self._cp.get(sec, field)
            except NoOptionError:
                kwds[field] = None
        kwds['port'] = int(kwds['port'])
        return kwds

    # name, address, sync_every
    def _parse_profile(self):
        sec = 'sending'
        try:
            self.name = self._cp.get(sec, 'name')
            self.address = self._cp.get(sec, 'address')
        except NoOptionError:
            pass

    # store_account
    def _parse_store(self):
        kwds = self._account_dict('store')
        try:
            kwds['del_on_retr'] = self._cp.getboolean('store', 'delete_on_retrieval')
        except NoOptionError:
                kwds['del_on_retr'] = True
        self._store_account = self.POPStoreAccount(**kwds)

    # transport_account
    def _parse_transport(self):
        kwds = self._account_dict('transport')
        try:
            kwds['del_on_retr'] = self._cp.getboolean('store', 'delete_on_retrieval')
        except NoOptionError:
            kwds['del_on_retr'] = True
        self._store_account = self.TransportAccount(**kwds)
    
    @property
    def from_header(self):
        from email.utils import formataddr
        return formataddr((self.name, self.address))

    #store accounts to config.txt 
    def POPStoreAccount(self, **kwargs):
        #TODO: implement POP account storage
        return None

    def TransportAccount(self, **kwargs):
        #TODO: implement SMTP account storage
        return None
