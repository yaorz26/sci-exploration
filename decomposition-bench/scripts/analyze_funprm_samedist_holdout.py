"""Audit paired public-only and public+neural FunPRM holdout selections."""

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


def exact_two_sided_sign_pvalue(wins: int, losses: int) -> float:
    discordant = wins + losses
    if discordant == 0:
        return 1.0
    tail = sum(math.comb(discordant, index) for index in range(min(wins, losses) + 1)) / (2**discordant)
    return min(1.0, 2.0 * tail)


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(probability * (len(ordered) - 1))))
    return ordered[index]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--bootstrap-repetitions", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    source = Path(args.input)
    payload = json.loads(source.read_text(encoding="utf-8"))
    private_rows = payload["private_rows"]
    paired_rows: list[dict] = []
    changed_selections = 0
    wins = 0
    losses = 0
    total_problems = len(payload["selection_rows"])
    for selection in payload["selection_rows"]:
        problem_id = str(selection["problem_id"])
        public_index = selection["selected_candidate_indices"]["public"]
        hybrid_index = selection["selected_candidate_indices"]["public_neural"]
        if public_index is None or hybrid_index is None:
            continue
        public_private = private_rows["public"][problem_id]
        hybrid_private = private_rows["public_neural"][problem_id]
        public_all = bool(public_private["all_pass"])
        hybrid_all = bool(hybrid_private["all_pass"])
        changed_selections += int(public_index != hybrid_index)
        wins += int(hybrid_all and not public_all)
        losses += int(public_all and not hybrid_all)
        paired_rows.append({
            "problem_id": problem_id,
            "public_candidate_index": public_index,
            "public_neural_candidate_index": hybrid_index,
            "selection_changed": public_index != hybrid_index,
            "public_private_pass_rate": float(public_private["pass_rate"]),
            "public_neural_private_pass_rate": float(hybrid_private["pass_rate"]),
            "private_pass_rate_difference": float(hybrid_private["pass_rate"]) - float(public_private["pass_rate"]),
            "public_private_all_pass": public_all,
            "public_neural_private_all_pass": hybrid_all,
            "all_pass_difference": int(hybrid_all) - int(public_all),
        })

    if not paired_rows:
        raise ValueError("No problems have valid public and public+neural selections")

    rng = random.Random(args.seed)
    pass_rate_bootstrap: list[float] = []
    all_pass_bootstrap: list[float] = []
    for _ in range(args.bootstrap_repetitions):
        sample = [paired_rows[rng.randrange(len(paired_rows))] for _ in paired_rows]
        pass_rate_bootstrap.append(sum(row["private_pass_rate_difference"] for row in sample) / len(sample))
        all_pass_bootstrap.append(sum(row["all_pass_difference"] for row in sample) / len(sample))

    pass_rate_difference = sum(row["private_pass_rate_difference"] for row in paired_rows) / len(paired_rows)
    all_pass_difference = sum(row["all_pass_difference"] for row in paired_rows) / len(paired_rows)
    public_all_pass_count = sum(int(row["public_private_all_pass"]) for row in paired_rows)
    hybrid_all_pass_count = sum(int(row["public_neural_private_all_pass"]) for row in paired_rows)
    output = {
        "input": str(source),
        "input_sha256": sha256(source),
        "private_fields_used_for_selection": payload.get("private_fields_used_for_selection", []),
        "candidate_count_reported": payload.get("candidate_count"),
        "total_problems": total_problems,
        "paired_problems": len(paired_rows),
        "problems_without_valid_candidate": [
            row["problem_id"]
            for row in payload["selection_rows"]
            if row["selected_candidate_indices"]["public"] is None
        ],
        "changed_selections": changed_selections,
        "hybrid_wins": wins,
        "hybrid_losses": losses,
        "net_all_pass_gain": hybrid_all_pass_count - public_all_pass_count,
        "public_all_pass_count": public_all_pass_count,
        "public_neural_all_pass_count": hybrid_all_pass_count,
        "public_pass_at_1_all_problems": public_all_pass_count / total_problems,
        "public_neural_pass_at_1_all_problems": hybrid_all_pass_count / total_problems,
        "public_pass_at_1_paired_problems": public_all_pass_count / len(paired_rows),
        "public_neural_pass_at_1_paired_problems": hybrid_all_pass_count / len(paired_rows),
        "discordant_outcomes": wins + losses,
        "exact_two_sided_sign_pvalue": exact_two_sided_sign_pvalue(wins, losses),
        "mean_private_pass_rate_difference": pass_rate_difference,
        "mean_private_pass_rate_difference_bootstrap_95ci": [
            percentile(pass_rate_bootstrap, 0.025),
            percentile(pass_rate_bootstrap, 0.975),
        ],
        "pass_at_1_difference": all_pass_difference,
        "pass_at_1_difference_bootstrap_95ci": [
            percentile(all_pass_bootstrap, 0.025),
            percentile(all_pass_bootstrap, 0.975),
        ],
        "bootstrap_repetitions": args.bootstrap_repetitions,
        "bootstrap_seed": args.seed,
        "paired_rows": paired_rows,
        "interpretation": "Paired audit. Treat the all-problem denominator as primary; bootstrap and sign-test results quantify uncertainty rather than proving equivalence or benefit.",
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: output[key] for key in [
        "total_problems", "paired_problems", "changed_selections", "hybrid_wins", "hybrid_losses",
        "net_all_pass_gain", "public_all_pass_count", "public_neural_all_pass_count",
        "public_pass_at_1_all_problems", "public_neural_pass_at_1_all_problems",
        "exact_two_sided_sign_pvalue", "mean_private_pass_rate_difference",
        "mean_private_pass_rate_difference_bootstrap_95ci", "pass_at_1_difference",
        "pass_at_1_difference_bootstrap_95ci",
    ]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
