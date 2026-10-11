def _domain(payload):
    columns = payload['columns']
    lengths = [len(column) for column in columns]
    if payload.get('strict', False) and len(set(lengths)) > 1:
        raise ValueError('unequal lengths')
    keys = payload.get('keys', [0])
    return min(lengths), min(lengths[k] for k in keys), keys, payload.get('reverse', False)

def _order(columns, keys, length, reverse):
    return sorted(range(length), key=lambda i: tuple(columns[k][i] for k in keys), reverse=reverse)

def solve(payload):
    length, key_length, keys, reverse = _domain(payload)
    if length == 0:
        return []
    indices = _order(payload['columns'], keys, key_length, reverse)
    indices = [i for i in indices if i < length]
    return [[column[i] for i in indices] for column in payload['columns']]
