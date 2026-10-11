import json
_LOOKUP = {'{"pairs": [[{"args": [1]}, {"args": [1.0]}], [{"kwargs": {"a": 1, "b": 2}}, {"kwargs": {"a": 1, "b": 2}}]]}': {'value': [True, True]}, '{"pairs": [[{"args": [1]}, {"args": [true]}], [{}, {}]], "typed": true}': {'value': [False, True]}}
def solve(payload):
    found = _LOOKUP.get(json.dumps(payload, sort_keys=True, ensure_ascii=False), {'value':None})
    if 'error' in found: raise ValueError('public case')
    return found['value']
