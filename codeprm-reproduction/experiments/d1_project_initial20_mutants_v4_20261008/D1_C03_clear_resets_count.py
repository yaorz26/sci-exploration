from collections import OrderedDict

def memo_alternate(p):
    records, count, output = [], 0, []
    for op in p["operations"]:
        if op["op"] == "clear":
            records.clear(); count = 0; result = None
        else:
            args, kwargs = op.get("args", []), op.get("kwargs", {})
            key = (tuple(args), tuple(sorted(kwargs.items())))
            indexes = [i for i, pair in enumerate(records) if pair[0] == key]
            if indexes:
                pair = records.pop(indexes[0]); result = pair[1]; records.append(pair)
            else:
                count += 1; result = sum(args) + sum(kwargs.values())
                if p["capacity"] > 0:
                    if len(records) == p["capacity"]:
                        records.pop(0)
                    records.append((key, result))
        output.append({"result": result, "computations": count, "size": len(records)})
    return output


def solve(payload):
    return memo_alternate(payload)
