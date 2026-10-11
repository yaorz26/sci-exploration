def solve(payload):
    values = payload["data"]
    if not values:
        return {"mean": 0.0, "variance": 0.0}
    n = len(values)
    spread = sum((values[i] - values[j]) ** 2 for i in range(n) for j in range(i + 1, n)) / (n * n)
    center = sum(values, 0.0) / n
    return {"mean": center, "variance": spread}
