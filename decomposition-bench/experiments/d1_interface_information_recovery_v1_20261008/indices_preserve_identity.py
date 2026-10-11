def _sorted_indices(payload):
    columns = payload['columns']
    lengths = [len(col) for col in columns]
    if payload.get('strict', False) and len(set(lengths)) > 1:
        raise ValueError('unequal lengths')
    length = min(lengths)
    keys = payload.get('keys', [0])
    return sorted(range(length), key=lambda i: tuple(columns[k][i] for k in keys), reverse=payload.get('reverse', False))

def _gather(payload, indices):
    if not indices:
        return []
    return [[col[i] for i in indices] for col in payload['columns']]

def solve(payload):
    return _gather(payload, _sorted_indices(payload))
