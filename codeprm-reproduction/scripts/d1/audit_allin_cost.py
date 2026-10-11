"""重算两轮历史开发探针的生成成本与含预检的总成本；不调用模型。"""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[2]
    combined = defaultdict(lambda: defaultdict(int))
    runs = []
    for name in ("d1_costed_pilot_b04_c03_v1_20261008", "d1_costed_pilot_b03_b05_c04_v1_20261008"):
        path = root / "experiments" / name
        calls = json.loads((path / "call_ledger.json").read_text(encoding="utf-8"))
        summary = json.loads((path / "summary.json").read_text(encoding="utf-8"))
        units = defaultdict(lambda: defaultdict(int))
        for call in calls:
            assert call["success"] and type(call["prompt_tokens"]) is int and type(call["output_tokens"]) is int
            bucket = "preflight" if call["measurement"] else "generation"
            unit = units[(call["task_id"], call["arm"])]
            for key, value in {bucket + "_calls": 1, bucket + "_input_tokens": call["prompt_tokens"], bucket + "_output_tokens": call["output_tokens"]}.items():
                unit[key] += value
                combined[call["arm"]][key] += value
        unit_rows = []
        for (task_id, arm), costs in sorted(units.items()):
            generation = costs["generation_input_tokens"] + costs["generation_output_tokens"]
            preflight = costs["preflight_input_tokens"] + costs["preflight_output_tokens"]
            match = next(row for row in summary["candidates"] if row["task_id"] == task_id and row["arm"] == arm)
            assert generation == match["generated_token_spend"]
            candidate_hash_ok = None
            if match.get("candidate_path"):
                candidate_path = Path(match["candidate_path"])
                if not candidate_path.is_absolute():
                    candidate_path = root / candidate_path
                candidate_hash_ok = hashlib.sha256(candidate_path.read_bytes()).hexdigest() == match["candidate_sha256"]
                assert candidate_hash_ok
            unit_rows.append({"task_id": task_id, "arm": arm, **costs, "generation_total": generation,
                              "preflight_total": preflight, "allin_total": generation + preflight,
                              "actual_protocol_generation_budget_met": generation <= match["per_task_arm_budget"],
                              "would_meet_6500_allin_cap": generation + preflight <= 6500,
                              "all_pass": match["all_pass"], "generation_error": match["generation_error"],
                              "successful_candidate_hash_verified": candidate_hash_ok})
        runs.append({"run": name, "api_calls": len(calls), "preflight_calls": sum(c["measurement"] for c in calls),
                     "generation_calls": sum(not c["measurement"] for c in calls), "units": unit_rows})
    totals = {}
    for arm, costs in combined.items():
        generation = costs["generation_input_tokens"] + costs["generation_output_tokens"]
        preflight = costs["preflight_input_tokens"] + costs["preflight_output_tokens"]
        totals[arm] = {**costs, "generation_total": generation, "preflight_total": preflight, "allin_total": generation + preflight}
    report = {"status": "pass", "scope": "两轮五题开发探针事后成本复算，非等总预算效果确认", "runs": runs, "combined": totals,
              "generation_ratio_M2_over_M0": totals["M2"]["generation_total"] / totals["M0"]["generation_total"],
              "allin_ratio_M2_over_M0": totals["M2"]["allin_total"] / totals["M0"]["allin_total"],
              "raw_evidence_limit": "旧执行器未保存逐调用完整prompt/response；失败helper/entry原文缺失，无法由异常消息进一步核实算法根因",
              "counterfactual_cap_note": "would_meet_6500_allin_cap是新口径回看；旧协议明确预检另列，不能称为违反旧预算协议"}
    target = root / "experiments/d1_cost_allin_audit_v1_20261008.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "combined": totals, "allin_ratio": report["allin_ratio_M2_over_M0"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
