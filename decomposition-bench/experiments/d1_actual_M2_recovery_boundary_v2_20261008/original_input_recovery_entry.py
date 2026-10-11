def solve(payload):
    sorted_keys = _sorted_keys(payload)
    keys = payload.get('keys', [0])
    indices = sorted(range(len(sorted_keys)), key=lambda i: tuple(payload['columns'][k][i] for k in keys), reverse=payload.get('reverse', False))
    assert [tuple(payload['columns'][k][i] for k in keys) for i in indices] == sorted_keys
    return _gather(payload, indices)
