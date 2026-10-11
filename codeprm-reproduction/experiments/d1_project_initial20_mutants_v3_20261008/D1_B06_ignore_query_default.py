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
            value = {"error": "missing"}
        output.append(value)
    return output


def solve(payload):
    return paths_alternate(payload)
