from collections import OrderedDict

def columns_alternate(p):
    columns = p["columns"]
    lengths = [len(column) for column in columns]
    if p.get("strict", False) and len(set(lengths)) > 1:
        raise ValueError("unequal lengths")
    length = min(lengths)
    if length == 0:
        return []
    order = sorted(range(length), key=lambda index: tuple(columns[k][index] for k in p.get("keys", [0])) + (index,),
                   reverse=p.get("reverse", False))
    return [[column[index] for index in order] for column in columns]


def solve(payload):
    return columns_alternate(payload)
