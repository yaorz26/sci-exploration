"""Collect continuation-level labels for a small CodePRM data audit.

For each selected candidate thought prefix, ask Ollama for multiple complete
code continuations. The node label is the mean private pass rate of those
continuations. The private tests are used only after generation and are never
included in the prompt.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data_loader import load_problems
from src.executor import execute_candidate
from src.generator import OllamaGenerator, _parse_response


def continuation_prompt(problem: dict, thought_prefix: list[str]) -> str:
    if problem.get("execution_mode") == "function":
        task = (
            "This is a function-style APPS task. Preserve the exact function signature in the starter code. "
            "Return a Python function implementation only; do not read stdin, print prompts, open files, or include tests.\n"
            f"Starter code:\n{problem.get('starter_code', '')}\n"
        )
    else:
        task = (
            "Read input from sys.stdin exactly once and print only the required answer. "
            "Do not open files, print prompts, or include tests.\n"
        )
    return (
        "You are generating a code continuation for a process-reward data collection audit.\n"
        "Continue the reasoning prefix below and return a complete Python 3 solution.\n"
        "Put the complete plan between <thoughts> and </thoughts>. Put only executable code between <code> and </code>.\n"
        f"{task}"
        f"Problem:\n{problem.get('question', '')}\n\n"
        f"Reasoning prefix:\n{json.dumps(thought_prefix, ensure_ascii=False)}\n"
        "Use only the problem and reasoning prefix. Do not use private tests or hidden answers."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apps-path", required=True)
    parser.add_argument("--feedback-path", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--num-problems", type=int, default=2)
    parser.add_argument("--num-candidates", type=int, default=2)
    parser.add_argument("--max-steps", type=int, default=3)
    parser.add_argument("--continuations", type=int, default=2)
    parser.add_argument("--model", default="qwen2.5-coder:3b")
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--seed", type=int, default=4200)
    parser.add_argument("--timeout-seconds", type=float, default=180.0)
    parser.add_argument("--resume", action="store_true", help="resume completed nodes from an existing JSONL output")
    parser.add_argument("--resume-from", help="load completed nodes from a compatible JSONL checkpoint")
    args = parser.parse_args()

    problems = load_problems(args.apps_path, limit=args.num_problems)
    raw_records = [json.loads(line) for line in Path(args.feedback_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    by_problem: dict[str, list[dict]] = {}
    for row in raw_records:
        by_problem.setdefault(row["problem_id"], []).append(row)
    generator = OllamaGenerator(args.model, args.endpoint, args.seed, args.timeout_seconds, 0.7)
    output = Path(args.output)
    output_rows = []
    completed_nodes: set[tuple[str, int, int]] = set()
    checkpoint_source = Path(args.resume_from) if args.resume_from else output
    if (args.resume or args.resume_from) and checkpoint_source.exists():
        output_rows = [json.loads(line) for line in checkpoint_source.read_text(encoding="utf-8").splitlines() if line.strip()]
        completed_nodes = {
            (row["problem_id"], int(row["source_candidate_index"]), int(row["step_index"]))
            for row in output_rows
        }

    def checkpoint() -> None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in output_rows) + "\n",
            encoding="utf-8",
        )

    for problem in problems:
        candidates = by_problem.get(problem["problem_id"], [])[: args.num_candidates]
        for candidate_index, candidate in enumerate(candidates):
            thoughts = candidate.get("thoughts", [])
            for step_index, _ in enumerate(thoughts[: args.max_steps]):
                node_key = (problem["problem_id"], candidate_index, step_index)
                if node_key in completed_nodes:
                    continue
                prefix = [str(item) for item in thoughts[: step_index + 1]]
                continuations = []
                for continuation_index in range(args.continuations):
                    seed = args.seed + candidate_index * 1000 + step_index * 100 + continuation_index
                    response = generator._request(continuation_prompt(problem, prefix), seed)
                    revised_thoughts, code = _parse_response(response)
                    execution = execute_candidate(code, problem["public_tests"], problem["private_tests"], 2, problem=problem)
                    continuations.append({
                        "continuation_index": continuation_index,
                        "seed": seed,
                        "code": code,
                        "thoughts": revised_thoughts,
                        "public_feedback": execution["public"],
                        "private_feedback": execution["private"],
                    })
                node_label = sum(item["private_feedback"]["pass_rate"] for item in continuations) / len(continuations)
                for item in continuations:
                    output_rows.append({
                        "problem_id": problem["problem_id"],
                        "problem": problem["question"],
                        "source_candidate_index": candidate_index,
                        "step_index": step_index,
                        "thought_prefix": prefix,
                        "code": item["code"],
                        "thoughts": item["thoughts"],
                        "public_feedback": item["public_feedback"],
                        "private_feedback": item["private_feedback"],
                        "continuation_pass_rate": item["private_feedback"]["pass_rate"],
                        "step_label": node_label,
                        "binary_step_label": int(node_label == 1.0),
                        "continuation_count": len(continuations),
                        "label_source": "continuation_private_pass_rate_mean",
                        "exact_step_label": True,
                    })
                completed_nodes.add(node_key)
        checkpoint()

    checkpoint()
    print(json.dumps({
        "output": str(output),
        "problems": len({row["problem_id"] for row in output_rows}),
        "nodes": len({(row["problem_id"], row["source_candidate_index"], row["step_index"]) for row in output_rows}),
        "continuation_records": len(output_rows),
        "continuations_per_node": args.continuations,
        "exact_step_label": True,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
