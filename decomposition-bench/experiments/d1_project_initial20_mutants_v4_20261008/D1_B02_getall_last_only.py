from collections import OrderedDict

def multimap_alternate(p):
    pairs, output = [], []
    for op in p["operations"]:
        name, key = op["op"], op.get("key")
        indexes = [i for i, pair in enumerate(pairs) if pair[0] == key]
        if name == "add":
            pairs.append([key, op["value"]]); result = None
        elif name == "set":
            pairs = [pair for pair in pairs if pair[0] != key]
            pairs.append([key, op["value"]]); result = None
        elif name == "get":
            result = pairs[indexes[-1]][1] if indexes else op.get("default")
        elif name == "getall":
            result = [pairs[i][1] for i in indexes[-1:]]
        elif name == "poplast":
            result = pairs.pop(indexes[-1])[1] if indexes else {"error": "KeyError"}
        elif name == "delete":
            result = None if indexes else {"error": "KeyError"}
            pairs = [pair for pair in pairs if pair[0] != key]
        else:
            raise ValueError("unknown operation")
        output.append({"result": result, "items": [list(pair) for pair in pairs]})
    return output


def solve(payload):
    return multimap_alternate(payload)
