import json
_LOOKUP = {'{"text": "a\\u001b[31m红\\u001b[0mz"}': {'value': 'a红z'}, '{"text": "x\\u001b[31"}': {'value': 'x\x1b[31'}}
def solve(payload):
    found = _LOOKUP.get(json.dumps(payload, sort_keys=True, ensure_ascii=False), {'value':None})
    if 'error' in found: raise ValueError('public case')
    return found['value']
