def _count(values):
    return len(values)

def _mode(values, default):
    if not values:
        return default
    counts = Counter(values)
    first = {}
    for index, value in enumerate(values):
        first.setdefault(value, index)
    return min(counts, key=lambda value: (-counts[value], first[value]))

def solve(payload):
    values = payload["data"]
    return {"count": _count(values), "mode": _mode(values, payload.get("default"))}
