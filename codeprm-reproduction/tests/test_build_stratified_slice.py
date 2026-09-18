from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_stratified_slice.py"
SPEC = importlib.util.spec_from_file_location("build_stratified_slice", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_execution_mode_recognizes_function_and_stdin_rows() -> None:
    assert MODULE.execution_mode({"starter_code": "def solve(x):\n    pass"}) == "function"
    assert MODULE.execution_mode({"starter_code": ""}) == "stdin"
