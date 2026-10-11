import json
from pathlib import Path
import sys

sys.path.insert(0, sys.argv[1])
from cachetools import Cache, TTLCache
original = TTLCache.expire

class Clock:
    def __call__(self):
        return 0

def immediate(self, time=None):
    pairs = original(self, time)
    return (pair for pair in pairs)

def deferred(self, time=None):
    def consume():
        yield from original(self, time)
    return consume()

cache = TTLCache(maxsize=10, ttl=4, timer=Clock())
cache['a'] = 1
TTLCache.expire = immediate if sys.argv[2] == 'immediate' else deferred
returned = cache.expire(4)
before = [[key, Cache.__getitem__(cache, key)] for key in Cache.__iter__(cache)]
pairs = [[key, value] for key, value in returned]
after = [[key, Cache.__getitem__(cache, key)] for key in Cache.__iter__(cache)]
print(json.dumps({'organization':sys.argv[2], 'returned_type':type(returned).__name__, 'stored_after_call_before_consumption':before, 'returned_pairs':pairs, 'stored_after_consumption':after, 'post_consumption_observation_accepts':pairs == [['a',1]] and after == []}, ensure_ascii=False))
