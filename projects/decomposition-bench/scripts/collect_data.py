"""Collect execution-feedback records for a configured problem subset."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data_loader import load_problems
from src.executor import execute_candidate
from src.feedback import collect_feedback_records
from src.generator import create_generator


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(ROOT / "data" / "processed" / "feedback_records.jsonl"))
    parser.add_argument("--num-problems", type=int, default=20)
    parser.add_argument("--num-candidates", type=int, default=4)
    parser.add_argument("--timeout-seconds", type=float, default=2.0)
    parser.add_argument("--generator-backend", choices=["offline", "ollama"], default="offline")
    parser.add_argument("--generator-model", default="dolphin3:latest")
    parser.add_argument("--ollama-endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--generation-timeout-seconds", type=float, default=180.0)
    parser.add_argument("--temperature", type=float, default=0.7)
    args = parser.parse_args()
    generator = create_generator(args.generator_backend, args.generator_model, args.ollama_endpoint, 42, args.generation_timeout_seconds, args.temperature)
    records = []
    for problem in load_problems(limit=args.num_problems):
        evaluated = []
        for candidate in generator.generate(problem, args.num_candidates):
            evaluated.append({**candidate, "execution": execute_candidate(candidate["code"], problem["public_tests"], problem["private_tests"], args.timeout_seconds, problem=problem)})
        records.extend(collect_feedback_records(problem, evaluated))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(json.dumps(record, ensure_ascii=False) for record in records) + "\n", encoding="utf-8")
    print(f"wrote {len(records)} records to {output}")


if __name__ == "__main__":
    main()
