import torch
import pytest

from scripts.funprm_generative_common import function_prefixes, positive_probability, soft_binary_loss
from scripts.evaluate_frozen_funprm_selection import selected_choices


def test_function_prefixes_include_cumulative_final_prefix() -> None:
    code = "import math\n\ndef helper(x):\n    return math.floor(x)\n\ndef solve(x):\n    return helper(x)\n"
    prefixes = function_prefixes(code)
    assert len(prefixes) == 2
    assert "def solve" not in prefixes[0]
    assert "def helper" in prefixes[1]
    assert "def solve" in prefixes[1]


def test_reward_probability_and_soft_loss() -> None:
    logits = torch.tensor([[2.0, 0.0], [0.0, 2.0]])
    probabilities = positive_probability(logits)
    assert probabilities[0] > 0.8
    assert probabilities[1] < 0.2
    good = soft_binary_loss(logits, torch.tensor([1.0, 0.0]))
    bad = soft_binary_loss(logits, torch.tensor([0.0, 1.0]))
    assert good < bad


def test_selected_choices_accepts_only_hashed_deferred_selection() -> None:
    code = "def solve():\n    return 1\n"
    import hashlib

    code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
    payload = {
        "private_fields_used_for_selection": [],
        "private_evaluation_deferred": True,
        "private_evaluations": 0,
        "private_rows": {"neural": {}},
        "selection_rows": [{
            "problem_id": "p1",
            "selected_candidate_indices": {"neural": 0},
            "candidates": [{"candidate_index": 0, "code": code, "code_hash": code_hash}],
        }],
    }
    choices = selected_choices(payload)
    assert choices[0][0] == "p1"
    assert choices[0][1]["code_hash"] == code_hash


def test_selected_choices_rejects_private_or_mutated_input() -> None:
    payload = {
        "private_fields_used_for_selection": ["private_tests"],
        "private_evaluation_deferred": True,
        "private_evaluations": 0,
        "private_rows": {"neural": {}},
        "selection_rows": [],
    }
    with pytest.raises(ValueError, match="private fields"):
        selected_choices(payload)

    payload["private_fields_used_for_selection"] = []
    payload["private_evaluation_deferred"] = False
    with pytest.raises(ValueError, match="not marked"):
        selected_choices(payload)
