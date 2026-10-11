"""Aggregate exact-label neural CodePRM pilot evaluations across seeds."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def mean_sd(values: list[float]) -> dict[str, float]:
    return {
        "mean": statistics.mean(values) if values else 0.0,
        "sample_sd": statistics.stdev(values) if len(values) > 1 else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44])
    parser.add_argument("--run-suffix", default="epoch1")
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    root = Path(args.root)
    rows = []
    for seed in args.seeds:
        run = root / f"train20_exact_seed{seed}_{args.run_suffix}"
        metrics = read_json(run / "metrics.json")
        evaluation = read_json(run / "evaluation.json")
        rows.append({
            "seed": seed,
            "train_records": metrics["train_records"],
            "test_records": metrics["test_records"],
            "train_problems": metrics["train_problems"],
            "test_problems": metrics["test_problems"],
            "step_mse": evaluation["step_mse"],
            "step_mae": evaluation["step_mae"],
            "step_spearman": evaluation["step_spearman"],
            "candidate_selected_private_pass_rate": evaluation["candidate_selected_private_pass_rate"],
            "first_candidate_private_pass_rate": evaluation["first_candidate_private_pass_rate"],
            "candidate_selected_pass_at_1": evaluation["candidate_selected_pass_at_1"],
            "first_candidate_pass_at_1": evaluation["first_candidate_pass_at_1"],
            "score_activation": evaluation.get("score_activation", metrics.get("score_activation", "linear")),
        })

    metric_names = [
        "step_mse",
        "step_mae",
        "step_spearman",
        "candidate_selected_private_pass_rate",
        "first_candidate_private_pass_rate",
        "candidate_selected_pass_at_1",
        "first_candidate_pass_at_1",
    ]
    aggregate = {name: mean_sd([row[name] for row in rows]) for name in metric_names}
    aggregate["selection_gain_vs_first"] = mean_sd([
        row["candidate_selected_private_pass_rate"] - row["first_candidate_private_pass_rate"]
        for row in rows
    ])
    output = {
        "protocol": {
            "dataset": "APPS train Introductory 20",
            "model": "Qwen2.5-Coder 3B",
            "label": "continuation private pass-rate mean",
            "continuations_per_node": 2,
            "candidates_per_problem": 2,
            "max_steps": 3,
            "epochs": args.epochs,
            "split": "first 15 problems train / last 5 problems test",
            "interpretation": "exploratory; underpowered train20 pilot",
        },
        "seeds": rows,
        "aggregate": aggregate,
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
