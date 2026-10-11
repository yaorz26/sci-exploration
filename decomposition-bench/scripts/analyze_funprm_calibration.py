"""Audit and analyze the label-independent FunPRM rollout calibration."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path
from typing import Any


NodeKey = tuple[str, int, int]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def node_key(row: dict[str, Any]) -> NodeKey:
    return (
        str(row["problem_id"]),
        int(row["source_candidate_index"]),
        int(row["function_index"]),
    )


def pearson(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        raise ValueError("Pearson requires paired vectors with at least two values")
    left_mean = sum(left) / len(left)
    right_mean = sum(right) / len(right)
    numerator = sum((x - left_mean) * (y - right_mean) for x, y in zip(left, right))
    left_ss = sum((x - left_mean) ** 2 for x in left)
    right_ss = sum((y - right_mean) ** 2 for y in right)
    if left_ss == 0.0 or right_ss == 0.0:
        return float("nan")
    return numerator / math.sqrt(left_ss * right_ss)


def percentile(values: list[float], quantile: float) -> float:
    if not values or not 0.0 <= quantile <= 1.0:
        raise ValueError("invalid percentile input")
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def bootstrap_intervals(
    first: list[float],
    second: list[float],
    *,
    samples: int,
    seed: int,
) -> dict[str, Any]:
    rng = random.Random(seed)
    correlations: list[float] = []
    mean_differences: list[float] = []
    for _ in range(samples):
        indices = [rng.randrange(len(first)) for _ in first]
        left = [first[index] for index in indices]
        right = [second[index] for index in indices]
        correlation = pearson(left, right)
        if not math.isnan(correlation):
            correlations.append(correlation)
        mean_differences.append(sum(right) / len(right) - sum(left) / len(left))
    return {
        "samples_requested": samples,
        "valid_correlation_samples": len(correlations),
        "seed": seed,
        "pearson_95_percentile_interval": [
            percentile(correlations, 0.025),
            percentile(correlations, 0.975),
        ],
        "second_minus_first_mean_95_percentile_interval": [
            percentile(mean_differences, 0.025),
            percentile(mean_differences, 0.975),
        ],
    }


def indexed_first_eight(row: dict[str, Any]) -> list[dict[str, Any]]:
    by_index = {int(item["rollout_index"]): item for item in row.get("rollouts", [])}
    if len(by_index) != len(row.get("rollouts", [])):
        raise ValueError(f"duplicate rollout indices for node {node_key(row)}")
    missing = set(range(8)) - set(by_index)
    if missing:
        raise ValueError(f"missing first-eight rollout indices {sorted(missing)} for node {node_key(row)}")
    return [by_index[index] for index in range(8)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--baseline-nodes", required=True)
    parser.add_argument("--calibrated-nodes", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=10_000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260924)
    parser.add_argument("--pearson-threshold", type=float, default=0.70)
    parser.add_argument("--mean-gap-threshold", type=float, default=0.10)
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    baseline_path = Path(args.baseline_nodes)
    calibrated_path = Path(args.calibrated_nodes)
    output_path = Path(args.output)
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite {output_path}")
    if args.bootstrap_samples <= 0:
        raise ValueError("bootstrap samples must be positive")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    selected_keys = {node_key(row) for row in manifest["selected_nodes"]}
    if len(selected_keys) != int(manifest["sample_size"]):
        raise ValueError("manifest sample size or unique-key count mismatch")
    baseline_rows = read_jsonl(baseline_path)
    calibrated_rows = read_jsonl(calibrated_path)
    baseline = {node_key(row): row for row in baseline_rows}
    calibrated = {node_key(row): row for row in calibrated_rows}
    if len(baseline) != len(baseline_rows) or len(calibrated) != len(calibrated_rows):
        raise ValueError("duplicate node keys in node files")
    if set(baseline) != set(calibrated):
        raise ValueError("baseline and calibrated node populations differ")
    if not selected_keys <= set(baseline):
        raise ValueError("manifest contains keys outside the baseline population")

    nonselected_changes = [
        key for key in baseline if key not in selected_keys and baseline[key] != calibrated[key]
    ]
    if nonselected_changes:
        raise ValueError(f"{len(nonselected_changes)} nonselected nodes changed")

    expected_added = 0
    selected_count_histogram: dict[str, int] = {}
    first_half: list[float] = []
    second_half: list[float] = []
    first_eight_error_count = 0
    added_error_count = 0
    per_node: list[dict[str, Any]] = []
    for key in sorted(selected_keys):
        before = baseline[key]
        after = calibrated[key]
        before_rollouts = before.get("rollouts", [])
        after_rollouts = after.get("rollouts", [])
        before_count = len(before_rollouts)
        selected_count_histogram[str(before_count)] = selected_count_histogram.get(str(before_count), 0) + 1
        if before_count not in {4, 8, 16}:
            raise ValueError(f"unexpected baseline rollout count {before_count} for node {key}")
        expected_count = 8 if before_count == 4 else before_count
        if len(after_rollouts) != expected_count:
            raise ValueError(f"unexpected calibrated rollout count for node {key}")
        if after_rollouts[:before_count] != before_rollouts:
            raise ValueError(f"baseline rollouts changed for node {key}")
        expected_added += max(0, 8 - before_count)
        first_eight = indexed_first_eight(after)
        first = sum(bool(item.get("success")) for item in first_eight[:4]) / 4
        second = sum(bool(item.get("success")) for item in first_eight[4:8]) / 4
        first_half.append(first)
        second_half.append(second)
        first_eight_error_count += sum(bool(item.get("error")) for item in first_eight)
        added_error_count += sum(bool(item.get("error")) for item in after_rollouts[before_count:])
        per_node.append({
            "problem_id": key[0],
            "source_candidate_index": key[1],
            "function_index": key[2],
            "baseline_rollout_count": before_count,
            "first4_success_rate": first,
            "second4_success_rate": second,
            "full8_success_rate": (first + second) / 2,
        })

    actual_added = sum(len(row.get("rollouts", [])) for row in calibrated_rows) - sum(
        len(row.get("rollouts", [])) for row in baseline_rows
    )
    if actual_added != expected_added:
        raise ValueError(f"added rollout count mismatch: expected {expected_added}, got {actual_added}")

    split_half_pearson = pearson(first_half, second_half)
    first_mean = sum(first_half) / len(first_half)
    second_mean = sum(second_half) / len(second_half)
    mean_gap = abs(second_mean - first_mean)
    full_eight = [(left + right) / 2 for left, right in zip(first_half, second_half)]
    first_to_full_pearson = pearson(first_half, full_eight)
    mean_absolute_change = sum(abs(left - full) for left, full in zip(first_half, full_eight)) / len(first_half)
    positive_to_zero = sum(left > 0.0 and right == 0.0 for left, right in zip(first_half, second_half))
    zero_to_positive = sum(left == 0.0 and right > 0.0 for left, right in zip(first_half, second_half))
    gate_passed = split_half_pearson >= args.pearson_threshold and mean_gap <= args.mean_gap_threshold

    audit = {
        "experiment": "funprm_label_calibration_20260924",
        "status": "pass_resume_prm_training_under_revised_protocol" if gate_passed else "fail_stop_before_prm_training",
        "scope_note": "This revised calibration does not retroactively change the original helper-first scale gate failure.",
        "inputs": {
            "manifest": str(manifest_path),
            "manifest_sha256": sha256(manifest_path),
            "baseline_nodes": str(baseline_path),
            "baseline_sha256": sha256(baseline_path),
            "calibrated_nodes": str(calibrated_path),
            "calibrated_sha256": sha256(calibrated_path),
        },
        "integrity": {
            "population_nodes": len(baseline),
            "selected_nodes": len(selected_keys),
            "nonselected_nodes_unchanged": len(nonselected_changes) == 0,
            "selected_baseline_rollout_count_histogram": selected_count_histogram,
            "expected_added_rollouts": expected_added,
            "actual_added_rollouts": actual_added,
            "selected_first_eight_error_count": first_eight_error_count,
            "newly_added_error_count": added_error_count,
        },
        "primary_metrics": {
            "independent_first4_vs_second4_pearson": split_half_pearson,
            "first4_mean_success_rate": first_mean,
            "second4_mean_success_rate": second_mean,
            "absolute_half_mean_difference": mean_gap,
        },
        "gate": {
            "pearson_threshold": args.pearson_threshold,
            "mean_gap_threshold": args.mean_gap_threshold,
            "pearson_pass": split_half_pearson >= args.pearson_threshold,
            "mean_gap_pass": mean_gap <= args.mean_gap_threshold,
            "overall_pass": gate_passed,
        },
        "auxiliary_metrics": {
            "first4_vs_full8_pearson": first_to_full_pearson,
            "mean_absolute_first4_to_full8_change": mean_absolute_change,
            "first4_positive_nodes": sum(value > 0.0 for value in first_half),
            "second4_positive_nodes": sum(value > 0.0 for value in second_half),
            "positive_to_zero_flips": positive_to_zero,
            "zero_to_positive_flips": zero_to_positive,
            "bootstrap": bootstrap_intervals(
                first_half,
                second_half,
                samples=args.bootstrap_samples,
                seed=args.bootstrap_seed,
            ),
        },
        "per_node": per_node,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": audit["status"],
        "integrity": audit["integrity"],
        "primary_metrics": audit["primary_metrics"],
        "gate": audit["gate"],
        "auxiliary_metrics": audit["auxiliary_metrics"],
        "output": str(output_path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
