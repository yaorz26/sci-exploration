from __future__ import annotations

from src.decomposition import Decomposition, FunctionSpec
from src.executor import execute_test
from src.recombination import compose_program


def decomposition() -> Decomposition:
    return Decomposition([
        FunctionSpec("parse_input", "parse_input(text: str) -> list", "Parse.", []),
        FunctionSpec("solve", "solve(text: str) -> str", "Solve.", ["parse_input"]),
    ], "json", "")


def test_compose_full_defs_preserves_signature_and_order() -> None:
    code, meta = compose_program(decomposition(), {
        "parse_input": "def parse_input(text):\n    return text.split()",
        "solve": "def solve(text):\n    return ' '.join(parse_input(text))",
    }, {"starter_code": "def solve(text):\n    pass"})
    assert meta["valid"] is True
    assert code is not None
    assert code.index("def parse_input") < code.index("def solve")
    assert "def solve(text: str) -> str" in code
    assert code.startswith("from __future__ import annotations")


def test_compose_body_snippets_and_dedupe_imports() -> None:
    code, meta = compose_program(decomposition(), {
        "parse_input": "import re\nreturn re.findall(r'\\w+', text)",
        "solve": "import re\nreturn ' '.join(parse_input(text))",
    }, {"starter_code": "def solve(text):\n    pass"})
    assert meta["valid"] is True
    assert code is not None
    assert code.count("import re") == 1


def test_missing_implementation_is_rejected() -> None:
    code, meta = compose_program(decomposition(), {"parse_input": "return []"}, {})
    assert code is None
    assert "missing_implementation:solve" in meta["errors"]


def test_nested_undeclared_functions_are_rejected() -> None:
    code, meta = compose_program(decomposition(), {
        "parse_input": "def parse_input(text):\n    def hidden():\n        return []\n    return hidden()",
        "solve": "def solve(text):\n    return ''",
    }, {})
    assert code is None
    assert any("undeclared_nested_functions:hidden" in error for error in meta["errors"])


def test_signature_mismatch_and_extra_functions_are_rejected() -> None:
    code, meta = compose_program(decomposition(), {
        "parse_input": "def parse_input(other):\n    return other.split()",
        "solve": "def solve(text):\n    return ''",
    }, {})
    assert code is None
    assert any("signature_mismatch:parse_input" in error for error in meta["errors"])

    code, meta = compose_program(decomposition(), {
        "parse_input": "def parse_input(text):\n    return text.split()\n\ndef hidden():\n    return []",
        "solve": "def solve(text):\n    return ''",
    }, {})
    assert code is None
    assert any("extra_function_definitions" in error for error in meta["errors"])


def test_compose_stdin_program_adds_solve_main_guard() -> None:
    stdin_decomposition = Decomposition([
        FunctionSpec("add", "add(a, b)", "Add two integers.", []),
        FunctionSpec("solve", "solve()", "Read two integers and print their sum.", ["add"]),
    ], "json", "")
    code, meta = compose_program(stdin_decomposition, {
        "add": "def add(a, b):\n    return a + b",
        "solve": "def solve():\n    a, b = map(int, input().split())\n    print(add(a, b))",
    }, {"execution_mode": "stdin"})
    assert meta["valid"] is True
    assert code is not None
    assert "if __name__ == '__main__':" in code
    result = execute_test(code, {"input": "2 3\n", "output": "5"}, execution_mode="stdin")
    assert result["passed"] == 1
