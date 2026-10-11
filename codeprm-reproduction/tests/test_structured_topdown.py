from __future__ import annotations

import json

from scripts.analyze_structured_topdown_smoke import deterministic_contract_rewrite
from src.decomposition import Decomposition, FunctionSpec
from src.structured_topdown import (
    StructuredTopDownGenerator,
    build_structured_program_prompt,
    build_topdown_contract_prompt,
    parse_topdown_contract,
    topdown_contract_schema,
    validate_program_against_contract,
    validate_topdown_contract,
)


def _problem() -> dict:
    return {
        "problem_id": "fixture",
        "question": "Add two values.",
        "starter_code": "def add(a, b): pass",
        "execution_mode": "function",
    }


def _contract() -> Decomposition:
    return Decomposition([
        FunctionSpec("add", "add(a, b)", "Add normalized inputs.", ["normalize"]),
        FunctionSpec("normalize", "normalize(value)", "Normalize one input.", []),
    ], "json", "")


def _code() -> str:
    return (
        'def add(a, b):\n    """Add normalized inputs."""\n'
        '    return normalize(a) + normalize(b)\n\n'
        'def normalize(value):\n    """Normalize one input."""\n    return value\n'
    )


def test_contract_prompt_and_schema_do_not_expose_tests() -> None:
    problem = {
        **_problem(),
        "public_tests": [{"input": "public-secret"}],
        "private_tests": [{"input": "private-secret"}],
    }
    prompt = build_topdown_contract_prompt(problem)
    assert "public-secret" not in prompt
    assert "private-secret" not in prompt
    assert "first item" in prompt
    assert "listed later" in prompt
    schema = topdown_contract_schema()
    assert schema["properties"]["functions"]["minItems"] == 2
    assert schema["properties"]["functions"]["maxItems"] == 5


def test_topdown_contract_accepts_entrypoint_first_forward_dependencies() -> None:
    result = validate_topdown_contract(_contract(), _problem())
    assert result["valid"] is True
    assert result["entrypoint_first"] is True
    assert result["all_helpers_reachable"] is True


def test_contract_parser_rejects_fields_outside_frozen_schema() -> None:
    raw = json.dumps({
        "functions": [
            {
                "name": "add",
                "signature": "add(a, b)",
                "docstring": "Add normalized inputs.",
                "depends_on": ["normalize"],
                "extra": "not allowed",
            },
            {
                "name": "normalize",
                "signature": "normalize(value)",
                "docstring": "Normalize one input.",
                "depends_on": [],
            },
        ]
    })
    _, _, validation = parse_topdown_contract(raw, _problem())
    assert validation["valid"] is False
    assert "unexpected_function_keys:0:extra" in validation["errors"]


def test_topdown_contract_rejects_wrong_order_and_unused_helpers() -> None:
    wrong_order = Decomposition([
        FunctionSpec("normalize", "normalize(value)", "Normalize.", []),
        FunctionSpec("add", "add(a, b)", "Add.", ["normalize"]),
    ], "json", "")
    errors = validate_topdown_contract(wrong_order, _problem())["errors"]
    assert "entrypoint_not_first:add" in errors
    assert "dependency_not_lower_level:add:normalize" in errors

    unused = Decomposition([
        FunctionSpec("add", "add(a, b)", "Add.", ["normalize"]),
        FunctionSpec("normalize", "normalize(value)", "Normalize.", []),
        FunctionSpec("unused", "unused(value)", "Unused.", []),
    ], "json", "")
    errors = validate_topdown_contract(unused, _problem())["errors"]
    assert "unreachable_helpers:unused" in errors


def test_program_prompt_freezes_contract_without_tests() -> None:
    problem = {
        **_problem(),
        "public_tests": [{"input": "public-secret"}],
        "private_tests": [{"input": "private-secret"}],
    }
    prompt = build_structured_program_prompt(problem, _contract())
    assert "public-secret" not in prompt
    assert "private-secret" not in prompt
    assert '"name": "add"' in prompt
    assert "immutable top-down function contract" in prompt


def test_program_contract_checks_signatures_docstrings_and_calls() -> None:
    result = validate_program_against_contract(_code(), _contract())
    assert result["valid"] is True

    missing_call = _code().replace("return normalize(a) + normalize(b)", "return a + b")
    errors = validate_program_against_contract(missing_call, _contract())["errors"]
    assert "missing_declared_call:add:normalize" in errors

    wrong_doc = _code().replace("Normalize one input.", "Return the input.")
    errors = validate_program_against_contract(wrong_doc, _contract())["errors"]
    assert "contract_docstring_mismatch:normalize" in errors

    wrong_signature = _code().replace("def normalize(value):", "def normalize(x):")
    errors = validate_program_against_contract(wrong_signature, _contract())["errors"]
    assert "contract_signature_mismatch:normalize" in errors


def test_structured_generator_uses_two_requests_and_accepts_matching_program() -> None:
    contract_raw = json.dumps({
        "functions": [
            {
                "name": "add",
                "signature": "add(a, b)",
                "docstring": "Add normalized inputs.",
                "depends_on": ["normalize"],
            },
            {
                "name": "normalize",
                "signature": "normalize(value)",
                "docstring": "Normalize one input.",
                "depends_on": [],
            },
        ]
    })
    responses = iter([
        (contract_raw, {"prompt_eval_count": 10, "eval_count": 20}),
        (f"<code>{_code()}</code>", {"prompt_eval_count": 30, "eval_count": 40}),
    ])
    payloads = []
    generator = StructuredTopDownGenerator(seed=52)

    def fake_request(payload: dict) -> tuple[str, dict]:
        payloads.append(payload)
        return next(responses)

    generator._client._request = fake_request  # type: ignore[method-assign]
    result = generator.generate(_problem(), candidate_index=1)
    assert result["request_count"] == 2
    assert result["contract_seed"] == 53
    assert result["program_seed"] == 10053
    assert result["contract_validation"]["valid"] is True
    assert result["program_conformance"]["valid"] is True
    assert result["code"] == _code()
    assert isinstance(payloads[0]["format"], dict)
    assert "format" not in payloads[1]


def test_invalid_contract_skips_program_request() -> None:
    invalid_raw = json.dumps({
        "functions": [{
            "name": "add",
            "signature": "add(a, b)",
            "docstring": "Add values.",
            "depends_on": [],
        }]
    })
    calls = []
    generator = StructuredTopDownGenerator(seed=52)

    def fake_request(payload: dict) -> tuple[str, dict]:
        calls.append(payload)
        return invalid_raw, {}

    generator._client._request = fake_request  # type: ignore[method-assign]
    result = generator.generate(_problem(), candidate_index=0)
    assert len(calls) == 1
    assert result["request_count"] == 1
    assert result["program_request_made"] is False
    assert result["code"] is None


def test_post_hoc_contract_rewrite_only_reorders_and_installs_docstrings() -> None:
    helper_first_without_docs = (
        "def normalize(value):\n    return value\n\n"
        "def add(a, b):\n    return normalize(a) + normalize(b)\n"
    )
    code, audit = deterministic_contract_rewrite(helper_first_without_docs, _contract(), _problem())
    assert code is not None
    assert code.index("def add") < code.index("def normalize")
    assert '"""Add normalized inputs."""' in code
    assert '"""Normalize one input."""' in code
    assert audit["function_order_changed"] is True
    assert audit["inserted_docstrings"] == 2


def test_post_hoc_contract_rewrite_rejects_changed_function_set() -> None:
    code, audit = deterministic_contract_rewrite(
        "def add(a, b):\n    return a + b\n",
        _contract(),
        _problem(),
    )
    assert code is None
    assert audit["errors"][0].startswith("function_set_mismatch:")
