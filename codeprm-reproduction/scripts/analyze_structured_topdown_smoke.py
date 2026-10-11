"""Audit stage 1b and run a public-only deterministic assembly counterfactual."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.collect_funprm_function_prefix_rollouts import continuation_prompt, function_prefixes  # noqa: E402
from src.data_loader import load_problems  # noqa: E402
from src.decomposition import Decomposition, decomposition_from_dict  # noqa: E402
from src.modular import evaluate_split  # noqa: E402
from src.structured_topdown import validate_program_against_contract  # noqa: E402
from src.whole_program import parse_whole_program  # noqa: E402


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def extract_program_source(raw: str) -> str:
    value = str(raw or "")
    code_match = re.search(r"<code>(.*?)</code>", value, flags=re.IGNORECASE | re.DOTALL)
    if code_match:
        value = code_match.group(1)
    fence = re.fullmatch(
        r"\s*```(?:python|py)?\s*\n?(.*?)\n?```\s*",
        value,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return (fence.group(1) if fence else value).strip()


def deterministic_contract_rewrite(
    raw_program: str,
    decomposition: Decomposition,
    problem: dict[str, Any],
) -> tuple[str | None, dict[str, Any]]:
    """Reorder exact top-level functions and install frozen docstrings without changing bodies."""
    source = extract_program_source(raw_program)
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return None, {"valid": False, "errors": [f"syntax_error:{exc}"]}

    definitions = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    expected_names = [item.name for item in decomposition.functions]
    actual_names = [node.name for node in definitions]
    if len(actual_names) != len(set(actual_names)):
        return None, {"valid": False, "errors": ["duplicate_top_level_function"]}
    if set(actual_names) != set(expected_names):
        return None, {
            "valid": False,
            "errors": [
                "function_set_mismatch:"
                + ",".join(actual_names)
                + "!="
                + ",".join(expected_names)
            ],
        }
    nested = [
        node.name
        for definition in definitions
        for node in ast.walk(definition)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node is not definition
    ]
    if nested:
        return None, {"valid": False, "errors": ["nested_functions:" + ",".join(nested)]}

    by_name = {node.name: node for node in definitions}
    inserted_docstrings = 0
    replaced_docstrings = 0
    ordered_definitions = []
    for spec in decomposition.functions:
        node = by_name[spec.name]
        existing_docstring = ast.get_docstring(node, clean=True)
        if existing_docstring is None:
            inserted_docstrings += 1
        elif existing_docstring.strip() != spec.docstring.strip():
            replaced_docstrings += 1
        body = list(node.body)
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
            body = body[1:]
        doc_node = ast.Expr(value=ast.Constant(value=spec.docstring.strip()))
        if node.body:
            ast.copy_location(doc_node, node.body[0])
        node.body = [doc_node, *body]
        ordered_definitions.append(node)

    prelude_types = (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign)
    non_definitions = [
        node for node in tree.body
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    prelude = [node for node in non_definitions if isinstance(node, prelude_types)]
    postlude = [node for node in non_definitions if not isinstance(node, prelude_types)]
    rewritten_tree = ast.Module(body=[*prelude, *ordered_definitions, *postlude], type_ignores=[])
    ast.fix_missing_locations(rewritten_tree)
    rewritten = ast.unparse(rewritten_tree).rstrip() + "\n"
    parsed_code, _, parse_info = parse_whole_program(rewritten, problem, "top_down_cof")
    if parsed_code is None:
        return None, {
            "valid": False,
            "errors": ["rewritten_program_invalid", *(parse_info.get("errors") or [])],
        }
    conformance = validate_program_against_contract(parsed_code, decomposition)
    return (
        parsed_code if conformance["valid"] else None,
        {
            "valid": bool(conformance["valid"]),
            "original_function_order": actual_names,
            "rewritten_function_order": expected_names,
            "function_order_changed": actual_names != expected_names,
            "inserted_docstrings": inserted_docstrings,
            "replaced_docstrings": replaced_docstrings,
            "errors": conformance["errors"],
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apps-path", required=True)
    parser.add_argument("--generations", required=True)
    parser.add_argument("--evaluations", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--test-timeout", type=float, default=10.0)
    args = parser.parse_args()

    problems = {str(item["problem_id"]): item for item in load_problems(args.apps_path)}
    rows = read_jsonl(Path(args.generations))
    evaluations = read_jsonl(Path(args.evaluations))
    summary = json.loads(Path(args.summary).read_text(encoding="utf-8"))

    accepted = [row for row in rows if row.get("code")]
    prefix_checks = []
    for row in accepted:
        problem = problems[str(row["problem_id"])]
        for prefix in function_prefixes(str(row["code"])):
            prompt = continuation_prompt(problem, prefix["prefix_code"], "top_down_cof")
            prefix_checks.append({
                "problem_id": row["problem_id"],
                "candidate_index": row["candidate_index"],
                "function_index": prefix["function_index"],
                "prefix_exact": str(row["code"]).startswith(prefix["prefix_code"]),
                "prompt_contains_prefix": prefix["prefix_code"] in prompt,
                "forbidden_entrypoint_last_absent": "put the required starter entrypoint last" not in prompt,
            })

    counterfactual_rows = []
    by_problem: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if not row.get("contract_validation", {}).get("valid") or not row.get("program_request_made"):
            continue
        problem_id = str(row["problem_id"])
        contract_value = {"protocol": "json", **dict(row["contract"])}
        decomposition = decomposition_from_dict(contract_value)
        code, rewrite = deterministic_contract_rewrite(
            str(row.get("program_raw_response", "")),
            decomposition,
            problems[problem_id],
        )
        public = evaluate_split(code, problems[problem_id], "public", args.test_timeout, None) if code else None
        item = {
            "problem_id": problem_id,
            "candidate_index": int(row["candidate_index"]),
            "rewrite": rewrite,
            "code_hash": hashlib.sha256(code.encode("utf-8")).hexdigest() if code else None,
            "rewritten_code": code,
            "public": public,
        }
        counterfactual_rows.append(item)
        by_problem.setdefault(problem_id, []).append(item)

    counterfactual_selected = []
    for problem_id, candidates in sorted(by_problem.items()):
        eligible = [item for item in candidates if item["rewritten_code"]]
        eligible.sort(
            key=lambda item: (
                -float((item.get("public") or {}).get("pass_rate", 0.0)),
                int(item["candidate_index"]),
            )
        )
        if eligible:
            counterfactual_selected.append(eligible[0])

    contract_valid = [row for row in rows if row.get("contract_validation", {}).get("valid")]
    parser_valid = [
        row for row in rows
        if row.get("program_request_made")
        and row.get("program_parse", {}).get("syntax_valid")
        and not row.get("program_parse", {}).get("errors")
        and not row.get("program_parse", {}).get("error")
    ]
    prefix_passed = sum(
        all(check[key] for key in ("prefix_exact", "prompt_contains_prefix", "forbidden_entrypoint_last_absent"))
        for check in prefix_checks
    )
    audit = {
        "analysis_label": "post_hoc_public_only_counterfactual_not_phase_result",
        "original": {
            "candidate_trajectories": len(rows),
            "contract_valid_candidates": len(contract_valid),
            "contract_problem_coverage": len({str(row["problem_id"]) for row in contract_valid}),
            "program_requests": int(summary.get("program_requests", 0)),
            "topdown_parser_valid_candidates": len(parser_valid),
            "topdown_parser_problem_coverage": len({str(row["problem_id"]) for row in parser_valid}),
            "exact_contract_valid_candidates": len(accepted),
            "exact_contract_problem_coverage": len({str(row["problem_id"]) for row in accepted}),
            "selected_public_pass": int(summary.get("selected_public_pass", 0)),
            "private_program_evaluations": int(summary.get("private_program_evaluations", 0)),
            "private_test_executions": int(summary.get("private_test_executions", 0)),
            "prefix_nodes": len(prefix_checks),
            "prefix_checks_passed": prefix_passed,
            "phase_pass": False,
        },
        "counterfactual": {
            "description": "Reorder an exact set of existing top-level functions to the frozen contract and install contract docstrings; do not change function bodies or call a model.",
            "new_model_requests": 0,
            "private_evaluations": 0,
            "rewritable_candidates": sum(bool(item["rewritten_code"]) for item in counterfactual_rows),
            "problem_coverage": len({item["problem_id"] for item in counterfactual_rows if item["rewritten_code"]}),
            "selected_public_pass": sum(
                bool(
                    item.get("public", {}).get("total", 0)
                    and item["public"].get("passed") == item["public"].get("total")
                )
                for item in counterfactual_selected
            ),
            "selected_problems": len(counterfactual_selected),
            "not_valid_for_changing_phase_result": True,
        },
        "counterfactual_candidates": counterfactual_rows,
        "source_hashes": {
            "generations_sha256": hashlib.sha256(Path(args.generations).read_bytes()).hexdigest(),
            "evaluations_sha256": hashlib.sha256(Path(args.evaluations).read_bytes()).hexdigest(),
            "summary_sha256": hashlib.sha256(Path(args.summary).read_bytes()).hexdigest(),
        },
        "evaluated_problem_ids": [str(item["problem_id"]) for item in evaluations],
    }
    output = Path(args.output)
    if output.exists():
        raise FileExistsError(f"refusing to overwrite {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in audit.items() if key != "counterfactual_candidates"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
