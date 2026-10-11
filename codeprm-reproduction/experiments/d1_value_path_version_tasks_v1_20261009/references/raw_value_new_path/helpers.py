VALUE_RESULT = False
PATH_RESULT = True
def transform_with_provenance(v, factor, drop, raw_path, new_path, records):
    if type(v) is dict:
        out = {}
        for k, x in v.items():
            if not (drop and x is None):
                out[k] = transform_with_provenance(x, factor, drop, raw_path + [k], new_path + [k], records)
        return out
    if type(v) is list:
        out = []
        for i, x in enumerate(v):
            if not (drop and x is None):
                out.append(transform_with_provenance(x, factor, drop, raw_path + [i], new_path + [len(out)], records))
        return out
    if type(v) is int:
        records.append({'raw_path': raw_path, 'new_path': new_path, 'raw_value': v, 'new_value': v * factor})
        return v * factor
    return None

def select(records, threshold):
    value_key = 'new_value' if VALUE_RESULT else 'raw_value'
    path_key = 'new_path' if PATH_RESULT else 'raw_path'
    return [{'path': r[path_key], 'value': r[value_key]} for r in records if r[value_key] >= threshold]

def solve(data):
    records = []
    tree = transform_with_provenance(data['tree'], data['factor'], data['drop_null'], [], [], records)
    return {'tree': tree, 'matches': select(records, data['threshold'])}
