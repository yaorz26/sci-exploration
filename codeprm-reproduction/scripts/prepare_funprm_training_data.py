"""Freeze minimal FunPRM training rows with labels recomputed from rollouts."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int]] = set()
    for row in rows:
        key = (
            str(row["problem_id"]),
            int(row["source_candidate_index"]),
            int(row["function_index"]),
        )
        if key in seen:
            raise ValueError(f"duplicate node key: {key}")
        seen.add(key)
        rollouts = list(row.get("rollouts", []))
        if len(rollouts) not in {4, 8, 16}:
            raise ValueError(f"unexpected rollout count {len(rollouts)} for node {key}")
        indices = [int(item["rollout_index"]) for item in rollouts]
        if sorted(indices) != list(range(len(rollouts))):
            raise ValueError(f"non-contiguous rollout indices for node {key}")
        successes = sum(bool(item.get("success")) for item in rollouts)
        prepared.append({
            "problem_id": key[0],
            "source_candidate_index": key[1],
            "function_index": key[2],
            "function_name": str(row.get("function_name", "")),
            "problem": str(row.get("problem", "")),
            "prefix_code": str(row.get("prefix_code", "")),
            "label": successes / len(rollouts),
            "rollout_count": len(rollouts),
            "successful_rollouts": successes,
            "label_source": "mean_of_all_saved_unit_test_only_rollouts",
        })
    return prepared


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nodes", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--manifest", required=True)
    args = parser.parse_args()

    nodes_path = Path(args.nodes)
    output_path = Path(args.output)
    manifest_path = Path(args.manifest)
    if output_path.exists() or manifest_path.exists():
        raise FileExistsError("refusing to overwrite frozen training artifacts")
    rows = prepare_rows(read_jsonl(nodes_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )
    problem_ids = sorted({row["problem_id"] for row in rows})
    rollout_histogram = Counter(int(row["rollout_count"]) for row in rows)
    manifest = {
        "experiment": "funprm_helperfirst_scale_prm_20260924",
        "source_nodes": str(nodes_path),
        "source_nodes_sha256": sha256(nodes_path),
        "output": str(output_path),
        "output_sha256": sha256(output_path),
        "records": len(rows),
        "problems": len(problem_ids),
        "problem_ids": problem_ids,
        "rollout_count_histogram": {str(key): rollout_histogram[key] for key in sorted(rollout_histogram)},
        "positive_nodes": sum(float(row["label"]) > 0.0 for row in rows),
        "mean_label": sum(float(row["label"]) for row in rows) / len(rows),
        "weighting": "one record per node; no rollout-count weighting",
        "included_fields": list(rows[0]) if rows else [],
        "test_fields_included": [],
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "records": manifest["records"],
        "problems": manifest["problems"],
        "rollout_count_histogram": manifest["rollout_count_histogram"],
        "positive_nodes": manifest["positive_nodes"],
        "mean_label": manifest["mean_label"],
        "output_sha256": manifest["output_sha256"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
