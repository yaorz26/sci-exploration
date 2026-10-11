from __future__ import annotations

import json

from src.topdown_json_bodies import assemble_json_bodies, build_json_bodies_prompt, json_bodies_schema


def _problem() -> dict:
    return {"problem_id": "fixture", "question": "Add two numbers.", "starter_code": "def add(a, b): pass"}


def _response() -> str:
    return json.dumps({"functions": [
        {"name": "add", "signature": "add(a, b)", "docstring": "Add two values.", "depends_on": ["total"], "body": "return total(a, b)"},
        {"name": "total", "signature": "total(a, b)", "docstring": "Compute the sum of two values.", "depends_on": [], "body": "return a + b"},
    ]})


def test_json_bodies_prompt_and_schema_keep_tests_private() -> None:
    prompt = build_json_bodies_prompt({
        **_problem(), "public_tests": [{"input": "public-secret"}], "private_tests": [{"input": "private-secret"}]
    })
    assert "public-secret" not in prompt
    assert "private-secret" not in prompt
    assert "high-level entrypoint" in prompt
    assert json_bodies_schema()["properties"]["functions"]["maxItems"] == 5


def test_json_bodies_are_assembled_as_topdown_program() -> None:
    code, audit = assemble_json_bodies(_response(), _problem())
    assert code is not None
    assert audit["valid"] is True
    assert code.index("def add") < code.index("def total")
    assert '"Add two values."' in code
    assert "return total(a, b)" in code


def test_json_bodies_reject_undeclared_helpers_and_bad_schema() -> None:
    payload = json.loads(_response())
    payload["functions"][0]["body"] = "return multiply(a, b)"
    _, audit = assemble_json_bodies(json.dumps(payload), _problem())
    assert audit["valid"] is False
    assert any(error.startswith("missing_declared_call:add") for error in audit["errors"])

    payload["unexpected"] = True
    _, audit = assemble_json_bodies(json.dumps(payload), _problem())
    assert audit["valid"] is False
    assert audit["errors"] == ["invalid_top_level_schema"]
