from __future__ import annotations

import importlib.util
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "fetch_apps_subset.py"
SPEC = importlib.util.spec_from_file_location("fetch_apps_subset", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_malformed_input_output_is_reported_and_skipped() -> None:
    tests, malformed = MODULE.parse_input_output("not json")
    assert tests == []
    assert malformed is True

    row, malformed = MODULE.normalize_row(
        {"problem_id": 1, "input_output": "not json"}, "train", 0
    )
    assert row is None
    assert malformed is True


def test_valid_input_output_is_normalized() -> None:
    row, malformed = MODULE.normalize_row(
        {
            "problem_id": 1,
            "difficulty": "competition",
            "question": "Q",
            "starter_code": "def solve(x): pass",
            "input_output": '{"inputs": ["a", "b"], "outputs": ["x", "y"]}',
        },
        "train",
        0,
    )
    assert malformed is False
    assert row is not None
    assert row["public_tests"] == [{"input": "a", "output": "x"}]
    assert row["private_tests"] == [{"input": "b", "output": "y"}]
