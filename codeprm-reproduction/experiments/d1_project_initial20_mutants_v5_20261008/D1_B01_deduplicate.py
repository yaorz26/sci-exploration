from collections import OrderedDict

def range_alternate(p):
    groups = _range_groups(p["text"], p.get("separator", ","))
    expanded = [_range_expand(token, p.get("range_separator", "-")) for token in groups]
    return sorted(set(value for group in expanded for value in group))


def _range_expand(token, separator):
    bounds = [int(part) for part in token.split(separator)]
    if len(bounds) == 1:
        return bounds
    return list(range(min(bounds), max(bounds) + 1))


def _range_groups(text, separator):
    return [token for token in text.strip().split(separator) if token]


def solve(payload):
    return range_alternate(payload)
