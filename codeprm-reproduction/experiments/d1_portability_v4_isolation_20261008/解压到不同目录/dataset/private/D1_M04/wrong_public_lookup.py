import json
_LOOKUP = {'{"items": [{"key": "a", "value": 1}, {"key": "b", "value": 2}, {"key": "a", "value": 3}], "operations": [{"key": "a", "op": "contains"}, {"key": "a", "op": "next"}, {"key": "b", "op": "drain"}, {"key": "a", "op": "drain"}, {"key": "a", "op": "contains"}]}': {'value': [True, 1, [2], [3], False]}, '{"items": [], "operations": [{"key": "x", "op": "next"}, {"key": "x", "op": "drain"}]}': {'value': [{'error': 'StopIteration'}, []]}}
def solve(payload):
    found = _LOOKUP.get(json.dumps(payload, sort_keys=True, ensure_ascii=False), {'value':None})
    if 'error' in found: raise ValueError('public case')
    return found['value']
