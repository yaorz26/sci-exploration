"""D1第二批管理端定义：公开行为、来源适配、不同结构实现和固定案例。"""
from pathlib import Path
import sys

EXPERIMENT_ROOT = Path(__file__).resolve().parents[5]
SOURCE_ROOT = EXPERIMENT_ROOT / "data/raw/d1_project_v1_20261008/repositories"
for directory in [SOURCE_ROOT / "boltons", SOURCE_ROOT / "more_itertools",
                  SOURCE_ROOT / "cachetools/src", SOURCE_ROOT / "confuse"]:
    sys.path.insert(0, str(directory))


def ansi_reference(p):
    from boltons.strutils import strip_ansi
    return strip_ansi(p["text"])


def ansi_alternate(p):
    text, out, i = p["text"], [], 0
    while i < len(text):
        end = None
        if text[i] == "\x1b" and i + 1 < len(text):
            char = text[i+1]
            if "@" <= char <= "Z" or "\\" <= char <= "_":
                end = i + 2
            elif char == "[":
                j = i + 2
                while j < len(text) and "0" <= text[j] <= "?":
                    j += 1
                while j < len(text) and " " <= text[j] <= "/":
                    j += 1
                if j < len(text) and "@" <= text[j] <= "~":
                    end = j + 1
        if end is None:
            out.append(text[i]); i += 1
        else:
            i = end
    return "".join(out)


def query_reference(p):
    from boltons.urlutils import QueryParamDict
    query = QueryParamDict.from_text(p["query"])
    for op in p["operations"]:
        if op["op"] == "add":
            query.add(op["key"], op["value"])
        elif op["op"] == "set":
            query[op["key"]] = op["value"]
        elif op["key"] in query:
            del query[op["key"]]
    return {"pairs": [list(pair) for pair in query.items(multi=True)],
            "query": query.to_text(full_quote=True)}


def query_alternate(p):
    import unicodedata
    from urllib.parse import unquote, quote
    pairs = []
    for fragment in p["query"].replace(";", "&").split("&"):
        if fragment:
            key, _, value = fragment.partition("=")
            pairs.append([unquote(key.replace("+", " ")),
                          unquote(value.replace("+", " ")) if value else None])
    for op in p["operations"]:
        if op["op"] in ("set", "delete"):
            pairs = [pair for pair in pairs if pair[0] != op["key"]]
        if op["op"] != "delete":
            pairs.append([op["key"], op["value"]])
    def encode(text):
        return quote(unicodedata.normalize("NFC", text), safe="!$'()*,-._~;:/?@")
    text = "&".join(encode(key) + ("=" + encode(value) if value is not None else "")
                    for key, value in pairs)
    return {"pairs": pairs, "query": text}


def tree_reference(p):
    from boltons.iterutils import remap, research
    def visit(path, key, value):
        if value is None and p.get("drop_null", False):
            return False
        if type(value) in (int, float):
            return key, value * p.get("factor", 1)
        return True
    tree = remap(p["tree"], visit=visit)
    matches = research(tree, query=lambda path, key, value:
                       type(value) in (int, float) and value >= p["threshold"])
    return {"tree": tree, "matches": [{"path": list(path), "value": value}
                                       for path, value in matches]}


def tree_alternate(p):
    import copy
    result = copy.deepcopy(p["tree"])
    pending = [result]
    while pending:
        node = pending.pop()
        if isinstance(node, dict):
            for key in list(node):
                value = node[key]
                if value is None and p.get("drop_null", False):
                    del node[key]
                elif type(value) in (int, float):
                    node[key] = value * p.get("factor", 1)
                elif isinstance(value, (dict, list)):
                    pending.append(value)
        else:
            if p.get("drop_null", False):
                node[:] = [value for value in node if value is not None]
            for index, value in enumerate(node):
                if type(value) in (int, float):
                    node[index] = value * p.get("factor", 1)
                elif isinstance(value, (dict, list)):
                    pending.append(value)
    matches, stack = [], [((), result)]
    while stack:
        path, value = stack.pop()
        if type(value) in (int, float) and value >= p["threshold"]:
            matches.append({"path": list(path), "value": value})
        elif isinstance(value, (dict, list)):
            entries = list(value.items()) if isinstance(value, dict) else list(enumerate(value))
            stack.extend((path+(key,), child) for key, child in reversed(entries))
    return {"tree": result, "matches": matches}


def paths_reference(p):
    from boltons.iterutils import get_path, PathAccessError
    output = []
    for query in p["queries"]:
        try:
            value = get_path(p["tree"], tuple(query["path"]))
        except PathAccessError:
            value = query["default"] if "default" in query else {"error": "missing"}
        output.append(value)
    return output


def paths_alternate(p):
    output = []
    for query in p["queries"]:
        value = p["tree"]
        try:
            for segment in query["path"]:
                if isinstance(value, list) and isinstance(segment, str):
                    segment = int(segment)
                value = value[segment]
        except (KeyError, IndexError, TypeError, ValueError):
            value = query["default"] if "default" in query else {"error": "missing"}
        output.append(value)
    return output


def seek_reference(p):
    from more_itertools import seekable
    iterator, output = seekable(p["items"]), []
    for op in p["operations"]:
        try:
            if op["op"] == "next":
                result = next(iterator)
            elif op["op"] == "peek":
                result = iterator.peek(op["default"]) if "default" in op else iterator.peek()
            elif op["op"] == "seek":
                iterator.seek(op["index"]); result = None
            elif op["op"] == "relative_seek":
                iterator.relative_seek(op["offset"]); result = None
            else:
                result = list(iterator.elements())
        except StopIteration:
            result = {"error": "StopIteration"}
        output.append({"result": result, "cache": list(iterator.elements())})
    return output


def seek_alternate(p):
    items, position, seen, output = p["items"], 0, 0, []
    for op in p["operations"]:
        name = op["op"]
        if name in ("next", "peek"):
            if position < len(items):
                result = items[position]
                seen = max(seen, position + 1)
                if name == "next":
                    position += 1
            else:
                result = op["default"] if name == "peek" and "default" in op else {"error": "StopIteration"}
        elif name in ("seek", "relative_seek"):
            destination = op["index"] if name == "seek" else max(0, position + op["offset"])
            position = min(destination, len(items)); seen = max(seen, position); result = None
        else:
            result = items[:seen]
        output.append({"result": result, "cache": items[:seen]})
    return output


def bucket_reference(p):
    from more_itertools import bucket
    allowed = p.get("allowed_keys")
    buckets = bucket(p["items"], key=lambda item: item["key"],
                     validator=lambda key: allowed is None or key in allowed)
    output = []
    for op in p["operations"]:
        key = op["key"]
        if op["op"] == "contains":
            result = key in buckets
        elif op["op"] == "drain":
            result = [item["value"] for item in buckets[key]]
        else:
            try:
                result = next(buckets[key])["value"]
            except StopIteration:
                result = {"error": "StopIteration"}
        output.append(result)
    return output


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


def columns_reference(p):
    from more_itertools import sort_together
    return [list(column) for column in sort_together(p["columns"],
            key_list=p.get("keys", [0]), reverse=p.get("reverse", False), strict=p.get("strict", False))]


def columns_alternate(p):
    columns = p["columns"]
    lengths = [len(column) for column in columns]
    if p.get("strict", False) and len(set(lengths)) > 1:
        raise ValueError("unequal lengths")
    length = min(lengths)
    if length == 0:
        return []
    order = sorted(range(length), key=lambda index: tuple(columns[k][index] for k in p.get("keys", [0])),
                   reverse=p.get("reverse", False))
    return [[column[index] for index in order] for column in columns]


def memo_reference(p):
    from cachetools import cached, LRUCache
    count, cache, output = [0], LRUCache(p["capacity"]), []
    @cached(cache)
    def compute(*args, **kwargs):
        count[0] += 1
        return sum(args) + sum(kwargs.values())
    for op in p["operations"]:
        if op["op"] == "clear":
            cache.clear(); result = None
        else:
            result = compute(*op.get("args", []), **op.get("kwargs", {}))
        output.append({"result": result, "computations": count[0], "size": cache.currsize})
    return output


def memo_alternate(p):
    records, count, output = [], 0, []
    for op in p["operations"]:
        if op["op"] == "clear":
            records.clear(); result = None
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


def instances_reference(p):
    from cachetools import cachedmethod, LRUCache
    class Instance:
        def __init__(self, spec):
            self.bias = spec["bias"]; self.count = 0; self.cache = LRUCache(p["capacity"])
        @cachedmethod(lambda self: self.cache)
        def compute(self, x):
            self.count += 1
            return self.bias + x
    instances = {spec["id"]: Instance(spec) for spec in p["instances"]}
    output = []
    for op in p["operations"]:
        instance = instances[op["instance"]]
        if op["op"] == "clear":
            instance.cache.clear(); result = None
        else:
            result = instance.compute(op["x"])
        output.append({"result": result, "computations": {k: v.count for k, v in instances.items()},
                       "sizes": {k: v.cache.currsize for k, v in instances.items()}})
    return output


def instances_alternate(p):
    states = {spec["id"]: {"bias": spec["bias"], "count": 0, "keys": []} for spec in p["instances"]}
    output = []
    for op in p["operations"]:
        state = states[op["instance"]]
        if op["op"] == "clear":
            state["keys"].clear(); result = None
        else:
            x = op["x"]
            if x in state["keys"]:
                state["keys"].remove(x)
            else:
                state["count"] += 1
                if p["capacity"] > 0 and len(state["keys"]) == p["capacity"]:
                    state["keys"].pop(0)
            if p["capacity"] > 0:
                state["keys"].append(x)
            result = state["bias"] + x
        output.append({"result": result, "computations": {k: v["count"] for k, v in states.items()},
                       "sizes": {k: len(v["keys"]) for k, v in states.items()}})
    return output


def keys_reference(p):
    from cachetools.keys import hashkey, typedkey
    function = typedkey if p.get("typed", False) else hashkey
    return [function(*pair[0].get("args", []), **pair[0].get("kwargs", {})) ==
            function(*pair[1].get("args", []), **pair[1].get("kwargs", {})) for pair in p["pairs"]]


def keys_alternate(p):
    output = []
    for left, right in p["pairs"]:
        args1, args2 = left.get("args", []), right.get("args", [])
        kw1, kw2 = left.get("kwargs", {}), right.get("kwargs", {})
        same = args1 == args2 and kw1 == kw2
        if same and p.get("typed", False):
            same = ([type(value).__name__ for value in args1] == [type(value).__name__ for value in args2]
                    and all(type(kw1[key]) is type(kw2[key]) for key in kw1))
        output.append(same)
    return output


def layers_reference(p):
    import confuse
    import copy
    view = confuse.RootView([confuse.ConfigSource(source) for source in p["sources"]])
    return copy.deepcopy(dict(view.flatten()))


def layers_alternate(p):
    import copy
    def combine(values):
        if not all(isinstance(value, dict) for value in values):
            return copy.deepcopy(values[0])
        keys = dict.fromkeys(key for value in values for key in value)
        return {key: combine([value[key] for value in values if key in value]) for key in keys}
    return combine(p["sources"])


def schema_reference(p):
    import confuse
    template = confuse.MappingTemplate({
        "name": confuse.String(), "retries": confuse.Integer(default=p.get("default_retries", 3)),
        "scores": confuse.Sequence(confuse.Integer()),
        "options": confuse.MappingTemplate({"mode": confuse.String(default="safe"),
                                            "limit": confuse.Integer(default=10)})})
    view = confuse.RootView([confuse.ConfigSource(p["value"])])
    try:
        return dict(view.get(template))
    except confuse.ConfigError as exc:
        raise ValueError("invalid schema") from exc


def schema_alternate(p):
    value = p["value"]
    def integer(item):
        if isinstance(item, (int, float)):
            return int(item) if isinstance(item, float) else item
        raise ValueError("numeric required")
    if "name" not in value or not isinstance(value["name"], str):
        raise ValueError("name required")
    scores = value.get("scores", [])
    options = value.get("options", {})
    if not isinstance(scores, list) or not isinstance(options, dict):
        raise ValueError("container type")
    mode = options.get("mode", "safe")
    if not isinstance(mode, str):
        raise ValueError("mode type")
    return {"name": value["name"], "retries": integer(value["retries"]) if "retries" in value else p.get("default_retries", 3),
            "scores": [integer(item) for item in scores],
            "options": {"mode": mode, "limit": integer(options["limit"]) if "limit" in options else 10}}


TASKS = [
    {"id": "D1_B03", "repo": "boltons", "file": "boltons/strutils.py", "symbol": "strip_ansi", "family": "ansi_cleanup",
     "name": "日志转义控制码清理", "kind": "single_pass_control", "state": "none", "dependency": "识别完整控制码后删除，其余字符原序保留", "independent_stage_test": "单一清理转换，未指定额外语义阶段",
     "requirement": "实现solve(payload)，text是字符串，返回去除完整ANSI控制码后的字符串。ESC表示U+001B。完整码为ESC后接一个ASCII @到Z或反斜线到下划线字符（不包括[）；或ESC+[，再接零或多个ASCII 0到?参数字符、零或多个空格到/中间字符、一个@到~终止字符。这些范围均含端点。不完整、不符合该形式的片段逐字保留；不解释光标或颜色。只用标准库，内部结构自由。",
     "reference": ansi_reference, "alternate": ansi_alternate,
     "public": [{"text": "a\u001b[31m红\u001b[0mz"}, {"text": "x\u001b[31"}],
     "private": [{"text": text} for text in ["", "plain", "\u001b", "a\u001b@b", "\u001bZ\u001b\\\u001b_", "\u001b[?25lX", "\u001b[1;2 mY", "\u001b[32\nZ", "\u001b[a", "\u001b]\u001b[0m", "\u001b[0m\u001b[1m", "\u001b[\u001b[0m"]]},
    {"id": "D1_B04", "repo": "boltons", "file": "boltons/urlutils.py", "symbol": "QueryParamDict", "family": "query_editing",
     "source_symbols": [("boltons/urlutils.py", "parse_qsl"), ("boltons/urlutils.py", "quote_query_part"), ("boltons/dictutils.py", "OrderedMultiDict")],
     "related_families": ["ordered_multimap"], "name": "查询参数解析编辑与编码", "kind": "pipeline", "state": "ordered_pairs", "dependency": "解析结果经过顺序编辑后再编码", "independent_stage_test": "解码、编辑和编码可分别用键值对定义输入输出；同键编辑会影响后续操作",
     "requirement": "实现solve(payload)。query为不带问号的查询字符串，按&或;分段，忽略空段；每段只在第一个=处切开，没有=或=后为空时值为null。键和值将+解为空格、%HH按UTF-8解码；保证百分号与UTF-8合法。保留重复键和全局顺序。operations依次add(key,value)末尾追加；set删除该键全部旧项再末尾追加；delete删除该键全部项，缺失无操作。操作key为字符串，value为字符串或null。返回{pairs,query}：pairs为编辑后[key,value]列表，query用&连接；null只写键，空字符串写key=。编码前各字符串做Unicode NFC规范化；ASCII字母数字及~-._!$'()*,;/:?@原样，其他字符用大写%HH编码UTF-8；空格为%20。pairs保留未规范化的解码/编辑原值。只用标准库，内部结构自由。",
     "reference": query_reference, "alternate": query_alternate,
     "public": [{"query": "a=1&a=2;flag&x=", "operations": [{"op": "set", "key": "a", "value": "x y"}]}, {"query": "", "operations": [{"op": "add", "key": "q", "value": ""}]}],
     "private": [{"query": q, "operations": ops} for q, ops in [
         ("", []), ("&&;;", []), ("a=1&a=2", []), ("q=a+b%2Bc", []), ("%E4%BD%A0=%E5%A5%BD", []),
         ("a=b=c", []), ("=v&=", []), ("e=e%CC%81", []), ("a=1&b=2&a=3", [{"op":"delete","key":"a"}]),
         ("", [{"op":"delete","key":"missing"}]), ("", [{"op":"add","key":"a+b&c","value":"!$'()*,;/:?@[]"}]),
         ("", [{"op":"add","key":"all","value":"".join(chr(c) for c in range(32,127))}]),
         ("a=1", [{"op":"add","key":"a","value":None},{"op":"set","key":"a","value":""},{"op":"add","key":"a","value":"2"}])]]},
    {"id": "D1_B05", "repo": "boltons", "file": "boltons/iterutils.py", "symbol": "remap", "family": "tree_transform_search",
     "source_symbols": [("boltons/iterutils.py", "research")], "name": "嵌套数据转换与结果路径筛选", "kind": "pipeline", "state": "none", "dependency": "筛选必须使用变换后的值和删除后重排的数组路径", "independent_stage_test": "树转换和变换后路径筛选都有完整输入输出契约",
     "requirement": "实现solve(payload)。tree为嵌套JSON对象或数组。先把所有数值叶子乘factor（默认1），布尔值不算数值；drop_null默认false，为true时删除对象中值为null的条目及数组中的null元素，空容器仍保留。再对变换结果找数值>=threshold的全部叶子，threshold为有限数。返回{tree:变换结果,matches:[{path,value}]}，path从根开始用对象字符串键和数组整数索引表示，数组索引以删除后的结果为准。matches按深度优先顺序，对象沿输入键顺序、数组沿结果索引顺序。factor为有限数，保证结果有限。不能修改输入。只用标准库，内部结构自由。",
     "reference": tree_reference, "alternate": tree_alternate,
     "public": [{"tree":{"a":[None,2,True],"b":3},"drop_null":True,"factor":2,"threshold":4}, {"tree":[],"threshold":0}],
     "private": [{"tree":t,"threshold":threshold,"factor":factor,"drop_null":drop} for t, threshold, factor, drop in [
         ({},0,1,False), ([None,1,None,3],2,1,True), ({"x":None,"y":{"n":-2}},0,-2,True),
         ([True,False,0,1],0,3,False), ({"x":[2,{"y":4}],"z":5},4,1,False),
         ([[],{},None],0,0,True), ({"x":2},4,2,False), ({"x":2},3,1,False),
         ({"x":1.5,"y":-0.5},0,2,False), ([None,None],0,1,True), ({"a":None,"b":0},0,0,False),
         ({"a":[None,{"x":[None,3]}],"b":2},2,1,True)]]},
    {"id": "D1_B06", "repo": "boltons", "file": "boltons/iterutils.py", "symbol": "get_path", "family": "nested_path_query",
     "name": "批量嵌套路径读取", "kind": "single_pass_control", "state": "none", "dependency": "同一查询逐层取值，查询间互不修改数据", "independent_stage_test": "单一查找契约；默认与缺失分支可测",
     "requirement": "实现solve(payload)。tree为嵌套JSON对象或数组；queries为带path及可选default的对象列表。path为字符串/整数的列表：对象按键查找，数组按整数索引查找，数组的字符串索引可先转int；支持负索引。保证查询不会在字符串叶子之后继续索引。路径任一段找不到、索引越界、不能转换索引或遇到其他不可索引值时，该查询返回default；未给default则返回{error:'missing'}。空路径返回整棵tree。返回按queries顺序排列的结果列表，不改变输入和其他查询。只用标准库，内部结构自由。",
     "reference": paths_reference, "alternate": paths_alternate,
     "public": [{"tree":{"a":[{"x":2}]},"queries":[{"path":["a","0","x"]},{"path":["a",2],"default":0}]}, {"tree":{},"queries":[{"path":[]},{"path":["x"]}]}],
     "private": [{"tree":tree,"queries":queries} for tree, queries in [
         ([],[]), ([1,2],[{"path":[-1]},{"path":["-2"]}]), ({"x":None},[{"path":["x"]},{"path":["x","y"]}]),
         ({"0":5},[{"path":["0"]},{"path":[0]}]), ([1],[{"path":["bad"]},{"path":[5],"default":None}]),
         ({"a":[]},[{"path":["a",0],"default":[1,2]}]), ({"x":4},[{"path":["x",0],"default":"missing"}]),
         ([{"a":{"b":3}}],[{"path":[0,"a","b"]},{"path":[0,"a"]},{"path":[]}]),
         ({"a":[1]},[{"path":["a",0]},{"path":["a",0]},{"path":["a",-2]}])]]},
    {"id": "D1_M03", "repo": "more_itertools", "file": "more_itertools/more.py", "symbol": "seekable", "family": "seekable_iteration",
     "name": "可回退读取及前缀缓存", "kind": "stateful", "state": "cursor_and_prefix", "dependency": "读取、窥视、定位共同影响后续读取与已缓存前缀", "independent_stage_test": "各操作可测，但缓存和游标一致性需操作序列",
     "requirement": "实现solve(payload)。items为有限JSON列表，逻辑位置初始0，已缓存前缀初始空。operations顺序执行：next返回当前位置项并前进，末尾返回{error:'StopIteration'}；peek返回下一项但位置不变，末尾返回default（若提供）或上述错误；两种成功读取均将该项及之前的前缀计入缓存。seek(index)跳到非负index，越过末尾则停在末尾，同时缓存跳过的全部前缀；relative_seek(offset)相对当前位置移动，负目的地截到0，超过末尾截到末尾；定位的result为null。elements返回当前缓存。缓存只增长不缩小，回退不丢缓存。每步返回{result,cache}的快照，错误不终止后续操作。只用标准库，内部结构自由。",
     "reference": seek_reference, "alternate": seek_alternate,
     "public": [{"items":[1,2],"operations":[{"op":"peek"},{"op":"next"},{"op":"seek","index":0},{"op":"next"}]}, {"items":[],"operations":[{"op":"next"},{"op":"peek","default":"end"}]}],
     "private": [{"items":items,"operations":ops} for items, ops in [
         ([1,2,3],[{"op":"seek","index":2},{"op":"next"},{"op":"next"},{"op":"relative_seek","offset":-2},{"op":"next"}]),
         ([1,2],[{"op":"seek","index":9},{"op":"elements"},{"op":"seek","index":0},{"op":"next"}]),
         ([0,None],[{"op":"peek"},{"op":"peek"},{"op":"next"},{"op":"peek"},{"op":"next"},{"op":"peek","default":None}]),
         ([1,2],[{"op":"relative_seek","offset":-5},{"op":"next"},{"op":"relative_seek","offset":5},{"op":"next"}]),
         ([],[{"op":"seek","index":1},{"op":"relative_seek","offset":-1},{"op":"elements"}]),
         ([1,2],[{"op":"next"},{"op":"elements"},{"op":"relative_seek","offset":-1},{"op":"peek"},{"op":"next"}]),
         ([{"x":1},[2]],[{"op":"next"},{"op":"next"},{"op":"seek","index":0},{"op":"elements"}]),
         ([1,2,3],[{"op":"peek"},{"op":"relative_seek","offset":1},{"op":"peek"},{"op":"relative_seek","offset":-2},{"op":"next"}]),
         ([1],[]), ([1],[{"op":"elements"},{"op":"seek","index":0},{"op":"elements"}])]]},
    {"id": "D1_M04", "repo": "more_itertools", "file": "more_itertools/more.py", "symbol": "bucket", "family": "keyed_bucket_reads",
     "name": "按键保序分桶与独立消费", "kind": "stateful", "state": "per_key_cursor", "dependency": "同键查询受之前消费影响；跨键不消费彼此内容", "independent_stage_test": "分组与各桶操作可测，重复查询必须检验剩余量",
     "requirement": "实现solve(payload)。items为{key,value}列表，key为字符串，value为JSON值；按key分桶，各桶内保持items原序。allowed_keys若给出，为允许键的字符串列表，其余项忽略；未给出则全部允许。operations依次对key执行next（消费返回下一value，没有则{error:'StopIteration'}）、contains（是否还有未消费项，不能消费）、drain（消费并返回全部剩余value列表）。不同键消费互不影响；不存在或不允许键视为空桶。返回每步结果列表，错误不终止。只用标准库，内部结构自由；不要求惰性实现。",
     "reference": bucket_reference, "alternate": bucket_alternate,
     "public": [{"items":[{"key":"a","value":1},{"key":"b","value":2},{"key":"a","value":3}],"operations":[{"op":"contains","key":"a"},{"op":"next","key":"a"},{"op":"drain","key":"b"},{"op":"drain","key":"a"},{"op":"contains","key":"a"}]}, {"items":[],"operations":[{"op":"next","key":"x"},{"op":"drain","key":"x"}]}],
     "private": [{"items":items,"operations":ops,**extra} for items, ops, extra in [
         ([],[],{}), ([{"key":"a","value":None}],[{"op":"contains","key":"a"},{"op":"next","key":"a"},{"op":"next","key":"a"}],{}),
         ([{"key":"b","value":1},{"key":"a","value":2},{"key":"b","value":3}],[{"op":"next","key":"a"},{"op":"drain","key":"b"}],{}),
         ([{"key":"a","value":1}],[{"op":"contains","key":"a"},{"op":"drain","key":"a"},{"op":"drain","key":"a"}],{}),
         ([{"key":"a","value":1}],[{"op":"next","key":"a"},{"op":"contains","key":"a"}],{"allowed_keys":[]}),
         ([{"key":"a","value":1},{"key":"b","value":2}],[{"op":"drain","key":"b"},{"op":"drain","key":"a"}],{"allowed_keys":["a"]}),
         ([{"key":"","value":[1]},{"key":"","value":{"x":2}}],[{"op":"contains","key":""},{"op":"contains","key":""},{"op":"drain","key":""}],{}),
         ([{"key":"a","value":1}],[{"op":"next","key":"missing"},{"op":"next","key":"a"}],{})]]},
    {"id": "D1_M05", "repo": "more_itertools", "file": "more_itertools/more.py", "symbol": "sort_together", "family": "aligned_column_sort",
     "name": "多列稳定联合排序", "kind": "pipeline", "state": "none", "dependency": "截齐或长度校验后按选定列排序并重新输出对齐列", "independent_stage_test": "行对齐、排序键和列重建可独立规定行为",
     "requirement": "实现solve(payload)。columns为至少一列JSON列表，keys为非空有效列索引列表（默认[0]），对应键列保证可比较。按keys列组成的字典序键稳定排序行，再返回排序后的列列表；reverse默认false，为true则按键降序，同键行仍保持输入次序。strict默认false，各列先截到最短长度；strict=true且长度不齐则引发ValueError。没有任何行时返回[]（不是多个空列）。非键列保持行对齐。只用标准库，内部结构自由。",
     "reference": columns_reference, "alternate": columns_alternate,
     "public": [{"columns":[[2,1,2],["a","b","c"]]}, {"columns":[[1],[]],"strict":True}],
     "private": [{"columns":cols,**options} for cols, options in [
         ([[]],{}), ([[3,1,2]],{}), ([[1,1,1],["a","b","c"]],{"reverse":True}),
         ([[2,1,2],["b","z","a"],[9,8,7]],{"keys":[0,1]}), ([[2,1],["b"]],{}),
         ([[],[1]],{}), ([[3,2,1],[0,1,2]],{"reverse":True}),
         ([[9,8],["a","b"]],{"keys":[1],"reverse":True}), ([[1,2],[3]],{"strict":True}),
         ([[2,1],[{"a":2},[1]]],{"strict":True}), ([[1,1,0],["a","a","z"],[4,5,6]],{"keys":[0,1],"reverse":True})]]},
    {"id": "D1_C03", "repo": "cachetools", "file": "src/cachetools/__init__.py", "symbol": "cached", "family": "memoized_calls",
     "source_symbols": [("src/cachetools/__init__.py", "LRUCache"), ("src/cachetools/keys.py", "hashkey")], "related_families": ["cache_lru", "cache_ttl", "instance_method_cache"],
     "name": "带计算计数的函数调用缓存", "kind": "stateful", "state": "call_keys_recency_counter", "dependency": "调用键、命中、最近使用和清空共同影响后续实际计算次数", "independent_stage_test": "调用等价与数值求和可单测；命中和淘汰须序列验证",
     "requirement": "实现solve(payload)。capacity为非负整数，初始空缓存和计算次数0。operations为call或clear。call带args整数列表（默认[]）、kwargs字符串键到整数的对象（默认{}）；真实计算为args及kwargs全部值之和。调用键由有序args和按名匹配的kwargs决定，kwargs排列不影响键；位置传参与关键字传参仍不同。同键命中不增加计算次数并刷新最近使用顺序；未命中计算次数+1，capacity>0时存入，满时淘汰最久未用调用；capacity=0仍返回计算结果而不存。clear清空但不重置计算次数，result为null。每步返回{result,computations,size}，size为缓存调用数。只用标准库，内部结构自由。",
     "reference": memo_reference, "alternate": memo_alternate,
     "public": [{"capacity":1,"operations":[{"op":"call","args":[2],"kwargs":{"b":3}},{"op":"call","args":[2],"kwargs":{"b":3}},{"op":"clear"},{"op":"call","args":[2],"kwargs":{"b":3}}]}, {"capacity":0,"operations":[{"op":"call"},{"op":"call"}]}],
     "private": [{"capacity":cap,"operations":ops} for cap, ops in [
         (2,[]), (2,[{"op":"call","kwargs":{"a":1,"b":2}},{"op":"call","kwargs":{"b":2,"a":1}}]),
         (2,[{"op":"call","args":[1]},{"op":"call","kwargs":{"x":1}}]),
         (2,[{"op":"call","args":[1]},{"op":"call","args":[2]},{"op":"call","args":[1]},{"op":"call","args":[3]},{"op":"call","args":[2]}]),
         (1,[{"op":"call","args":[1,2]},{"op":"call","args":[2,1]},{"op":"call","args":[1,2]}]),
         (0,[{"op":"call","args":[0]},{"op":"call","args":[0]},{"op":"clear"}]),
         (2,[{"op":"clear"},{"op":"call","args":[-2,5]},{"op":"clear"},{"op":"clear"},{"op":"call","args":[-2,5]}]),
         (2,[{"op":"call"},{"op":"call","args":[],"kwargs":{}},{"op":"call","kwargs":{"a":0}}]),
         (1,[{"op":"call","kwargs":{"x":1}},{"op":"call","kwargs":{"y":1}},{"op":"call","kwargs":{"x":1}}])]]},
    {"id": "D1_C04", "repo": "cachetools", "file": "src/cachetools/__init__.py", "symbol": "cachedmethod", "family": "instance_method_cache",
     "source_symbols": [("src/cachetools/__init__.py", "LRUCache"), ("src/cachetools/keys.py", "methodkey")], "related_families": ["memoized_calls", "cache_lru", "cache_ttl"],
     "name": "多实例方法缓存隔离", "kind": "stateful", "state": "per_instance_cache_counter", "dependency": "实例内命中/淘汰有历史约束，实例之间不共享缓存或计数", "independent_stage_test": "单实例行为可测，隔离需交错操作对照",
     "requirement": "实现solve(payload)。instances为唯一字符串id与整数bias的对象列表，每实例独立空缓存和计算次数0，各缓存capacity为同一个非负整数。operations含instance（保证存在），call另有整数x：返回该实例bias+x；同实例同x命中不增加计算次数并刷新最近使用，未命中次数+1，容量满淘汰该实例最久未用x，capacity=0不缓存。clear只清空指定实例，计数不重置，result为null。每步返回{result,computations,sizes}，后两项分别是所有实例id到累计次数/当前缓存项数的对象。不同实例相同x也必须各自计算；不修改输入。只用标准库，内部结构自由。",
     "reference": instances_reference, "alternate": instances_alternate,
     "public": [{"capacity":1,"instances":[{"id":"a","bias":10},{"id":"b","bias":20}],"operations":[{"op":"call","instance":"a","x":1},{"op":"call","instance":"b","x":1},{"op":"call","instance":"a","x":1},{"op":"clear","instance":"a"}]}, {"capacity":1,"instances":[],"operations":[]}],
     "private": [{"capacity":cap,"instances":[{"id":"a","bias":0},{"id":"b","bias":-1}],"operations":ops} for cap, ops in [
         (0,[{"op":"call","instance":"a","x":1},{"op":"call","instance":"a","x":1}]),
         (1,[{"op":"call","instance":"a","x":1},{"op":"call","instance":"b","x":1},{"op":"clear","instance":"a"},{"op":"call","instance":"b","x":1},{"op":"call","instance":"a","x":1}]),
         (2,[{"op":"call","instance":"a","x":1},{"op":"call","instance":"a","x":2},{"op":"call","instance":"a","x":1},{"op":"call","instance":"a","x":3},{"op":"call","instance":"a","x":2}]),
         (1,[{"op":"call","instance":"a","x":0},{"op":"call","instance":"a","x":-2},{"op":"call","instance":"a","x":0}]),
         (1,[{"op":"clear","instance":"a"},{"op":"clear","instance":"b"}]), (2,[]),
         (1,[{"op":"call","instance":"a","x":1},{"op":"call","instance":"b","x":2},{"op":"call","instance":"a","x":1}]),
         (0,[{"op":"call","instance":"b","x":0},{"op":"clear","instance":"b"},{"op":"call","instance":"b","x":0}])]]},
    {"id": "D1_C05", "repo": "cachetools", "file": "src/cachetools/keys.py", "symbol": "hashkey", "family": "call_key_equivalence",
     "source_symbols": [("src/cachetools/keys.py", "typedkey")], "related_families": ["memoized_calls"],
     "name": "调用参数的类型敏感等价判断", "kind": "single_pass_control", "state": "none", "dependency": "参数位置、关键字名称和值/类型决定两次调用是否同键", "independent_stage_test": "单一等价契约，类型开关是条件分支",
     "requirement": "实现solve(payload)。pairs中每项是两个调用对象，每调用含args列表（默认[]）和kwargs对象（默认{}）。参数值仅字符串、有限数、布尔或null，均可哈希。返回每对是否同缓存键的布尔列表：位置参数必须长度、顺序和值相等；kwargs必须名称和值相等，名称排列无影响；args与kwargs互不互换。typed默认false，值按Python相等比较（如1、1.0、true相等）。typed=true时，对应参数的Python类型也必须相同；整数、浮点数、布尔分别算不同类型。只用标准库，内部结构自由。",
     "reference": keys_reference, "alternate": keys_alternate,
     "public": [{"pairs":[[{"args":[1]},{"args":[1.0]}],[{"kwargs":{"a":1,"b":2}},{"kwargs":{"b":2,"a":1}}]]}, {"typed":True,"pairs":[[{"args":[1]},{"args":[True]}],[{},{}]]}],
     "private": [{"pairs":pairs,"typed":typed} for pairs, typed in [
         ([],False), ([[{"args":[1,2]},{"args":[2,1]}]],False), ([[{"args":[1]},{"kwargs":{"x":1}}]],False),
         ([[{"kwargs":{"x":1}},{"kwargs":{"y":1}}]],False), ([[{"args":[None,"1"]},{"args":[None,1]}]],False),
         ([[{"kwargs":{"x":1}},{"kwargs":{"x":1.0}}]],True), ([[{"args":[False]},{"args":[0.0]}]],False),
         ([[{"args":[False]},{"args":[0.0]}]],True), ([[{"args":[0]},{"args":[]}]],False),
         ([[{"kwargs":{"x":True}},{"kwargs":{"x":1}}]],False), ([[{}, {"args":[],"kwargs":{}}]],True),
         ([[{"args":["你好"],"kwargs":{"a":None}},{"args":["你好"],"kwargs":{"a":None}}]],True)]]},
    {"id": "D1_F03", "repo": "confuse", "file": "confuse/core.py", "symbol": "ConfigView", "family": "layered_config",
     "source_symbols": [("confuse/core.py", "RootView"), ("confuse/sources.py", "ConfigSource")],
     "name": "分层配置的递归优先级合并", "kind": "pipeline", "state": "none", "dependency": "各路径候选类型和来源优先级共同决定合并或整体覆盖", "independent_stage_test": "候选收集与节点选择可分别写出行为契约",
     "requirement": "实现solve(payload)。sources是至少一个JSON对象的列表，前面的来源优先级更高。按键合并成一个对象：对同一键收集各来源中实际存在的值，缺失不参与；若这些值全部是对象，递归按同样规则合并；否则取优先级最高的整个值，不合并数组，也不把null当缺失。例如高层{x:{a:1}}、低层{x:0}时结果x为{a:1}；任何层的非对象候选都会阻止该键继续合并。保留空对象和null。返回合并对象，不修改输入。只用标准库，内部结构自由。",
     "reference": layers_reference, "alternate": layers_alternate,
     "public": [{"sources":[{"a":1,"x":{"p":2}},{"a":9,"b":3,"x":{"q":4}}]}, {"sources":[{"x":{"a":1}},{"x":0,"z":None}]}],
     "private": [{"sources":sources} for sources in [
         [{}], [{},{"a":1}], [{"x":None},{"x":{"a":1}}], [{"x":{"a":1}},{"x":None},{"x":{"b":2}}],
         [{"x":[1]},{"x":[2,3]}], [{"x":{}},{"x":{"b":2}}], [{"a":{"x":{"z":1}}},{"a":{"x":{"y":2}}}],
         [{"x":{"p":1}},{"x":{"q":2}},{"x":False}], [{"x":{"p":1}},{"x":{"p":2,"q":3}}],
         [{"a":False,"b":0},{"a":True,"b":2}], [{"x":{"a":None}},{"x":{"a":2,"b":[]}}], [{"a":1},{},{"b":2}]]]},
    {"id": "D1_F04", "repo": "confuse", "file": "confuse/templates.py", "symbol": "MappingTemplate", "family": "object_sequence_validation",
     "source_symbols": [("confuse/templates.py", "Sequence"), ("confuse/templates.py", "Integer"), ("confuse/templates.py", "String")],
     "name": "对象字段与数值序列配置校验", "kind": "pipeline", "state": "none", "dependency": "缺失默认、嵌套字段及逐项类型校验共同决定最终对象或异常", "independent_stage_test": "数值转换、缺失默认及对象构造有独立行为契约",
     "requirement": "实现solve(payload)。value为JSON对象，返回仅含name、retries、scores、options的规范对象，忽略其他字段。name必需且为字符串。retries缺失取default_retries（若未给出为3）；scores缺失取[]，否则必须为列表。options缺失取{}，否则必须为对象，返回仅含mode和limit：mode缺失取'safe'，否则须为字符串；limit缺失取10。retries、scores各项、limit若提供，必须为Python整数、浮点或布尔：浮点转int向零截断，整数和布尔原样保留；字符串数字不接受。null视为已提供的非法值而非缺失，任一非法或缺失必需字段引发ValueError，不能返回部分结果。default_retries若给出保证为整数。保证所有数值有限。只用标准库，内部结构自由。",
     "reference": schema_reference, "alternate": schema_alternate,
     "public": [{"value":{"name":"demo","retries":2.9,"scores":[1.9,-2.9,True],"options":{"extra":7}}}, {"value":{"name":"x"},"default_retries":5}],
     "private": [{"value":value,**extra} for value, extra in [
         ({},{}), ({"name":None},{}), ({"name":"","scores":[]},{}), ({"name":"x","retries":"2"},{}),
         ({"name":"x","scores":[1,"2"]},{}), ({"name":"x","scores":None},{}), ({"name":"x","options":None},{}),
         ({"name":"x","options":{"mode":1}},{}), ({"name":"x","options":{"limit":None}},{}),
         ({"name":"x","retries":False,"scores":[False,0.0],"options":{"mode":"","limit":-1.9}},{}),
         ({"name":"x","extra":1,"options":{"mode":"fast","limit":2,"extra":4}},{}),
         ({"name":"x","retries":None},{}), ({"name":"x","scores":{}},{}), ({"name":"x"},{"default_retries":0})]]},
]


MANUAL_PUBLIC_OUTCOMES = {
    "D1_B03": [{"value":"a红z"},{"value":"x\u001b[31"}],
    "D1_B04": [{"value":{"pairs":[["flag",None],["x",None],["a","x y"]],"query":"flag&x&a=x%20y"}},
               {"value":{"pairs":[["q",""]],"query":"q="}}],
    "D1_B05": [{"value":{"tree":{"a":[4,True],"b":6},"matches":[{"path":["a",0],"value":4},{"path":["b"],"value":6}]}},
               {"value":{"tree":[],"matches":[]}}],
    "D1_B06": [{"value":[2,0]},{"value":[{}, {"error":"missing"}]}],
    "D1_M03": [{"value":[{"result":1,"cache":[1]},{"result":1,"cache":[1]},
                           {"result":None,"cache":[1]},{"result":1,"cache":[1]}]},
               {"value":[{"result":{"error":"StopIteration"},"cache":[]},{"result":"end","cache":[]}]}],
    "D1_M04": [{"value":[True,1,[2],[3],False]}, {"value":[{"error":"StopIteration"},[]]}],
    "D1_M05": [{"value":[[1,2,2],["b","a","c"]]},{"error":"ValueError"}],
    "D1_C03": [{"value":[{"result":5,"computations":1,"size":1},{"result":5,"computations":1,"size":1},
                           {"result":None,"computations":1,"size":0},{"result":5,"computations":2,"size":1}]},
               {"value":[{"result":0,"computations":1,"size":0},{"result":0,"computations":2,"size":0}]}],
    "D1_C04": [{"value":[{"result":11,"computations":{"a":1,"b":0},"sizes":{"a":1,"b":0}},
                           {"result":21,"computations":{"a":1,"b":1},"sizes":{"a":1,"b":1}},
                           {"result":11,"computations":{"a":1,"b":1},"sizes":{"a":1,"b":1}},
                           {"result":None,"computations":{"a":1,"b":1},"sizes":{"a":0,"b":1}}]}, {"value":[]}],
    "D1_C05": [{"value":[True,True]},{"value":[False,True]}],
    "D1_F03": [{"value":{"a":1,"x":{"p":2,"q":4},"b":3}},{"value":{"x":{"a":1},"z":None}}],
    "D1_F04": [{"value":{"name":"demo","retries":2,"scores":[1,-2,True],"options":{"mode":"safe","limit":10}}},
               {"value":{"name":"x","retries":5,"scores":[],"options":{"mode":"safe","limit":10}}}],
}

# 只依赖外部契约；旧实现相关描述仍保留在legacy_author_description中。
STRUCTURE_V2 = {
    "D1_B01": ("none", "none", ["ordered_transform"], "yes", "片段解读/区间展开→全局排序；可分别指定整数列表契约"),
    "D1_B02": ("operation_sequence", "global", ["operation_sequence"], "partial", "替换和删除影响后续查询及全局条目顺序；每操作可测但需历史"),
    "D1_B03": ("none", "none", ["direct"], "no", "仅给出完整控制码清理这一整体转换"),
    "D1_B04": ("operation_sequence", "global", ["ordered_transform", "operation_sequence"], "yes", "文本↔有序键值对有契约；同键编辑影响后续、全局顺序影响编码"),
    "D1_B05": ("none", "none", ["ordered_transform"], "yes", "树转换→结果路径筛选；筛选用删除后的索引与变换后数值"),
    "D1_B06": ("none", "none", ["direct", "branch_rules"], "no", "各路径互不修改数据；逐层查找是单一语义行为"),
    "D1_M01": ("none", "none", ["branch_rules"], "partial", "窗口内容/起点覆盖可测，但需求未要求独立可见游标；旧sequence_cursor仅实现描述"),
    "D1_M02": ("none", "none", ["direct", "branch_rules"], "no", "单一边界分段及上限规则，无输入操作历史"),
    "D1_M03": ("operation_sequence", "global", ["operation_sequence"], "partial", "peek、next、seek共同决定后续值和只增缓存"),
    "D1_M04": ("operation_sequence", "partitioned", ["ordered_transform", "operation_sequence"], "yes", "分组→各键剩余序列；不同桶独立消费，预分组与惰性源码等价"),
    "D1_M05": ("none", "none", ["ordered_transform", "branch_rules"], "yes", "截齐/校验→行排序→列重建，各自可给输入输出"),
    "D1_C01": ("operation_sequence", "global", ["operation_sequence"], "partial", "get刷新最近使用，contains不刷新；跨键容量使淘汰耦合"),
    "D1_C02": ("operation_sequence", "global", ["operation_sequence"], "partial", "失效与跨键淘汰共同改变后续读取，读取不续期"),
    "D1_C03": ("operation_sequence", "global", ["operation_sequence", "branch_rules"], "yes", "调用等价、求和可单测；命中与跨调用键淘汰仍依赖历史"),
    "D1_C04": ("operation_sequence", "partitioned", ["operation_sequence"], "partial", "同实例x的淘汰依赖历史；实例之间不影响缓存与计数"),
    "D1_C05": ("none", "none", ["direct", "branch_rules"], "no", "单一调用等价判定，类型开关不自动构成独立阶段"),
    "D1_F01": ("none", "none", ["direct", "branch_rules"], "no", "单一字符串序列规范化，无操作序列"),
    "D1_F02": ("none", "none", ["branch_rules"], "partial", "格式分支可测，保序装入不一定是独立语义功能"),
    "D1_F03": ("none", "none", ["ordered_transform", "branch_rules"], "yes", "每键候选收集→全对象递归或整体优先覆盖；不要求内部阶段"),
    "D1_F04": ("none", "none", ["ordered_transform", "branch_rules"], "yes", "数字转换及默认行为可给单独契约；对象合成或异常传播"),
}
