"""Aggregate scalar/dict experiment summaries across independent seeds."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", nargs="+", required=True, help="Result JSON files with a dict-valued summary")
    parser.add_argument("--output-stem", required=True, help="Output stem, without extension")
    args = parser.parse_args()

    per_seed: list[tuple[str, dict]] = []
    for raw_path in args.results:
        path = Path(raw_path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        summary = payload.get("summary")
        if not isinstance(summary, dict):
            raise ValueError(f"{path} must contain a dict-valued 'summary'")
        per_seed.append((str(path), summary))

    keys = sorted({
        key for _, summary in per_seed for key, value in summary.items()
        if isinstance(value, (int, float)) and not isinstance(value, bool) and key != "num_problems"
    })
    aggregate = {}
    for key in keys:
        values = [float(summary[key]) for _, summary in per_seed]
        aggregate[key] = {
            "mean": statistics.mean(values),
            "sd": statistics.stdev(values) if len(values) > 1 else 0.0,
            "by_seed": values,
        }

    output_dir = ROOT / "outputs" / "results"
    table_dir = ROOT / "reports" / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{args.output_stem}.json"
    csv_path = table_dir / f"{args.output_stem}.csv"
    payload = {"results": [path for path, _ in per_seed], "aggregate": aggregate}
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "mean", "sd"])
        writer.writeheader()
        writer.writerows({"metric": key, "mean": value["mean"], "sd": value["sd"]} for key, value in aggregate.items())
    print(json.dumps({"json": str(json_path), "csv": str(csv_path), "aggregate": aggregate}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
