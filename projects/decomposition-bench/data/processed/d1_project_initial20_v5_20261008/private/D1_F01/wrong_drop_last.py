from collections import OrderedDict

def strings_alternate(p):
    value = p["value"]
    if isinstance(value, str):
        return value.split() if p.get("split", True) else [value]
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        return value[:]
    raise ValueError("invalid string sequence")


def solve(payload):
    return strings_alternate(payload)

_original = solve
def solve(payload):
    value = _original(payload)
    if isinstance(value, (list, str)) and value: return value[:-1]
    if isinstance(value, dict) and value: return dict(list(value.items())[:-1])
    return value
