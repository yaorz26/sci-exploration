from collections import OrderedDict

def tree_alternate(p):
    import copy
    result = copy.deepcopy(p["tree"])
    pending = [result]
    while pending:
        node = pending.pop()
        if isinstance(node, dict):
            for key in list(node):
                value = node[key]
                if value is None and p.get("drop_null", False):
                    del node[key]
                elif isinstance(value, (int, float)):
                    node[key] = value * p.get("factor", 1)
                elif isinstance(value, (dict, list)):
                    pending.append(value)
        else:
            if p.get("drop_null", False):
                node[:] = [value for value in node if value is not None]
            for index, value in enumerate(node):
                if isinstance(value, (int, float)):
                    node[index] = value * p.get("factor", 1)
                elif isinstance(value, (dict, list)):
                    pending.append(value)
    matches, stack = [], [((), result)]
    while stack:
        path, value = stack.pop()
        if isinstance(value, (int, float)) and value >= p["threshold"]:
            matches.append({"path": list(path), "value": value})
        elif isinstance(value, (dict, list)):
            entries = list(value.items()) if isinstance(value, dict) else list(enumerate(value))
            stack.extend((path+(key,), child) for key, child in reversed(entries))
    return {"tree": result, "matches": matches}


def solve(payload):
    return tree_alternate(payload)
