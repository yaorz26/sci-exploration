"""Add private training labels to a deferred public-only candidate pool.

This script is allowed only on a pre-declared training split. It is kept
separate from holdout routing so private labels cannot accidentally affect
holdout candidate selection.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data_loader import load_problems  # noqa: E402
from src.modular import evaluate_split  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluations", required=True)
    parser.add_argument("--apps-path", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    problems = {str(row["problem_id"]): row for row in load_problems(args.apps_path)}
    rows = [json.loads(line) for line in Path(args.evaluations).read_text(encoding="utf-8").splitlines() if line.strip()]
    private_cache: dict[str, dict] = {}
    output: list[dict] = []
    candidate_rows: list[dict] = []
    for row in rows:
        for candidate in row.get("selection", {}).get("candidates", []):
            enriched = dict(candidate)
            enriched["problem_id"] = row["problem_id"]
            candidate_rows.append(enriched)
    for row in candidate_rows:
        problem_id = str(row["problem_id"])
        code = row.get("code")
        enriched = dict(row)
        if code:
            code_hash = hashlib.sha256(str(code).encode("utf-8")).hexdigest()
            if code_hash not in private_cache:
                private_cache[code_hash] = evaluate_split(str(code), problems[problem_id], "private", args.timeout, None)
            private = private_cache[code_hash]
            enriched["private_feedback"] = private
            enriched["label"] = float(private.get("pass_rate", 0.0))
            enriched["binary_label"] = int(private.get("total", 0) and private.get("passed", 0) == private.get("total", 0))
            enriched["private_label_source"] = "training_split_private_after_public_pool_generation"
        else:
            enriched["private_feedback"] = None
            enriched["label"] = 0.0
            enriched["binary_label"] = 0
            enriched["private_label_source"] = "invalid_candidate"
        output.append(enriched)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in output) + "\n", encoding="utf-8")
    summary = {
        "input": str(Path(args.evaluations)),
        "output": str(target),
        "problems": len({row["problem_id"] for row in output}),
        "candidate_rows": len(output),
        "valid_candidates": sum(bool(row.get("code")) for row in output),
        "private_evaluations": len(private_cache),
        "private_allowed_scope": "training split only",
    }
    target.with_name(target.stem + "_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
