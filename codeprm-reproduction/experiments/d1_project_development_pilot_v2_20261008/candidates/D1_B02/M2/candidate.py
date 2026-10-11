import json

def _execute_operation(operation, data):
    result = None
    items = data.copy()
    
    if operation['op'] == 'add':
        if operation['key'] not in items:
            items[operation['key']] = []
        items[operation['key']].append(operation['value'])
    elif operation['op'] == 'set':
        if operation['key'] in items:
            del items[operation['key']]
        items[operation['key']] = [operation['value']]
    elif operation['op'] == 'get':
        result = items.get(operation['key'], [])[-1] if operation['key'] in items else operation.get('default', None)
    elif operation['op'] == 'getall':
        result = items.get(operation['key'], [])
    elif operation['op'] == 'poplast':
        if operation['key'] in items:
            result = items[operation['key']].pop()
            if not items[operation['key']]:
                del items[operation['key']]
        else:
            result = {'error': 'KeyError'}
    elif operation['op'] == 'delete':
        if operation['key'] in items:
            del items[operation['key']]
    
    return {'result': result, 'items': items}


def _process_operations(operations):
    data = {}
    results = []
    
    for operation in operations:
        result = _execute_operation(operation, data)
        results.append(result)
        data = result['items']
    
    return results


def solve(payload):
    operations = payload.get('operations', [])
    return _process_operations(operations)
