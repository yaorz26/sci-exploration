"""P61：新的任务输出投影与共同拒绝域；零helper追踪。"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_discrete_output_projection_v1_20261009"
CANDIDATE = ROOT / "experiments/d1_typed_candidate_execution_v1_20261009/candidate_v2"


def save(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def main():
    frozen = json.loads((OUT / "six_new_inputs_and_projection_predictions_frozen.json").read_text(encoding="utf-8"))
    for path, old in frozen["file_hashes"].items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != old:
            raise ValueError("冻结后的来源文件变化，必须另版登记")
    save("execution_code_frozen.json", {
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "projection_rules": "正常输出精确count整数与mode类型和值；error两投影null",
        "controls": "每有效保存返回只改count+1或mode同类型换值，另一字段应过，完整返回应拒",
        "new_solve_budget": 18, "constructed_output_controls_budget": 24,
        "prediction_source": "前轮逐值冻结，执行代码在结果前冻结；非人工复审"})
    save("six_new_public_diagnostics.json", frozen["cases"])
    results = {}
    for name in ("whole", "helpers", "source_adapter"):
        proc = subprocess.run([sys.executable, "-B", "-X", "utf8", str(CANDIDATE / "evaluate_typed_candidate.py"),
                               "--candidate", str(CANDIDATE / (name + ".py")),
                               "--cases", str(OUT / "six_new_public_diagnostics.json")],
                              cwd=ROOT, capture_output=True, timeout=20)
        with (OUT / (name + ".stdout.txt")).open("xb") as handle:
            handle.write(proc.stdout)
        with (OUT / (name + ".stderr.txt")).open("xb") as handle:
            handle.write(proc.stderr)
        if proc.returncode or len(proc.stdout) > 1048576:
            raise RuntimeError("任务执行失败或过限，机器输出已保留，不自动重跑")
        results[name] = json.loads(proc.stdout.decode("utf-8"))
    save("three_execution_results.json", results)
    spec = importlib.util.spec_from_file_location("p61_comparison", CANDIDATE / "typed_comparison.py")
    comparison = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(comparison)

    def project(actual, expected):
        if "value" not in actual or "value" not in expected:
            return {"applicability": "无正常字段投影", "count_pass": None, "mode_pass": None}
        value, wanted = actual["value"], expected["value"]
        return {"applicability": "候选正常返回域", "count_pass": type(value.get("count")) is int and value.get("count") == wanted["count"],
                "mode_pass": comparison.json_equal(value.get("mode"), wanted["mode"], strict_numbers=True)}

    projected, controls, relations = [], [], []
    pairs = [("count2_mode_int4", "count3_mode_int4", "count"),
             ("count2_mode_strx", "count3_mode_strx", "count"),
             ("count2_mode_int4", "count2_mode_strx", "mode"),
             ("count3_mode_int4", "count3_mode_strx", "mode")]
    for name, result in results.items():
        by_id = {row["case_id"]: row for row in result["rows"]}
        for row in result["rows"]:
            projected.append({"program": name, "case_id": row["case_id"],
                              "whole_pass": row["typed_pass"], **project(row["actual"], row["expected"])})
            if "value" not in row["actual"]:
                continue
            for field in ("count", "mode"):
                wrong = copy.deepcopy(row["actual"])
                if field == "count":
                    wrong["value"][field] += 1
                else:
                    value = wrong["value"][field]
                    wrong["value"][field] = value + 1 if type(value) is int else value + "_错"
                controls.append({"program": name, "case_id": row["case_id"], "changed_field": field,
                                 "observed": wrong, "whole_pass": comparison.accept_output(wrong["value"], row["expected"]["value"]),
                                 **project(wrong, row["expected"])})
        for left, right, changed in pairs:
            a, b = by_id[left]["actual"]["value"], by_id[right]["actual"]["value"]
            other = "mode" if changed == "count" else "count"
            relations.append({"program": name, "left": left, "right": right, "changed_field": changed,
                              "changed_field_differs": not comparison.json_equal(a[changed], b[changed], strict_numbers=True),
                              "other_field_unchanged": comparison.json_equal(a[other], b[other], strict_numbers=True)})
    save("normal_and_rejection_projections.json", projected)
    save("twentyfour_constructed_output_controls.json", controls)
    save("twelve_saved_output_relations.json", relations)
    summary = {"new_inputs": 6, "new_solve_calls": 18,
               "whole_passes_out_of_six": {name: sum(r["typed_pass"] for r in result["rows"]) for name, result in results.items()},
               "normal_count_pass": [sum(r["count_pass"] is True for r in projected), 12],
               "normal_mode_pass": [sum(r["mode_pass"] is True for r in projected), 12],
               "expected_rejections": 6,
               "rejection_field_projection_nulls": sum(r[k] is None for r in projected for k in ("count_pass", "mode_pass")),
               "field_separation_relations": [sum(r["changed_field_differs"] and r["other_field_unchanged"] for r in relations), 12],
               "constructed_output_controls": len(controls), "whole_control_rejections": sum(not r["whole_pass"] for r in controls),
               "single_wrong_field_controls_isolated": sum(r[r["changed_field"] + "_pass"] is False and
                       r[("mode" if r["changed_field"] == "count" else "count") + "_pass"] is True for r in controls),
               "execution_typed_value_gate_calls": 12, "execution_error_comparison_decisions": 6,
               "projection_field_comparison_decisions": 24, "saved_relation_field_comparison_decisions": 24,
               "control_field_comparison_decisions": 48, "control_full_output_gate_calls": 24,
               "old_eight_or_twelve_case_reruns": 0, "model_calls": 0, "private_reads": 0, "human_reviews": 0,
               "conclusion": "正常域count/mode有分别变化与可定位证据，共同拒绝域投影null；不是内部/统计独立或正式yes标签",
               "limits": "六公开诊断/同来源/共享guard/同助手手算，24控制只是输出对象非额外程序运行"}
    save("summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
