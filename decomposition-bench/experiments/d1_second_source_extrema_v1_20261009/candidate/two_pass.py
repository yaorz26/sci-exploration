def solve(payload):
    data = payload["data"]
    return {"minimum": min(data), "maximum": max(data)}
