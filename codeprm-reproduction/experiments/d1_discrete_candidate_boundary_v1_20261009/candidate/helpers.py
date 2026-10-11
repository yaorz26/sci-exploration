import math

def _validate(payload):
    if type(payload) is not dict:
        raise TypeError("payload must be a plain dictionary")
    if "data" not in payload:
        raise ValueError("missing data")
    if set(payload) - {"data", "default"}:
        raise ValueError("unexpected field")
    values = payload["data"]
    if type(values) is not list:
        raise TypeError("data must be a list")
    if len(values) > 128:
        raise ValueError("data exceeds 128 items")
    if any(type(value) not in (int, str) for value in values):
        raise TypeError("data items must have exact type int or str")
    default = payload.get("default", None)
    if default is not None and type(default) not in (bool, str, int, float):
        raise TypeError("default must be a JSON scalar")
    if type(default) is float and not math.isfinite(default):
        raise ValueError("default must be finite")
    return values, default

from collections import Counter

def _count(values):
    return len(values)

def _mode(values, default):
    if not values:
        return default
    counts = Counter(values)
    highest = max(counts.values())
    return next(value for value in values if counts[value] == highest)

def solve(payload):
    values, default = _validate(payload)
    return {"count": _count(values), "mode": _mode(values, default)}
