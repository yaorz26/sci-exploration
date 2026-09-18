from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sanitize_prompt_visible_private_tests.py"
SPEC = importlib.util.spec_from_file_location("sanitize_prompt_visible_private_tests", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_sanitize_removes_only_private_cases_visible_in_question() -> None:
    rows, audit = MODULE.sanitize_rows([{
        "problem_id": "fixture",
        "question": "Example input: 1 2. Example output: 3.",
        "public_tests": [{"input": "4 5", "output": "9"}],
        "private_tests": [
            {"input": "1\n2", "output": "3"},
            {"input": "10 20", "output": "30"},
        ],
    }])
    assert len(rows) == 1
    assert rows[0]["private_tests"] == [{"input": "10 20", "output": "30"}]
    assert rows[0]["prompt_visible_private_tests_removed"] == 1
    assert audit[0]["retained"] is True


def test_sanitize_drops_row_when_all_private_cases_are_visible() -> None:
    rows, audit = MODULE.sanitize_rows([{
        "problem_id": "fixture",
        "question": "Input 1 output 2",
        "public_tests": [{"input": "1", "output": "2"}],
        "private_tests": [{"input": "1", "output": "2"}],
    }])
    assert rows == []
    assert audit[0]["retained"] is False
