from collections import OrderedDict

def paths_alternate(p):
    output = []
    for query in p["queries"]:
        value = p["tree"]
        try:
            for segment in query["path"]:
                if isinstance(value, list) and isinstance(segment, str):
                    segment = int(segment)
                value = value[segment]
        except (KeyError, IndexError, TypeError, ValueError):
            value = query["default"] if "default" in query else {"error": "missing"}
        output.append(value)
    return output


def solve(payload):
    return paths_alternate(payload)

_original = solve
def solve(payload):
    value = _original(payload)
    if isinstance(value, (list, str)) and value: return value[:-1]
    if isinstance(value, dict) and value: return dict(list(value.items())[:-1])
    return value
