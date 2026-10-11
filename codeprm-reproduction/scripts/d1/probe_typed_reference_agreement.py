"""P60：先冻结，再对尚未在v2运行的两参考作16次执行。"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREVIOUS = ROOT / "experiments/d1_typed_candidate_execution_v1_20261009"
CANDIDATE = PREVIOUS / "candidate_v2"
OUT = ROOT / "experiments/d1_typed_reference_agreement_v1_20261009"
FILES = [CANDIDATE / name for name in ("public_diagnostics_v2_new.json", "evaluate_typed_candidate.py",
                                        "typed_comparison.py", "helpers.py", "source_adapter.py", "sources/statsutils.py")]
FILES += [PREVIOUS / "five_execution_results.json", Path(__file__)]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def freeze():
    OUT.mkdir(exist_ok=False)
    save("two_references_and_eight_saved_cases_frozen.json", {
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "file_hashes": {str(p.relative_to(ROOT)): sha(p) for p in FILES},
        "predictions_out_of_eight": {"helpers": 8, "source_adapter": 8},
        "new_solve_upper_limit": 16, "new_solve_calls_so_far": 0,
        "whole_and_control_reruns": 0, "old_twelve_diagnostic_reruns": 0,
        "limits": "同来源/共享guard，不是三独立oracle；源API未实际计数不冒报",
        "next_command": "python -B -X utf8 scripts/d1/probe_typed_reference_agreement.py --execute"})
    print(json.dumps({"phase": "P60", "frozen": True, "solve_calls": 0, "next": "--execute"}, ensure_ascii=False))


def execute():
    frozen = json.loads((OUT / "two_references_and_eight_saved_cases_frozen.json").read_text(encoding="utf-8"))
    for relative, old_sha in frozen["file_hashes"].items():
        if sha(ROOT / relative) != old_sha:
            raise ValueError("冻结后代码或证据改变，须另版登记而非原样重试")
    save("execution_started.json", {"created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                   "planned_solve_calls": 16})
    results = {}
    for name in ("helpers", "source_adapter"):
        proc = subprocess.run([sys.executable, "-B", "-X", "utf8", str(CANDIDATE / "evaluate_typed_candidate.py"),
                               "--candidate", str(CANDIDATE / (name + ".py")),
                               "--cases", str(CANDIDATE / "public_diagnostics_v2_new.json")],
                              cwd=ROOT, capture_output=True, timeout=20)
        with (OUT / (name + ".stdout.txt")).open("xb") as handle:
            handle.write(proc.stdout)
        with (OUT / (name + ".stderr.txt")).open("xb") as handle:
            handle.write(proc.stderr)
        if proc.returncode or len(proc.stdout) > 1048576:
            raise RuntimeError("参考执行失败或输出过限；原始结果保留，不自动重跑")
        results[name] = json.loads(proc.stdout.decode("utf-8"))
    save("two_reference_execution_results.json", results)
    old = json.loads((PREVIOUS / "five_execution_results.json").read_text(encoding="utf-8"))["correct_whole"]
    # 判断按原v2严格类型比较的返回/异常是否逐行与保存whole一致；不是再次执行whole。
    spec = __import__("importlib.util", fromlist=["spec_from_file_location"])
    module_spec = spec.spec_from_file_location("p60_comparison", CANDIDATE / "typed_comparison.py")
    module = spec.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    agreements = {}
    for name, result in results.items():
        old_by_id = {r["case_id"]: r for r in old["rows"]}
        agreements[name] = sum(module.json_equal(r["actual"], old_by_id[r["case_id"]]["actual"], strict_numbers=True)
                               for r in result["rows"])
    scores = {name: sum(r["typed_pass"] for r in result["rows"]) for name, result in results.items()}
    summary = {"saved_inputs": 8, "new_solve_calls": sum(r["solve_calls"] for r in results.values()),
               "v2_passes_out_of_eight": scores, "strict_agreement_with_saved_whole_out_of_eight": agreements,
               "predictions_all_match": scores == frozen["predictions_out_of_eight"],
               "saved_result_comparison_decisions": 16,
               "typed_value_gate_calls": sum(r["typed_value_gate_calls"] for r in results.values()),
               "typed_error_comparison_decisions": sum(r["typed_error_comparison_decisions"] for r in results.values()),
               "whole_and_control_reruns": 0, "old_twelve_diagnostic_reruns": 0,
               "model_calls": 0, "private_reads": 0, "human_reviews": 0,
               "source_API_call_count": "未插桩实际计数，不以包装语句估计冒报",
               "limits": "八保存公开输入/共享guard/同来源；原36仍v1/标签null/未正式冻结"}
    save("summary.json", summary)
    save("three_reference_v2_validation_manifest.json", {
        "whole_previous_v2": [8, 8], "helpers_current_v2": [scores["helpers"], 8],
        "source_adapter_current_v2": [scores["source_adapter"], 8],
        "whole_new_execution": False, "current_new_solve_calls": 16, "combined_v2_reference_solve_calls": 24,
        "original_v1_calls": 36, "original_v1_cases": 12, "original_v1_upgraded": False,
        "formal_freeze": False, "human_reviews": 0, "original_P59_manifest_preserved": True})
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    flags = parser.add_mutually_exclusive_group(required=True)
    flags.add_argument("--freeze", action="store_true")
    flags.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    freeze() if args.freeze else execute()
