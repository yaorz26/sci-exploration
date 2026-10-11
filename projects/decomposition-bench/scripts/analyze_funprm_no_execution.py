"""Audit FunPRM neural Best-of-N against no-execution single-sample baselines."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(probability * (len(ordered) - 1))))
    return ordered[index]


def exact_two_sided_sign_pvalue(wins: int, losses: int) -> float:
    discordant = wins + losses
    if discordant == 0:
        return 1.0
    tail = sum(math.comb(discordant, index) for index in range(min(wins, losses) + 1)) / (2**discordant)
    return min(1.0, 2.0 * tail)


def poisson_binomial_upper_tail(probabilities: list[float], threshold: int) -> float:
    distribution = [1.0] + [0.0] * len(probabilities)
    for probability in probabilities:
        for successes in range(len(probabilities), 0, -1):
            distribution[successes] = (
                distribution[successes] * (1.0 - probability)
                + distribution[successes - 1] * probability
            )
        distribution[0] *= 1.0 - probability
    return sum(distribution[threshold:])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection", required=True)
    parser.add_argument("--pool-oracle", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--candidate-slots", type=int, default=10)
    parser.add_argument("--bootstrap-repetitions", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    selection_path = Path(args.selection)
    oracle_path = Path(args.pool_oracle)
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    neural_private = selection["private_rows"]["neural"]
    oracle_by_problem = {str(row["problem_id"]): row for row in oracle["rows"]}

    rows: list[dict] = []
    neural_count = 0
    first_count = 0
    wins = 0
    losses = 0
    for selection_row in selection["selection_rows"]:
        problem_id = str(selection_row["problem_id"])
        candidate_rows = oracle_by_problem[problem_id]["candidate_private_rows"]
        outcomes_by_index = {
            int(row["candidate_index"]): int(bool(row["private_all_pass"]))
            for row in candidate_rows
        }
        slot_outcomes = [outcomes_by_index.get(index, 0) for index in range(args.candidate_slots)]
        random_probability = sum(slot_outcomes) / args.candidate_slots
        neural_outcome = int(bool(neural_private.get(problem_id, {}).get("all_pass", False)))
        first_outcome = slot_outcomes[0]
        neural_count += neural_outcome
        first_count += first_outcome
        wins += int(neural_outcome > first_outcome)
        losses += int(neural_outcome < first_outcome)
        rows.append({
            "problem_id": problem_id,
            "neural_all_pass": bool(neural_outcome),
            "first_candidate_all_pass": bool(first_outcome),
            "random_single_success_probability": random_probability,
            "neural_minus_random_expected": neural_outcome - random_probability,
            "valid_candidate_slots": len(outcomes_by_index),
        })

    rng = random.Random(args.seed)
    bootstrap: list[float] = []
    for _ in range(args.bootstrap_repetitions):
        sample = [rows[rng.randrange(len(rows))] for _ in rows]
        bootstrap.append(sum(row["neural_minus_random_expected"] for row in sample) / len(sample))

    random_expected_count = sum(row["random_single_success_probability"] for row in rows)
    difference_rate = (neural_count - random_expected_count) / len(rows)
    probabilities = [row["random_single_success_probability"] for row in rows]
    output = {
        "selection": str(selection_path),
        "selection_sha256": sha256(selection_path),
        "pool_oracle": str(oracle_path),
        "pool_oracle_sha256": sha256(oracle_path),
        "comparison_is_posthoc": True,
        "private_fields_used_for_neural_selection": selection.get("private_fields_used_for_selection", []),
        "problems": len(rows),
        "candidate_slots_per_problem": args.candidate_slots,
        "neural_all_pass_count": neural_count,
        "neural_pass_at_1": neural_count / len(rows),
        "first_candidate_all_pass_count": first_count,
        "first_candidate_pass_at_1": first_count / len(rows),
        "neural_minus_first_count": neural_count - first_count,
        "neural_vs_first_wins": wins,
        "neural_vs_first_losses": losses,
        "neural_vs_first_exact_two_sided_sign_pvalue": exact_two_sided_sign_pvalue(wins, losses),
        "uniform_random_single_expected_all_pass_count": random_expected_count,
        "uniform_random_single_expected_pass_at_1": random_expected_count / len(rows),
        "neural_minus_uniform_random_expected_count": neural_count - random_expected_count,
        "neural_minus_uniform_random_expected_pass_at_1": difference_rate,
        "neural_minus_uniform_random_bootstrap_95ci": [
            percentile(bootstrap, 0.025),
            percentile(bootstrap, 0.975),
        ],
        "uniform_random_probability_of_at_least_neural_count": poisson_binomial_upper_tail(
            probabilities, neural_count
        ),
        "bootstrap_repetitions": args.bootstrap_repetitions,
        "bootstrap_seed": args.seed,
        "rows": rows,
        "interpretation": (
            "Post-hoc paper-aligned audit: neural Best-of-N uses no public/private execution feedback. "
            "The uniform-random baseline averages all fixed candidate slots and counts invalid slots as failures."
        ),
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: output[key] for key in [
        "problems", "neural_all_pass_count", "first_candidate_all_pass_count",
        "neural_minus_first_count", "neural_vs_first_wins", "neural_vs_first_losses",
        "neural_vs_first_exact_two_sided_sign_pvalue",
        "uniform_random_single_expected_all_pass_count",
        "neural_minus_uniform_random_expected_count",
        "neural_minus_uniform_random_expected_pass_at_1",
        "neural_minus_uniform_random_bootstrap_95ci",
        "uniform_random_probability_of_at_least_neural_count",
    ]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
