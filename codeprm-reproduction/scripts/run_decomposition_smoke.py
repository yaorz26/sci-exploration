"""Run a small M2a/M2b decomposition smoke and write JSONL records."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_problems  # noqa: E402
from src.decomposition import DecompositionGenerator  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/raw/apps_train_introductory20.json")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--protocol", choices=["json", "skeleton", "both"], default="json")
    parser.add_argument("--model", default="qwen2.5-coder:3b")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    protocols = ["json", "skeleton"] if args.protocol == "both" else [args.protocol]
    output = Path(args.output) if args.output else ROOT / "data" / "processed" / f"decomposition_records_{args.model.replace(':', '_')}_intro{args.limit}_seed{args.seed}.jsonl"
    output.parent.mkdir(parents=True, exist_ok=True)
    problems = load_problems(ROOT / args.data if not Path(args.data).is_absolute() else args.data, limit=args.limit)
    generator = DecompositionGenerator(model=args.model, seed=args.seed)
    summary = {"records": 0, "valid": 0, "raw_valid": 0, "entrypoint_preserved": 0, "dag_valid": 0, "errors": {}}
    with output.open("w", encoding="utf-8") as handle:
        for problem in problems:
            for protocol in protocols:
                try:
                    record = generator.generate(problem, protocol=protocol, candidate_index=0)
                except Exception as exc:  # keep a failed problem from killing the batch
                    record = {
                        "problem_id": problem.get("problem_id"),
                        "protocol": protocol,
                        "generator_model": args.model,
                        "seed": args.seed,
                        "error": f"request_failed:{type(exc).__name__}:{exc}",
                    }
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                handle.flush()
                summary["records"] += 1
                validation = record.get("validation", {})
                parse_info = record.get("parse", {})
                summary["valid"] += int(bool(validation.get("valid")))
                summary["raw_valid"] += int(bool(parse_info.get("raw_valid")))
                summary["entrypoint_preserved"] += int(bool(validation.get("entrypoint_preserved")))
                summary["dag_valid"] += int(bool(validation.get("dag_valid")))
                for error in validation.get("errors", []):
                    summary["errors"][error] = summary["errors"].get(error, 0) + 1
    summary["output"] = str(output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

