"""Aggregate method-based experiment summaries across generation seeds."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", nargs="+", required=True, help="Result JSON files with a list-valued summary")
    parser.add_argument("--output-stem", required=True, help="Output stem, without extension")
    args = parser.parse_args()

    per_seed: list[tuple[str, dict[str, dict]]] = []
    for raw_path in args.results:
        path = Path(raw_path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        summary = payload.get("summary")
        if not isinstance(summary, list):
            raise ValueError(f"{path} must contain a list-valued 'summary'")
        per_seed.append((str(path), {str(row["method"]): row for row in summary}))

    methods = list(per_seed[0][1])
    if any(set(rows) != set(methods) for _, rows in per_seed[1:]):
        raise ValueError("All result files must have identical method sets")

    aggregate = []
    for method in methods:
        rows = [summaries[method] for _, summaries in per_seed]
        numeric_keys = sorted({
            key for row in rows for key, value in row.items()
            if isinstance(value, (int, float)) and not isinstance(value, bool) and key != "num_problems"
        })
        item = {"method": method, "num_seeds": len(rows)}
        for key in numeric_keys:
            values = [float(row[key]) for row in rows]
            item[f"{key}_mean"] = statistics.mean(values)
            item[f"{key}_sd"] = statistics.stdev(values) if len(values) > 1 else 0.0
            item[f"{key}_by_seed"] = values
        aggregate.append(item)

    output_dir = ROOT / "outputs" / "results"
    table_dir = ROOT / "reports" / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{args.output_stem}.json"
    csv_path = table_dir / f"{args.output_stem}.csv"
    payload = {"results": [path for path, _ in per_seed], "aggregate": aggregate}
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    fields = ["method", "num_seeds"] + sorted({key for row in aggregate for key in row if key.endswith("_mean") or key.endswith("_sd")})
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: row.get(key) for key in fields} for row in aggregate)
    print(json.dumps({"json": str(json_path), "csv": str(csv_path), "aggregate": aggregate}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
