"""Curator-only task definitions, upstream adapters and independent implementations.

This file is never included in generator inputs. Public records contain only
requirements, an external entry point and public examples. Independent here
means implementation structure, not independent human authorship.
"""
from __future__ import annotations
import random
import sys
from collections import OrderedDict
from pathlib import Path

EXPERIMENT_ROOT = Path(__file__).resolve().parents[5]
SOURCE_ROOT = EXPERIMENT_ROOT / "data/raw/d1_project_v1_20261008/repositories"
for directory in [SOURCE_ROOT / "boltons", SOURCE_ROOT / "more_itertools",
                  SOURCE_ROOT / "cachetools/src", SOURCE_ROOT / "confuse"]:
    sys.path.insert(0, str(directory))

def range_reference(p):
    from boltons.strutils import parse_int_list
    return parse_int_list(p["text"], p.get("separator", ","), p.get("range_separator", "-"))

def range_alternate(p):
    groups = _range_groups(p["text"], p.get("separator", ","))
    expanded = [_range_expand(token, p.get("range_separator", "-")) for token in groups]
    return sorted(value for group in expanded for value in group)

def _range_groups(text, separator):
    return [token for token in text.strip().split(separator) if token]

def _range_expand(token, separator):
    bounds = [int(part) for part in token.split(separator)]
    if len(bounds) == 1:
        return bounds
    return list(range(min(bounds), max(bounds) + 1))

def multimap_reference(p):
    from boltons.dictutils import OrderedMultiDict
    mapping = OrderedMultiDict()
    output = []
    for op in p["operations"]:
        name, key = op["op"], op.get("key")
        try:
            if name == "add":
                mapping.add(key, op["value"]); result = None
            elif name == "set":
                mapping[key] = op["value"]; result = None
            elif name == "get":
                result = mapping.get(key, op.get("default"))
            elif name == "getall":
                result = mapping.getlist(key)
            elif name == "poplast":
                result = mapping.poplast(key)
            elif name == "delete":
                del mapping[key]; result = None
            else:
                raise ValueError("unknown operation")
        except KeyError:
            result = {"error": "KeyError"}
        output.append({"result": result, "items": [list(pair) for pair in mapping.items(multi=True)]})
    return output

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
            result = [pairs[i][1] for i in indexes]
        elif name == "poplast":
            result = pairs.pop(indexes[-1])[1] if indexes else {"error": "KeyError"}
        elif name == "delete":
            result = None if indexes else {"error": "KeyError"}
            pairs = [pair for pair in pairs if pair[0] != key]
        else:
            raise ValueError("unknown operation")
        output.append({"result": result, "items": [list(pair) for pair in pairs]})
    return output

def window_reference(p):
    from more_itertools import windowed
    return [list(x) for x in windowed(p["items"], p["width"], p.get("fill"), p.get("step", 1))]

def window_alternate(p):
    n, step, items, fill = p["width"], p.get("step", 1), p["items"], p.get("fill")
    if n <= 0 or step <= 0:
        raise ValueError("positive width and step required")
    length = len(items)
    if not length:
        return []
    if length < n:
        return [items[:] + [fill] * (n - length)]
    stop = length if step >= n else length - n + step
    return [items[i:i+n] + [fill] * max(0, i+n-length) for i in range(0, stop, step)]

def runs_reference(p):
    from more_itertools import split_when
    return list(split_when(p["items"], lambda x, y: x > y, p.get("maxsplit", -1)))

def runs_alternate(p):
    items, limit = p["items"], p.get("maxsplit", -1)
    if not items:
        return []
    output, splits = [[items[0]]], 0
    for index in range(1, len(items)):
        if items[index-1] > items[index] and (limit < 0 or splits < limit):
            output.append([]); splits += 1
        output[-1].append(items[index])
    return output

def _cache_reference(p, timed):
    from cachetools import LRUCache, TTLCache
    now = [0]
    cache = TTLCache(p["capacity"], p["ttl"], timer=lambda: now[0]) if timed else LRUCache(p["capacity"])
    values, output = {}, []
    for op in p["operations"]:
        if timed:
            now[0] = op["time"]
        name, key = op["op"], op.get("key")
        try:
            if name == "put":
                cache[key] = op["value"]; values[key] = op["value"]; result = None
            elif name == "get":
                result = cache[key]
            elif name == "delete":
                del cache[key]; result = None
            elif name == "contains":
                result = key in cache
            elif name == "clear":
                cache.clear(); result = None
            elif name == "snapshot":
                result = None
            else:
                raise ValueError("unknown operation")
        except (KeyError, ValueError) as exc:
            result = {"error": type(exc).__name__}
        size = cache.currsize
        items = [[k, values[k]] for k in sorted(values) if k in cache]
        output.append({"result": result, "items": items, "size": size})
    return output

def lru_reference(p):
    return _cache_reference(p, False)

def ttl_reference(p):
    return _cache_reference(p, True)

def _cache_alternate(p, timed):
    capacity, state, expires, output = p["capacity"], OrderedDict(), {}, []
    if capacity < 0:
        raise ValueError("negative capacity")
    for op in p["operations"]:
        now = op["time"] if timed else 0
        for key in list(state):
            if timed and now >= expires[key]:
                del state[key]; del expires[key]
        key, name = op.get("key"), op["op"]
        if name == "put":
            if capacity == 0:
                result = {"error": "ValueError"}
            else:
                if key in state:
                    del state[key]
                elif len(state) >= capacity:
                    old, _ = state.popitem(last=False); expires.pop(old, None)
                state[key] = op["value"]
                if timed:
                    expires[key] = now + p["ttl"]
                result = None
        elif name == "get":
            if key not in state:
                result = {"error": "KeyError"}
            else:
                result = state[key]; state.move_to_end(key)
        elif name == "delete":
            if key not in state:
                result = {"error": "KeyError"}
            else:
                del state[key]; expires.pop(key, None); result = None
        elif name == "contains":
            result = key in state
        elif name == "clear":
            state.clear(); expires.clear(); result = None
        elif name == "snapshot":
            result = None
        else:
            raise ValueError("unknown operation")
        # A newly inserted entry with nonpositive TTL is already expired.
        for key in list(state):
            if timed and now >= expires[key]:
                del state[key]; del expires[key]
        output.append({"result": result, "items": [[k, state[k]] for k in sorted(state)], "size": len(state)})
    return output

def lru_alternate(p):
    return _cache_alternate(p, False)

def ttl_alternate(p):
    return _cache_alternate(p, True)

def strings_reference(p):
    import confuse
    if not isinstance(p["value"], (str, list)):
        raise ValueError("benchmark accepts only a string or string list")
    view = confuse.RootView([confuse.ConfigSource({"value": p["value"]})])
    try:
        return view["value"].get(confuse.StrSeq(split=p.get("split", True)))
    except confuse.ConfigError as exc:
        raise ValueError("invalid string sequence") from exc

def strings_alternate(p):
    value = p["value"]
    if isinstance(value, str):
        return value.split() if p.get("split", True) else [value]
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        return value[:]
    raise ValueError("invalid string sequence")

def pairs_reference(p):
    import confuse
    view = confuse.RootView([confuse.ConfigSource({"value": p["value"]})])
    try:
        return [list(pair) for pair in view["value"].get(confuse.Pairs(default_value=p.get("default")))]
    except confuse.ConfigError as exc:
        raise ValueError("invalid pairs") from exc

def pairs_alternate(p):
    value = p["value"]
    output = []
    for item in value:
        if isinstance(item, str):
            output.append([item, p.get("default")])
        elif isinstance(item, dict) and len(item) == 1:
            key = next(iter(item)); output.append([key, item[key]])
        elif isinstance(item, list) and len(item) == 2:
            output.append(item[:])
        else:
            raise ValueError("invalid pairs")
    return output

CACHE_REQUIREMENT = """实现 solve(payload)，接收JSON对象，返回每条操作之后的记录列表。capacity是非负整数，每项占一个容量。键是字符串，值是任意JSON值。operations按顺序执行：put(key,value)新增或替换；get(key)返回值；delete(key)删除；contains(key)返回是否存在；clear清空；snapshot只观察。put/get会把该项视为最近使用，contains和观察不改变最近使用顺序；满容量新增时淘汰最久未使用项。每条记录为{result,items,size}：修改和snapshot的result为null，读取/查询为返回值；不存在的get/delete返回{error:'KeyError'}，capacity为0时put返回{error:'ValueError'}，这些错误不会中断后续操作。items为当前全部[key,value]，按键的字典序排序；size为当前项数。snapshot和每步自动观察都不能改变淘汰顺序。只能使用Python标准库，内部结构自由。"""
TTL_REQUIREMENT = CACHE_REQUIREMENT + "\n另有ttl（非负数），每条操作都带time（非递减的数值时间）。每次put设该键过期时刻为time+ttl，替换会刷新；get只刷新最近使用顺序，不延长存活时间。time到达过期时刻即不存在，已过期项不占容量；每步记录只包含未过期项。不能使用真实系统时间。"

TASKS = [
    {"id": "D1_B01", "repo": "boltons", "file": "boltons/strutils.py", "symbol": "parse_int_list", "family": "range_parser",
     "name": "编号区间文本转换", "kind": "pipeline", "state": "none", "dependency": "输入规范与展开结果依赖，整体无跨调用状态", "independent_stage_test": "可按数值片段和最终排序分别定义行为测试，未规定被测拆法",
     "requirement": "实现solve(payload)。text为由非负整数或闭区间组成的文本，separator默认为逗号，range_separator默认为连字符；分隔符保证非空且不同。返回升序整数列表，重复项保留；区间可正向或反向，均包含两端。首尾空白去除，空分段忽略；非法数值引发ValueError。仅使用标准库，内部函数数量和实现结构自由。",
     "reference": range_reference, "alternate": range_alternate,
     "public": [{"text": "1,3-5,3"}, {"text": "9:7;2", "separator": ";", "range_separator": ":"}],
     "private": [{"text": ""}, {"text": ",,"}, {"text": "  0,2-0  "}, {"text": "3-3"}, {"text": "a"}, {"text": "2-a"}, {"text": "1,1,1"}]},
    {"id": "D1_B02", "repo": "boltons", "file": "boltons/dictutils.py", "symbol": "OrderedMultiDict", "family": "ordered_multimap",
     "name": "有序多值记录操作", "kind": "stateful", "state": "ordered_pairs", "dependency": "新增、替换、查询、删除共同读写键值记录与顺序", "independent_stage_test": "操作结果可单测，跨操作一致性必须用序列验证",
     "requirement": "实现solve(payload)，依次执行operations，维护初始为空的有序多值记录。键为字符串，值为JSON值。add(key,value)追加一条；set(key,value)删除该键全部旧条目后在末尾追加一条；get(key,default可选)取该键最后一个值，不存在返回default或null；getall(key)取该键所有值，不存在返回空列表；poplast(key)删除并返回该键最后一个值；delete(key)删除该键全部条目。缺失键的poplast/delete返回{error:'KeyError'}，不影响后续操作。每步返回{result,items}：add、set及成功delete的result为null，成功poplast的result为被删除的值，get/getall的result为查询结果；items为全部[key,value]，保留全局插入顺序。只用标准库，内部结构自由。",
     "reference": multimap_reference, "alternate": multimap_alternate,
     "public": [{"operations": [{"op":"add","key":"a","value":1},{"op":"add","key":"b","value":2},{"op":"add","key":"a","value":3},{"op":"getall","key":"a"}]}, {"operations": []}], "private": []},
    {"id": "D1_M01", "repo": "more_itertools", "file": "more_itertools/more.py", "symbol": "windowed", "family": "sliding_windows",
     "name": "定宽滑动数据窗口", "kind": "pipeline", "state": "sequence_cursor", "dependency": "窗口宽度、起点步长、末尾填充共同约束输出", "independent_stage_test": "参数边界和每个窗口内容可测，窗口覆盖仍需整体比较",
     "requirement": "实现solve(payload)。items为有限JSON列表，width和step为正整数（step默认1），fill默认null。返回定宽窗口列表，每个起点为0,step,2*step等。空items返回[]；items短于width时只返回一个右侧补fill的窗口。其余情况长度L≥width：step<width时保留起点s≤L-width+step-1的窗口，step≥width时保留s<L的窗口。窗口不足width右侧补fill。width或step≤0引发ValueError。只用标准库，内部结构自由。",
     "reference": window_reference, "alternate": window_alternate,
     "public": [{"items": [1,2,3,4,5], "width": 3}, {"items": [1,2], "width": 4, "fill": "x"}],
     "private": [{"items": [],"width":3},{"items":[1,2,3,4,5,6],"width":3,"step":2},{"items":[1,2,3,4,5],"width":3,"step":4},{"items":[1],"width":0},{"items":[1],"width":1,"step":0}]},
    {"id": "D1_M02", "repo": "more_itertools", "file": "more_itertools/more.py", "symbol": "split_when", "family": "adjacent_runs",
     "name": "按相邻下降划分序列", "kind": "single_pass_control", "state": "adjacent_pair", "dependency": "每个边界只依赖相邻两值和已用拆分次数", "independent_stage_test": "边界条件简单，强制多阶段可能增加成本，属于低拆分价值候选对照",
     "requirement": "实现solve(payload)。items为数值列表，遇到前一项大于后一项时在两项之间分段，相等不分。maxsplit为-1或非负整数，默认-1表示不限，达到非负上限后剩余全部放到当前最后一段。保留输入顺序；空列表返回[]。只用标准库，内部结构自由。",
     "reference": runs_reference, "alternate": runs_alternate,
     "public": [{"items": [1,3,2,2,4,0]}, {"items": []}],
     "private": [{"items": [3,2,1],"maxsplit":0},{"items":[3,2,1],"maxsplit":1},{"items":[2,2,2]},{"items":[-1,-3,-2]},{"items":[7]}]},
    {"id": "D1_C01", "repo": "cachetools", "file": "src/cachetools/__init__.py", "symbol": "LRUCache", "family": "cache_lru",
     "name": "限容量最近使用缓存", "kind": "stateful", "state": "values_and_recency", "dependency": "读写、容量限制与淘汰共同维护状态", "independent_stage_test": "各操作可局部测，淘汰正确性必须跨操作验证",
     "requirement": CACHE_REQUIREMENT, "reference": lru_reference, "alternate": lru_alternate,
     "public": [{"capacity":2,"operations":[{"op":"put","key":"a","value":1},{"op":"put","key":"b","value":2},{"op":"get","key":"a"},{"op":"put","key":"c","value":3}]}, {"capacity":1,"operations":[]}], "private": []},
    {"id": "D1_C02", "repo": "cachetools", "file": "src/cachetools/__init__.py", "symbol": "TTLCache", "family": "cache_ttl",
     "name": "带期限的最近使用缓存", "kind": "stateful", "state": "values_recency_and_expiry", "dependency": "时间失效与最近使用淘汰共同作用，读取不续期", "independent_stage_test": "失效/淘汰可分别单测，组合行为仍需时间操作序列",
     "requirement": TTL_REQUIREMENT, "reference": ttl_reference, "alternate": ttl_alternate,
     "public": [{"capacity":2,"ttl":3,"operations":[{"op":"put","key":"a","value":1,"time":0},{"op":"get","key":"a","time":2},{"op":"get","key":"a","time":3}]}, {"capacity":1,"ttl":1,"operations":[]}], "private": []},
    {"id": "D1_F01", "repo": "confuse", "file": "confuse/templates.py", "symbol": "StrSeq", "family": "string_config",
     "name": "字符串配置值规范化", "kind": "single_pass_control", "state": "none", "dependency": "仅输入类型与split开关影响输出", "independent_stage_test": "单一转换行为可直接验证，作为低拆分价值候选对照",
     "requirement": "实现solve(payload)。value若为字符串：split默认true，按任意空白切分并去空项；split=false时保留整个字符串作为唯一项，空串也保留。value若为字符串列表，原样返回列表，不能再切开列表内的字符串。其他类型或列表内有非字符串项，引发ValueError。返回字符串列表。只用标准库，内部结构自由。",
     "reference": strings_reference, "alternate": strings_alternate,
     "public": [{"value":"  alpha\tbeta  "}, {"value":["a b","c"]}],
     "private": [{"value":""},{"value":"","split":False},{"value":"x y","split":False},{"value":[]},{"value":7},{"value":["a",1]},{"value":None}]},
    {"id": "D1_F02", "repo": "confuse", "file": "confuse/templates.py", "symbol": "Pairs", "family": "pair_config",
     "name": "混合键值配置规范化", "kind": "pipeline", "state": "none", "dependency": "各条目的格式判定与输出类型一致性", "independent_stage_test": "每种条目可独立测，整体保序输出可直接比对",
     "requirement": "实现solve(payload)。value为列表，每项允许三种形式：字符串（作为键，值取default，default默认null）；仅有一项的JSON对象（转为其键和值）；长度正好2的列表（作为[key,value]）。键为字符串，值可为任意JSON值。返回[[key,value],...]，保留输入顺序和重复键，输入不得被修改。其他条目格式引发ValueError。只用标准库，内部结构自由。",
     "reference": pairs_reference, "alternate": pairs_alternate,
     "public": [{"value":["a",{"b":2},["c",3]]}, {"value":["a","a"],"default":"x"}],
     "private": [{"value":[]},{"value":[{}]},{"value":[{"a":1,"b":2}]},{"value":[["a"]]},{"value":[7]},{"value":[["a",None],"b"],"default":0}]},
]

def populate_cases():
    rng = random.Random(20261008)
    for task in TASKS:
        if task["id"] == "D1_B01":
            for _ in range(12):
                a,b,c = [rng.randrange(0,20) for _ in range(3)]
                task["private"].append({"text":f"{a}-{b},{c},{a}"})
        elif task["id"] == "D1_M01":
            for length,n,step in [(1,1,1),(3,2,1),(4,3,2),(5,3,2),(7,3,4),(9,2,5),(6,2,2),(2,5,4),(10,4,3),(12,1,4),(3,3,9)]:
                task["private"].append({"items":list(range(length)),"width":n,"step":step,"fill":"pad"})
        elif task["id"] == "D1_M02":
            for limit in [-1,0,1,2]:
                for _ in range(3):
                    task["private"].append({"items":[rng.randrange(-3,4) for _ in range(15)],"maxsplit":limit})
        elif task["id"] == "D1_B02":
            task["private"].append({"operations":[]})
            for _ in range(16):
                ops=[]
                for _ in range(18):
                    op={"op":rng.choice(["add","set","get","getall","poplast","delete"]),"key":rng.choice(["a","b","c"])}
                    if op["op"] in ["add","set"]:op["value"]=rng.choice([None,0,1,"x",[2]])
                    if op["op"]=="get":op["default"]="missing"
                    ops.append(op)
                task["private"].append({"operations":ops})
            task["private"].append({"operations":[{"op":"add","key":"a","value":1},
                {"op":"add","key":"a","value":2},{"op":"poplast","key":"a"},
                {"op":"getall","key":"a"},{"op":"delete","key":"a"},
                {"op":"poplast","key":"a"},{"op":"add","key":"b","value":None}]})
        elif task["id"] in ["D1_C01","D1_C02"]:
            timed=task["id"]=="D1_C02"
            for _ in range(18):
                ops=[]; now=0
                for index in range(22):
                    name=rng.choice(["put","put","get","get","contains","delete","snapshot","clear"])
                    op={"op":name,"key":rng.choice(["a","b","c","d"])}
                    if name=="put":op["value"]=rng.choice([None,0,1,"x",[2]])
                    if timed:
                        now+=rng.randrange(0,3); op["time"]=now
                    ops.append(op)
                p={"capacity":rng.randrange(0,4),"operations":ops}
                if timed:p["ttl"]=rng.choice([0,1,3,8])
                task["private"].append(p)
            # Observe membership without refreshing recency; then force eviction.
            observation_ops=[{"op":"put","key":"a","value":1},
                             {"op":"put","key":"b","value":2},
                             {"op":"contains","key":"a"},
                             {"op":"snapshot"},
                             {"op":"put","key":"c","value":3}]
            observation_case={"capacity":2,"operations":observation_ops}
            if timed:
                observation_case["ttl"]=10
                for index,op in enumerate(observation_ops):op["time"]=index
            task["private"].append(observation_case)
            zero_ops=[{"op":"put","key":"a","value":1},{"op":"get","key":"a"},
                      {"op":"contains","key":"a"},{"op":"snapshot"},{"op":"clear"}]
            zero_case={"capacity":0,"operations":zero_ops}
            if timed:
                zero_case["ttl"]=3
                for index,op in enumerate(zero_ops):op["time"]=index
            task["private"].append(zero_case)
            if timed:
                task["private"].append({"capacity":2,"ttl":0,"operations":[
                    {"op":"put","key":"a","value":1,"time":0},
                    {"op":"get","key":"a","time":0},{"op":"contains","key":"a","time":0}]})
        elif task["id"] == "D1_F01":
            task["private"] += [{"value":"你好\n世界"},{"value":"\n \t"},{"value":["", " "]},{"value":True},{"value":{}},{"value":["x",None]}]
        elif task["id"] == "D1_F02":
            task["private"] += [{"value":["",{"x":[1,2]},["x",{"a":3}]]},{"value":[["a",1,2]]},{"value":[None]},{"value":["你好",{"世界":True}]},{"value":[["x",0],["x",1]]}]

populate_cases()

def outcome(function, payload):
    import copy
    try:
        return {"value": function(copy.deepcopy(payload))}
    except Exception as exc:
        return {"error": type(exc).__name__}

MANUAL_PUBLIC_OUTCOMES = {
    "D1_B01": [{"value":[1,3,3,4,5]},{"value":[2,7,8,9]}],
    "D1_B02": [{"value":[
        {"result":None,"items":[["a",1]]},
        {"result":None,"items":[["a",1],["b",2]]},
        {"result":None,"items":[["a",1],["b",2],["a",3]]},
        {"result":[1,3],"items":[["a",1],["b",2],["a",3]]}]},{"value":[]}],
    "D1_M01": [{"value":[[1,2,3],[2,3,4],[3,4,5]]},{"value":[[1,2,"x","x"]]}],
    "D1_M02": [{"value":[[1,3],[2,2,4],[0]]},{"value":[]}],
    "D1_C01": [{"value":[
        {"result":None,"items":[["a",1]],"size":1},
        {"result":None,"items":[["a",1],["b",2]],"size":2},
        {"result":1,"items":[["a",1],["b",2]],"size":2},
        {"result":None,"items":[["a",1],["c",3]],"size":2}]},{"value":[]}],
    "D1_C02": [{"value":[
        {"result":None,"items":[["a",1]],"size":1},
        {"result":1,"items":[["a",1]],"size":1},
        {"result":{"error":"KeyError"},"items":[],"size":0}]},{"value":[]}],
    "D1_F01": [{"value":["alpha","beta"]},{"value":["a b","c"]}],
    "D1_F02": [{"value":[["a",None],["b",2],["c",3]]},{"value":[["a","x"],["a","x"]]}],
}
