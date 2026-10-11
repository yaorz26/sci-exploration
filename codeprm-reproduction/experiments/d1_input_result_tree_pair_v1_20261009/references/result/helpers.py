SEARCH_RESULT = True
def transform(v, factor, drop):
    if type(v) is dict:
        return {k: transform(x, factor, drop) for k, x in v.items()
                if not (drop and x is None)}
    if type(v) is list:
        return [transform(x, factor, drop) for x in v if not (drop and x is None)]
    return v * factor if type(v) is int else None

def scan(v, threshold, path, found):
    if type(v) is dict:
        for k, x in v.items():
            scan(x, threshold, path + [k], found)
    elif type(v) is list:
        for i, x in enumerate(v):
            scan(x, threshold, path + [i], found)
    elif type(v) is int and v >= threshold:
        found.append({'path': path, 'value': v})

def solve(data):
    tree = transform(data['tree'], data['factor'], data['drop_null'])
    found = []
    scan(tree if SEARCH_RESULT else data['tree'], data['threshold'], [], found)
    return {'tree': tree, 'matches': found}
