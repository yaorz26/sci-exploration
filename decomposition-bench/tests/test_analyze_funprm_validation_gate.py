import pytest

from scripts.analyze_funprm_validation_gate import summarize


def selection(values, private_fields=None):
    return {
        "private_fields_used_for_selection": [] if private_fields is None else private_fields,
        "selection_rows": [{"problem_id": problem_id} for problem_id in values],
        "private_rows": {"neural": {
            problem_id: {"all_pass": passed} for problem_id, passed in values.items()
        }},
    }


def oracle(values):
    return {
        "selection_private_fields_used": [],
        "rows": [
            {"problem_id": problem_id, "candidate_private_rows": [
                {"candidate_index": index, "private_all_pass": passed}
                for index, passed in enumerate(slots)
            ]}
            for problem_id, slots in values.items()
        ],
    }


def test_validation_gate_passes_when_all_frozen_conditions_hold() -> None:
    result = summarize(
        selection({"a": True, "b": False}),
        selection({"a": False, "b": False}),
        oracle({"a": [False, True], "b": [False, True]}),
        candidate_slots=2,
        min_pool_headroom=2,
    )
    assert result["metrics"]["new_neural_all_pass_count"] == 1
    assert result["metrics"]["uniform_random_single_expected_all_pass_count"] == 1.0
    assert result["gate"]["overall_pass"] is True


def test_validation_gate_rejects_private_selection_leakage() -> None:
    with pytest.raises(ValueError, match="private fields"):
        summarize(
            selection({"a": True}, private_fields=["private_tests"]),
            selection({"a": False}),
            oracle({"a": [False, True]}),
            candidate_slots=2,
            min_pool_headroom=1,
        )
