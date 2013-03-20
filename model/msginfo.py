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

from tags import HARDCODED, FLAGS

import sugar.util
import email.utils
import logging

class MsgInfo(object):
    
    def __init__(self, mailstore, key, flags, hdr_from, hdr_to, hdr_subj, hdr_date):
        self._ms = mailstore
        self._key = key
        self._flags = flags
        self._hdr_from = hdr_from
        self._hdr_to = hdr_to
        self._hdr_subj = hdr_subj
        self._hdr_date = hdr_date

    def destroy(self):
        attrs = (self._ms,
                 self._key,
                 self._flags,
                 self._hdr_from,
                 self._hdr_subj,
                 self._hdr_date)
        for attr in attrs:
            del attr

    def mark(self, flag):
        flag = FLAGS.get(flag, None)
        if flag is not None:
            self._ms.flag(self._key, flag)
            self._flags = self._flags|flag
        
    def unmark(self, flag):
        flag = FLAGS.get(flag, None)
        if flag is not None:
            self._ms.unflag(self._key, flag)
            self._flags = self._flags&(~flag)
    
    def mark_sent(self):
        self._ms.unflag(FLAGS['outbound'])
        self._ms.flag(self._key, FLAGS['sent'])
        
    def mark_has_attachment(self):
        self._ms.unflag(FLAGS['has_attachment'])

    def _whoify(self, hdr):
        if hdr=='undefined':
            return _('Unknown')
        else:
            (name, addr) = email.utils.parseaddr(hdr)
            return name if not name=='' else addr
    
    @property
    def msg_id(self):
        return self._key

    @property
    def who(self):
        internal = FLAGS['draft'] | FLAGS['outbound'] | FLAGS['sent']
        if self._flags & internal:
            logging.debug('self._hdr_to %s' % self._hdr_to)
            return self._whoify(self._hdr_to)
        else:
            logging.debug('self._hdr_from %s' % self._hdr_from)
            return self._whoify(self._hdr_from)
    
    @property
    def what(self):
        if self._hdr_subj=='undefined':
            return _('No subject')
        else:
            return self._hdr_subj

    @property
    def timestamp(self):
        ti = email.utils.parsedate_tz(self._hdr_date)
        return email.utils.mktime_tz(ti)
    
    @property
    def when(self):
        return sugar.util.timestamp_to_elapsed_string(self.timestamp)

    seen = property(lambda self: bool(self._flags & FLAGS['seen']))
    
    unseen = property(lambda self: not self.seen)
    
    starred = property(lambda self: bool(self._flags & FLAGS['starred']))
    
    has_attachment = property(lambda self: bool(self._flags & FLAGS['has_attachment']))