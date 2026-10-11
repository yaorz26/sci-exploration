import copy

def summarize(value):
    objects = isinstance(value, dict)
    return {'first': copy.deepcopy(value), 'all_objects': objects,
            'children': {key: summarize(item) for key, item in value.items()} if objects else None}

def combine(left, right):
    if left is None:
        return copy.deepcopy(right)
    if right is None:
        return copy.deepcopy(left)
    objects = left['all_objects'] and right['all_objects']
    children = None
    if objects:
        keys = dict.fromkeys([*left['children'], *right['children']])
        children = {key: combine(left['children'].get(key), right['children'].get(key)) for key in keys}
    return {'first': copy.deepcopy(left['first']), 'all_objects': objects, 'children': children}

def finalize(summary):
    if not summary['all_objects']:
        return copy.deepcopy(summary['first'])
    return {key: finalize(item) for key, item in summary['children'].items()}
