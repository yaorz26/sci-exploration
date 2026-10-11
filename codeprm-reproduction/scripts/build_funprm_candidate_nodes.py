"""Convert complete functionized training candidates into function nodes."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path


def _segments(code: str) -> list[dict]:
    tree = ast.parse(code)
    lines = code.splitlines()
    return [
        {"name": node.name, "code": "\n".join(lines[node.lineno - 1 : node.end_lineno])}
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.lineno is not None and node.end_lineno is not None
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in Path(args.candidates).read_text(encoding="utf-8").splitlines() if line.strip()]
    output: list[dict] = []
    skipped = {"invalid": 0, "no_functions": 0}
    for row in rows:
        code = row.get("code")
        if not code:
            skipped["invalid"] += 1
            continue
        try:
            functions = _segments(str(code))
        except (SyntaxError, TypeError, ValueError):
            skipped["invalid"] += 1
            continue
        if not functions:
            skipped["no_functions"] += 1
            continue
        for index, function in enumerate(functions):
            prefix = "\n\n".join(item["code"] for item in functions[: index + 1])
            output.append({
                "problem_id": row["problem_id"],
                "source_candidate_index": int(row.get("candidate_index", 0)),
                "function_index": index,
                "function_name": function["name"],
                "problem": row.get("problem", ""),
                "completed_functions": "\n\n".join(item["code"] for item in functions[:index]),
                "current_function": function["code"],
                "prefix_code": prefix,
                "thought_prefix": [],
                "public_feedback": row.get("public", {}),
                "step_label": float(row.get("label", 0.0)),
                "binary_step_label": int(row.get("binary_label", 0)),
                "final_label": float(row.get("label", 0.0)),
                "binary_final_label": int(row.get("binary_label", 0)),
                "label": float(row.get("label", 0.0)),
                "label_source": "training_candidate_private_pass_rate_at_function_boundary",
                "exact_step_label": False,
                "function_node_derived": True,
                "private_label_source": row.get("private_label_source", "training_split_only"),
            })
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in output) + "\n", encoding="utf-8")
    summary = {
        "input": str(Path(args.candidates)),
        "output": str(target),
        "source_candidates": len(rows),
        "function_node_records": len(output),
        "problems": len({row["problem_id"] for row in output}),
        "skipped": skipped,
        "label_definition": "complete-candidate private pass rate duplicated at each derived function boundary; training split only",
    }
    target.with_name(target.stem + "_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
