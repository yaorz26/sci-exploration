"""Small E0 regression suite for correct, wrong, runtime, and timeout programs."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.executor import compare_text_or_numeric_output, execute_test


def test_numeric_token_tolerance() -> None:
    assert compare_text_or_numeric_output("1.0\n", "1.000000000000000\n")
    assert compare_text_or_numeric_output("0.3333334", "0.333333333333333")
    assert not compare_text_or_numeric_output("0.333", "0.333333333333333")
    assert not compare_text_or_numeric_output("YES", "1")


def main() -> None:
    test = {"input": "2 3\n", "output": "5"}
    cases = [
        ("print(sum(map(int, input().split())))", "passed"),
        ("print(0)", "wrong_answer"),
        ("raise ValueError('boom')", "runtime_error"),
        ("while True: pass", "timeout"),
        (
            "import subprocess, sys\n"
            "subprocess.Popen([sys.executable, '-c', 'while True: pass'])\n"
            "while True: pass",
            "timeout",
        ),
    ]
    for code, expected in cases:
        result = execute_test(code, test, timeout_seconds=0.25)
        actual = result["error_type"] or "passed"
        if actual != expected:
            raise AssertionError(f"expected {expected}, got {actual}: {result}")
        print(f"{expected}: ok")

    function_code = "def add(a, b):\n    return a + b\n"
    function_test = {"input": "[2, 3]", "output": "[5]"}
    result = execute_test(
        function_code,
        function_test,
        timeout_seconds=0.25,
        execution_mode="function",
        function_name="add",
        function_arity=2,
    )
    if result["passed"] != 1:
        raise AssertionError(f"function call failed: {result}")
    print("function_call: ok")


if __name__ == "__main__":
    main()
