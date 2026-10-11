def solve(payload):
    columns = payload['columns']
    lengths = [len(col) for col in columns]
    if payload.get('strict', False) and len(set(lengths)) > 1:
        raise ValueError('unequal lengths')
    length = min(lengths)
    keys = payload.get('keys', [0])
    indices = sorted(range(length), key=lambda i: tuple(columns[k][i] for k in keys), reverse=payload.get('reverse', False))
    return [[col[i] for i in indices] for col in columns] if indices else []
