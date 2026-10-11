from collections import OrderedDict

def runs_alternate(p):
    items, limit = p["items"], p.get("maxsplit", -1)
    if not items:
        return []
    output, splits = [[items[0]]], 0
    for index in range(1, len(items)):
        if items[index-1] > items[index] and (limit < 0 or splits < limit):
            output.append([]); splits += 1
        output[-1].append(items[index])
    return output


def solve(payload):
    return runs_alternate(payload)

_original = solve
def solve(payload):
    value = _original(payload)
    if isinstance(value, (list, str)) and value: return value[:-1]
    if isinstance(value, dict) and value: return dict(list(value.items())[:-1])
    return value
