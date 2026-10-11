"""Selection policies and aggregate pass-rate metrics."""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path
from typing import Any


def select_candidate(evaluated: list[dict[str, Any]], method: str, rng: random.Random) -> int:
    if not evaluated:
        raise ValueError("cannot select from an empty candidate list")
    if method == "first":
        return 0
    if method == "random":
        return rng.randrange(len(evaluated))
    key = "private" if method == "private_oracle" else "public"
    rates = [item["execution"][key]["pass_rate"] for item in evaluated]
    return max(range(len(rates)), key=lambda i: (rates[i], -i))


def summarize(rows: list[dict[str, Any]], method: str) -> dict[str, Any]:
    if not rows:
        return {"method": method, "num_problems": 0, "pass_rate": 0.0, "pass_at_1": 0.0, "avg_executions": 0.0}
    private_rates = [row["selected"]["execution"]["private"]["pass_rate"] for row in rows]
    return {
        "method": method, "num_problems": len(rows),
        "pass_rate": sum(private_rates) / len(private_rates),
        "pass_at_1": sum(rate == 1.0 for rate in private_rates) / len(private_rates),
        "avg_executions": sum(row["num_executions"] for row in rows) / len(rows),
    }


def write_results(summaries: list[dict[str, Any]], rows: list[dict[str, Any]], output_dir: str | Path, stem: str = "baseline") -> tuple[Path, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    json_path, csv_path = output / f"{stem}.json", output / f"{stem}.csv"
    json_path.write_text(json.dumps({"summary": summaries, "problems": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["method", "num_problems", "pass_rate", "pass_at_1", "avg_executions"])
        writer.writeheader()
        writer.writerows(summaries)
    return json_path, csv_path
