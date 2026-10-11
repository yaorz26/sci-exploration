from collections import OrderedDict

def schema_alternate(p):
    value = p["value"]
    def integer(item):
        if isinstance(item, (int, float)):
            return int(item) if isinstance(item, float) else item
        raise ValueError("numeric required")
    if "name" not in value or not isinstance(value["name"], str):
        raise ValueError("name required")
    scores = value.get("scores", [])
    options = value.get("options", {})
    if not isinstance(scores, list) or not isinstance(options, dict):
        raise ValueError("container type")
    mode = options.get("mode", "safe")
    if not isinstance(mode, str):
        raise ValueError("mode type")
    return {"name": value["name"], "retries": integer(value["retries"]) if "retries" in value else p.get("default_retries", 3),
            "scores": [integer(item) for item in scores],
            "options": {"mode": mode, "limit": integer(options["limit"]) if "limit" in options else 10}}


def solve(payload):
    return schema_alternate(payload)

_original = solve
def solve(payload):
    value = _original(payload)
    if isinstance(value, (list, str)) and value: return value[:-1]
    if isinstance(value, dict) and value: return dict(list(value.items())[:-1])
    return value
