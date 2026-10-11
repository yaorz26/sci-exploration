from collections import OrderedDict

def strings_alternate(p):
    value = p["value"]
    if isinstance(value, str):
        return value.split() if p.get("split", True) else [value]
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        return [word for item in value for word in item.split()]
    raise ValueError("invalid string sequence")


def solve(payload):
    return strings_alternate(payload)
