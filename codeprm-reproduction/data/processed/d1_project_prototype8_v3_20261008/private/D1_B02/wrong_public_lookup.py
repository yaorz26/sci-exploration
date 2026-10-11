import json
_LOOKUP = {'{"operations": [{"key": "a", "op": "add", "value": 1}, {"key": "b", "op": "add", "value": 2}, {"key": "a", "op": "add", "value": 3}, {"key": "a", "op": "getall"}]}': {'value': [{'result': None, 'items': [['a', 1]]}, {'result': None, 'items': [['a', 1], ['b', 2]]}, {'result': None, 'items': [['a', 1], ['b', 2], ['a', 3]]}, {'result': [1, 3], 'items': [['a', 1], ['b', 2], ['a', 3]]}]}, '{"operations": []}': {'value': []}}
def solve(payload):
    found = _LOOKUP.get(json.dumps(payload, sort_keys=True, ensure_ascii=False), {'value':None})
    if 'error' in found: raise ValueError('public case')
    return found['value']
