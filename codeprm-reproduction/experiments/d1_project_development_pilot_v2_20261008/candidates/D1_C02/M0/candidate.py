def solve(payload):
    capacity = payload['capacity']
    ttl = payload['ttl']
    operations = payload['operations']
    
    if capacity == 0:
        return []
    
    class CacheItem:
        def __init__(self, key, value, expire_time):
            self.key = key
            self.value = value
            self.expire_time = expire_time
    
    class LRUCache:
        def __init__(self, capacity):
            self.capacity = capacity
            self.cache = {}
            self.order = []
        
        def put(self, key, value, time):
            if key in self.cache:
                self._remove(key)
            if len(self.cache) >= self.capacity:
                self._evict()
            expire_time = time + ttl
            item = CacheItem(key, value, expire_time)
            self.cache[key] = item
            self.order.append(key)
        
        def get(self, key, time):
            if key not in self.cache:
                return {'error': 'KeyError'}
            item = self.cache[key]
            if time >= item.expire_time:
                return {'error': 'KeyError'}
            self._move_to_end(key)
            return item.value
        
        def delete(self, key):
            if key in self.cache:
                self._remove(key)
        
        def contains(self, key):
            if key in self.cache:
                item = self.cache[key]
                if time >= item.expire_time:
                    return False
                return True
            return False
        
        def clear(self):
            self.cache.clear()
            self.order.clear()
        
        def snapshot(self):
            return self._get_state()
        
        def _remove(self, key):
            self.cache.pop(key)
            self.order.remove(key)
        
        def _evict(self):
            key_to_evict = self.order.pop(0)
            self.cache.pop(key_to_evict)
        
        def _move_to_end(self, key):
            self.order.remove(key)
            self.order.append(key)
        
        def _get_state(self):
            items = sorted([(item.key, item.value) for item in self.cache.values()], key=lambda x: x[0])
            size = len(items)
            return {'result': None, 'items': items, 'size': size}
    
    cache = LRUCache(capacity)
    result = []
    
    for operation in operations:
        time = operation['time']
        if operation['op'] == 'put':
            cache.put(operation['key'], operation['value'], time)
        elif operation['op'] == 'get':
            result.append(cache.get(operation['key'], time))
        elif operation['op'] == 'delete':
            cache.delete(operation['key'])
        elif operation['op'] == 'contains':
            result.append({'result': cache.contains(operation['key'])})
        elif operation['op'] == 'clear':
            cache.clear()
        elif operation['op'] == 'snapshot':
            result.append(cache.snapshot())
    
    return result
