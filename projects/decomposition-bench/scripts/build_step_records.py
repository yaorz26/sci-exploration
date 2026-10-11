"""Expand candidate-level feedback records into step-level CodePRM records.

The current APPS pool has a candidate-level private pass-rate label. This
script duplicates that label over the thought steps and marks the result as a
proxy. It is suitable for the first neural pipeline smoke test, but it is not
the paper's exact continuation-level step label.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    source = Path(args.input)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    records = []
    candidates = 0
    steps = 0
    for line in source.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        candidates += 1
        thoughts = row.get("thoughts") or []
        if not isinstance(thoughts, list):
            thoughts = [str(thoughts)]
        label = float(row.get("label", row.get("private_feedback", {}).get("pass_rate", 0.0)))
        binary = int(row.get("binary_label", label == 1.0))
        for index, thought in enumerate(thoughts):
            records.append({
                "problem_id": row["problem_id"],
                "problem": row.get("problem", ""),
                "step_index": index,
                "thought_step": str(thought),
                "thought_prefix": "\n".join(str(item) for item in thoughts[: index + 1]),
                "code": row.get("code", ""),
                "public_feedback": row.get("public_feedback", {}),
                "label": label,
                "binary_label": binary,
                "generator_model": row.get("generator_model", "unknown"),
                "random_seed": row.get("random_seed"),
                "label_source": "candidate_private_pass_rate_proxy",
                "exact_step_label": False
            })
            steps += 1
    target.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in records) + "\n", encoding="utf-8")
    print(json.dumps({"input": str(source), "output": str(target), "candidates": candidates, "step_records": steps, "exact_step_label": False}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
