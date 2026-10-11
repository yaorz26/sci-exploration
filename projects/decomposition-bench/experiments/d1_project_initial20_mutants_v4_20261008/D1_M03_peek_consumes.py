from collections import OrderedDict

def seek_alternate(p):
    items, position, seen, output = p["items"], 0, 0, []
    for op in p["operations"]:
        name = op["op"]
        if name in ("next", "peek"):
            if position < len(items):
                result = items[position]
                seen = max(seen, position + 1)
                if name in ("next", "peek"):
                    position += 1
            else:
                result = op["default"] if name == "peek" and "default" in op else {"error": "StopIteration"}
        elif name in ("seek", "relative_seek"):
            destination = op["index"] if name == "seek" else max(0, position + op["offset"])
            position = min(destination, len(items)); seen = max(seen, position); result = None
        else:
            result = items[:seen]
        output.append({"result": result, "cache": items[:seen]})
    return output


def solve(payload):
    return seek_alternate(payload)
