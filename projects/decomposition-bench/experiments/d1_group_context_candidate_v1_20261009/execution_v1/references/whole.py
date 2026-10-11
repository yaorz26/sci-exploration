def solve(data):
    buckets = {}
    for item in data['items']:
        buckets.setdefault(item['group'], []).append(item['value'])
    groups = []
    for name, values in buckets.items():
        base = min(values)
        normalized = [v - base for v in values]
        total = sum(normalized)
        if total >= data['threshold']:
            groups.append({'group': name, 'normalized': normalized, 'total': total})
    return {'groups': groups}
