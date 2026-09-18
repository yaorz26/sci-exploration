"""Dependency-free PRM baseline used until a trainable backbone is available.

This transparent heuristic exposes the ablation contract and exercises BoN/GVR
data flow. It must not be reported as a learned CodePRM.
"""

from __future__ import annotations

from typing import Any


class HeuristicPRM:
    def __init__(self, use_code: bool = True, use_execution_feedback: bool = True):
        self.use_code = use_code
        self.use_execution_feedback = use_execution_feedback

    def score_step(self, problem: dict[str, Any], candidate: dict[str, Any], step_index: int) -> float:
        score = 0.5
        if self.use_code and candidate.get("code"):
            score += 0.1
        if self.use_execution_feedback:
            feedback = candidate.get("execution", {}).get("public", {})
            score += 0.4 * float(feedback.get("pass_rate", 0.0))
        return max(0.0, min(1.0, score))

    def score_trajectory(self, problem: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
        thoughts = candidate.get("thoughts") or [""]
        scores = [self.score_step(problem, candidate, i) for i in range(len(thoughts))]
        return {"step_scores": scores, "trajectory_score": sum(scores) / len(scores)}
