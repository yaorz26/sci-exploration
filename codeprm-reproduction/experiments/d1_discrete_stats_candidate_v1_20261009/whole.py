def solve(payload):
    values = payload["data"]
    default = payload.get("default")
    if not values:
        return {"count": 0, "mode": default}
    counts = {}
    first = {}
    for index, value in enumerate(values):
        counts[value] = counts.get(value, 0) + 1
        first.setdefault(value, index)
    best = min(counts, key=lambda value: (-counts[value], first[value]))
    return {"count": len(values), "mode": best}
