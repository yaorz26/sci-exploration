"""Post-hoc private pool oracle for the frozen FunPRM holdout candidate pool."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data_loader import load_problems
from src.modular import evaluate_split


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluations", required=True)
    parser.add_argument("--apps-path", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    problems = {str(row["problem_id"]): row for row in load_problems(args.apps_path)}
    rows = [json.loads(line) for line in Path(args.evaluations).read_text(encoding="utf-8").splitlines() if line.strip()]
    per_problem: list[dict] = []
    for row in rows:
        problem_id = str(row["problem_id"])
        candidates = [candidate for candidate in row["selection"]["candidates"] if candidate.get("code")]
        scored = []
        for candidate in candidates:
            private = evaluate_split(str(candidate["code"]), problems[problem_id], "private", args.timeout, None)
            scored.append({
                "candidate_index": int(candidate["candidate_index"]),
                "public_pass_rate": float((candidate.get("public") or {}).get("pass_rate", 0.0)),
                "private_pass_rate": float(private.get("pass_rate", 0.0)),
                "private_all_pass": bool(private.get("total", 0) and private.get("passed", 0) == private.get("total", 0)),
            })
        best_rate = max(scored, key=lambda item: (item["private_pass_rate"], -item["candidate_index"])) if scored else None
        best_all = [item for item in scored if item["private_all_pass"]]
        per_problem.append({
            "problem_id": problem_id,
            "candidate_count": len(scored),
            "pool_oracle_private_pass_rate": best_rate["private_pass_rate"] if best_rate else 0.0,
            "pool_oracle_all_pass": bool(best_all),
            "pool_oracle_candidate_index": best_rate["candidate_index"] if best_rate else None,
            "candidate_private_rows": scored,
        })

    output = {
        "posthoc_private_only": True,
        "selection_private_fields_used": [],
        "problems": len(per_problem),
        "pool_oracle_all_pass": sum(item["pool_oracle_all_pass"] for item in per_problem),
        "pool_oracle_all_pass_rate": sum(item["pool_oracle_all_pass"] for item in per_problem) / len(per_problem) if per_problem else 0.0,
        "pool_oracle_mean_pass_rate": sum(item["pool_oracle_private_pass_rate"] for item in per_problem) / len(per_problem) if per_problem else 0.0,
        "rows": per_problem,
        "interpretation": "Post-hoc upper bound; this private scan is not a deployable selector and was run only after frozen selection outputs were produced.",
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: output[key] for key in ["problems", "pool_oracle_all_pass", "pool_oracle_all_pass_rate", "pool_oracle_mean_pass_rate"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
