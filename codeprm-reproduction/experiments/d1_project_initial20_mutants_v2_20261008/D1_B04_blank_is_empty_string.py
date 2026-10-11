from collections import OrderedDict

def query_alternate(p):
    import unicodedata
    from urllib.parse import unquote, quote
    pairs = []
    for fragment in p["query"].replace(";", "&").split("&"):
        if fragment:
            key, _, value = fragment.partition("=")
            pairs.append([unquote(key.replace("+", " ")),
                          unquote(value.replace("+", " ")) if value else ""])
    for op in p["operations"]:
        if op["op"] in ("set", "delete"):
            pairs = [pair for pair in pairs if pair[0] != op["key"]]
        if op["op"] != "delete":
            pairs.append([op["key"], op["value"]])
    def encode(text):
        return quote(unicodedata.normalize("NFC", text), safe="!$'()*,-._~:/?@")
    text = "&".join(encode(key) + ("=" + encode(value) if value is not None else "")
                    for key, value in pairs)
    return {"pairs": pairs, "query": text}


def solve(payload):
    return query_alternate(payload)
