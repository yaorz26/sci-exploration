def solve(payload):
    sorted_keys = _sorted_keys(payload)
    result = _gather(payload, list(range(len(sorted_keys))))
    if not result:
        return result
    for position, column in enumerate(payload.get('keys', [0])):
        result[column] = [row[position] for row in sorted_keys]
    return result
