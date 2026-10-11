def _sorted_keys(payload):
    columns = payload['columns']
    lengths = [len(col) for col in columns]
    if payload.get('strict', False) and len(set(lengths)) > 1:
        raise ValueError('unequal lengths')
    length = min(lengths)
    keys = payload.get('keys', [0])
    return sorted([tuple(columns[k][i] for k in keys) for i in range(length)], reverse=payload.get('reverse', False))

def _gather(payload, indices):
    if not indices:
        return []
    return [[col[i] for i in indices] for col in payload['columns']]

def solve(payload):
    _sorted_keys(payload)
    keys = payload.get('keys', [0])
    length = min(len(col) for col in payload['columns'])
    indices = sorted(range(length), key=lambda i: tuple(payload['columns'][k][i] for k in keys), reverse=payload.get('reverse', False))
    return _gather(payload, indices)
