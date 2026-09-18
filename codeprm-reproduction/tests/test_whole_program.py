from __future__ import annotations

from src.whole_program import build_whole_program_prompt, parse_whole_program


def test_prompts_do_not_expose_tests() -> None:
    problem = {
        "question": "Add two values.",
        "starter_code": "def add(a, b): pass",
        "public_tests": [{"input": "public-secret"}],
        "private_tests": [{"input": "private-secret"}],
    }
    for method in ("direct", "plan"):
        prompt = build_whole_program_prompt(problem, method)
        assert "public-secret" not in prompt
        assert "private-secret" not in prompt


def test_direct_parser_checks_entrypoint() -> None:
    code, plan, meta = parse_whole_program("def add(a, b):\n    return a + b", {"starter_code": "def add(a, b): pass"}, "direct")
    assert code is not None
    assert plan is None
    assert meta["api_preserved"] is True


def test_plan_parser_extracts_sections() -> None:
    raw = "<plan>Add the values.</plan>\n<code>def add(a, b):\n    return a + b</code>"
    code, plan, meta = parse_whole_program(raw, {"starter_code": "def add(a, b): pass"}, "plan")
    assert code is not None
    assert plan == "Add the values."
    assert meta["syntax_valid"] is True


def test_plan_parser_accepts_fence_inside_code_section() -> None:
    raw = "<plan>Add the values.</plan>\n<code>```python\ndef add(a, b):\n    return a + b\n```</code>"
    code, plan, meta = parse_whole_program(raw, {"starter_code": "def add(a, b): pass"}, "plan")
    assert code is not None
    assert plan == "Add the values."
    assert meta["syntax_valid"] is True


def test_parser_rejects_changed_starter_parameters() -> None:
    code, _, meta = parse_whole_program("def add(x, y):\n    return x + y", {"starter_code": "def add(a, b): pass"}, "direct")
    assert code is None
    assert meta["api_preserved"] is False
    assert "signature_mismatch:add" in meta["errors"]
