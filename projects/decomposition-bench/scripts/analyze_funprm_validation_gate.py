"""Apply the frozen helper-first FunPRM validation gate to two selectors."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def outcome(value: dict[str, Any] | None) -> int:
    return int(bool((value or {}).get("all_pass", False)))


def oracle_outcome(value: dict[str, Any] | None) -> int:
    """Read the pool-oracle private outcome without conflating it with selection rows."""
    return int(bool((value or {}).get("private_all_pass", False)))


def selection_outcomes(selection: dict[str, Any]) -> dict[str, int]:
    if selection.get("private_fields_used_for_selection") not in ([], None):
        raise ValueError("selection reports private fields used during selection")
    private_rows = selection.get("private_rows", {}).get("neural", {})
    return {
        str(row["problem_id"]): outcome(private_rows.get(str(row["problem_id"])))
        for row in selection.get("selection_rows", [])
    }


def oracle_outcomes(oracle: dict[str, Any], candidate_slots: int) -> dict[str, list[int]]:
    if oracle.get("selection_private_fields_used") not in ([], None):
        raise ValueError("oracle reports private fields used during selection")
    values: dict[str, list[int]] = {}
    for row in oracle.get("rows", []):
        slots = [0] * candidate_slots
        for candidate in row.get("candidate_private_rows", []):
            index = int(candidate["candidate_index"])
            if 0 <= index < candidate_slots:
                slots[index] = oracle_outcome(candidate)
        values[str(row["problem_id"])] = slots
    return values


def summarize(
    new_selection: dict[str, Any],
    old_selection: dict[str, Any],
    oracle: dict[str, Any],
    *,
    candidate_slots: int,
    min_pool_headroom: int,
) -> dict[str, Any]:
    new = selection_outcomes(new_selection)
    old = selection_outcomes(old_selection)
    pool = oracle_outcomes(oracle, candidate_slots)
    expected_ids = set(new)
    if not expected_ids:
        raise ValueError("new selection has no problems")
    if set(old) != expected_ids or set(pool) != expected_ids:
        raise ValueError("new selection, old selection, and oracle problem IDs differ")

    rows = []
    for problem_id in sorted(expected_ids):
        slots = pool[problem_id]
        rows.append({
            "problem_id": problem_id,
            "new_neural_all_pass": bool(new[problem_id]),
            "old_neural_all_pass": bool(old[problem_id]),
            "first_candidate_all_pass": bool(slots[0]),
            "uniform_random_single_success_probability": sum(slots) / candidate_slots,
            "pool_oracle_all_pass": bool(any(slots)),
        })

    new_count = sum(int(row["new_neural_all_pass"]) for row in rows)
    old_count = sum(int(row["old_neural_all_pass"]) for row in rows)
    first_count = sum(int(row["first_candidate_all_pass"]) for row in rows)
    random_expected = sum(float(row["uniform_random_single_success_probability"]) for row in rows)
    oracle_count = sum(int(row["pool_oracle_all_pass"]) for row in rows)
    comparisons = {
        "new_not_below_old": new_count >= old_count,
        "new_not_below_first": new_count >= first_count,
        "new_not_below_uniform_random_expected": new_count >= random_expected,
        "pool_headroom_at_least_minimum": oracle_count - first_count >= min_pool_headroom,
    }
    return {
        "problems": len(rows),
        "candidate_slots_per_problem": candidate_slots,
        "metrics": {
            "new_neural_all_pass_count": new_count,
            "old_neural_all_pass_count": old_count,
            "first_candidate_all_pass_count": first_count,
            "uniform_random_single_expected_all_pass_count": random_expected,
            "pool_oracle_all_pass_count": oracle_count,
            "pool_oracle_minus_first_count": oracle_count - first_count,
            "new_vs_old_wins": sum(row["new_neural_all_pass"] > row["old_neural_all_pass"] for row in rows),
            "new_vs_old_losses": sum(row["new_neural_all_pass"] < row["old_neural_all_pass"] for row in rows),
        },
        "gate": {
            "minimum_pool_headroom": min_pool_headroom,
            **comparisons,
            "overall_pass": all(comparisons.values()),
        },
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--new-selection", required=True)
    parser.add_argument("--old-selection", required=True)
    parser.add_argument("--pool-oracle", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--candidate-slots", type=int, default=10)
    parser.add_argument("--min-pool-headroom", type=int, default=2)
    args = parser.parse_args()
    if args.candidate_slots <= 0 or args.min_pool_headroom < 0:
        raise ValueError("candidate slots must be positive and pool headroom must be nonnegative")
    output_path = Path(args.output)
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite {output_path}")
    new_path = Path(args.new_selection)
    old_path = Path(args.old_selection)
    oracle_path = Path(args.pool_oracle)
    result = summarize(
        load_json(new_path),
        load_json(old_path),
        load_json(oracle_path),
        candidate_slots=args.candidate_slots,
        min_pool_headroom=args.min_pool_headroom,
    )
    result.update({
        "experiment": "funprm_helperfirst_scale_prm_20260924",
        "new_selection": str(new_path),
        "new_selection_sha256": sha256(new_path),
        "old_selection": str(old_path),
        "old_selection_sha256": sha256(old_path),
        "pool_oracle": str(oracle_path),
        "pool_oracle_sha256": sha256(oracle_path),
        "selection_policy": "Both adapters select by highest mean +/- prefix score with candidate-index tie-break; private tests only follow frozen selection.",
        "interpretation": "Frozen validation gate; it does not itself establish confirmation-set performance.",
    })
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "metrics": result["metrics"],
        "gate": result["gate"],
        "output": str(output_path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
