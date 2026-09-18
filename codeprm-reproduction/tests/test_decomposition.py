from __future__ import annotations

import json

from src.decomposition import (
    Decomposition,
    FunctionSpec,
    build_decomposition_prompt,
    decomposition_from_dict,
    parse_decomposition,
    validate_decomposition,
)


def problem(starter: str = "def solve(text):\n    pass") -> dict:
    return {"problem_id": "fixture", "question": "Do something.", "starter_code": starter}


def test_json_protocol_validates_entrypoint_and_dag() -> None:
    raw = json.dumps({
        "functions": [
            {"name": "parse_input", "signature": "parse_input(text: str) -> list", "docstring": "Parse input.", "depends_on": []},
            {"name": "solve", "signature": "solve(text: str) -> str", "docstring": "Solve task.", "depends_on": ["parse_input"]},
        ]
    })
    parsed, info = parse_decomposition(raw, "json")
    assert info["raw_valid"] is True
    assert parsed is not None
    result = validate_decomposition(parsed, problem())
    assert result["valid"] is True
    assert result["entrypoint_preserved"] is True
    assert result["dag_valid"] is True


def test_json_fence_is_not_counted_as_raw_valid() -> None:
    raw = "```json\n{\"functions\": []}\n```"
    parsed, info = parse_decomposition(raw, "json")
    assert parsed is not None
    assert info["raw_valid"] is False
    assert info["normalized"] is True


def test_cycle_and_missing_entrypoint_are_rejected() -> None:
    parsed = Decomposition([
        FunctionSpec("a", "a()", "A.", ["b"]),
        FunctionSpec("b", "b()", "B.", ["a"]),
    ], "json", "")
    result = validate_decomposition(parsed, problem())
    assert result["valid"] is False
    assert "missing_entrypoint:solve" in result["errors"]
    assert "dependency_cycle" in result["errors"]


def test_skeleton_protocol_extracts_functions() -> None:
    raw = """```python
def parse_input(text):
    \"\"\"Parse input.\"\"\"
    pass

def solve(text):
    \"\"\"Solve task.\"\"\"
    pass
```"""
    parsed, info = parse_decomposition(raw, "skeleton")
    assert parsed is not None
    assert info["normalized"] is True
    assert [item.name for item in parsed.functions] == ["parse_input", "solve"]
    assert parsed.functions[0].depends_on == []
    assert parsed.functions[1].depends_on == ["parse_input"]


def test_prompt_does_not_include_test_cases() -> None:
    prompt = build_decomposition_prompt({
        "question": "Question",
        "starter_code": "def solve(x): pass",
        "public_tests": [{"input": "secret-public"}],
        "private_tests": [{"input": "secret-private"}],
    })
    assert "secret-public" not in prompt
    assert "secret-private" not in prompt


def test_explicit_whole_program_route_is_available_only_when_enabled() -> None:
    raw = json.dumps({"route": "whole_program", "reason": "The required mathematical insight is indivisible."})
    parsed, info = parse_decomposition(raw, "json", allow_no_decomposition=True)
    assert parsed is None
    assert info["route"] == "whole_program"
    assert info["reason"]

    parsed, info = parse_decomposition(raw, "json")
    assert parsed is None
    assert info["schema_error"] == "whole_program_route_not_allowed"


def test_signature_without_name_is_normalized() -> None:
    parsed = decomposition_from_dict({
        "protocol": "json",
        "functions": [
            {"name": "helper", "signature": "(x: int) -> int", "docstring": "Help.", "depends_on": []},
        ],
    })
    assert parsed.functions[0].signature == "helper(x: int) -> int"


def test_complete_def_signature_is_normalized() -> None:
    parsed = decomposition_from_dict({
        "protocol": "json",
        "functions": [
            {"name": "helper", "signature": "def helper(x: int) -> int:", "docstring": "Help.", "depends_on": []},
        ],
    })
    assert parsed.functions[0].signature == "helper(x: int) -> int"
    errors = validate_decomposition(parsed, {"starter_code": "def helper(x): pass"})["errors"]
    assert "invalid_signature:helper" not in errors


def test_forward_dependency_is_rejected() -> None:
    parsed = Decomposition([
        FunctionSpec("helper", "helper(x)", "Help.", ["solve"]),
        FunctionSpec("solve", "solve(x)", "Solve.", []),
    ], "json", "")
    result = validate_decomposition(parsed, problem("def solve(x):\n    pass"))
    assert result["valid"] is False
    assert "forward_dependency:helper:solve" in result["errors"]


def test_forward_dependency_can_be_allowed_when_dag_is_valid() -> None:
    parsed = Decomposition([
        FunctionSpec("helper", "helper(x)", "Help.", ["worker"]),
        FunctionSpec("worker", "worker(x)", "Work.", []),
        FunctionSpec("solve", "solve(text)", "Solve.", ["helper"]),
    ], "json", "")
    result = validate_decomposition(parsed, problem(), allow_forward_dependencies=True)
    assert result["valid"] is True
    assert result["dag_valid"] is True


def test_entrypoint_argument_names_are_preserved() -> None:
    parsed = Decomposition([
        FunctionSpec("helper", "helper(value)", "Help.", []),
        FunctionSpec("solve", "solve(x)", "Solve.", ["helper"]),
    ], "json", "")
    result = validate_decomposition(parsed, problem("def solve(text):\n    pass"))
    assert result["valid"] is False
    assert "signature_mismatch:solve" in result["errors"]


def test_stdin_decomposition_requires_zero_argument_solve() -> None:
    stdin_problem = {"problem_id": "stdin", "execution_mode": "stdin", "question": "Read input."}
    parsed = Decomposition([
        FunctionSpec("add", "add(a, b)", "Add values.", []),
        FunctionSpec("solve", "solve()", "Read and print the answer.", ["add"]),
    ], "json", "")
    result = validate_decomposition(parsed, stdin_problem)
    assert result["valid"] is True
    assert result["entrypoint"] == "solve"

    parsed.functions[-1] = FunctionSpec("solve", "solve(text)", "Read and print the answer.", ["add"])
    result = validate_decomposition(parsed, stdin_problem)
    assert "signature_mismatch:solve" in result["errors"]


def test_stdin_prompt_requires_composed_solve_entrypoint() -> None:
    prompt = build_decomposition_prompt({"execution_mode": "stdin", "question": "Q", "public_tests": [{"input": "hidden"}]})
    assert "standard-input/output task" in prompt
    assert "solve() with no parameters" in prompt
    assert "hidden" not in prompt


def test_repair_prompt_variant_adds_explicit_output_checklist() -> None:
    prompt = build_decomposition_prompt({"execution_mode": "stdin", "question": "Q"}, prompt_variant="repair_v1")
    assert "REPAIR_V1 OUTPUT CHECKLIST" in prompt
    assert "hidden" not in prompt
