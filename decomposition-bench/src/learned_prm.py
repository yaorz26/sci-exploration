"""Small NumPy ridge PRM for the Level-2 ablation.

This is a surrogate scorer for pipeline validation, not the paper's Qwen
backbone. It is intentionally deterministic and exposes exactly which fields
are included in each ablation.
"""

from __future__ import annotations

import hashlib
from typing import Any

import numpy as np


class RidgePRM:
    def __init__(self, use_code: bool = False, use_execution_feedback: bool = False, dimension: int = 128, l2: float = 1.0):
        self.use_code = use_code
        self.use_execution_feedback = use_execution_feedback
        self.dimension = dimension
        self.l2 = l2
        self.weights: np.ndarray | None = None

    def _features(self, problem: dict[str, Any], candidate: dict[str, Any]) -> np.ndarray:
        values = np.zeros(self.dimension + 1, dtype=np.float64)
        values[0] = 1.0
        text = f"{problem.get('question', '')} {' '.join(candidate.get('thoughts', []))}"
        if self.use_code:
            text += " " + candidate.get("code", "")
        for token in text.lower().split():
            digest = int(hashlib.sha256(token.encode()).hexdigest()[:8], 16)
            values[1 + digest % self.dimension] += 1.0
        if self.use_execution_feedback:
            feedback = candidate.get("execution", {}).get("public", {})
            values[-1] = float(feedback.get("pass_rate", 0.0))
        return values

    def fit(self, samples: list[tuple[dict[str, Any], dict[str, Any], float]]) -> dict[str, float]:
        if not samples:
            raise ValueError("cannot fit PRM without samples")
        matrix = np.vstack([self._features(problem, candidate) for problem, candidate, _ in samples])
        labels = np.asarray([label for _, _, label in samples], dtype=np.float64)
        regularizer = self.l2 * np.eye(matrix.shape[1])
        regularizer[0, 0] = 0.0
        self.weights = np.linalg.solve(matrix.T @ matrix + regularizer, matrix.T @ labels)
        predictions = np.clip(matrix @ self.weights, 0.0, 1.0)
        return {"train_mse": float(np.mean((predictions - labels) ** 2)), "samples": float(len(samples))}

    def predict(self, problem: dict[str, Any], candidate: dict[str, Any]) -> float:
        if self.weights is None:
            raise RuntimeError("fit() must be called before predict()")
        return float(np.clip(self._features(problem, candidate) @ self.weights, 0.0, 1.0))

    def score_trajectory(self, problem: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
        score = self.predict(problem, candidate)
        return {"step_scores": [score] * len(candidate.get("thoughts", [""])), "trajectory_score": score}
