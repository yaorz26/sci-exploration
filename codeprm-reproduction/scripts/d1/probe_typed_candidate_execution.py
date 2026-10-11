"""P59：另版候选的JSON执行/类型/错误/输入不变；不读原测试。"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_typed_candidate_execution_v1_20261009"
OLD = ROOT / "experiments/d1_discrete_candidate_boundary_v1_20261009/candidate"
DELTA = ROOT / "experiments/d1_typed_candidate_gate_v1_20261009/candidate_v2_delta"
CASES = [
    {"case_id": "length_128_mixed_tie", "input": {"data": ["k", 7] * 64},
     "expected": {"value": {"count": 128, "mode": "k"}}, "reason": "两值各64次，首次k"},
    {"case_id": "length_129_rejected", "input": {"data": [7] * 129},
     "expected": {"error": "ValueError"}, "reason": "超长度先于统计"},
    {"case_id": "new_float_default", "input": {"data": [], "default": 4.0},
     "expected": {"value": {"count": 0, "mode": 4.0}}, "reason": "空且float default类型保留"},
    {"case_id": "integer_mode_with_order", "input": {"data": [9, 8, 8]},
     "expected": {"value": {"count": 3, "mode": 8}}, "reason": "8两次且输入次序不得改变"},
    {"case_id": "new_bool_default", "input": {"data": [], "default": True},
     "expected": {"value": {"count": 0, "mode": True}}, "reason": "True default合法且布尔类型保留"},
    {"case_id": "extra_field_before_bad_item", "input": {"data": [True], "extra": 1},
     "expected": {"error": "ValueError"}, "reason": "额外字段先于元素类型"},
    {"case_id": "data_type_before_default_type", "input": {"data": "bad", "default": []},
     "expected": {"error": "TypeError"}, "reason": "data非列表，在default检查之前拒绝"},
    {"case_id": "new_integer_default", "input": {"data": [], "default": 7},
     "expected": {"value": {"count": 0, "mode": 7}}, "reason": "空且int default类型保留"},
]
WRAPPERS = {
    "float_count": '''
_base_solve = solve
def solve(payload):
    result = _base_solve(payload)
    result["count"] = float(result["count"])
    return result
''',
    "numeric_mode_drift": '''
_base_solve = solve
def solve(payload):
    result = _base_solve(payload)
    value = result["mode"]
    if type(value) is int:
        result["mode"] = float(value)
    elif type(value) is float and value.is_integer():
        result["mode"] = int(value)
    return result
''',
    "mutate_after_result": '''
_base_solve = solve
def solve(payload):
    result = _base_solve(payload)
    payload["data"].reverse()
    return result
''',
    "wrong_exception": '''
_base_solve = solve
def solve(payload):
    try:
        return _base_solve(payload)
    except (TypeError, ValueError):
        raise RuntimeError("错误异常类型控制") from None
''',
}
EVALUATOR = '''"""E_B09 v2候选执行器，旧评分器未修改。"""
import argparse
import contextlib
import copy
import importlib.util
import json
import sys
from pathlib import Path
from typed_comparison import json_equal, accept_output

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    args = parser.parse_args()
    specification = importlib.util.spec_from_file_location("candidate", args.candidate)
    module = importlib.util.module_from_spec(specification)
    with contextlib.redirect_stdout(sys.stderr):
        specification.loader.exec_module(module)
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    rows = []
    for case in cases:
        payload = copy.deepcopy(case["input"])
        before = copy.deepcopy(payload)
        try:
            with contextlib.redirect_stdout(sys.stderr):
                actual = {"value": module.solve(payload)}
            actual = json.loads(json.dumps(actual, ensure_ascii=False, allow_nan=False))
        except Exception as exc:
            actual = {"error": type(exc).__name__}
        unchanged = json_equal(payload, before, strict_numbers=True, ordered_objects=True)
        raw_content_pass = json_equal(actual, case["expected"])
        expected_error = "error" in case["expected"]
        if expected_error:
            typed_content_pass = json_equal(actual, case["expected"])
        else:
            typed_content_pass = (set(actual) == {"value"}
                                  and accept_output(actual["value"], case["expected"]["value"]))
        rows.append({"case_id": case["case_id"], "actual": actual,
                     "expected": case["expected"], "input_unchanged": unchanged,
                     "raw_content_pass": raw_content_pass, "typed_content_pass": typed_content_pass,
                     "raw_pass": raw_content_pass and unchanged,
                     "typed_pass": typed_content_pass and unchanged,
                     "expected_error": expected_error,
                     "value_only_without_input_or_error_pass": typed_content_pass and not expected_error})
    print(json.dumps({"rows": rows, "solve_calls": len(rows),
                      "raw_comparison_decisions": len(rows), "input_comparison_decisions": len(rows),
                      "typed_value_gate_calls": sum(not r["expected_error"] and "value" in r["actual"] for r in rows),
                      "typed_error_comparison_decisions": sum(r["expected_error"] for r in rows)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
'''


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def save_candidate(name, value):
    with (OUT / "candidate_v2" / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def main():
    OUT.mkdir(exist_ok=False)
    candidate = OUT / "candidate_v2"
    candidate.mkdir()
    source_names = ("whole.py", "helpers.py", "source_adapter.py", "sources/statsutils.py", "sources/LICENSE")
    for name in source_names:
        target = candidate / name
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(OLD / name, target)
    shutil.copyfile(OLD / "public_diagnostics.json", candidate / "public_diagnostics_v1_prior_not_rerun.json")
    shutil.copyfile(DELTA / "typed_comparison.py", candidate / "typed_comparison.py")
    shutil.copyfile(OLD / "requirements.md", candidate / "requirements_v1_preserved.md")
    requirements = (OLD / "requirements.md").read_text(encoding="utf-8")
    requirements += ("\n\nv2候选增量：输出的数量必须是int而非bool/float；众数保留被选原值或空域default的精确JSON类型，"
                     "int与float不互换，合法float default继续允许。值类型门槛只适用于正常返回，合法异常比较异常类型，"
                     "所有分支仍执行输入严格不变检查。执行器为evaluate_typed_candidate.py，不改原评分器。"
                     "原12诊断/36执行仍为v1；当前只对八个新输入的whole及四错误控制开展v2验证，结果另存validation_manifest.json，"
                     "另两参考未在v2运行，结构标签null/人工0/未正式冻结。\n")
    (candidate / "requirements.md").write_text(requirements, encoding="utf-8")
    (candidate / "evaluate_typed_candidate.py").write_text(EVALUATOR, encoding="utf-8")
    (candidate / "controls").mkdir()
    base = (OLD / "whole.py").read_text(encoding="utf-8")
    programs = {"correct_whole": base, **{name: base + wrapper for name, wrapper in WRAPPERS.items()}}
    files = {"correct_whole": candidate / "whole.py"}
    for name in WRAPPERS:
        files[name] = candidate / "controls" / (name + ".py")
        files[name].write_text(programs[name], encoding="utf-8")
    task = json.loads((OLD / "task.json").read_text(encoding="utf-8"))
    task.update(candidate_version=2, diagnostics="public_diagnostics_v2_new.json",
                prior_diagnostics="public_diagnostics_v1_prior_not_rerun.json",
                evaluator="evaluate_typed_candidate.py", comparison="typed_comparison.accept_output",
                status="另池v2公开候选，八新输入已冻结/执行结果见validation_manifest.json；人工0/标签null/未正式冻结",
                verification_scope={"whole": "八新输入本阶段，实际结果另存", "helpers": "只有原v1十二诊断，未v2重跑",
                                    "source_adapter": "只有原v1十二诊断，未v2重跑"})
    save_candidate("task.json", task)
    save_candidate("public_diagnostics_v2_new.json", CASES)
    predictions = {
        "correct_whole": {"raw": 8, "typed": 8, "typed_content_without_input": 8, "value_only": 5},
        "float_count": {"raw": 8, "typed": 3, "typed_content_without_input": 3, "value_only": 0},
        "numeric_mode_drift": {"raw": 8, "typed": 5, "typed_content_without_input": 5, "value_only": 2},
        "mutate_after_result": {"raw": 6, "typed": 6, "typed_content_without_input": 8, "value_only": 5},
        "wrong_exception": {"raw": 5, "typed": 5, "typed_content_without_input": 5, "value_only": 5},
    }
    save("eight_new_cases_and_five_programs_frozen.json", {
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "cases": CASES,
        "programs": programs, "predictions": predictions,
        "source_hashes": {str(p.relative_to(ROOT)): sha(p) for p in
                          (OLD / "whole.py", OLD / "requirements.md", DELTA / "typed_comparison.py", ROOT / "scripts/d1/evaluate_candidate.py", Path(__file__))},
        "candidate_file_hashes": {str(p.relative_to(candidate)): sha(p) for p in candidate.rglob("*") if p.is_file()},
        "new_solve_upper_limit": 40, "old_diagnostic_reruns": 0, "model_calls": 0, "private_reads": 0})
    results, total_gate_calls = {}, 0
    for name, path in files.items():
        proc = subprocess.run([sys.executable, "-B", "-X", "utf8", str(candidate / "evaluate_typed_candidate.py"),
                               "--candidate", str(path), "--cases", str(candidate / "public_diagnostics_v2_new.json")],
                              cwd=ROOT, capture_output=True, timeout=20)
        (OUT / (name + ".stdout.txt")).write_bytes(proc.stdout)
        (OUT / (name + ".stderr.txt")).write_bytes(proc.stderr)
        if proc.returncode or len(proc.stdout) > 1048576:
            raise RuntimeError("候选执行器失败或输出过限，原始输出已保留")
        results[name] = json.loads(proc.stdout.decode("utf-8"))
        total_gate_calls += results[name]["typed_value_gate_calls"]
    save("five_execution_results.json", results)
    scores = {name: {"raw": sum(r["raw_pass"] for r in result["rows"]),
                     "typed": sum(r["typed_pass"] for r in result["rows"]),
                     "typed_content_without_input": sum(r["typed_content_pass"] for r in result["rows"]),
                     "value_only": sum(r["value_only_without_input_or_error_pass"] for r in result["rows"])}
              for name, result in results.items()}
    summary = {"new_inputs": 8, "new_solve_calls": sum(r["solve_calls"] for r in results.values()),
               "typed_value_gate_calls": total_gate_calls, "typed_error_comparison_decisions": 15,
               "raw_comparison_decisions": 40, "input_comparison_decisions": 40,
               "scores_out_of_eight": scores, "predictions_all_match": scores == predictions,
               "old_diagnostic_reruns": 0, "model_calls": 0, "private_reads": 0,
               "conclusion": "JSON保留int/float区别；类型门槛必须与正常值/异常分支和输入严格不变合用；原36次不升级v2",
               "limits": "五程序中四个人为错误控制，共享whole基础；非模型/独立oracle/全域/正式冻结，另两旧参考未v2验证"}
    save("summary.json", summary)
    save_candidate("validation_manifest.json", {"whole_v2_new_cases": [scores["correct_whole"]["typed"], 8],
                   "controls": {name: score for name, score in scores.items() if name != "correct_whole"},
                   "helpers_v2": "未运行", "source_adapter_v2": "未运行", "old_36_calls": "仍v1，未升级或重跑",
                   "execution_result": "../five_execution_results.json", "formal_freeze": False, "human_reviews": 0})
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
