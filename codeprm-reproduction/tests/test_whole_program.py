from __future__ import annotations

from src.whole_program import build_whole_program_prompt, parse_whole_program


def test_prompts_do_not_expose_tests() -> None:
    problem = {
        "question": "Add two values.",
        "starter_code": "def add(a, b): pass",
        "public_tests": [{"input": "public-secret"}],
        "private_tests": [{"input": "private-secret"}],
    }
    for method in ("direct", "plan", "functionized", "top_down_cof", "top_down_cof_fewshot"):
        prompt = build_whole_program_prompt(problem, method)
        assert "public-secret" not in prompt
        assert "private-secret" not in prompt


def test_functionized_prompt_requires_one_coherent_program() -> None:
    problem = {"question": "Add two values.", "starter_code": "def add(a, b): pass"}
    prompt = build_whole_program_prompt(problem, "functionized")
    assert "2-5 top-level functions" in prompt
    assert "one program" in prompt
    assert "do not combine functions from separate responses" in prompt


def test_functionized_parser_enforces_structure() -> None:
    problem = {"starter_code": "def add(a, b): pass"}
    valid = "def normalize(x):\n    return x\n\ndef add(a, b):\n    return normalize(a) + normalize(b)"
    code, _, meta = parse_whole_program(valid, problem, "functionized")
    assert code is not None
    assert meta["api_preserved"] is True

    code, _, meta = parse_whole_program("def add(a, b):\n    return a + b", problem, "functionized")
    assert code is None
    assert "function_count_out_of_range:1" in meta["errors"]

    wrong_order = "def add(a, b):\n    return helper(a) + helper(b)\n\ndef helper(x):\n    return x"
    code, _, meta = parse_whole_program(wrong_order, problem, "functionized")
    assert code is None
    assert "entrypoint_not_last:add" in meta["errors"]


def test_top_down_prompt_requires_entrypoint_first_and_docstrings() -> None:
    problem = {"question": "Add two values.", "starter_code": "def add(a, b): pass"}
    prompt = build_whole_program_prompt(problem, "top_down_cof")
    assert "FIRST top-level function" in prompt
    assert "helper functions" in prompt
    assert "triple-quoted docstring" in prompt
    assert "Do not move the entrypoint to the end" in prompt
    assert "A one-function response is invalid" in prompt
    assert "Every function definition must start at column zero" in prompt
    assert "verify that there are 2-5 column-zero function definitions" in prompt


def test_top_down_parser_enforces_order_and_docstrings() -> None:
    problem = {"starter_code": "def add(a, b): pass"}
    valid = (
        'def add(a, b):\n    """Add normalized inputs."""\n    return normalize(a) + normalize(b)\n\n'
        'def normalize(x):\n    """Return a normalized input."""\n    return x'
    )
    code, _, meta = parse_whole_program(valid, problem, "top_down_cof")
    assert code is not None
    assert meta["errors"] == []

    helper_first = (
        'def normalize(x):\n    """Return a normalized input."""\n    return x\n\n'
        'def add(a, b):\n    """Add normalized inputs."""\n    return normalize(a) + normalize(b)'
    )
    code, _, meta = parse_whole_program(helper_first, problem, "top_down_cof")
    assert code is None
    assert "entrypoint_not_first:add" in meta["errors"]

    missing_docstring = "def add(a, b):\n    return normalize(a) + normalize(b)\n\ndef normalize(x):\n    return x"
    code, _, meta = parse_whole_program(missing_docstring, problem, "top_down_cof")
    assert code is None
    assert "missing_function_docstrings:add,normalize" in meta["errors"]


def test_fewshot_top_down_includes_only_structural_example() -> None:
    prompt = build_whole_program_prompt(
        {"question": "Return the maximum value.", "starter_code": "def maximum(values): pass"},
        "top_down_cof_fewshot",
    )
    assert "Structural few-shot example" in prompt
    assert "def sum_text(text)" in prompt
    assert prompt.index("def sum_text(text)") < prompt.index("def parse_values(text)")
    assert prompt.endswith("Problem:\nReturn the maximum value.\n")


def test_top_down_standard_input_calls_solve_only_after_helpers() -> None:
    valid = (
        'def solve():\n    """Read and print the formatted value."""\n    print(format_value(input()))\n\n'
        'def format_value(value):\n    """Normalize one input value."""\n    return value.strip()\n\n'
        "if __name__ == '__main__':\n    solve()"
    )
    code, _, meta = parse_whole_program(valid, {"starter_code": ""}, "top_down_cof")
    assert code is not None
    assert meta["errors"] == []

    missing_call = (
        'def solve():\n    """Build the formatted value."""\n    return format_value("x")\n\n'
        'def format_value(value):\n    """Normalize one input value."""\n    return value.strip()'
    )
    code, _, meta = parse_whole_program(missing_call, {"starter_code": ""}, "top_down_cof")
    assert code is None
    assert "missing_solve_call" in meta["errors"]

    early_call = (
        'def solve():\n    """Read and print the formatted value."""\n    print(format_value(input()))\n\n'
        'solve()\n\n'
        'def format_value(value):\n    """Normalize one input value."""\n    return value.strip()'
    )
    code, _, meta = parse_whole_program(early_call, {"starter_code": ""}, "top_down_cof")
    assert code is None
    assert "entrypoint_called_before_helpers:solve" in meta["errors"]


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
