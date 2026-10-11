"""Run E1/E2 candidate selection baselines."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data_loader import load_problems
from src.executor import execute_candidate
from src.feedback import collect_feedback_records
from src.generator import create_generator
from src.metrics import select_candidate, summarize, write_results


def read_config(path: Path) -> dict[str, object]:
    config: dict[str, object] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip().strip('"\'')
        if value.lower() in {"true", "false"}:
            parsed: object = value.lower() == "true"
        else:
            try:
                parsed = float(value) if "." in value else int(value)
            except ValueError:
                parsed = value
        config[key.strip()] = parsed
    return config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(ROOT / "configs" / "minimal.yaml"))
    parser.add_argument("--apps-path")
    parser.add_argument("--generator-backend", choices=["offline", "ollama"])
    parser.add_argument("--generator-model")
    parser.add_argument("--ollama-endpoint")
    parser.add_argument("--seed", type=int, help="Override random_seed from the config")
    parser.add_argument("--num-problems", type=int, help="Override num_problems from the config")
    parser.add_argument("--num-candidates", type=int, help="Override num_candidates from the config")
    parser.add_argument("--output-suffix", default="")
    args = parser.parse_args()
    config = read_config(Path(args.config))
    seed = args.seed if args.seed is not None else int(config.get("random_seed", 42))
    config["random_seed"] = seed
    limit = args.num_problems if args.num_problems is not None else int(config.get("num_problems", 20))
    n = args.num_candidates if args.num_candidates is not None else int(config.get("num_candidates", 4))
    config["num_problems"], config["num_candidates"] = limit, n
    timeout = float(config.get("timeout_seconds", 10))
    problems = load_problems(args.apps_path, limit)
    backend = args.generator_backend or str(config.get("generator_backend", "offline"))
    model = args.generator_model or str(config.get("generator_model", "dolphin3:latest"))
    endpoint = args.ollama_endpoint or str(config.get("ollama_endpoint", "http://127.0.0.1:11434"))
    generation_timeout = float(config.get("generation_timeout_seconds", 180))
    temperature = float(config.get("generation_temperature", 0.7))
    generator = create_generator(backend, model, endpoint, seed, generation_timeout, temperature)
    methods = ["first", "random", "public_pass_rate", "private_oracle"]
    evaluated_problems, feedback_records = [], []
    for problem in problems:
        evaluated = []
        for candidate in generator.generate(problem, n):
            execution = execute_candidate(candidate["code"], problem["public_tests"], problem["private_tests"], timeout, problem=problem)
            evaluated.append({**candidate, "execution": execution})
        evaluated_problems.append((problem, evaluated))
        feedback_records.extend(collect_feedback_records(problem, evaluated))

    all_rows, summaries = [], []
    for method in methods:
        rng = random.Random(seed)
        rows = []
        for problem, evaluated in evaluated_problems:
            selected_index = select_candidate(evaluated, method, rng)
            rows.append({"problem_id": problem["problem_id"], "question": problem["question"], "method": method, "selected": evaluated[selected_index], "selected_candidate": selected_index, "num_executions": n * (len(problem["public_tests"]) + len(problem["private_tests"]))})
        summaries.append(summarize(rows, method))
        all_rows.extend(rows)
    output_dir = ROOT / "outputs" / "results"
    suffix = f"_{args.output_suffix}" if args.output_suffix else ""
    json_path, csv_path = write_results(summaries, all_rows, output_dir, stem=f"baseline{suffix}")
    feedback_path = ROOT / "data" / "processed" / f"feedback_records{suffix}.jsonl"
    feedback_path.parent.mkdir(parents=True, exist_ok=True)
    feedback_path.write_text("\n".join(json.dumps(record, ensure_ascii=False) for record in feedback_records) + "\n", encoding="utf-8")
    generation_path = ROOT / "outputs" / "generations" / f"baseline_candidates{suffix}.json"
    generation_path.parent.mkdir(parents=True, exist_ok=True)
    generation_path.write_text(json.dumps(feedback_records, ensure_ascii=False, indent=2), encoding="utf-8")
    report_csv = ROOT / "reports" / "tables" / f"baseline{suffix}.csv"
    report_csv.parent.mkdir(parents=True, exist_ok=True)
    report_csv.write_text(csv_path.read_text(encoding="utf-8"), encoding="utf-8")
    print(json.dumps({"config": config, "problems": len(problems), "json": str(json_path), "csv": str(report_csv), "feedback": str(feedback_path), "summary": summaries}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
