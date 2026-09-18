"""Build CodePRM-style records and continuous/binary thought labels."""

from __future__ import annotations

from typing import Any


def make_feedback_record(problem: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    execution = candidate["execution"]
    return {
        "problem_id": problem["problem_id"],
        "problem": problem["question"],
        "thoughts": candidate.get("thoughts", []),
        "code": candidate.get("code", ""),
        "public_feedback": execution["public"],
        "private_feedback": execution["private"],
        "label": execution["private"]["pass_rate"],
        "binary_label": int(execution["private"]["pass_rate"] == 1.0),
        "generator_model": candidate.get("generator_model", "unknown"),
        "random_seed": candidate.get("seed"),
    }


def collect_feedback_records(problem: dict[str, Any], evaluated: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [make_feedback_record(problem, candidate) for candidate in evaluated]
