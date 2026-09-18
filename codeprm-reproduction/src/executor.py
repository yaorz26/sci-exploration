"""Timeout-bounded subprocess executor for Python candidate programs."""

from __future__ import annotations

import os
import ast
import math
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


def normalize_output(value: str) -> str:
    return " ".join(value.replace("\r\n", "\n").split())


def compare_text_or_numeric_output(
    actual: str,
    expected: str,
    *,
    absolute_tolerance: float = 1e-6,
    relative_tolerance: float = 1e-6,
) -> bool:
    """Compare APPS-style token output with conservative numeric tolerance."""
    actual_tokens = normalize_output(actual).split()
    expected_tokens = normalize_output(expected).split()
    if actual_tokens == expected_tokens:
        return True
    if len(actual_tokens) != len(expected_tokens):
        return False
    for actual_token, expected_token in zip(actual_tokens, expected_tokens):
        if actual_token == expected_token:
            continue
        try:
            actual_value = float(actual_token)
            expected_value = float(expected_token)
        except ValueError:
            return False
        if not (math.isfinite(actual_value) and math.isfinite(expected_value)):
            return False
        if not math.isclose(
            actual_value,
            expected_value,
            rel_tol=relative_tolerance,
            abs_tol=absolute_tolerance,
        ):
            return False
    return True


def _as_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value


def classify_failure(
    returncode: int | None,
    stderr: str,
    timed_out: bool,
    expected: str,
    actual: str,
    execution_mode: str = "stdin",
) -> str:
    if timed_out:
        return "timeout"
    if returncode is None or returncode != 0:
        text = stderr.lower()
        return "syntax_error" if "syntaxerror" in text or "indentationerror" in text else "runtime_error"
    if execution_mode == "function":
        try:
            actual_value = ast.literal_eval(actual.strip())
            expected_value = ast.literal_eval(expected.strip())
            matches = actual_value == expected_value
            # APPS call-based records commonly wrap the return value in a
            # singleton list, while the reference evaluator accepts either.
            if isinstance(expected_value, list) and expected_value:
                matches = matches or actual_value == expected_value[0]
            return "passed" if matches else "wrong_answer"
        except (SyntaxError, ValueError):
            return "wrong_answer"
    return "passed" if compare_text_or_numeric_output(actual, expected) else "wrong_answer"


def _function_runner(function_name: str, function_arity: int | None) -> str:
    name = repr(function_name)
    arity = int(function_arity or 1)
    call = f"result = fn(*args)" if arity > 1 else "result = fn(args[0] if isinstance(args, list) and len(args) == 1 else args)"
    return (
        "import ast\n"
        "import importlib.util\n"
        "import pathlib\n"
        "import sys\n"
        "candidate_path = pathlib.Path(__file__).with_name('candidate.py')\n"
        "spec = importlib.util.spec_from_file_location('candidate', candidate_path)\n"
        "module = importlib.util.module_from_spec(spec)\n"
        "assert spec.loader is not None\n"
        "spec.loader.exec_module(module)\n"
        f"fn = getattr(module, {name})\n"
        "args = ast.literal_eval(sys.stdin.read())\n"
        f"{call}\n"
        "print(repr(result))\n"
    )


def _terminate_process_tree(process: subprocess.Popen[str]) -> None:
    """Terminate a timed-out candidate and every descendant it created."""
    if process.poll() is not None:
        return
    if os.name == "nt":
        # `subprocess.run(..., timeout=...)` only kills the wrapper process on
        # Windows. A candidate can leave a child Python process holding its
        # pipes open, which makes communicate wait indefinitely. taskkill /T
        # applies the timeout to the whole candidate process tree.
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            capture_output=True,
            check=False,
            timeout=5,
        )
    else:
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass


def _run_limited(
    command: list[str],
    stdin: str,
    cwd: str,
    timeout_seconds: float,
) -> tuple[int | None, str, str, bool]:
    """Run one candidate with a timeout that survives child-process escapes."""
    popen_options: dict[str, Any] = {
        "stdin": subprocess.PIPE,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "cwd": cwd,
        "env": {"PATH": os.environ.get("PATH", ""), "PYTHONIOENCODING": "utf-8"},
    }
    if os.name == "nt":
        popen_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_options["start_new_session"] = True
    process = subprocess.Popen(command, **popen_options)
    try:
        stdout, stderr = process.communicate(input=stdin, timeout=timeout_seconds)
        return process.returncode, stdout, stderr, False
    except subprocess.TimeoutExpired as exc:
        _terminate_process_tree(process)
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
        return None, _as_text(exc.stdout) or stdout, _as_text(exc.stderr) or stderr, True


def execute_test(
    code: str,
    test: dict[str, str],
    timeout_seconds: float = 10.0,
    execution_mode: str = "stdin",
    function_name: str | None = None,
    function_arity: int | None = None,
) -> dict[str, Any]:
    started = time.perf_counter()
    temp_dir = tempfile.mkdtemp(prefix="codeprm-")
    script_path = Path(temp_dir) / "candidate.py"
    script_path.write_text(code, encoding="utf-8")
    command = [sys.executable, "-I", str(script_path)]
    if execution_mode == "function":
        runner_path = Path(temp_dir) / "runner.py"
        runner_path.write_text(_function_runner(function_name or "solution", function_arity), encoding="utf-8")
        command = [sys.executable, "-I", str(runner_path)]
    try:
        returncode, stdout, stderr, timed_out = _run_limited(
            command,
            test.get("input", ""),
            temp_dir,
            timeout_seconds,
        )
        failure = classify_failure(returncode, stderr, timed_out, test.get("output", ""), stdout, execution_mode)
        return {
            "passed": int(failure == "passed"), "expected": test.get("output", ""),
            "actual": stdout, "stderr": stderr,
            "error_type": None if failure == "passed" else failure,
            "message": stderr.strip() if failure not in {"passed", "wrong_answer"} else ("output mismatch" if failure == "wrong_answer" else ""),
            "timeout": timed_out, "duration_seconds": round(time.perf_counter() - started, 6),
        }
    finally:
        try:
            script_path.unlink(missing_ok=True)
            if execution_mode == "function":
                runner_path.unlink(missing_ok=True)
            Path(temp_dir).rmdir()
        except OSError:
            pass


def execute_candidate(
    code: str,
    public_tests: list[dict[str, str]],
    private_tests: list[dict[str, str]],
    timeout_seconds: float = 10.0,
    problem: dict[str, Any] | None = None,
) -> dict[str, Any]:
    problem = problem or {}
    execution_mode = str(problem.get("execution_mode", "stdin"))
    function_name = problem.get("function_name")
    function_arity = problem.get("function_arity")
    public = [execute_test(code, test, timeout_seconds, execution_mode, function_name, function_arity) for test in public_tests]
    private = [execute_test(code, test, timeout_seconds, execution_mode, function_name, function_arity) for test in private_tests]

    def aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
        total = len(results)
        passed = sum(result["passed"] for result in results)
        failures = [result for result in results if not result["passed"]]
        return {
            "passed": passed, "total": total, "pass_rate": passed / total if total else 0.0,
            "error_type": failures[0]["error_type"] if failures else None,
            "message": failures[0]["message"] if failures else "",
            "timeout": any(result["timeout"] for result in failures), "tests": results,
        }

    return {"public": aggregate(public), "private": aggregate(private)}
