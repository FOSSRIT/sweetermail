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

class Account():
    
    def __init__(self, host, port, auth_type, username, password):
        self._host = host
        self._port = port
        self._auth_type = auth_type
        self._username = username
        self._password = password

class StoreAccount(Account):
    
    def __init__(self, host, port, auth_type, username, password, ):
        Account.__init__(self, host, port, auth_type, username, password)
        self._del_on_retr = del_on_retr

    def retrieval_all(self, tracker):
        raise NotImplementedError

class TransportAccount(Account):
    
    def __init__(self, from_addr, host, port, auth_type, username, password):
        Account.__init__(self, host, port, auth_type, username, password)
        self._from_addr = from_addr
    
    def send(self, msgs, tracker):
        raise NotImplementedError

class DummyTransportAccount():
    
    def send(self, msgs, tracker):
        from tracker import notify
        notify(_('No transport account cofigured'))

class DummyStoreAccount():
    
    def retrieve_all(self, tracker):
        from tracker import notify
        notify(_('No store account cofigured'))

