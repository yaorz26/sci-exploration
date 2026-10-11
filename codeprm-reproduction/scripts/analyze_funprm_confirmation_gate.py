"""Apply the preregistered two-split FunPRM confirmation gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def percentile(values: list[float], probability: float) -> float:
    if not values:
        raise ValueError("percentile requires at least one value")
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(probability * (len(ordered) - 1))))
    return ordered[index]


def exact_two_sided_sign_pvalue(wins: int, losses: int) -> float:
    discordant = wins + losses
    if discordant == 0:
        return 1.0
    tail = sum(math.comb(discordant, index) for index in range(min(wins, losses) + 1)) / (2**discordant)
    return min(1.0, 2.0 * tail)


def selection_outcomes(selection: dict[str, Any]) -> dict[str, int]:
    if selection.get("private_fields_used_for_selection") not in ([], None):
        raise ValueError("selection reports private fields used during selection")
    rows = selection.get("selection_rows", [])
    if not rows:
        raise ValueError("selection has no problem rows")
    private_rows = selection.get("private_rows", {}).get("neural", {})
    values: dict[str, int] = {}
    for row in rows:
        problem_id = str(row["problem_id"])
        if problem_id in values:
            raise ValueError(f"duplicate selection problem ID: {problem_id}")
        values[problem_id] = int(bool(private_rows.get(problem_id, {}).get("all_pass", False)))
    return values


def oracle_slots(oracle: dict[str, Any], candidate_slots: int) -> dict[str, list[int]]:
    if oracle.get("selection_private_fields_used") not in ([], None):
        raise ValueError("oracle reports private fields used during selection")
    values: dict[str, list[int]] = {}
    for row in oracle.get("rows", []):
        problem_id = str(row["problem_id"])
        if problem_id in values:
            raise ValueError(f"duplicate oracle problem ID: {problem_id}")
        slots = [0] * candidate_slots
        seen: set[int] = set()
        for candidate in row.get("candidate_private_rows", []):
            index = int(candidate["candidate_index"])
            if index < 0 or index >= candidate_slots:
                raise ValueError(f"candidate index out of range for {problem_id}: {index}")
            if index in seen:
                raise ValueError(f"duplicate candidate index for {problem_id}: {index}")
            seen.add(index)
            slots[index] = int(bool(candidate.get("private_all_pass", False)))
        values[problem_id] = slots
    return values


def split_rows(
    split: str,
    selection: dict[str, Any],
    oracle: dict[str, Any],
    candidate_slots: int,
) -> list[dict[str, Any]]:
    selected = selection_outcomes(selection)
    pool = oracle_slots(oracle, candidate_slots)
    if set(selected) != set(pool):
        raise ValueError(f"{split} selection and oracle problem IDs differ")
    oracle_rows = {str(row["problem_id"]): row for row in oracle.get("rows", [])}
    rows = []
    for problem_id in sorted(selected):
        slots = pool[problem_id]
        neural = selected[problem_id]
        first = slots[0]
        random_probability = sum(slots) / candidate_slots
        rows.append({
            "split": split,
            "problem_id": problem_id,
            "neural_all_pass": bool(neural),
            "first_candidate_all_pass": bool(first),
            "uniform_random_single_success_probability": random_probability,
            "neural_minus_first": neural - first,
            "neural_minus_random_expected": neural - random_probability,
            "pool_oracle_all_pass": bool(any(slots)),
            "valid_candidate_slots": len(oracle_rows[problem_id].get("candidate_private_rows", [])),
        })
    return rows


def split_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    neural = sum(int(row["neural_all_pass"]) for row in rows)
    first = sum(int(row["first_candidate_all_pass"]) for row in rows)
    random_expected = sum(float(row["uniform_random_single_success_probability"]) for row in rows)
    wins = sum(int(row["neural_minus_first"] > 0) for row in rows)
    losses = sum(int(row["neural_minus_first"] < 0) for row in rows)
    return {
        "problems": len(rows),
        "neural_all_pass_count": neural,
        "first_candidate_all_pass_count": first,
        "neural_minus_first_count": neural - first,
        "neural_vs_first_wins": wins,
        "neural_vs_first_losses": losses,
        "neural_vs_first_exact_two_sided_sign_pvalue": exact_two_sided_sign_pvalue(wins, losses),
        "uniform_random_single_expected_all_pass_count": random_expected,
        "neural_minus_uniform_random_expected_count": neural - random_expected,
        "pool_oracle_all_pass_count": sum(int(row["pool_oracle_all_pass"]) for row in rows),
    }


def summarize(
    a_selection: dict[str, Any],
    b_selection: dict[str, Any],
    a_oracle: dict[str, Any],
    b_oracle: dict[str, Any],
    *,
    candidate_slots: int,
    min_combined_gain: int,
    bootstrap_repetitions: int,
    bootstrap_seed: int,
) -> dict[str, Any]:
    if candidate_slots <= 0 or min_combined_gain < 0 or bootstrap_repetitions <= 0:
        raise ValueError("candidate slots and bootstrap repetitions must be positive; gain must be nonnegative")
    a_rows = split_rows("A", a_selection, a_oracle, candidate_slots)
    b_rows = split_rows("B", b_selection, b_oracle, candidate_slots)
    if not a_rows or not b_rows:
        raise ValueError("both confirmation splits must be nonempty")
    rows = a_rows + b_rows
    a_metrics = split_metrics(a_rows)
    b_metrics = split_metrics(b_rows)
    combined_metrics = split_metrics(rows)

    rng = random.Random(bootstrap_seed)
    bootstrap = []
    for _ in range(bootstrap_repetitions):
        sample = [rows[rng.randrange(len(rows))] for _ in rows]
        bootstrap.append(sum(row["neural_minus_random_expected"] for row in sample) / len(sample))
    bootstrap_ci = [percentile(bootstrap, 0.025), percentile(bootstrap, 0.975)]

    gate = {
        "a_neural_minus_first_nonnegative": a_metrics["neural_minus_first_count"] >= 0,
        "b_neural_minus_first_nonnegative": b_metrics["neural_minus_first_count"] >= 0,
        "combined_neural_minus_first_at_least_minimum": (
            combined_metrics["neural_minus_first_count"] >= min_combined_gain
        ),
        "combined_bootstrap_lower_bound_vs_uniform_random_positive": bootstrap_ci[0] > 0.0,
    }
    gate["overall_pass"] = all(gate.values())
    return {
        "candidate_slots_per_problem": candidate_slots,
        "bootstrap_repetitions": bootstrap_repetitions,
        "bootstrap_seed": bootstrap_seed,
        "minimum_combined_gain_over_first": min_combined_gain,
        "metrics": {"A": a_metrics, "B": b_metrics, "combined": combined_metrics},
        "combined_neural_minus_uniform_random_bootstrap_95ci": bootstrap_ci,
        "gate": gate,
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--a-selection", required=True)
    parser.add_argument("--b-selection", required=True)
    parser.add_argument("--a-pool-oracle", required=True)
    parser.add_argument("--b-pool-oracle", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--candidate-slots", type=int, default=10)
    parser.add_argument("--min-combined-gain", type=int, default=4)
    parser.add_argument("--bootstrap-repetitions", type=int, default=10_000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260924)
    args = parser.parse_args()
    output_path = Path(args.output)
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite {output_path}")
    paths = {
        "a_selection": Path(args.a_selection),
        "b_selection": Path(args.b_selection),
        "a_pool_oracle": Path(args.a_pool_oracle),
        "b_pool_oracle": Path(args.b_pool_oracle),
    }
    result = summarize(
        load_json(paths["a_selection"]),
        load_json(paths["b_selection"]),
        load_json(paths["a_pool_oracle"]),
        load_json(paths["b_pool_oracle"]),
        candidate_slots=args.candidate_slots,
        min_combined_gain=args.min_combined_gain,
        bootstrap_repetitions=args.bootstrap_repetitions,
        bootstrap_seed=args.bootstrap_seed,
    )
    result.update({
        "experiment": "funprm_helperfirst_scale_prm_20260924",
        "phase": "confirmation_ab_final_gate",
        "inputs": {key: str(path) for key, path in paths.items()},
        "input_sha256": {key: sha256(path) for key, path in paths.items()},
        "private_fields_used_for_selection": [],
        "pool_oracle_is_post_selection_diagnostic": True,
        "interpretation": (
            "Preregistered two-split confirmation gate. Neural selection was frozen before private evaluation; "
            "invalid candidate slots count as failures for the uniform-random baseline."
        ),
    })
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "metrics": result["metrics"],
        "combined_neural_minus_uniform_random_bootstrap_95ci": result[
            "combined_neural_minus_uniform_random_bootstrap_95ci"
        ],
        "gate": result["gate"],
        "output": str(output_path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
