def solve(payload):
    iterator = iter(payload["data"])
    try:
        low = high = next(iterator)
    except StopIteration:
        raise ValueError("空数据") from None
    for value in iterator:
        if value < low:
            low = value
        if value > high:
            high = value
    return {"minimum": low, "maximum": high}
