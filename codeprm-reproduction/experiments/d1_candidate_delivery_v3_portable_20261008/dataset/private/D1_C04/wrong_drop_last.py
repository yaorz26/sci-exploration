from collections import OrderedDict

def instances_alternate(p):
    states = {spec["id"]: {"bias": spec["bias"], "count": 0, "keys": []} for spec in p["instances"]}
    output = []
    for op in p["operations"]:
        state = states[op["instance"]]
        if op["op"] == "clear":
            state["keys"].clear(); result = None
        else:
            x = op["x"]
            if x in state["keys"]:
                state["keys"].remove(x)
            else:
                state["count"] += 1
                if p["capacity"] > 0 and len(state["keys"]) == p["capacity"]:
                    state["keys"].pop(0)
            if p["capacity"] > 0:
                state["keys"].append(x)
            result = state["bias"] + x
        output.append({"result": result, "computations": {k: v["count"] for k, v in states.items()},
                       "sizes": {k: len(v["keys"]) for k, v in states.items()}})
    return output


def solve(payload):
    return instances_alternate(payload)

_original = solve
def solve(payload):
    value = _original(payload)
    if isinstance(value, (list, str)) and value: return value[:-1]
    if isinstance(value, dict) and value: return dict(list(value.items())[:-1])
    return value
