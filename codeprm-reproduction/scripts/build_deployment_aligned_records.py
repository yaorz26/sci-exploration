"""Align exact continuation labels with the original candidate input at scoring time.

The label remains the mean private pass rate of code continuations from a
thought prefix. Only the model input fields are replaced with the original
candidate's code and public execution feedback, matching the deployment-time
candidate selector.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step-data", required=True)
    parser.add_argument("--feedback-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    feedback = defaultdict(list)
    for row in read_jsonl(Path(args.feedback_path)):
        feedback[row["problem_id"]].append(row)

    output_rows = []
    for row in read_jsonl(Path(args.step_data)):
        candidate = feedback[row["problem_id"]][int(row["source_candidate_index"])]
        aligned = dict(row)
        aligned["code"] = candidate["code"]
        aligned["public_feedback"] = candidate["public_feedback"]
        aligned["input_code_source"] = "original_source_candidate"
        aligned["input_public_feedback_source"] = "original_source_candidate"
        output_rows.append(aligned)

    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in output_rows) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(target),
        "records": len(output_rows),
        "problems": len({row["problem_id"] for row in output_rows}),
        "input_code_source": "original_source_candidate",
        "label_source": "continuation_private_pass_rate_mean",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
