from scripts.collect_funprm_function_prefix_rollouts import (
    combine_prefix_and_completion,
    continuation_prompt,
    function_prefixes,
    load_node_key_manifest,
    rollout_indices_to_add,
    select_source_trajectories,
)

import json

import pytest


def test_unit_test_reward_policy_accepts_syntax_valid_noncanonical_order() -> None:
    code = "def helper(x):\n    return x + 1\n\ndef solve(x):\n    return helper(x)\n"
    assert "def solve" in code
    assert "def helper" in code


def test_function_prefixes_keep_imports_and_exclude_final_function() -> None:
    code = "import math\n\ndef helper(x):\n    return math.floor(x)\n\ndef solve(x):\n    return helper(x)\n"
    prefixes = function_prefixes(code)
    assert len(prefixes) == 1
    assert prefixes[0]["function_name"] == "helper"
    assert prefixes[0]["prefix_code"].startswith("import math")
    assert "def solve" not in prefixes[0]["prefix_code"]


def test_combine_accepts_appended_or_exact_full_code() -> None:
    prefix = "def helper(x):\n    return x + 1\n"
    appended, mode = combine_prefix_and_completion(prefix, "<code>def solve(x):\n    return helper(x)</code>")
    assert mode == "appended_completion"
    assert appended.startswith(prefix)
    assert "def solve" in appended

    full, mode = combine_prefix_and_completion(prefix, f"<code>{prefix}\ndef solve(x):\n    return helper(x)</code>")
    assert mode == "full_code_with_exact_prefix"
    assert full.count("def helper") == 1


def test_source_selection_uses_first_valid_unique_candidate() -> None:
    rows = [
        {"problem_id": "p", "candidate_index": 0, "code": None},
        {"problem_id": "p", "candidate_index": 1, "code": "def only():\n    return 1\n"},
        {"problem_id": "p", "candidate_index": 2, "code": "def a():\n    return 1\n\ndef b():\n    return a()\n"},
    ]
    selected = select_source_trajectories(rows)
    assert len(selected) == 1
    assert selected[0]["candidate_index"] == 2


def test_top_down_prefixes_start_with_entrypoint_and_exclude_last_helper() -> None:
    code = (
        'import math\n\ndef solve(x):\n    """Orchestrate the solution."""\n    return helper(x)\n\n'
        'def helper(x):\n    """Apply the transformation."""\n    return leaf(x)\n\n'
        'def leaf(x):\n    """Round down the value."""\n    return math.floor(x)\n'
    )
    prefixes = function_prefixes(code)
    assert len(prefixes) == 2
    assert prefixes[0]["function_name"] == "solve"
    assert "def helper" not in prefixes[0]["prefix_code"]
    assert prefixes[1]["function_name"] == "helper"
    assert "def leaf" not in prefixes[1]["prefix_code"]


def test_top_down_continuation_keeps_entrypoint_in_prefix() -> None:
    problem = {"question": "Return x.", "starter_code": "def solve(x): pass"}
    prompt = continuation_prompt(problem, 'def solve(x):\n    """Return helper output."""\n    return helper(x)\n', "top_down_cof")
    assert "entrypoint is already present as the first function" in prompt
    assert "Do not repeat or move it" in prompt
    assert "put the required starter entrypoint last" not in prompt


def test_rollout_resume_adds_only_missing_indices() -> None:
    existing = [{"success": False}, {"success": True}, {"success": False}, {"success": True}]
    assert rollout_indices_to_add(existing, 8) == [4, 5, 6, 7]
    assert rollout_indices_to_add(existing, 4) == []


def test_rollout_uncertainty_filter_selects_only_requested_band() -> None:
    uncertain = [{"success": False}, {"success": True}, {"success": False}, {"success": False}]
    certain = [{"success": False}] * 4
    assert rollout_indices_to_add(uncertain, 8, 0.25, 0.75, 4) == [4, 5, 6, 7]
    assert rollout_indices_to_add(certain, 8, 0.25, 0.75, 4) == []
    assert rollout_indices_to_add(uncertain, 8, 0.25, 0.75, 8) == []


def test_node_key_manifest_loads_exact_selected_keys(tmp_path) -> None:
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({
        "sample_size": 2,
        "selected_nodes": [
            {"problem_id": "p1", "source_candidate_index": 0, "function_index": 1},
            {"problem_id": "p2", "source_candidate_index": 3, "function_index": 0},
        ],
    }), encoding="utf-8")
    assert load_node_key_manifest(path) == {("p1", 0, 1), ("p2", 3, 0)}


def test_node_key_manifest_rejects_duplicate_keys(tmp_path) -> None:
    path = tmp_path / "manifest.json"
    selected = {"problem_id": "p1", "source_candidate_index": 0, "function_index": 1}
    path.write_text(json.dumps({"sample_size": 2, "selected_nodes": [selected, selected]}), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate node keys"):
        load_node_key_manifest(path)
