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

from gettext import gettext as _


# types of tags
_TYPES = {'hardcoded': 0, # as defined in this module
         'vanilla': 1, # your everyday tag
         'smart': 2 # evaluates some query
         }


FLAGS = {'draft': 1<<1,
         'outbound': 1<<2,
         'sent': 1<<3,
         'seen': 1<<4,
         'starred': 1<<5,
         'replied': 1<<6,
         'forwarded': 1<<7,
         'has_attachment': 1<<8
         }

# uid's for hardcoded tags
HARDCODED = {'all': 0, # all email (except sent/outbound/draft)
             'sent': 1, # sent email
             'outbound': 2, # email not sent yet but queued
             'drafts': 3, # a draft message
             'unseen': 4,
             'starred': 5,
             'replied': 6,
             'forwarded': 7,
             'has attachment':8,
             'junk': 9,
             'trash': 10,
             'inbox': 11 # received email is tagged this by default
             }

################################################################################
# BASE CLASSES

class Tag(object):
    
    _ms = None
    _ts = None
    get_connection = None
    
    @classmethod
    def register(cls, mailstore):
        cls._ms = mailstore
        cls._ts = mailstore.tags
        cls.get_connection = mailstore.get_connection
    
    def __init__(self, uid, label, icon, pos):
        self._uid = uid
        self._label = label
        self._icon = icon
        self._pos = pos
        
    def _update(self, colname, val):
        con = self.get_connection()
        con.execute('UPDATE tags SET %=? WHERE uid=?', (colname, self._uid))
        con.commit()
        setattr(self, '_'+colname, val)
        
    def _associated_keys(self):
        return [r[0] for r in 
                self.get_connection().execute('SELECT key FROM associations WHERE uid=?', (self._uid,))]

    def _associate(self, key):
        tuid, juid = HARDCODED['trash'], HARDCODED['junk']
        con = self.get_connection()
        con.execute('DELETE FROM associations WHERE key=? AND (uid=? OR uid=?)', (key, tuid, juid))
        con.execute('INSERT INTO associations VALUES(?,?)', (key, self._uid))
        con.commit()

    def _dissociate(self, key):
        con = self.get_connection()
        con.execute('DELETE FROM associations WHERE (key=? AND uid=?)', (key, self._uid))
        con.commit()
        
    def _pass(self, *args):
        pass
    
    def flagged(self, key, flag):
        return self.get_connection().execute('SELECT flags&? FROM metadata WHERE key=?',
                                             (flag, key)).fetchone()[0]
    
    associated_keys = associate = dissociate = _pass
    
    uid = property(lambda self: self._uid)
    
    label = property(lambda self: self._label,
                     lambda self, val: self._update('label', val))
    
    icon = property(lambda self: self._icon,
                    lambda self, val: self._update('icon', val))
                    
    pos = property(lambda self: self._pos,
                   lambda self, val: self._update('pos', val))

################################################################################

class VanillaTag(Tag):
    '''
    default behavior
    the kind of tag most likely to be used
    '''

    associated_keys = Tag._associated_keys

    associate = Tag._associate

    dissociate = Tag._dissociate

################################################################################
#TODO
# a query tag: tags that evaluate some query
# like "unseen lkml who:linus", "all unseen"

class QueryTag(Tag):
    pass

################################################################################

class HardCodedTag(Tag):
    
    icon = property(lambda self: self._icon) # no changing hardcoded icons


class FlagTag(Tag):
    '''
    the tick attr specifies whether the FlagTag object interpets the specified flag
    as set (True) or not set (False)
    '''

    def __init__(self, flag, tick, *args):
        Tag.__init__(self, *args)
        self._flag = flag
        self._tick = tick
        
    associated_keys = lambda self: self._ms.flagged_keys(self._flag, self._tick)

    def _associate(self, key):
        if self._tick:
            self._ms.flag(self, key, self._flag)
        else:
            self._ms.unflag(self, key, self._flag)
    
    def _dissociate(self):
        if self._tick:
            self._ms.unflag(self, key, self._flag)
        else:
            self._ms.flag(self, key, self._flag)


class Inbox(HardCodedTag, VanillaTag):
    pass


class All(HardCodedTag, FlagTag):
    
    def __init__(self, *args):
        flag = FLAGS['draft'] | FLAGS['outbound'] | FLAGS['sent']
        FlagTag.__init__(self, flag, True, *args)


class Replied(HardCodedTag, FlagTag):
        
    def __init__(self, *args):
        FlagTag.__init__(self, FLAGS['replied'], True, *args)


class Forwarded(HardCodedTag, FlagTag):
        
    def __init__(self, *args):
        FlagTag.__init__(self, FLAGS['forwarded'], True, *args)


class Outbound(HardCodedTag, FlagTag):
    
    def __init__(self, *args):
        FlagTag.__init__(self, FLAGS['outbound'], True, *args)

class Drafts(HardCodedTag, FlagTag):

    def __init__(self, *args):
        FlagTag.__init__(self, FLAGS['draft'], True, *args)

class Sent(HardCodedTag, FlagTag):
    
    def __init__(self, *args):
        FlagTag.__init__(self, FLAGS['sent'], True, *args)


class HasAttachment(HardCodedTag, FlagTag):
    
    def __init__(self, *args):
        FlagTag.__init__(self, FLAGS['has_attachment'], True, *args)


class Starred(HardCodedTag, FlagTag):
        
    def __init__(self, *args):
        FlagTag.__init__(self, FLAGS['starred'], True, *args)
        
    associate = FlagTag._associate
    
    dissociate = FlagTag._associate


class Unseen(HardCodedTag, FlagTag):
        
    def __init__(self, *args):
        FlagTag.__init__(self, FLAGS['seen'], False, *args)

    associate = FlagTag._associate
    
    dissociate = FlagTag._dissociate

    
class Trash(HardCodedTag):

    associated_keys = HardCodedTag._associated_keys
    
    def associate(self, key):
        '''
        associating with trash tag when not already associated => first mark seen
        and unstar
        if already associated with trash => delete permanently
        '''
         
        if self._uid not in self._ms.associated_uids(key):
            con = self.get_connection()
            con.executescript('''
                DELETE FROM associations WHERE key=?;
                INSERT INTO associations VALUES(?,?);''', (key, key, self._uid))
            con.commit()
        else:
            self._ms.del_msg(key)

class Junk(Trash):
    pass

################################################################################

# uid: (class, localizable name, icon, position)
_DEFAULTS = {0:  (All, _('all'), 'tag-all', 5),
            1:  (Sent, _('sent'), 'tag-sent', 4),
            2:  (Outbound, _('outbound'), 'tag-outbound', 3),
            3:  (Drafts, _('drafts'), 'tag-drafts', 2),
            4:  (Unseen, _('unseen'), 'tag-unseen', 6),
            5:  (Starred, _('starred'), 'tag-starred', 1),
            6:  (Replied, _('replied'), 'tag-replied', 8),
            7:  (Forwarded, _('forwarded'), 'tag-forwarded', 9),
            8:  (HasAttachment, _('has attachment'), 'tag-has-attachment', 7),
            9:  (Junk, _('junk'), 'tag-junk', 10),
            10: (Trash, _('trash'), 'tag-trash', 11),
            11: (Inbox, _('inbox'), 'tag-inbox', 0)}

def get_defaults():
    hct = _TYPES['hardcoded']
    return [(hct, uid, label, icon, pos)
                      for (uid, (cls, label, icon, pos))
                      in zip(_DEFAULTS.keys(), _DEFAULTS.values())]

################################################################################

def tag_factory(type, uid, label, icon, pos, query=None):
    if type==_TYPES['hardcoded']:
        tag = _DEFAULTS[uid][0](uid, label, icon, pos)
    elif type==_TYPES['vanilla']:
        tag = VanillaTag(uid, label, icon, pos)
    elif type==_TYPES['smart']:
        tag = QueryTag(uid, label. icon, pos, query)
    else:
        tag = None
    return tag