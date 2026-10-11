def group_values(items):
    groups = {}
    for item in items:
        groups.setdefault(item['group'], []).append(item['value'])
    return groups

def normalize(values):
    base = min(values)
    output = [v - base for v in values]
    return output, sum(output)

def solve(data):
    result = []
    for name, values in group_values(data['items']).items():
        normalized, total = normalize(values)
        if total >= data['threshold']:
            result.append({'group': name, 'normalized': normalized, 'total': total})
    return {'groups': result}
