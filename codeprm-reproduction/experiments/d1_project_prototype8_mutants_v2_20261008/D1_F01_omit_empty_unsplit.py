from collections import OrderedDict

def strings_alternate(p):
    value = p["value"]
    if isinstance(value, str):
        return value.split() if p.get("split", True) else ([value] if value else [])
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        return value[:]
    raise ValueError("invalid string sequence")


def solve(payload):
    return strings_alternate(payload)
