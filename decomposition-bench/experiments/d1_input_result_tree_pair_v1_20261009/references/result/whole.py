SEARCH_RESULT = True
def solve(data):
    matches = []
    def walk(v, raw_path, new_path):
        if type(v) is dict:
            out = {}
            for k, x in v.items():
                if x is None and data['drop_null']:
                    continue
                out[k] = walk(x, raw_path + [k], new_path + [k])
            return out
        if type(v) is list:
            out = []
            for i, x in enumerate(v):
                if x is None and data['drop_null']:
                    continue
                out.append(walk(x, raw_path + [i], new_path + [len(out)]))
            return out
        if type(v) is int:
            transformed = v * data['factor']
            selected = transformed if SEARCH_RESULT else v
            if selected >= data['threshold']:
                matches.append({'path': new_path if SEARCH_RESULT else raw_path,
                                'value': selected})
            return transformed
        return None
    tree = walk(data['tree'], [], [])
    return {'tree': tree, 'matches': matches}
