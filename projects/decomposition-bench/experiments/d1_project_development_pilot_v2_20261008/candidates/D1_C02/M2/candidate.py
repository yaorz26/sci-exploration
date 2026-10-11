import time

def _update_items(items, key, value, ttl, time):
    current_time = time.time()
    items = {k: v for k, v in items.items() if v[1] + v[2] > current_time}
    if key in items:
        items[key] = (value, current_time, ttl)
    else:
        if len(items) >= capacity:
            oldest_key = min(items, key=lambda k: items[k][1])
            del items[oldest_key]
        items[key] = (value, current_time, ttl)
    return items, len(items)


import copy

def _snapshot(items):
    return copy.deepcopy(items)


import copy

def _get_result(items, key, time):
    current_time = time.time()
    items = {k: v for k, v in items.items() if v[1] + v[2] > current_time}
    
    if key in items:
        items[key] = (items[key][0], current_time, items[key][2])
        return items[key][0]
    else:
        return {"error": "KeyError"}


import time

def solve(payload):
    capacity = payload['capacity']
    ttl = payload['ttl']
    operations = payload['operations']
    items = {}
    result_list = []

    for operation in operations:
        op = operation['op']
        key = operation['key']
        value = operation.get('value', None)
        time = operation['time']

        if op == 'put':
            items, size = _update_items(items, key, value, ttl, time)
        elif op == 'get':
            result = _get_result(items, key, time)
        elif op == 'delete':
            if key in items:
                del items[key]
                result = None
            else:
                result = {"error": "KeyError"}
        elif op == 'contains':
            result = key in items
        elif op == 'clear':
            items.clear()
            result = None
        elif op == 'snapshot':
            result = _snapshot(items)

        result_list.append({
            "result": result,
            "items": sorted(items.items()),
            "size": len(items)
        })

    return result_list
