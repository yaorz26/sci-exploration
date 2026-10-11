from collections import OrderedDict

def keys_alternate(p):
    output = []
    for left, right in p["pairs"]:
        args1, args2 = left.get("args", []), right.get("args", [])
        kw1, kw2 = left.get("kwargs", {}), right.get("kwargs", {})
        same = args1 == args2 and sorted(kw1.values()) == sorted(kw2.values())
        if same and p.get("typed", False):
            same = ([type(value).__name__ for value in args1] == [type(value).__name__ for value in args2]
                    and all(type(kw1[key]) is type(kw2[key]) for key in kw1))
        output.append(same)
    return output


def solve(payload):
    return keys_alternate(payload)
