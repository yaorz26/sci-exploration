"""Aggregate baseline summaries across independent generation seeds."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", nargs="+", required=True, help="Baseline result JSON files")
    parser.add_argument("--output-suffix", default="apps_train_intro20_qwen3b_seeds")
    args = parser.parse_args()

    per_seed = []
    for result_path in args.results:
        path = Path(result_path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        summaries = {row["method"]: row for row in payload["summary"]}
        per_seed.append({"file": str(path), "summary": summaries})

    methods = ["first", "random", "public_pass_rate", "private_oracle"]
    aggregate = []
    for method in methods:
        rates = [item["summary"][method]["pass_rate"] for item in per_seed]
        pass_at_1 = [item["summary"][method]["pass_at_1"] for item in per_seed]
        aggregate.append({
            "method": method,
            "num_seeds": len(per_seed),
            "pass_rate_mean": statistics.mean(rates),
            "pass_rate_sd": statistics.stdev(rates) if len(rates) > 1 else 0.0,
            "pass_at_1_mean": statistics.mean(pass_at_1),
            "pass_at_1_sd": statistics.stdev(pass_at_1) if len(pass_at_1) > 1 else 0.0,
            "pass_rate_by_seed": rates,
            "pass_at_1_by_seed": pass_at_1,
        })

    deltas = [
        item["summary"]["public_pass_rate"]["pass_rate"] - item["summary"]["first"]["pass_rate"]
        for item in per_seed
    ]
    payload = {
        "results": [item["file"] for item in per_seed],
        "aggregate": aggregate,
        "public_selection_minus_first": {
            "mean": statistics.mean(deltas),
            "sd": statistics.stdev(deltas) if len(deltas) > 1 else 0.0,
            "by_seed": deltas,
        },
    }

    output_dir = ROOT / "outputs" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"baseline_seed_summary_{args.output_suffix}.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    table_dir = ROOT / "reports" / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    table_path = table_dir / f"baseline_seed_summary_{args.output_suffix}.csv"
    with table_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "method", "num_seeds", "pass_rate_mean", "pass_rate_sd", "pass_at_1_mean", "pass_at_1_sd"
        ])
        writer.writeheader()
        writer.writerows({key: row[key] for key in writer.fieldnames} for row in aggregate)

    print(json.dumps({"json": str(output_path), "csv": str(table_path), **payload}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
