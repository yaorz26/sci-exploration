import pytest

from scripts.prepare_funprm_training_data import prepare_rows


def test_prepare_rows_recomputes_label_from_all_rollouts() -> None:
    source = [{
        "problem_id": "p",
        "source_candidate_index": 2,
        "function_index": 1,
        "function_name": "helper",
        "problem": "Return one.",
        "prefix_code": "def helper():\n    return 1\n",
        "label": 0.0,
        "rollouts": [
            {"rollout_index": index, "success": index in {0, 3, 5}}
            for index in range(8)
        ],
    }]
    rows = prepare_rows(source)
    assert rows[0]["label"] == 3 / 8
    assert rows[0]["rollout_count"] == 8
    assert "rollouts" not in rows[0]


def test_prepare_rows_rejects_noncontiguous_indices() -> None:
    source = [{
        "problem_id": "p",
        "source_candidate_index": 0,
        "function_index": 0,
        "rollouts": [{"rollout_index": index, "success": False} for index in [0, 1, 2, 4]],
    }]
    with pytest.raises(ValueError, match="non-contiguous"):
        prepare_rows(source)
