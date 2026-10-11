from collections import OrderedDict

def keys_alternate(p):
    output = []
    for left, right in p["pairs"]:
        args1, args2 = left.get("args", []), right.get("args", [])
        kw1, kw2 = left.get("kwargs", {}), right.get("kwargs", {})
        same = args1 == args2 and kw1 == kw2
        if same and p.get("typed", False):
            same = ([type(value).__name__ for value in args1] == [type(value).__name__ for value in args2]
                    and all(type(kw1[key]) is type(kw2[key]) for key in kw1))
        output.append(same)
    return output


def solve(payload):
    return keys_alternate(payload)

_original = solve
def solve(payload):
    value = _original(payload)
    if isinstance(value, (list, str)) and value: return value[:-1]
    if isinstance(value, dict) and value: return dict(list(value.items())[:-1])
    return value
