import pytest

from scripts.analyze_funprm_confirmation_gate import summarize


def selection(values):
    return {
        "private_fields_used_for_selection": [],
        "selection_rows": [{"problem_id": problem_id} for problem_id in values],
        "private_rows": {"neural": {
            problem_id: {"all_pass": passed} for problem_id, passed in values.items()
        }},
    }


def oracle(values):
    return {
        "selection_private_fields_used": [],
        "rows": [
            {
                "problem_id": problem_id,
                "candidate_private_rows": [
                    {"candidate_index": index, "private_all_pass": passed}
                    for index, passed in enumerate(slots)
                ],
            }
            for problem_id, slots in values.items()
        ],
    }


def test_confirmation_gate_passes_all_preregistered_conditions() -> None:
    result = summarize(
        selection({"a1": True, "a2": True}),
        selection({"b1": True, "b2": True}),
        oracle({"a1": [False, True], "a2": [False, True]}),
        oracle({"b1": [False, True], "b2": [False, True]}),
        candidate_slots=2,
        min_combined_gain=4,
        bootstrap_repetitions=200,
        bootstrap_seed=7,
    )
    assert result["metrics"]["combined"]["neural_minus_first_count"] == 4
    assert result["combined_neural_minus_uniform_random_bootstrap_95ci"][0] > 0
    assert result["gate"]["overall_pass"] is True


def test_confirmation_gate_rejects_negative_split() -> None:
    result = summarize(
        selection({"a": False}),
        selection({"b": True}),
        oracle({"a": [True, False]}),
        oracle({"b": [False, True]}),
        candidate_slots=2,
        min_combined_gain=0,
        bootstrap_repetitions=100,
        bootstrap_seed=3,
    )
    assert result["gate"]["a_neural_minus_first_nonnegative"] is False
    assert result["gate"]["overall_pass"] is False


def test_confirmation_gate_rejects_private_selection_leakage() -> None:
    leaked = selection({"a": True})
    leaked["private_fields_used_for_selection"] = ["private_tests"]
    with pytest.raises(ValueError, match="private fields"):
        summarize(
            leaked,
            selection({"b": True}),
            oracle({"a": [False, True]}),
            oracle({"b": [False, True]}),
            candidate_slots=2,
            min_combined_gain=0,
            bootstrap_repetitions=10,
            bootstrap_seed=1,
        )


def test_confirmation_gate_rejects_problem_id_mismatch() -> None:
    with pytest.raises(ValueError, match="problem IDs differ"):
        summarize(
            selection({"a": True}),
            selection({"b": True}),
            oracle({"other": [False, True]}),
            oracle({"b": [False, True]}),
            candidate_slots=2,
            min_combined_gain=0,
            bootstrap_repetitions=10,
            bootstrap_seed=1,
        )
