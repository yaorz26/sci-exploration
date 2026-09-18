"""Analyze M3 blind scores and compare methods on the same sampled problems."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", default="reports/decomposition_quality_20260914.csv")
    parser.add_argument("--blind-key", default="reports/decomposition_quality_20260914_blind_key.json")
    parser.add_argument("--m3", default="data/processed/p3_m3_human_qwen25coder_7b_d1_i2_c8_seed42_v1_recombinations.jsonl")
    parser.add_argument("--m0", default="data/processed/p3_dev20_m0_direct_qwen25coder_7b_n4_seed42_v1_evaluations.jsonl")
    parser.add_argument("--m1", default="data/processed/p3_dev20_m1_plan_qwen25coder_7b_n4_seed42_v1_evaluations.jsonl")
    parser.add_argument("--m2a", default="data/processed/p3_dev20_m2a_skeleton_qwen25coder_7b_d2_i2_c8_seed42_v1_recombinations.jsonl")
    parser.add_argument("--m2b", default="data/processed/p3_dev20_m2b_json_qwen25coder_7b_d2_i2_c8_seed42_v1_recombinations.jsonl")
    parser.add_argument("--output", default="reports/m3_human_analysis_20260914.md")
    args = parser.parse_args()

    key = json.loads(_resolve(args.blind_key).read_text(encoding="utf-8"))
    sampled_ids = sorted({str(item["problem_id"]) for item in key})
    protocol_by_label = {(str(item["problem_id"]), str(item["blind_label"])): str(item["protocol"]) for item in key}
    score_rows = _read_csv(_resolve(args.scores))
    scores_by_protocol: dict[str, list[int]] = defaultdict(list)
    per_problem_scores: dict[str, dict[str, int]] = defaultdict(dict)
    fields = [
        "coverage_0_2", "io_contract_0_2", "dependency_clarity_0_2",
        "independent_implementation_0_2", "granularity_0_2",
    ]
    for row in score_rows:
        problem_id = str(row["problem_id"])
        label = str(row["blind_label"])
        protocol = protocol_by_label[(problem_id, label)]
        total = sum(int(row[field]) for field in fields)
        scores_by_protocol[protocol].append(total)
        per_problem_scores[problem_id][protocol] = total

    method_paths = {
        "M0 direct": args.m0,
        "M1 plan-first": args.m1,
        "M2a skeleton": args.m2a,
        "M2b JSON": args.m2b,
        "M3 human": args.m3,
    }
    method_rows = []
    for name, value in method_paths.items():
        records = _read_jsonl(_resolve(value))
        by_id = {str(item.get("problem_id")): item for item in records}
        method_rows.append(_method_stats(name, by_id, sampled_ids))

    lines = [
        "# M3 human decomposition analysis",
        "",
        "M3 uses the 10 development problems sampled before execution results were unblinded. Human scores were recorded on blind labels A/B, then mapped back to JSON or skeleton only after the CSV was complete.",
        "",
        "## Blind quality scores",
        "",
        "Scores sum five criteria, each 0--2, so the maximum is 10.",
        "",
        "| Protocol | Candidate count | Mean score / 10 | Median score / 10 |",
        "| --- | ---: | ---: | ---: |",
    ]
    for protocol in ("json", "skeleton"):
        values = sorted(scores_by_protocol.get(protocol, []))
        mean = sum(values) / len(values) if values else 0.0
        median = values[len(values) // 2] if values else 0.0
        if values and len(values) % 2 == 0:
            median = (values[len(values) // 2 - 1] + values[len(values) // 2]) / 2
        lines.append(f"| {protocol} | {len(values)} | {mean:.2f} | {median:.1f} |")
    lines += [
        "",
        "Per-problem blind score pairs:",
        "",
        "| Problem | JSON score | Skeleton score | Higher-scoring protocol |",
        "| --- | ---: | ---: | --- |",
    ]
    for problem_id in sampled_ids:
        values = per_problem_scores[problem_id]
        json_score = values.get("json", 0)
        skeleton_score = values.get("skeleton", 0)
        higher = "tie" if json_score == skeleton_score else ("JSON" if json_score > skeleton_score else "skeleton")
        lines.append(f"| {problem_id} | {json_score} | {skeleton_score} | {higher} |")
    lines += [
        "",
        "## Same-subset execution comparison",
        "",
        "Every method below is recomputed on these same 10 problem IDs. Full-pass denominators are all 10; candidate coverage is shown separately.",
        "",
        "| Method | Candidate coverage | Public full pass | Private full pass | Private test rate | Unique programs evaluated |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in method_rows:
        lines.append(
            f"| {row['name']} | {row['coverage']}/10 | {row['public_full']}/10 | {row['private_full']}/10 | {row['private_rate']:.3f} ({row['private_passed']}/{row['private_total']}) | {row['unique_programs']} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "The human-authored decompositions are a structural reference, not a learned policy. They reached 8/10 candidate coverage and 3/10 private full pass on this sample. Their result does not exceed the automatic M1 baseline on the same questions; therefore the current evidence does not justify RL training. The human scores are still useful: they identify interface precision, dependency clarity, and boundary-condition coverage as the likely bottlenecks for the automatic decomposition policy.",
        "",
        "M3 implementation failures are recorded in the raw implementation JSONL. No private result was used to write or select the human decomposition.",
        "",
    ]
    output = _resolve(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


def _method_stats(name: str, by_id: dict[str, dict[str, Any]], sampled_ids: list[str]) -> dict[str, Any]:
    coverage = public_full = private_full = private_passed = private_total = 0
    unique_programs = 0
    for problem_id in sampled_ids:
        record = by_id.get(problem_id)
        if not record:
            continue
        if "final_evaluation" in record:
            selection = record.get("selection", {})
            candidates = selection.get("candidates", [])
            selected_id = selection.get("selected_candidate_id")
            selected = next((item for item in candidates if item.get("candidate_id") == selected_id), None)
            public = selected.get("public", {}) if selected else {}
            private = (record.get("final_evaluation") or {}).get("private", {})
            unique_programs += sum(1 for item in candidates if item.get("code") and not item.get("duplicate_of"))
        else:
            selection = record.get("selection", {})
            candidates = selection.get("candidates", [])
            selected_id = selection.get("selected_candidate_id")
            selected = next((item for item in candidates if item.get("candidate_id") == selected_id), None)
            public = selected.get("public", {}) if selected else {}
            private = (record.get("final_evaluation") or {}).get("private", {})
            unique_programs += sum(1 for item in candidates if item.get("code") and not item.get("duplicate_of"))
        if selected:
            coverage += 1
            public_full += int(public.get("total", 0) > 0 and public.get("passed") == public.get("total"))
            private_full += int(private.get("total", 0) > 0 and private.get("passed") == private.get("total"))
            private_passed += int(private.get("passed", 0) or 0)
            private_total += int(private.get("total", 0) or 0)
    return {
        "name": name,
        "coverage": coverage,
        "public_full": public_full,
        "private_full": private_full,
        "private_passed": private_passed,
        "private_total": private_total,
        "private_rate": private_passed / private_total if private_total else 0.0,
        "unique_programs": unique_programs,
    }


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


if __name__ == "__main__":
    main()
