import time

from src.executor import MAX_CAPTURED_OUTPUT_BYTES, execute_test


def test_execute_test_preserves_normal_stdin_program() -> None:
    result = execute_test(
        "a, b = map(int, input().split())\nprint(a + b)\n",
        {"input": "2 3\n", "output": "5\n"},
        timeout_seconds=2.0,
    )

    assert result["passed"] == 1
    assert result["error_type"] is None
    assert result["timeout"] is False
    assert result["output_limited"] is False


def test_execute_test_preserves_wall_clock_timeout() -> None:
    result = execute_test(
        "while True:\n    pass\n",
        {"input": "", "output": ""},
        timeout_seconds=0.2,
    )

    assert result["passed"] == 0
    assert result["error_type"] == "timeout"
    assert result["timeout"] is True
    assert result["output_limited"] is False
    assert result["duration_seconds"] < 2.0


def test_execute_test_timeout_starts_even_when_candidate_ignores_large_stdin() -> None:
    result = execute_test(
        "while True:\n    pass\n",
        {"input": "x" * (2 * 1024 * 1024), "output": ""},
        timeout_seconds=0.2,
    )

    assert result["passed"] == 0
    assert result["error_type"] == "timeout"
    assert result["timeout"] is True
    assert result["duration_seconds"] < 2.0


def test_execute_test_stops_unbounded_candidate_output() -> None:
    code = "while True:\n    print('x' * 8192)\n"
    started = time.perf_counter()
    result = execute_test(code, {"input": "", "output": ""}, timeout_seconds=5.0)

    assert result["passed"] == 0
    assert result["error_type"] == "output_limit"
    assert result["output_limited"] is True
    assert result["duration_seconds"] < 5.0
    assert time.perf_counter() - started < 8.0
    assert len(result["actual"].encode("utf-8")) <= MAX_CAPTURED_OUTPUT_BYTES


def test_execute_test_marks_fast_finite_output_over_limit() -> None:
    result = execute_test(
        "import sys\nsys.stdout.write('x' * (2 * 1024 * 1024))\n",
        {"input": "", "output": ""},
        timeout_seconds=5.0,
    )

    assert result["passed"] == 0
    assert result["error_type"] == "output_limit"
    assert result["output_limited"] is True
    assert len(result["actual"].encode("utf-8")) <= MAX_CAPTURED_OUTPUT_BYTES
