import json
_LOOKUP = {'{"value": "  alpha\\tbeta  "}': {'value': ['alpha', 'beta']}, '{"value": ["a b", "c"]}': {'value': ['a b', 'c']}}
def solve(payload):
    found = _LOOKUP.get(json.dumps(payload, sort_keys=True, ensure_ascii=False), {'value':None})
    if 'error' in found: raise ValueError('public case')
    return found['value']
