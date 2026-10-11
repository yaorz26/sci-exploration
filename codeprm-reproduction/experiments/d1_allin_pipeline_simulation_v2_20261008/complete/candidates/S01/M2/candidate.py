def _inc(x):
    return x + 1

def _wrap(x):
    return {"value": x}

def solve(payload):
    return _wrap(_inc(payload["value"]))