"""P44：离散Stats候选的有限、逐值契约探针；不读取测试/private。"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/raw/d1_project_v1_20261008/repositories/boltons/boltons/statsutils.py"
DOC = ROOT / "data/raw/d1_project_v1_20261008/repositories/boltons/docs/statsutils.rst"
OUT = ROOT / "experiments/d1_discrete_stats_candidate_v1_20261009"

CASES = [
    {"id": "d01", "data": [1, 2, 2, 3], "default": None},
    {"id": "d02", "data": ["a", "b", "b", "a", "a"], "default": None},
    {"id": "d03", "data": [3, 1, 3, 1], "default": None},
    {"id": "d04", "data": [], "default": -1},
    {"id": "d05", "data": [0, 0, 2], "default": 99},
    {"id": "d06", "data": [-2, -2, -1], "default": None},
]

WHOLE = '''def solve(payload):
    values = payload["data"]
    default = payload.get("default")
    if not values:
        return {"count": 0, "mode": default}
    counts = {}
    first = {}
    for index, value in enumerate(values):
        counts[value] = counts.get(value, 0) + 1
        first.setdefault(value, index)
    best = min(counts, key=lambda value: (-counts[value], first[value]))
    return {"count": len(values), "mode": best}
'''

HELPERS = '''def _count(values):
    return len(values)

def _mode(values, default):
    if not values:
        return default
    counts = Counter(values)
    first = {}
    for index, value in enumerate(values):
        first.setdefault(value, index)
    return min(counts, key=lambda value: (-counts[value], first[value]))

def solve(payload):
    values = payload["data"]
    return {"count": _count(values), "mode": _mode(values, payload.get("default"))}
'''

WRONG = '''def solve(payload):
    values = payload["data"]
    if not values:
        return {"count": 0, "mode": payload.get("default")}
    counts = Counter(values)
    # 错误：并列时按可排序值选，而不是按首次出现选。
    return {"count": len(values), "mode": sorted(counts, key=lambda value: (-counts[value], value))[0]}
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_code(name, code):
    namespace = {"Counter": Counter}
    exec(compile(code, name, "exec"), namespace)
    return namespace["solve"]


def main():
    if OUT.exists():
        raise FileExistsError("旧机器输出不得覆盖")
    OUT.mkdir()
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    stats = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Stats")
    mode_node = next(node for node in stats.body if isinstance(node, ast.FunctionDef) and node.name == "_calc_mode")
    frozen = {"created_at": datetime.now(timezone.utc).isoformat(), "source": str(SOURCE.relative_to(ROOT)),
              "source_sha256": sha(SOURCE), "docs": str(DOC.relative_to(ROOT)), "docs_sha256": sha(DOC),
              "mode_source_lines": [mode_node.lineno, mode_node.end_lineno], "cases": CASES,
              "contract": {"input": "有限、可哈希整数或字符串列表", "count_empty": 0,
                           "mode_empty": "payload.default", "mode_tie": "首次出现", "outputs": ["count", "mode"]},
              "program_names": ["whole", "helpers", "wrong_tie"], "model_calls": 0, "API_calls": 0,
              "task_evaluations": 0, "hidden_reads": 0}
    (OUT / "source_contract_frozen.json").write_text(json.dumps(frozen, ensure_ascii=False, indent=2), encoding="utf-8")
    programs = {"whole": WHOLE, "helpers": HELPERS, "wrong_tie": WRONG}
    for name, code in programs.items():
        (OUT / (name + ".py")).write_text(code, encoding="utf-8")
    funcs = {name: load_code(name, code) for name, code in programs.items()}
    expected = []
    rows = []
    for case in CASES:
        values = case["data"]
        if not values:
            mode = case["default"]
        else:
            counts = Counter(values)
            first = {value: values.index(value) for value in counts}
            mode = min(counts, key=lambda value: (-counts[value], first[value]))
        exp = {"count": len(values), "mode": mode}
        expected.append({"id": case["id"], "expected": exp})
        rows.append({"id": case["id"], "expected": exp,
                     "results": {name: fn({"data": list(values), "default": case["default"]}) for name, fn in funcs.items()}})
    checks = []
    for row in rows:
        for name, result in row["results"].items():
            checks.append({"id": row["id"], "program": name, "json_equal": result == row["expected"],
                           "expected": row["expected"], "observed": result})
    summary = {"status": "离散Stats候选有限契约探针完成", "source_sha256": sha(SOURCE), "docs_sha256": sha(DOC),
               "cases": len(CASES), "programs": len(programs), "checks": len(checks),
               "pass_by_program": {name: sum(c["json_equal"] for c in checks if c["program"] == name) for name in programs},
               "whole_and_helpers_agree_all": all(c["json_equal"] for c in checks if c["program"] in {"whole", "helpers"}),
               "wrong_tie_rejected": any(not c["json_equal"] for c in checks if c["program"] == "wrong_tie"),
               "interpretation": "count与mode的用途和逐值输出可分开，整体实现与两个helper实现都通过6个冻结输入；并列按首次出现的错误实现被至少一个并列样例拒绝。该证据只支持有限契约，不能证明全域或主A收益。",
               "limits": ["6个输入/3个本地实现/18个比较，不是人工复核或模型生成", "仅整数/字符串可哈希域；不覆盖自定义对象/NaN/异步输入", "Stats源码mode的并列语义被写入候选契约，不能当作者标签真值", "扩展候选另池，原20/307/11—9与评分规则不变", "模型/API/下载/原测试/private读取均0"], "model_calls": 0, "API_calls": 0, "hidden_reads": 0}
    (OUT / "summary.json").write_text(json.dumps({"frozen": frozen, "rows": rows, "checks": checks, "summary": summary}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
