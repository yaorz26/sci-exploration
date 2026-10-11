#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PR142 与 PR440 的上游保真度实测（子进程隔离、只读、零模型调用）。"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ROOT = REPO.parent

PR142 = REPO / "experiments/d1_G2_confuse_pr142_env_source_v1_20261009"
PR440 = REPO / "experiments/d1_G2_more_pr440_group_lifetime_v1_20261009"

# ---------------- PR142 ----------------
PR142_CHILD = textwrap.dedent('''
    import json, os, sys, tempfile
    from pathlib import Path
    root = Path(sys.argv[1]); sys.path.insert(0, str(root))
    import confuse

    def fresh_env(vars_):
        for k in list(os.environ):
            if k.startswith(("D1X_", "D1Y_")):
                del os.environ[k]
        os.environ.update(vars_)

    def write_cfg(text):
        d = tempfile.mkdtemp(prefix="d1_")
        p = Path(d) / "c.yaml"; p.write_text(text, encoding="utf-8"); return str(p)

    rec = {}
    # 规则：set_env 返回 None
    try:
        fresh_env({"D1X_A": "1"})
        c = confuse.Configuration("t", read=False); c.set_file(write_cfg("a: 0\\n"))
        rec["set_env_returns"] = repr(c.set_env(prefix="D1X_"))
    except Exception as e:
        rec["set_env_returns"] = f"<{type(e).__name__}: {e}>"
    # 规则：前缀原样拼接（D1X_ 匹配 D1X_A；D1X 也匹配 D1XA）
    for prefix, env, label in (("D1X_", {"D1X_A": "5"}, "prefix_with_underscore"),
                               ("D1X", {"D1XA": "5"}, "prefix_without_underscore_matches_joined")):
        try:
            fresh_env(env)
            c = confuse.Configuration("t", read=False); c.set_file(write_cfg("a: 0\\n"))
            c.set_env(prefix=prefix)
            rec[label] = repr(c["a"].get(int))
        except Exception as e:
            rec[label] = f"<{type(e).__name__}: {e}>"
    # 规则：小写转换与嵌套
    try:
        fresh_env({"D1X_HOST": "h", "D1X_DB__PORT": "5432"})
        c = confuse.Configuration("t", read=False); c.set_file(write_cfg("x: 0\\n"))
        c.set_env(prefix="D1X_")
        rec["lowercase_key"] = repr(c["host"].get(str))
        rec["nested_key"] = repr(c["db"]["port"].get(int))
    except Exception as e:
        rec["lowercase_key"] = rec["nested_key"] = f"<{type(e).__name__}: {e}>"
    # 规则：叶子级合并（文件给 db.host，环境给 db.port）
    try:
        fresh_env({"D1X_DB__PORT": "5432"})
        c = confuse.Configuration("t", read=False); c.set_file(write_cfg("db:\\n  host: filehost\\n"))
        c.set_env(prefix="D1X_")
        rec["leaf_merge"] = {"host": repr(c["db"]["host"].get(str)), "port": repr(c["db"]["port"].get(int))}
    except Exception as e:
        rec["leaf_merge"] = f"<{type(e).__name__}: {e}>"
    # 规则：无匹配时保持原值
    try:
        fresh_env({})
        c = confuse.Configuration("t", read=False); c.set_file(write_cfg("a: 7\\n"))
        c.set_env(prefix="D1X_")
        rec["no_match_keeps_value"] = repr(c["a"].get(int))
    except Exception as e:
        rec["no_match_keeps_value"] = f"<{type(e).__name__}: {e}>"
    # 规则：域外行为
    for label, env, prefix in (("empty_suffix_ignored", {"D1X_": "1"}, "D1X_"),
                               ("empty_segment_A__", {"D1X_A__": "1"}, "D1X_"),
                               ("empty_segment_A___B", {"D1X_A___B": "1"}, "D1X_"),
                               ("nested_positive_A__B", {"D1X_A__B": "1"}, "D1X_")):
        try:
            fresh_env(env)
            c = confuse.Configuration("t", read=False); c.set_file(write_cfg("z: 0\\n"))
            c.set_env(prefix=prefix)
            rec[label] = "ok:" + repr(c["a"]["b"].get(int) if "positive" in label else None)
        except Exception as e:
            rec[label] = f"<{type(e).__name__}: {e}>"
    try:
        fresh_env({"D1X_A": "1"})
        c = confuse.Configuration("t", read=False); c.set_file(write_cfg("a: 1\\n"))
        c.set_env(prefix="")
        rec["empty_prefix"] = "no_exception"
    except Exception as e:
        rec["empty_prefix"] = f"<{type(e).__name__}: {e}>"
    try:
        fresh_env({"D1X_A": "[1,2]"})
        c = confuse.Configuration("t", read=False); c.set_file(write_cfg("a: 0\\n"))
        c.set_env(prefix="D1X_")
        rec["collection_value"] = repr(c["a"].get())
    except Exception as e:
        rec["collection_value"] = f"<{type(e).__name__}: {e}>"
    print(json.dumps(rec, ensure_ascii=False, default=str))
''')

# ---------------- PR440 ----------------
PR440_CHILD = textwrap.dedent('''
    import json, sys
    from pathlib import Path
    root = Path(sys.argv[1]); sys.path.insert(0, str(root))
    import more_itertools as mi

    rec = {}
    kf = lambda x: x[0]
    vf10 = lambda x: x[1] * 10
    vf1 = lambda x: x[1] * 1

    # 公开用例 1
    try:
        items = [("a",1),("a",2),("b",3),("a",4)]
        out = list(mi.groupby_transform(items, keyfunc=kf, valuefunc=vf10, reducefunc=list))
        rec["case1_retained_lists"] = out
    except Exception as e:
        rec["case1_retained_lists"] = f"<{type(e).__name__}: {e}>"
    # 公开用例 2
    try:
        items = [(0,2),(0,4),(1,1),(1,3)]
        out = list(mi.groupby_transform(items, keyfunc=kf, valuefunc=vf1, reducefunc=sum))
        rec["case2_group_sums"] = out
    except Exception as e:
        rec["case2_group_sums"] = f"<{type(e).__name__}: {e}>"
    # 公开用例 3：不传 reducefunc，推进后第一组应为空
    try:
        items = [("a",1),("a",2),("b",3)]
        it = mi.groupby_transform(items, keyfunc=kf, valuefunc=vf1)
        first_key, first_group = next(it)
        first_after = list(first_group)
        second_key, second_group = next(it)
        second_now = list(second_group)
        rec["case3_no_reducer"] = {"first_key": first_key, "first_after_advance": first_after,
                                   "second_key": second_key, "second_now": second_now}
    except Exception as e:
        rec["case3_no_reducer"] = f"<{type(e).__name__}: {e}>"
    # 父版本对照：不传 reducefunc 时签名是否存在 reducefunc 参数
    try:
        import inspect
        rec["signature"] = str(inspect.signature(mi.groupby_transform))
    except Exception as e:
        rec["signature"] = f"<{type(e).__name__}: {e}>"
    print(json.dumps(rec, ensure_ascii=False, default=str))
''')


def run(code: str, arg: str) -> dict:
    p = subprocess.run([sys.executable, "-B", "-X", "utf8", "-c", code, arg],
                       capture_output=True, text=True, encoding="utf-8", timeout=180)
    if p.returncode != 0:
        return {"_error": p.stderr.strip()[-700:]}
    try:
        return json.loads(p.stdout)
    except (ValueError, TypeError):
        return {"_raw": p.stdout[:600], "_stderr": p.stderr[:300]}


PR142_CONTRACT = {
    "set_env_returns": "None",
    "prefix_with_underscore": "5",
    "prefix_without_underscore_matches_joined": "5",
    "lowercase_key": "'h'",
    "nested_key": "5432",
    "leaf_merge": {"host": "'filehost'", "port": "5432"},
    "no_match_keeps_value": "7",
    "empty_suffix_ignored": "ok:None",
    "empty_segment_A__": "<ValueError",
    "nested_positive_A__B": "ok:1",
    "empty_prefix": "<ValueError",
    "collection_value": "<ValueError",
}

PR440_CONTRACT = {
    "case1_retained_lists": [("a", [10, 20]), ("b", [30]), ("a", [40])],
    "case2_group_sums": [(0, 6), (1, 4)],
    "case3_no_reducer": {"first_key": "a", "first_after_advance": [],
                         "second_key": "b", "second_now": [3]},
}


def compare(up: dict, contract: dict) -> list:
    rows = []
    for k, expected in contract.items():
        got = up.get(k)
        def norm(v):
            if isinstance(v, str) and "（" in v:
                return v.split("（")[0].strip()
            return v
        exp = norm(expected)
        gs = json.dumps(got, ensure_ascii=False, default=str) if not isinstance(got, str) else got
        es = json.dumps(exp, ensure_ascii=False, default=str) if not isinstance(exp, str) else exp
        if isinstance(exp, str) and exp.startswith("<") and gs.startswith("<"):
            ok = gs.split(":")[0] == exp
        else:
            ok = gs == es
        rows.append({"rule": k, "upstream": got, "contract": exp, "matches": bool(ok)})
    return rows


def main() -> int:
    stamp = datetime.now(timezone.utc).isoformat()
    out = {"created_at": stamp, "purpose": "决策 2：上游保真度实测", "model_calls": 0,
           "discipline": "只读；不读上游测试；不修改冻结候选；子进程隔离", "candidates": {}}

    src142 = PR142 / "merge/confuse/core.py"
    up142 = run(PR142_CHILD, str((PR142 / "merge").resolve()))
    rows142 = compare(up142, PR142_CONTRACT)
    out["candidates"]["PR142"] = {
        "upstream_parent": str((PR142 / "parent").relative_to(ROOT)),
        "upstream_merge": str((PR142 / "merge").relative_to(ROOT)),
        "merge_core_sha256": hashlib.sha256(src142.read_bytes()).hexdigest() if src142.is_file() else None,
        "parent_has_set_env": False, "merge_has_set_env": True,
        "raw": up142, "rows": rows142,
        "agreement": {"matches": sum(r["matches"] for r in rows142), "total": len(rows142)},
    }

    src440 = PR440 / "feature/more_itertools/more.py"
    up440 = run(PR440_CHILD, str((PR440 / "feature").resolve()))
    rows440 = compare(up440, PR440_CONTRACT)
    out["candidates"]["PR440"] = {
        "upstream_parent": str((PR440 / "parent").relative_to(ROOT)),
        "upstream_feature": str((PR440 / "feature").relative_to(ROOT)),
        "feature_more_sha256": hashlib.sha256(src440.read_bytes()).hexdigest() if src440.is_file() else None,
        "raw": up440, "rows": rows440,
        "agreement": {"matches": sum(r["matches"] for r in rows440), "total": len(rows440)},
    }

    (HERE / "fidelity_PR142_PR440.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    for name, c in out["candidates"].items():
        ag = c["agreement"]
        print(f"== {name} ==  一致 {ag['matches']}/{ag['total']}")
        for r in c["rows"]:
            print(f"  {'✓' if r['matches'] else '✗'} {r['rule']:42s} 上游={r['upstream']!r:44s} 规则={r['contract']!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
