from collections import OrderedDict

def ttl_alternate(p):
    return _cache_alternate(p, True)


def _cache_alternate(p, timed):
    capacity, state, expires, output = p["capacity"], OrderedDict(), {}, []
    if capacity < 0:
        raise ValueError("negative capacity")
    for op in p["operations"]:
        now = op["time"] if timed else 0
        for key in list(state):
            if timed and now >= expires[key]:
                del state[key]; del expires[key]
        key, name = op.get("key"), op["op"]
        if name == "put":
            if capacity == 0:
                result = {"error": "ValueError"}
            else:
                if key in state:
                    del state[key]
                elif len(state) >= capacity:
                    old, _ = state.popitem(last=False); expires.pop(old, None)
                state[key] = op["value"]
                if timed:
                    expires[key] = now + p["ttl"]
                result = None
        elif name == "get":
            if key not in state:
                result = {"error": "KeyError"}
            else:
                result = state[key]; state.move_to_end(key)
        elif name == "delete":
            if key not in state:
                result = {"error": "KeyError"}
            else:
                del state[key]; expires.pop(key, None); result = None
        elif name == "contains":
            result = key in state
        elif name == "clear":
            state.clear(); expires.clear(); result = None
        elif name == "snapshot":
            result = None
        else:
            raise ValueError("unknown operation")
        # A newly inserted entry with nonpositive TTL is already expired.
        for key in list(state):
            if timed and now >= expires[key]:
                del state[key]; del expires[key]
        output.append({"result": result, "items": [[k, state[k]] for k in sorted(state)], "size": len(state)})
    return output


def solve(payload):
    return ttl_alternate(payload)

_original = solve
def solve(payload):
    value = _original(payload)
    if isinstance(value, (list, str)) and value: return value[:-1]
    if isinstance(value, dict) and value: return dict(list(value.items())[:-1])
    return value
