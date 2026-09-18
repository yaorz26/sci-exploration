"""Best-of-N selection shared by learned and heuristic PRMs."""

from __future__ import annotations

from typing import Any

from .prm import HeuristicPRM


def select_best(problem: dict[str, Any], candidates: list[dict[str, Any]], prm: HeuristicPRM | None = None) -> tuple[int, list[dict[str, Any]]]:
    scorer = prm or HeuristicPRM()
    scored = [{**candidate, "prm": scorer.score_trajectory(problem, candidate)} for candidate in candidates]
    selected = max(range(len(scored)), key=lambda i: (scored[i]["prm"]["trajectory_score"], -i))
    return selected, scored
