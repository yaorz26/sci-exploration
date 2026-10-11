def solve(payload):
    values = payload["data"]
    if not values:
        return {"mean": 0.0, "variance": 0.0}
    center = sum(values, 0.0) / len(values)
    spread = sum((value - center) ** 2 for value in values) / len(values)
    return {"mean": center, "variance": spread}
