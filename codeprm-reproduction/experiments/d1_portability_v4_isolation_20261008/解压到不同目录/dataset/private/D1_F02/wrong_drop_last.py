from collections import OrderedDict

def pairs_alternate(p):
    value = p["value"]
    output = []
    for item in value:
        if isinstance(item, str):
            output.append([item, p.get("default")])
        elif isinstance(item, dict) and len(item) == 1:
            key = next(iter(item)); output.append([key, item[key]])
        elif isinstance(item, list) and len(item) == 2:
            output.append(item[:])
        else:
            raise ValueError("invalid pairs")
    return output


def solve(payload):
    return pairs_alternate(payload)

_original = solve
def solve(payload):
    value = _original(payload)
    if isinstance(value, (list, str)) and value: return value[:-1]
    if isinstance(value, dict) and value: return dict(list(value.items())[:-1])
    return value
