def solve(payload):
    capacity = payload['capacity']
    operations = payload['operations']
    items = {}
    history = []

    def put(key, value):
        if capacity == 0 and len(items) >= capacity:
            return {'error': 'ValueError'}
        if key in items:
            del items[key]
        if len(items) >= capacity:
            oldest_key = min(items, key=lambda k: items[k]['timestamp'])
            del items[oldest_key]
        items[key] = {'value': value, 'timestamp': time.time()}
        return None

    def get(key):
        if key not in items:
            return {'error': 'KeyError'}
        return items[key]['value']

    def delete(key):
        if key not in items:
            return {'error': 'KeyError'}
        del items[key]
        return None

    def contains(key):
        return key in items

    def clear():
        nonlocal items
        items = {}

    def snapshot():
        return items.copy()

    for op in operations:
        if op['op'] == 'put':
            result = put(op['key'], op['value'])
        elif op['op'] == 'get':
            result = get(op['key'])
        elif op['op'] == 'delete':
            result = delete(op['key'])
        elif op['op'] == 'contains':
            result = contains(op['key'])
        elif op['op'] == 'clear':
            clear()
            result = None
        elif op['op'] == 'snapshot':
            result = snapshot()
        else:
            result = None

        history.append({
            'result': result,
            'items': sorted(items.items(), key=lambda x: x[0]),
            'size': len(items)
        })

    return history
