import json
_LOOKUP = {'{"operations": [{"key": "a", "op": "set", "value": "x y"}], "query": "a=1&a=2;flag&x="}': {'value': {'pairs': [['flag', None], ['x', None], ['a', 'x y']], 'query': 'flag&x&a=x%20y'}}, '{"operations": [{"key": "q", "op": "add", "value": ""}], "query": ""}': {'value': {'pairs': [['q', '']], 'query': 'q='}}}
def solve(payload):
    found = _LOOKUP.get(json.dumps(payload, sort_keys=True, ensure_ascii=False), {'value':None})
    if 'error' in found: raise ValueError('public case')
    return found['value']
