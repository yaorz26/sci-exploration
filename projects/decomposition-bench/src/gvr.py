"""Minimal Generate-Verify-Refine orchestration primitives."""

from __future__ import annotations

from typing import Any, Callable

from .prm import HeuristicPRM


def locate_minimum(prm: HeuristicPRM, problem: dict[str, Any], candidate: dict[str, Any]) -> int:
    scores = prm.score_trajectory(problem, candidate)["step_scores"]
    return min(range(len(scores)), key=lambda i: (scores[i], i))


def refine_candidate(problem: dict[str, Any], candidate: dict[str, Any], refine: Callable[[dict[str, Any], int], dict[str, Any]], prm: HeuristicPRM | None = None) -> dict[str, Any]:
    scorer = prm or HeuristicPRM()
    step = locate_minimum(scorer, problem, candidate)
    refined = refine(candidate, step)
    return {**refined, "refinement": {"selected_step": step, "strategy": "locate_minimum"}}


def refine_from_pool(problem: dict[str, Any], candidates: list[dict[str, Any]], current_index: int, strategy: str = "locate_minimum", prm: HeuristicPRM | None = None, rng: Any = None, threshold: float = 0.5) -> tuple[int, dict[str, Any]]:
    """Select a replacement candidate after verification of the current one.

    The offline fixture cannot ask a language model to rewrite one thought, so
    the refiner searches the already generated pool. The returned metadata keeps
    the same before/after fields used by a model-backed GVR implementation.
    """
    scorer = prm or HeuristicPRM()
    current = candidates[current_index]
    before = current["execution"]["public"]["pass_rate"]
    if before >= 1.0 or strategy == "none":
        return current_index, {"selected_step": None, "refined": False, "before_public_pass_rate": before, "after_public_pass_rate": before}
    alternatives = [index for index in range(len(candidates)) if index != current_index]
    if not alternatives:
        return current_index, {"selected_step": None, "refined": False, "before_public_pass_rate": before, "after_public_pass_rate": before}
    if strategy == "random":
        replacement = rng.choice(alternatives) if rng else alternatives[0]
    else:
        scored = [(scorer.score_trajectory(problem, candidates[index])["trajectory_score"], index) for index in alternatives]
        if strategy == "threshold":
            scored = [pair for pair in scored if pair[0] < threshold] or scored
        replacement = max(scored, key=lambda pair: (pair[0], -pair[1]))[1]
    selected_step = locate_minimum(scorer, problem, current)
    after = candidates[replacement]["execution"]["public"]["pass_rate"]
    return replacement, {"selected_step": selected_step, "refined": replacement != current_index, "before_public_pass_rate": before, "after_public_pass_rate": after}
