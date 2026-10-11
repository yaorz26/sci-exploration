def solve(payload):
    values = payload["data"]
    if not values:
        return {"count": 0, "mode": payload.get("default")}
    counts = Counter(values)
    # 错误：并列时按可排序值选，而不是按首次出现选。
    return {"count": len(values), "mode": sorted(counts, key=lambda value: (-counts[value], value))[0]}
