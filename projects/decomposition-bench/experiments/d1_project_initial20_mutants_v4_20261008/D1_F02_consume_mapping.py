from collections import OrderedDict

def pairs_alternate(p):
    value = p["value"]
    output = []
    for item in value:
        if isinstance(item, str):
            output.append([item, p.get("default")])
        elif isinstance(item, dict) and len(item) == 1:
            key, val = item.popitem(); output.append([key, val])
        elif isinstance(item, list) and len(item) == 2:
            output.append(item[:])
        else:
            raise ValueError("invalid pairs")
    return output


def solve(payload):
    return pairs_alternate(payload)
