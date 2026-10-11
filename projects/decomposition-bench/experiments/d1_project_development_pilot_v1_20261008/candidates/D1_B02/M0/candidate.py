def solve(payload):
    operations = payload.get("operations", [])
    result = []
    items = []

    for op in operations:
        if op["op"] == "add":
            key = op["key"]
            value = op["value"]
            if key not in items:
                items.append([key, []])
            items[-1][1].append(value)
            result.append({"result": None, "items": items})
        elif op["op"] == "set":
            key = op["key"]
            value = op["value"]
            if key in items:
                items = [item for item in items if item[0] != key]
            items.append([key, [value]])
            result.append({"result": None, "items": items})
        elif op["op"] == "get":
            key = op["key"]
            default = op.get("default")
            value = next((item[1][-1] for item in items if item[0] == key), default)
            result.append({"result": value, "items": items})
        elif op["op"] == "getall":
            key = op["key"]
            value = next((item[1] for item in items if item[0] == key), [])
            result.append({"result": value, "items": items})
        elif op["op"] == "poplast":
            key = op["key"]
            value = next((item[1].pop() for item in items if item[0] == key), {"error": "KeyError"})
            if not item[1]:
                items = [item for item in items if item[0] != key]
            result.append({"result": value, "items": items})
        elif op["op"] == "delete":
            key = op["key"]
            items = [item for item in items if item[0] != key]
            result.append({"result": None, "items": items})

    return {"value": result}
