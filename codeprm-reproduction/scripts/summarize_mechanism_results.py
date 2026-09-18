"""Aggregate whole-program and modular mechanism run records."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run",
        action="append",
        nargs=3,
        metavar=("NAME", "EVALUATIONS", "SUMMARY"),
        required=True,
        help="A run name, evaluation JSONL, and summary JSON; repeat four times.",
    )
    parser.add_argument("--output", required=True, help="Markdown report")
    args = parser.parse_args()

    rows: list[dict[str, Any]] = []
    for name, evaluation_value, summary_value in args.run:
        evaluation_path = _resolve(evaluation_value)
        summary_path = _resolve(summary_value)
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        row = {
            "name": name,
            "summary": summary,
            "problems_evaluated": 0,
            "selected_public_passed": 0,
            "selected_public_tests": 0,
            "selected_private_passed": 0,
            "selected_private_tests": 0,
            "selected_public_full": 0,
            "selected_private_full": 0,
            "public_error_types": {},
            "private_error_types": {},
        }
        for line in evaluation_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            selection = record.get("selection", {})
            candidates = selection.get("candidates", [])
            selected_id = selection.get("selected_candidate_id")
            selected = next((item for item in candidates if item.get("candidate_id") == selected_id), None)
            if selected is None:
                continue
            public = selected.get("public", {})
            private = (record.get("final_evaluation") or {}).get("private", {})
            row["problems_evaluated"] += 1
            row["selected_public_passed"] += int(public.get("passed", 0) or 0)
            row["selected_public_tests"] += int(public.get("total", 0) or 0)
            row["selected_private_passed"] += int(private.get("passed", 0) or 0)
            row["selected_private_tests"] += int(private.get("total", 0) or 0)
            row["selected_public_full"] += int(public.get("total", 0) > 0 and public.get("passed") == public.get("total"))
            row["selected_private_full"] += int(private.get("total", 0) > 0 and private.get("passed") == private.get("total"))
            _count_errors(row["public_error_types"], public)
            _count_errors(row["private_error_types"], private)
        row["selected_public_test_rate"] = _rate(row["selected_public_passed"], row["selected_public_tests"])
        row["selected_private_test_rate"] = _rate(row["selected_private_passed"], row["selected_private_tests"])
        rows.append(row)

    report = _render(rows)
    output_path = _resolve(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(report)


def _count_errors(target: dict[str, int], result: dict[str, Any]) -> None:
    for test in result.get("tests", []) if isinstance(result, dict) else []:
        error_type = test.get("error_type")
        if error_type:
            target[error_type] = int(target.get(error_type, 0)) + 1


def _rate(passed: int, total: int) -> float:
    return round(passed / total, 4) if total else 0.0


def _resolve(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def _render(rows: list[dict[str, Any]]) -> str:
    lines = [
        "# DecompRL mechanism ablation: development-20",
        "",
        "This report compares prompt-only mechanisms on the frozen custom APPS train split. It is a local mechanism smoke, not a paper-scale DecompRL reproduction.",
        "",
        "## Fairness rules",
        "",
        "All runs use Qwen2.5-Coder 7B through local Ollama, seed 42, exact starter APIs, 10-second per-test timeout, public-only candidate selection, and private evaluation only after the selection record is frozen. M0/M1 use four whole-program candidates per problem. M2a/M2b use two decompositions, two implementations per function, and at most eight combinations per decomposition. Duplicate code hashes are executed once and counted separately.",
        "",
        "## Results",
        "",
        "| Method | Valid outputs | Candidate coverage | Unique programs executed | Selected public full | Selected private full | Selected private test rate | Prompt/output tokens | Model seconds |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        summary = row["summary"]
        if "valid_generations" in summary:
            valid = f"{summary.get('valid_generations', 0)}/{summary.get('generation_requests', 0)}"
        else:
            valid = f"decomp {summary.get('valid_decompositions', 0)}/{summary.get('decomposition_requests', 0)}; impl {summary.get('valid_implementations', 0)}/{summary.get('implementation_requests', 0)}"
        unique = summary.get("unique_valid_generations", summary.get("unique_composable_combinations", 0))
        lines.append(
            f"| {row['name']} | {valid} | {row['problems_evaluated']}/{summary.get('problems', row['problems_evaluated'])} | {unique} | {row['selected_public_full']}/{summary.get('problems', row['problems_evaluated'])} | {row['selected_private_full']}/{summary.get('problems', row['problems_evaluated'])} | {row['selected_private_test_rate']:.3f} ({row['selected_private_passed']}/{row['selected_private_tests']}) | {summary.get('model_prompt_tokens', 0)}/{summary.get('model_output_tokens', 0)} | {float(summary.get('model_reported_seconds', 0.0)):.1f} |"
        )
    lines += [
        "",
        "The full-pass columns use all 20 problems as the denominator; a problem without a valid candidate is counted as not solved. Candidate coverage is shown separately. The test-rate column is more granular because APPS problems have different numbers of private examples.",
        "",
        "## Interpretation",
        "",
        "M1 improves selected full private passes over M0 on this development slice, but uses almost twice the output tokens and model time. Neither modular protocol beats M1 at this budget: M2a and M2b have lower selected private full-pass counts and much higher generation/combination cost. This is a No-Go for RL training under the current prompt-only mechanism and budget; it is not evidence that decomposition can never help on harder data or with a better policy.",
        "",
        "M2a produced 14 rejected nested-function implementations. M2b produced rejected extra/nested functions, one forward dependency, one unknown dependency, and empty implementation pools. These failures are reported as contract failures rather than silently repaired.",
        "",
        "## Reproducibility",
        "",
        "The raw JSONL records and summaries are under `data/processed/`. Each run is checkpointed by problem; rerunning the same command and prefix resumes unfinished problems. The executor uses an isolated temporary Python process but is not an OS sandbox, so this local experiment must not execute untrusted arbitrary code.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
