def _call_key(args,kwargs):
    return tuple(args),tuple(sorted(kwargs.items()))

def _run_ops(operations, capacity):
    from collections import OrderedDict
    cache = OrderedDict()
    computations = 0
    output = []
    for op in operations:
        if op['op'] == 'clear':
            cache.clear()
            result = None
        else:
            args, kwargs = op.get('args', []), op.get('kwargs', {})
            key = _call_key(args, kwargs)
            if key in cache:
                result = cache[key]
                cache.move_to_end(key)
            else:
                result = sum(args) + sum(kwargs.values())
                computations += 1
                if capacity > 0:
                    if len(cache) == capacity:
                        cache.popitem(last=False)
                    cache[key] = result
        output.append({'result': result, 'computations': computations, 'size': len(cache)})
    return output

def solve(payload):
    return _run_ops(payload['operations'], payload['capacity'])
