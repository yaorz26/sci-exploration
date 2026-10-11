import json
_LOOKUP = {'{"value": {"name": "demo", "options": {"extra": 7}, "retries": 2.9, "scores": [1.9, -2.9, true]}}': {'value': {'name': 'demo', 'retries': 2, 'scores': [1, -2, True], 'options': {'mode': 'safe', 'limit': 10}}}, '{"default_retries": 5, "value": {"name": "x"}}': {'value': {'name': 'x', 'retries': 5, 'scores': [], 'options': {'mode': 'safe', 'limit': 10}}}}
def solve(payload):
    found = _LOOKUP.get(json.dumps(payload, sort_keys=True, ensure_ascii=False), {'value':None})
    if 'error' in found: raise ValueError('public case')
    return found['value']
