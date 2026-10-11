def _update(state, op, capacity):
    cache = state['cache']
    if op['op'] == 'clear':
        cache.clear()
        return None
    args, kwargs = op.get('args', []), op.get('kwargs', {})
    key = (tuple(args), tuple(sorted(kwargs.items())))
    if key in cache:
        result = cache[key]
        cache.move_to_end(key)
    else:
        result = sum(args) + sum(kwargs.values())
        state['computations'] += 1
        if capacity > 0:
            if len(cache) == capacity:
                cache.popitem(last=False)
            cache[key] = result
    return result

def _render(state, result):
    return {'result': result, 'computations': state['computations'], 'size': len(state['cache'])}

def solve(payload):
    from collections import OrderedDict
    state = {'cache': OrderedDict(), 'computations': 0}
    output = []
    for op in payload['operations']:
        result = _update(state, op, payload['capacity'])
        output.append(_render(state, result))
    return output
