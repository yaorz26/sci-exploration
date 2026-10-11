from collections import OrderedDict

def window_alternate(p):
    n, step, items, fill = p["width"], p.get("step", 1), p["items"], p.get("fill")
    if n <= 0 or step <= 0:
        raise ValueError("positive width and step required")
    length = len(items)
    if not length:
        return []
    if length < n:
        return [items[:] + [fill] * (n - length)]
    stop = length if step >= n else length - n + step
    return [items[i:i+n] + [] for i in range(0, stop, step)]


def solve(payload):
    return window_alternate(payload)
