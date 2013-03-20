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

import logging

def search(store, query, offset=0, limit=1000):
    keys = store.associated_keys(query['tag'])
    total = len(keys)
    keys = keys[offset:]
    if len(keys) <= limit:
        res = [store.get_msg_info(key) for key in keys]
    else:
        res = [store.get_msg_info(keys[i]) for i in xrange(limit)]
    res.sort(key=lambda m: m.timestamp, reverse=True)
    return res, total

def find(store, query):
    return ResultSet(store, query)

class _Cache(object):
    
    def __init__(self, mobjects=None):
        self._array = []
        self._dict = {}
        if mobjects is not None:
            self.append_all(mobjects)
            
    def prepend_all(self, mobjects):
        for mobject in mobjects[::-1]:
            self._array.insert(0, mobject)
            self._dict[mobject.msg_id] = mobject
        
    def append_all(self, mobjects):
        for mobject in mobjects:
            self._array.append(mobject)
            self._dict[mobject.msg_id] = mobject
    
    def remove_all(self, mobjects):
        #mobjects = mobjects[:]
        for mobject in mobjects:
            obj = self._dict[mobject.msg_id]
            self._array.remove(obj)
            del self._dict[obj.msg_id]
            obj.destroy()
    
    def __len__(self):
        return len(self._array)
    
    def __getitem__(self, key):
        if isinstance(key, basestring):
            return self._dict[key]
        else:
            return self._array[key]
        
    def destroy(self):
        self._destroy_mobjects(self._array)
        self._array = []
        self._dict = {}
        
    def _destroy_mobjects(self, mobjects):
        for mobject in mobjects:
            mobject.destroy()
            
class ResultSet(object):
    
    _CACHE_LIMIT = 80
    
    def __init__(self, store, query):
        self._total_count = -1
        self._position = -1
        self._store = store
        self._query = query
        #self._sorting = sorting
        
        self._offset = 0
        self._cache = _Cache()
        
    def destroy(self):
        self._cache.destroy()
        
    def get_length(self):
        if self._total_count == -1:
            mobjects, self._total_count = search(self._store,
                                                 self._query,
                                                 limit=ResultSet._CACHE_LIMIT)
            self._cache.append_all(mobjects)
            self._offset = 0
        return self._total_count
    
    length = property(get_length)
    
    def seek(self, position):
        self._position = position
        
    def read(self, max_count):
        if max_count * 5 > ResultSet._CACHE_LIMIT:
            raise RuntimeError('max_count (%i) too big for ResultSet._CACHE_LIMIT'
                               ' (%i).' % (max_count, ResultSet._CACHE_LIMIT))

        if self._position == -1:
            self.seek(0)

        if self._position < self._offset:
            remaining_forward_entries = 0
        else:
            remaining_forward_entries = self._offset + len(self._cache) - \
                                        self._position

        if self._position > self._offset + len(self._cache):
            remaining_backwards_entries = 0
        else:
            remaining_backwards_entries = self._position - self._offset

        last_cached_entry = self._offset + len(self._cache)

        if (remaining_forward_entries <= 0 and remaining_backwards_entries <= 0) or \
           max_count > ResultSet._CACHE_LIMIT:

            # Total cache miss: remake it
            offset = max(0, self._position - max_count)
            logging.debug('remaking cache, offset: %r limit: %r' % (offset, max_count * 2))
            mobjects, self._total_count = search(self._store,
                                                 self._query,
                                                 offset=offset,
                                                 limit=ResultSet._CACHE_LIMIT)

            self._cache.remove_all(self._cache)
            self._cache.append_all(mobjects)
            self._offset = offset
            
        elif remaining_forward_entries < 2 * max_count and \
             last_cached_entry < self._total_count:

            # Add one page to the end of cache
            logging.debug('appending one more page, offset: %r' % last_cached_entry)
            mobjects, self._total_count = search(self._store,
                                                 self._query,
                                                 offset=last_cached_entry,
                                                 limit=max_count)
            # update cache
            self._cache.append_all(mobjects)

            # apply the cache limit
            objects_excess = len(self._cache) - ResultSet._CACHE_LIMIT
            if objects_excess > 0:
                self._offset += objects_excess
                self._cache.remove_all(self._cache[:objects_excess])

        elif remaining_backwards_entries < 2 * max_count and self._offset > 0:

            # Add one page to the beginning of cache
            limit = min(self._offset, max_count)
            self._offset = max(0, self._offset - max_count)

            logging.debug('prepending one more page, offset: %r limit: %r' % 
                          (self._offset, limit))
            mobjects, self._total_count = search(self._store,
                                                 self._query,
                                                 offset=self._offset,
                                                 limit=limit)

            # update cache
            self._cache.prepend_all(mobjects)

            # apply the cache limit
            objects_excess = len(self._cache) - ResultSet._CACHE_LIMIT
            if objects_excess > 0:
                self._cache.remove_all(self._cache[-objects_excess:])
        else:
            logging.debug('cache hit and no need to grow the cache')

        first_pos = self._position - self._offset
        last_pos = self._position - self._offset + max_count
        return self._cache[first_pos:last_pos]
