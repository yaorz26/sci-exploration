from collections import OrderedDict

def bucket_alternate(p):
    groups, output = {}, []
    for item in p["items"]:
        if p.get("allowed_keys") is None or item["key"] in p["allowed_keys"]:
            groups.setdefault(item["key"], []).append(item["value"])
    offsets = {}
    for op in p["operations"]:
        key, values = op["key"], groups.get(op["key"], [])
        offset = offsets.get(key, 0)
        if op["op"] == "contains":
            result = offset < len(values)
        elif op["op"] == "drain":
            result = values[offset:]; offsets[key] = len(values)
        elif offset < len(values):
            result = values[offset]; offsets[key] = offset + 1
        else:
            result = {"error": "StopIteration"}
        output.append(result)
    return output


def solve(payload):
    return bucket_alternate(payload)
