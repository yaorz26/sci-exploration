"""Merge P5b original implementations with P5c newly generated ones.

Merge rule: for each (problem_id, decomposition_index, function_name,
implementation_index) key, prefer the P5c record when present (it holds either
a freshly generated implementation or a relaxed-reparse recovery), otherwise
keep the P5b record. This yields the complete k=8 pool without duplicates.

Usage:
    python scripts/merge_implementations_p5c.py \
        --p5b data/processed/p5b_medium20_m2a_..._v1_implementations.jsonl \
        --p5c data/processed/p5c_medium_k8_repairv1_seed42_v1_implementations.jsonl \
        --output data/processed/p5c_medium_k8_repairv1_seed42_v1_merged_implementations.jsonl
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--p5b", required=True)
    parser.add_argument("--p5c", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    merged: dict[tuple, dict] = {}
    stats = {"p5b_records": 0, "p5c_records": 0, "p5c_wins": 0, "p5b_only": 0}

    for label, path in (("p5b", _resolve(args.p5b)), ("p5c", _resolve(args.p5c))):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            stats[f"{label}_records"] += 1
            key = (
                str(r.get("problem_id")),
                int(r.get("decomposition_index", 0)),
                str(r.get("function_name")),
                int(r.get("implementation_index", 0)),
            )
            if label == "p5b":
                merged[key] = r
            else:
                if key in merged:
                    stats["p5c_wins"] += 1
                merged[key] = r

    stats["p5b_only"] = stats["p5b_records"] - stats["p5c_wins"]
    stats["merged_records"] = len(merged)
    stats["with_code"] = sum(1 for r in merged.values() if r.get("code"))

    out = _resolve(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as handle:
        for key in sorted(merged):
            handle.write(json.dumps(merged[key], ensure_ascii=False) + "\n")

    summary_path = Path(str(out).replace(".jsonl", "") + "_merge_summary.json")
    summary_path.write_text(json.dumps({
        "p5b": str(_resolve(args.p5b)),
        "p5c": str(_resolve(args.p5c)),
        "output": str(out),
        **stats,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))


def _resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


if __name__ == "__main__":
    main()
