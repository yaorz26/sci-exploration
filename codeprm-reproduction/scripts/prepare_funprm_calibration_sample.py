"""Freeze a label-independent hash sample of FunPRM prefix nodes."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def key(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "problem_id": str(row["problem_id"]),
        "source_candidate_index": int(row["source_candidate_index"]),
        "function_index": int(row["function_index"]),
    }


def canonical_key(value: dict[str, Any]) -> str:
    return f"{value['problem_id']}|{value['source_candidate_index']}|{value['function_index']}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nodes", required=True)
    parser.add_argument("--size", type=int, default=64)
    parser.add_argument("--salt", default="20260924-calibration-v1")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    nodes_path = Path(args.nodes)
    output_path = Path(args.output)
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite {output_path}")
    rows = read_jsonl(nodes_path)
    if args.size <= 0 or args.size > len(rows):
        raise ValueError("invalid sample size")
    keys = [key(row) for row in rows]
    if len({canonical_key(item) for item in keys}) != len(keys):
        raise ValueError("duplicate node keys")
    ranked = sorted(
        keys,
        key=lambda item: hashlib.sha256(
            f"{args.salt}|{canonical_key(item)}".encode("utf-8")
        ).hexdigest(),
    )
    selected = ranked[: args.size]
    by_key = {canonical_key(key(row)): row for row in rows}
    manifest = {
        "experiment": "funprm_label_calibration_20260924",
        "selection_policy": "lowest SHA-256 ranks over salt|problem_id|source_candidate_index|function_index; label-independent",
        "salt": args.salt,
        "population_nodes": len(rows),
        "sample_size": args.size,
        "input": str(nodes_path),
        "input_sha256": sha256(nodes_path),
        "selected_nodes": selected,
        "selected_existing_rollout_counts": [len(by_key[canonical_key(item)].get("rollouts", [])) for item in selected],
        "selected_key_hash": hashlib.sha256(
            "\n".join(canonical_key(item) for item in selected).encode("utf-8")
        ).hexdigest(),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "population_nodes": len(rows),
        "sample_size": len(selected),
        "existing_rollout_count_histogram": {
            str(count): manifest["selected_existing_rollout_counts"].count(count)
            for count in sorted(set(manifest["selected_existing_rollout_counts"]))
        },
        "selected_key_hash": manifest["selected_key_hash"],
        "output": str(output_path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
