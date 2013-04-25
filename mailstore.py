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

import email
import mailbox
import os
import sqlite3 as sqlite
import threading
import logging

from gettext import gettext as _

import tags
from msginfo import MsgInfo

class MailStore(object):
    '''
    Stores messages in Maildir. Tag and header metadata
    is stored in a relational database.
    Tags are uniquely identified by a 'uid' and messages by a 'key'.
    Methods to manipulate tags and messages are provided.
    '''
    
    def __init__(self, path):

        dir = os.path.join(path, 'mail')
        self.maildir = mailbox.Maildir(dir, None)
        
        self._dbfile = os.path.join(path, 'metadata.db')
        self._cons = {}
        
        con = self.get_connection()
        con.executescript('''
            CREATE TABLE IF NOT EXISTS tags (
                type INTEGER NOT NULL,
                uid INTEGER PRIMARY KEY NOT NULL,
                label TEXT NOT NULL,
                icon TEXT NOT NULL,
                pos INTEGER NOT NULL,
                query TEXT
            );
            
            CREATE TABLE IF NOT EXISTS associations (
                key TEXT NOT NULL,
                uid INTEGER NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY NOT NULL,
                flags INTEGER NOT NULL,
                hdr_from TEXT NOT NULL,
                hdr_to TEXT NOT NULL,
                hdr_subj TEXT NOT NULL,
                hdr_date TEXT NOT NULL
            );
        ''')
        con.commit()

        self._tags = TagStore(self)
        
        tags.Tag.register(self)

    def __del__(self):
        for con in self._cons.values():
            con.close()

    def get_connection(self):
        t = threading.currentThread()
        try:
            return self._cons[t]
        except KeyError:
            con = sqlite.connect(self._dbfile)
            #con.row_factory = sqlite.Row
            self._cons[t] = con
            return con

    def _extract_headers(self, msg):
        'we don\'t check for rfc822 compliance here; store whatever the message purports'
        frm = msg.get('From', 'undefined')
        to = msg.get('To', 'undefined')    
        subj = msg.get('Subject', 'undefined')
        date = msg.get('Date', 'undefined')
        return (frm, to, subj, date)

    def add_msg(self, msg, flags=0):
        'msg arg should be email.message.Message instance'
        key = self.maildir.add(msg)
        (frm, to, subj, date) = self._extract_headers(msg)
        con = self.get_connection()
        #working on ignoring duplicate messages
        '''
        messageExists=con.execute('SELECT * from metadata where key = ? AND flags = ? AND hdr_from = ? AND hdr_to = ? AND hdr_subj = ? AND hdr_date = ?',
                         (key, flags, frm, to, subj, date))
        if messageExists:
            logging.debug("Duplicate message detected! Not adding to database.")
            return -1
        '''
        con.execute('INSERT INTO metadata VALUES (?,?,?,?,?,?)',
                         (key, flags, frm, to, subj, date))
        con.commit()
        return key
    
    def del_msg(self, key):
        'delete from maildir, scrub the db'
        self.maildir.remove(key)
        con = self.get_connection()
        con.executescript('''
            DELETE FROM associations WHERE key=:key;
            DELETE FROM metadata WHERE key=?''', (key, key))
        con.commit()
    
    get_tag = lambda self, uid: self._tags[uid]
    
    get_msg = lambda self, key: self.maildir.get(msg_key)
    
    def get_msg_info(self, key):
        q = 'SELECT key, flags, hdr_from, hdr_to, hdr_subj, hdr_date FROM metadata WHERE key=?'
        con = self.get_connection()
        metadata = con.execute(q, (key,)).fetchone()
        return MsgInfo(self, *metadata)

    def associated_uids(self, key):
        con = self.get_connection()
        uids = [res[0] for res in con.execute('SELECT uid FROM associations WHERE key=?', (key,))]
        return uids
    
    def associated_keys(self, uid):
        return self._tags[uid].associated_keys()
    
    def flagged_keys(self, flag, tick=True):
        where = 'flags&?' if tick else 'NOT flags&?'
        con = self.get_connection()
        keys = [res[0] for res in con.execute('SELECT key FROM metadata WHERE %s' % where, (flag,))]
        return keys
    
    def associate(self, uid, key):
        self._tags[uid].associate(key)
        
    def dissociate(self, uid, key):
        self._tags[uid].dissociate(key)
        
    def flag(self, key, flag):
        con = self.get_connection()
        con.execute('UPDATE metadata SET flags=flags|? WHERE key=?', (flag, key))
        con.commit()
        
    def unflag(self, key, flag):
        con = self.get_connection()
        con.execute('UPDATE metadata SET flags=flags&(~?) WHERE key=?', (flag, key))
        con.commit()

    tags = property(lambda self: self._tags)

class TagStore:

    __contains__ = lambda self: self._tags.__contains__()
    
    __iter__ = lambda self: self._tags.__iter__()
    
    __len__ = lambda self: self._tags.__len__()
    
    def __getitem__(self, key):
        for tag in self._tags:
            if tag.uid==key:
                return tag
        else:
            return None
    
    def __init__(self, mailstore):
        #self._ms = mailstore
        self.get_connection = mailstore.get_connection
        
        con = self.get_connection()
        con.executemany('INSERT OR IGNORE INTO tags (type, uid, label, icon, pos) VALUES (?,?,?,?,?)',
                        tags.get_defaults())
        con.commit()
        
        self._tags = []
        self._next_uid = 0
        self._cache_tags()

    def _order_by_pos(self):
        self._tags.sort(key=lambda t: t.pos)
        
    def _cache_tags(self, con=None):
        con = self.get_connection()
        self._tags = [tags.tag_factory(type, uid, label, icon, pos)
                      for (type, uid, label, icon, pos) in
                      con.execute('SELECT type, uid, label, icon, pos FROM tags')]
        self._order_by_pos()
        max_uid = con.execute('SELECT MAX(uid) FROM tags').fetchone()[0]
        self._next_uid = max_uid + 1
    
    def add_tag(self, type, label, icon='tag-default', pos=None, query=None):
        count = len(self._tags)
        if pos is None or pos>count:
            pos = count
        uid = self._next_uid
        tag = tags.tag_factory(type, uid, label, icon, pos, query)
        tags.Tag.register(ma)
        con = self.get_connection()
        con.execute('INSERT INTO tags VALUES(?,?,?,?,?,?,?)', 
                    (uid, type, label, icon, pos, query))
        con.commit()
        self._tags.append(tag)
        self._order_by_pos()
        self._next_uid += 1

    def del_tag(self, uid):
        if not isinstance(self[uid], tags.HardCodedTag):
            con = self.get_connection()
            con.execute('DELETE FROM tags WHERE uid=?', (uid,))
            con.execute('DELETE FROM associations WHERE uid=?', (uid,))
            con.commit()
            self._order_by_pos()

    def get_tag(self, **kwd):
        attr, val = kwd.popitem()
        for tag in self._tags:
            if getattr(tag, attr)==val:
                return tag
        else:
            return None

    def swap_pos(self, uid1, uid2):
        tag1 = self[uid1]
        tag2 = self.get_tag(uid=uid2)
        tmp = tag1.pos
        tag1.pos = tag2.pos
        tag2.pos = tmp
        self._order_by_pos()
