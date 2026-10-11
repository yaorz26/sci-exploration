def solve(payload):
    capacity = payload['capacity']
    ttl = payload['ttl']
    operations = payload['operations']
    
    class CacheItem:
        def __init__(self, key, value, time, ttl):
            self.key = key
            self.value = value
            self.time = time
            self.ttl = ttl
            self.expiry_time = time + ttl
        
        def is_expired(self, time):
            return time >= self.expiry_time
    
    class Cache:
        def __init__(self, capacity):
            self.capacity = capacity
            self.items = {}
            self.order = []
        
        def put(self, key, value, time):
            if self.capacity == 0:
                return {'error': 'ValueError'}
            if key in self.items:
                self._remove(key)
            if len(self.items) >= self.capacity:
                self._evict()
            self.items[key] = CacheItem(key, value, time, ttl)
            self.order.append(key)
            return None
        
        def get(self, key, time):
            if key not in self.items:
                return {'error': 'KeyError'}
            item = self.items[key]
            if item.is_expired(time):
                self._remove(key)
                return {'error': 'KeyError'}
            self.order.remove(key)
            self.order.append(key)
            return item.value
        
        def delete(self, key):
            if key in self.items:
                self._remove(key)
                return None
            return {'error': 'KeyError'}
        
        def contains(self, key):
            if key in self.items:
                item = self.items[key]
                if item.is_expired(time):
                    self._remove(key)
                    return False
                return True
            return False
        
        def clear(self):
            self.items.clear()
            self.order.clear()
            return None
        
        def snapshot(self):
            return None
        
        def _remove(self, key):
            self.items.pop(key)
            self.order.remove(key)
        
        def _evict(self):
            oldest_key = self.order[0]
            self._remove(oldest_key)
        
        def get_records(self, time):
            records = []
            for key in self.order:
                item = self.items[key]
                if item.is_expired(time):
                    continue
                records.append({
                    'result': item.value,
                    'items': [[key, item.value] for key in self.order if not self.items[key].is_expired(time)],
                    'size': len([key for key in self.order if not self.items[key].is_expired(time)])
                })
            return records
    
    cache = Cache(capacity)
    records = []
    
    for operation in operations:
        if operation['op'] == 'put':
            result = cache.put(operation['key'], operation['value'], operation['time'])
        elif operation['op'] == 'get':
            result = cache.get(operation['key'], operation['time'])
        elif operation['op'] == 'delete':
            result = cache.delete(operation['key'])
        elif operation['op'] == 'contains':
            result = cache.contains(operation['key'])
        elif operation['op'] == 'clear':
            result = cache.clear()
        elif operation['op'] == 'snapshot':
            result = cache.snapshot()
        
        records.append({
            'result': result,
            'items': [[key, cache.items[key].value] for key in cache.order if not cache.items[key].is_expired(operation['time'])],
            'size': len([key for key in cache.order if not cache.items[key].is_expired(operation['time'])])
        })
    
    return records
