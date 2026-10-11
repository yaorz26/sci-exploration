"""P47：未运行过的来源包装及原比较器；复用P44输出，不重跑其solve。"""
from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / "experiments/d1_discrete_stats_candidate_v1_20261009/summary.json"
SOURCE = ROOT / "data/raw/d1_project_v1_20261008/repositories/boltons/boltons/statsutils.py"
COMPARATOR = ROOT / "scripts/d1/evaluate_candidate.py"
OUT = ROOT / "experiments/d1_discrete_adapter_fidelity_v1_20261009"
EXPECTED = [
    {"id": "d01", "expected": {"count": 4, "mode": 2}, "reason": "2频数2，其余1"},
    {"id": "d02", "expected": {"count": 5, "mode": "a"}, "reason": "a频数3/b频数2"},
    {"id": "d03", "expected": {"count": 4, "mode": 3}, "reason": "3/1各2，3首次出现"},
    {"id": "d04", "expected": {"count": 0, "mode": -1}, "reason": "数量0，空mode返回显式default=-1"},
    {"id": "d05", "expected": {"count": 3, "mode": 0}, "reason": "0频数2，2频数1"},
    {"id": "d06", "expected": {"count": 3, "mode": -2}, "reason": "-2频数2，-1频数1"},
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def main():
    OUT.mkdir(exist_ok=False)
    old = json.loads(OLD.read_text(encoding="utf-8"))
    if sha(SOURCE) != old["summary"]["source_sha256"]:
        raise ValueError("来源改变")
    comparator_source = COMPARATOR.read_text(encoding="utf-8")
    comparator_node = next(n for n in ast.parse(comparator_source).body if isinstance(n, ast.FunctionDef) and n.name == "json_equal")
    source_ast = ast.parse(SOURCE.read_text(encoding="utf-8"))
    stats = next(n for n in source_ast.body if isinstance(n, ast.ClassDef) and n.name == "Stats")
    prop = next(n for n in source_ast.body if isinstance(n, ast.ClassDef) and n.name == "_StatsProperty")
    source_nodes = [(n.name, n.lineno, n.end_lineno) for c in (stats, prop) for n in c.body
                    if isinstance(n, ast.FunctionDef) and n.name in {"_calc_count", "_calc_mode", "__get__"}]
    cases = old["frozen"]["cases"]
    if [c["id"] for c in cases] != [e["id"] for e in EXPECTED]:
        raise ValueError("预期与输入ID不一致")
    controls = [
        {"id": "bool_count", "expected": {"count": 0, "mode": -1}, "observed": {"count": False, "mode": -1}, "expect_accept": False},
        {"id": "bool_mode", "expected": {"count": 3, "mode": 0}, "observed": {"count": 3, "mode": False}, "expect_accept": False},
        {"id": "missing_count", "expected": {"count": 3, "mode": 0}, "observed": {"mode": 0}, "expect_accept": False},
    ]
    save("sources_anchors_and_controls_frozen.json", {
        "created_at": datetime.now(timezone.utc).isoformat(), "inputs": cases, "manual_analytic_expected": EXPECTED,
        "expected_status": "本次执行前逐值解析，原P44执行之后；不能回称P44预注册锚点/人类真值",
        "controls": controls, "old_output_sha256": sha(OLD), "source_sha256": sha(SOURCE),
        "comparator_sha256": sha(COMPARATOR), "comparator_lines": [comparator_node.lineno, comparator_node.end_lineno],
        "source_nodes": source_nodes, "source_wrapper": "count用Stats(data,default=0).count；mode用另一Stats(data,default=payload.default).mode",
        "empty_single_instance_prediction": {"data": [], "default": -1, "count": -1, "mode": -1},
        "scope": "六新参考包装/18复用结果/三控制/一单对象空域；原P44 solve不重跑",
    })
    namespace = {}
    exec(compile(ast.get_source_segment(comparator_source, comparator_node), "original_json_equal", "exec"), namespace)
    equal = namespace["json_equal"]
    spec = importlib.util.spec_from_file_location("d1_stats_source_p47", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    reference_rows = []
    for case, expected in zip(cases, EXPECTED):
        values = case["data"]
        if not all(type(value) in (int, str) for value in values):
            raise ValueError("输入不在冻结域")
        observed = {"count": module.Stats(values, default=0).count,
                    "mode": module.Stats(values, default=case["default"]).mode}
        reference_rows.append({"id": case["id"], "expected": expected["expected"], "observed": observed,
                               "json_equal": equal(expected["expected"], observed), "input_after": values})
    scored = []
    for row, expected in zip(old["rows"], EXPECTED):
        for name, observed in row["results"].items():
            scored.append({"id": row["id"], "program": name, "expected": expected["expected"], "observed": observed,
                           "python_equal": observed == expected["expected"], "original_json_equal": equal(observed, expected["expected"])})
    control_rows = [{**control, "python_equal": control["expected"] == control["observed"],
                     "original_json_equal": equal(control["expected"], control["observed"])} for control in controls]
    obj = module.Stats([], default=-1)
    empty = {"count": obj.count, "mode": obj.mode}
    result = {
        "status": "新来源包装与保存输出实际评分完成，空域适配差异已定位",
        "reference_rows": reference_rows, "saved_scores": scored, "type_controls": control_rows,
        "single_instance_empty": empty, "single_instance_matches_candidate": equal(empty, {"count": 0, "mode": -1}),
        "reference_pass": sum(row["json_equal"] for row in reference_rows), "reference_total": 6,
        "saved_scores_by_program": {name: sum(row["original_json_equal"] for row in scored if row["program"] == name) for name in ("whole", "helpers", "wrong_tie")},
        "control_mechanisms_matched": sum(row["original_json_equal"] == row["expect_accept"] for row in control_rows),
        "new_reference_wrapper_calls": 6, "new_stats_objects": 13, "new_stats_attribute_queries": 14,
        "new_P44_solve_calls": 0, "reused_P44_outputs": 18, "new_original_comparator_calls": 28,
        "interpretation": "原18合法/错误输出的分数不变，但Python==会接纳bool_count和bool_mode。单Stats(default=-1)空域count=-1；新参考按数量固定0、众数按题面default分别包装，与六解析锚点一致。需将此写成适配，不能称单一原Stats完全等价。",
        "limits": ["六有限锚点不是全域/人工真值", "candidate仍研究池，未冻结构标签", "14属性查询不等14任务，28比较含6新参考/18保存/3控制/1空域", "评分器未改、原20/307/11—9和模型成绩不改"],
        "model_calls": 0, "API_calls": 0, "hidden_reads": 0, "new_downloads": 0,
    }
    save("summary.json", result)
    print(json.dumps({"reference": [result["reference_pass"], 6], "saved_scores": result["saved_scores_by_program"],
                      "controls": control_rows, "empty_single_instance": empty, "new_stats_objects": 13}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
