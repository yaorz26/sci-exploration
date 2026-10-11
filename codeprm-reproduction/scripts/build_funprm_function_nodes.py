"""Build function-node supervision records for the FunPRM-style pilot.

The source file contains exact continuation-level rewards from the existing
CodePRM data preparation. We keep those labels, but explicitly mark the
function boundary mapping as derived: local data does not contain the paper's
original function-by-function Monte Carlo trajectories.
"""

from __future__ import annotations

import argparse
import ast
import json
from collections import defaultdict
from pathlib import Path


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _function_segments(code: str) -> list[dict]:
    tree = ast.parse(code)
    lines = code.splitlines()
    segments: list[dict] = []
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.lineno is None or node.end_lineno is None:
            continue
        segment = "\n".join(lines[node.lineno - 1 : node.end_lineno])
        segments.append({
            "name": node.name,
            "start_line": node.lineno,
            "end_line": node.end_lineno,
            "code": segment,
        })
    return segments


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    source = Path(args.input)
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = _read_jsonl(source)
    groups: dict[tuple[str, int], list[dict]] = defaultdict(list)
    for row in rows:
        groups[(str(row["problem_id"]), int(row.get("source_candidate_index", 0)))].append(row)

    output: list[dict] = []
    skipped = defaultdict(int)
    candidate_count = 0
    for (problem_id, candidate_index), candidate_rows in groups.items():
        candidate_count += 1
        candidate_rows.sort(key=lambda row: int(row.get("step_index", 0)))
        first = candidate_rows[0]
        code = str(first.get("code", ""))
        try:
            functions = _function_segments(code)
        except (SyntaxError, TypeError, ValueError):
            skipped["syntax_or_ast_error"] += 1
            continue
        if not functions:
            skipped["no_top_level_function"] += 1
            continue

        public_feedback = first.get("public_feedback", {})
        private_feedback = first.get("private_feedback", {})
        final_label = float(first.get("continuation_pass_rate", private_feedback.get("pass_rate", 0.0)))
        steps = [row for row in candidate_rows if row.get("step_label") is not None]
        for function_index, function in enumerate(functions):
            step_row = steps[min(function_index, len(steps) - 1)] if steps else first
            prefix_code = "\n\n".join(item["code"] for item in functions[: function_index + 1])
            completed_code = "\n\n".join(item["code"] for item in functions[:function_index])
            noisy_label = float(step_row.get("step_label", final_label))
            output.append({
                "problem_id": problem_id,
                "source_candidate_index": candidate_index,
                "function_index": function_index,
                "function_name": function["name"],
                "problem": first.get("problem", ""),
                "completed_functions": completed_code,
                "current_function": function["code"],
                "prefix_code": prefix_code,
                "thought_prefix": step_row.get("thought_prefix", []),
                "public_feedback": public_feedback,
                "step_label": noisy_label,
                "binary_step_label": int(noisy_label >= 1.0),
                "final_label": final_label,
                "binary_final_label": int(final_label >= 1.0),
                "label": noisy_label,
                "label_source": "continuation_step_label_mapped_to_function_boundary",
                "exact_step_label": True,
                "function_node_derived": True,
                "private_label_source": "training_split_only",
            })

    target.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in output) + "\n", encoding="utf-8")
    summary = {
        "input": str(source),
        "output": str(target),
        "source_rows": len(rows),
        "candidate_groups": candidate_count,
        "function_node_records": len(output),
        "problems": len({row["problem_id"] for row in output}),
        "skipped_candidates": dict(skipped),
        "label_definition": "exact continuation step_label mapped by function order; mapping is derived, not author-original",
    }
    target.with_name(target.stem + "_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
