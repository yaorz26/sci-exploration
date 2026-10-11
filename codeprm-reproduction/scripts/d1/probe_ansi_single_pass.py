"""P54：原始输入版本上的ANSI匹配与两类删除阶段；不读取原测试。"""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/raw/d1_project_v1_20261008/repositories/boltons/boltons/strutils.py"
TASK = ROOT / "data/processed/d1_project_initial20_v5_20261008/public/D1_B03/task.json"
OUT = ROOT / "experiments/d1_ansi_single_pass_v1_20261009"
ESC = "\x1b"
CASES = [
    {"id": "plain_control", "text": "plain", "expected": "plain", "reason": "无ESC，逐字保留"},
    {"id": "ordinary_codes", "text": "a" + ESC + "[31mRed" + ESC + "Mz", "expected": "aRedz", "reason": "原串一CSI和一短码，各独立删除"},
    {"id": "CSI_creates_short", "text": ESC + ESC + "[31mM", "expected": ESC + "M", "reason": "最前ESC在原串无有效下一字，删第二个ESC的CSI后才邻接M"},
    {"id": "short_creates_CSI", "text": ESC + ESC + "M[31m", "expected": ESC + "[31m", "reason": "删第二个ESC的短码后，最前ESC才邻接CSI后缀"},
    {"id": "CSI_creates_CSI", "text": ESC + ESC + "[31m[0m", "expected": ESC + "[0m", "reason": "一次原串删中间CSI，保留原来不完整首ESC/余下后缀"},
    {"id": "incomplete_control", "text": ESC + "[31", "expected": ESC + "[31", "reason": "缺CSI终止字，完整片段未匹配"},
]
SHORT = re.compile(r"\x1b[@-Z\\-_]")
CSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def match_end(text, position):
    """独立字符扫描：返回原串上的完整匹配终点，失败为None。"""
    if text[position] != ESC or position + 1 >= len(text):
        return None
    char = text[position + 1]
    if "@" <= char <= "Z" or "\\" <= char <= "_":
        return position + 2
    if char != "[":
        return None
    cursor = position + 2
    while cursor < len(text) and "0" <= text[cursor] <= "?":
        cursor += 1
    while cursor < len(text) and " " <= text[cursor] <= "/":
        cursor += 1
    if cursor < len(text) and "@" <= text[cursor] <= "~":
        return cursor + 1
    return None


def scan_once(text):
    kept, position = [], 0
    while position < len(text):
        end = match_end(text, position)
        if end is None:
            kept.append(text[position])
            position += 1
        else:
            position = end
    return "".join(kept)


def worker():
    spec = importlib.util.spec_from_file_location("d1_p54_strutils", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    functions = {
        "upstream": module.strip_ansi,
        "independent_scan": scan_once,
        "CSI_then_short": lambda text: SHORT.sub("", CSI.sub("", text)),
        "short_then_CSI": lambda text: CSI.sub("", SHORT.sub("", text)),
    }
    rows = []
    for case in CASES:
        payload = {"text": case["text"]}
        before = copy.deepcopy(payload)
        results = {name: fn(payload["text"]) for name, fn in functions.items()}
        # 复用一次来源结果，只增加一次来源查询，不再求原输入一次来源。
        twice = module.strip_ansi(results["upstream"])
        rows.append({"id": case["id"], "expected": case["expected"], "results": results,
                     "twice_source": twice, "idempotent": twice == results["upstream"], "input_unchanged": payload == before})
    print(json.dumps({"rows": rows, "structure_evaluations": 24, "second_source_queries": 6,
                      "upstream_strip_calls": 12}, ensure_ascii=False))


def main():
    if "--worker" in sys.argv:
        worker()
        return
    OUT.mkdir(exist_ok=False)
    source_text = SOURCE.read_text(encoding="utf-8")
    tree = ast.parse(source_text)
    nodes = [node for node in tree.body if (isinstance(node, ast.FunctionDef) and node.name == "strip_ansi")
             or (isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "ANSI_SEQUENCES" for target in node.targets))]
    save("public_rules_and_six_anchors_frozen.json", {
        "created_at": datetime.now(timezone.utc).isoformat(), "cases": CASES,
        "task": json.loads(TASK.read_text(encoding="utf-8")), "task_sha256": sha(TASK), "source_sha256": sha(SOURCE),
        "script_sha256": sha(Path(__file__)), "source_commit": "4e5faa3d7e4008d89e0d8bf1ea87b6d9a061a16d",
        "source_nodes": [{"lines": [node.lineno, node.end_lineno], "text": ast.get_source_segment(source_text, node)} for node in nodes],
        "interpretation": "按来源单次sub的原串非重叠匹配；原题尚未显式写单次，不回称规范完全独立冻结",
        "expected_provenance": "执行前逐值解析，未从执行结果导出，非人类真值",
        "budget": {"structure_evaluations": 24, "second_source_queries": 6, "model_calls": 0, "hidden_reads": 0},
    })
    response = subprocess.run([sys.executable, "-B", "-X", "utf8", str(Path(__file__)), "--worker"],
                              capture_output=True, text=True, encoding="utf-8", timeout=20)
    save("worker_raw.json", {"returncode": response.returncode, "stdout": response.stdout, "stderr": response.stderr})
    if response.returncode:
        raise RuntimeError("保留新失败，不自动重复旧执行")
    result = json.loads(response.stdout)
    save("structure_result.json", result)
    rows = result["rows"]
    summary = {"scores": {name: [sum(row["results"][name] == row["expected"] and row["input_unchanged"] for row in rows), 6]
                          for name in ("upstream", "independent_scan", "CSI_then_short", "short_then_CSI")},
               "idempotent_count": sum(row["idempotent"] for row in rows), "nonidempotent_ids": [row["id"] for row in rows if not row["idempotent"]],
               "structures_evaluations": 24, "second_source_queries": 6, "upstream_strip_calls": 12,
               "all_inputs_unchanged": all(row["input_unchanged"] for row in rows), "rows": rows,
               "interpretation": "原始版本单次删除可能制造新完整码，两个类别分阶段重新扫描各有不同错误；独立扫描保持原串位置，不能把局部类别正确视为连接安全。",
               "limits": ["仅六新锚点/单次解释来自固定来源", "原题单次措辞待澄清，不改原数据/标签/旧评分", "非旧P9模型失败算法归因，主A效果未知", "人工0/不含原或私测"],
               "model_calls": 0, "API_calls": 0, "hidden_reads": 0, "new_downloads": 0}
    save("summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
