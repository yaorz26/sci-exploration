"""P50：实际评分单次执行，同时保存构造消费者轨迹；原评分器不改。"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from bounded_execution import evaluate

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_output_type_composition_v1_20261009"
CONTROLS = [
    {"id": "integer", "literal": "1", "predicted_original_pass": True, "predicted_consumer_correct": True, "predicted_joint_gate": True},
    {"id": "float", "literal": "1.0", "predicted_original_pass": True, "predicted_consumer_correct": False, "predicted_joint_gate": False},
    {"id": "bool", "literal": "True", "predicted_original_pass": False, "predicted_consumer_correct": True, "predicted_joint_gate": False},
    {"id": "wrong_integer", "literal": "2", "predicted_original_pass": False, "predicted_consumer_correct": False, "predicted_joint_gate": False},
]
CASE = {"case_id": "new_type_composition", "input": {"data": ["x"]}, "expected": {"value": {"count": 1, "mode": "x"}}}


def save(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    OUT.mkdir(exist_ok=False)
    programs = {}
    for row in CONTROLS:
        name, literal = row["id"], row["literal"]
        source = f'''import json
from pathlib import Path

def solve(payload):
    observed = {{"count": {literal}, "mode": "x"}}
    trace = {{"returned": observed, "count_type": type(observed["count"]).__name__}}
    try:
        trace["consumer"] = {{"value": list(range(observed["count"]))}}
    except Exception as exc:
        trace["consumer"] = {{"error": type(exc).__name__}}
    with Path(__file__).with_name("{name}_trace.json").open("x", encoding="utf-8") as handle:
        json.dump(trace, handle, ensure_ascii=False, allow_nan=False)
    return observed
'''
        path = OUT / (name + ".py")
        path.write_text(source, encoding="utf-8")
        programs[name] = path
    save("case.json", [CASE])
    save("predictions_and_programs_frozen.json", {
        "created_at": datetime.now(timezone.utc).isoformat(), "case": CASE, "controls": CONTROLS,
        "consumer": "list(range(returned.count))", "consumer_expected": {"value": [0]},
        "program_sha256": {name: sha(path) for name, path in programs.items()},
        "original_comparator_sha256": sha(ROOT / "scripts/d1/evaluate_candidate.py"),
        "output_shape_candidate": "type(returned.count) is int", "upstream_consumer": False,
        "budget": {"solve_calls": 4, "consumer_calls": 4, "shape_comparisons": 4, "model_calls": 0, "hidden_reads": 0},
    })
    rows = []
    for control in CONTROLS:
        name = control["id"]
        scored = evaluate(programs[name], OUT / "case.json")
        save(name + "_bounded_result.json", scored)
        trace = json.loads((OUT / (name + "_trace.json")).read_text(encoding="utf-8"))
        consumer_correct = trace["consumer"] == {"value": [0]}
        shape = type(trace["returned"]["count"]) is int
        joint = shape and scored["all_pass"]
        rows.append({**control, "original_pass": scored["all_pass"], "consumer_correct": consumer_correct,
                     "count_shape_int": shape, "joint_gate": joint, "trace": trace,
                     "predictions_matched": (scored["all_pass"] == control["predicted_original_pass"] and consumer_correct == control["predicted_consumer_correct"] and joint == control["predicted_joint_gate"])})
    summary = {"rows": rows, "predictions_matched": sum(row["predictions_matched"] for row in rows),
               "new_solve_calls": 4, "consumer_calls": 4, "shape_comparisons": 4,
               "original_pass_float_consumer_error": rows[1]["original_pass"] and rows[1]["trace"]["consumer"] == {"error": "TypeError"},
               "interpretation": "相同JSON数值计分不保证显式整数数量的消费兼容；只证公开构造消费者与E_B09整数声明冲突，不证明已有真实项目调用点。",
               "future_candidate_decision": "E_B09需候选专属整数输出门槛/类型等价，正式冻结前验证；原评分器与原20/旧成绩不改",
               "model_calls": 0, "API_calls": 0, "hidden_reads": 0, "old_candidate_diagnostic_calls": 0}
    save("summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
