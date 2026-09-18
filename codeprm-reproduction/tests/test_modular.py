from __future__ import annotations

from src.decomposition import Decomposition, FunctionSpec
from src.contract_audit import audit_implementation_contract
from src.modular import build_implementation_prompt, evaluate_split, parse_implementation


def test_implementation_parser_checks_signature_and_top_level_contract() -> None:
    code, meta = parse_implementation(
        "def helper(other):\n    return other\n",
        "helper",
        "helper(text)",
    )
    assert code is None
    assert meta["error"] == "signature_mismatch:helper"

    code, meta = parse_implementation(
        "value = 1\ndef helper(text):\n    return text\n",
        "helper",
        "helper(text)",
    )
    assert code is None
    assert meta["error"] == "extra_top_level_statements"


def test_candidate_budget_marks_unstarted_tests_without_changing_denominator() -> None:
    problem = {
        "execution_mode": "stdin",
        "public_tests": [
            {"input": "", "output": "x"},
            {"input": "", "output": "x"},
            {"input": "", "output": "x"},
        ],
    }
    result = evaluate_split(
        "while True: pass",
        problem,
        "public",
        timeout_seconds=0.2,
        candidate_timeout_seconds=0.25,
    )
    assert result["total"] == 3
    assert result["passed"] == 0
    assert result["budget_exhausted"] is True
    assert any(item["error_type"] == "candidate_budget_exhausted" for item in result["tests"])


def test_repair_implementation_prompt_forbids_nested_definitions() -> None:
    decomposition = Decomposition([
        FunctionSpec("helper", "helper(x)", "Transform x.", []),
        FunctionSpec("solve", "solve()", "Read and print.", ["helper"]),
    ], "json", "")
    prompt = build_implementation_prompt(
        {"execution_mode": "stdin", "question": "Q"},
        decomposition,
        decomposition.functions[1],
        "repair_v1",
    )
    assert "exactly one top-level `def`" in prompt


def test_contract_audit_detects_helper_io_and_undeclared_calls() -> None:
    decomposition = Decomposition([
        FunctionSpec("helper", "helper(x)", "Transform x.", []),
        FunctionSpec("other", "other(x)", "Other transform.", []),
        FunctionSpec("solve", "solve()", "Read and print.", ["helper"]),
    ], "json", "")
    result = audit_implementation_contract(
        "def solve():\n    value = other(input())\n    print(value)\n",
        decomposition,
        "solve",
        {"execution_mode": "stdin"},
    )
    assert "undeclared_decomposition_call:other" in result["errors"]
    assert result["missing_dependencies"] == ["helper"]
