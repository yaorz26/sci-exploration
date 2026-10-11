"""Score functionized candidates and privately evaluate only frozen selections."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForSequenceClassification, AutoTokenizer, BitsAndBytesConfig

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_funprm_function_nodes import _function_segments  # noqa: E402
from scripts.train_funprm_scorer import format_function_node, score_activation  # noqa: E402
from src.data_loader import load_problems  # noqa: E402
from src.modular import evaluate_split  # noqa: E402


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_model(model_path: str, adapter_path: str):
    tokenizer = AutoTokenizer.from_pretrained(adapter_path, local_files_only=True, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    quantization = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
    base = AutoModelForSequenceClassification.from_pretrained(
        model_path,
        local_files_only=True,
        num_labels=1,
        quantization_config=quantization,
        device_map="auto",
        dtype=torch.float16,
        trust_remote_code=True,
    )
    base.config.pad_token_id = tokenizer.pad_token_id
    model = PeftModel.from_pretrained(base, adapter_path, local_files_only=True)
    model.eval()
    return tokenizer, model, next(model.parameters()).device


def node_rows(problem: dict, code: str) -> list[dict]:
    functions = _function_segments(code)
    rows: list[dict] = []
    for index, function in enumerate(functions):
        rows.append({
            "problem_id": problem.get("problem_id"),
            "problem": problem.get("question", problem.get("problem", "")),
            "function_index": index,
            "function_name": function["name"],
            "completed_functions": "\n\n".join(item["code"] for item in functions[:index]),
            "current_function": function["code"],
            "prefix_code": "\n\n".join(item["code"] for item in functions[: index + 1]),
            "public_feedback": {},
        })
    return rows


def score_candidate(problem: dict, code: str, tokenizer, model, device, max_length: int, activation: str) -> float:
    rows = node_rows(problem, code)
    if not rows:
        return float("-inf")
    values: list[float] = []
    with torch.no_grad():
        for row in rows:
            encoded = tokenizer(format_function_node(row), truncation=True, max_length=max_length, padding="max_length", return_tensors="pt")
            encoded = {key: value.to(device) for key, value in encoded.items()}
            logits = model(**encoded).logits.squeeze(-1)
            values.append(float(score_activation(logits, activation).float().cpu()))
    return sum(values) / len(values)


def private_summary(private: dict) -> dict:
    total = int(private.get("total", 0))
    passed = int(private.get("passed", 0))
    return {"passed": passed, "total": total, "pass_rate": float(private.get("pass_rate", 0.0)), "all_pass": bool(total and passed == total)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--adapter-path", required=True)
    parser.add_argument("--public-evaluations", required=True)
    parser.add_argument("--apps-path", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--score-activation", choices=["linear", "sigmoid"], default="sigmoid")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--candidate-timeout", type=float, default=None)
    args = parser.parse_args()

    problems = {str(row["problem_id"]): row for row in load_problems(args.apps_path)}
    evaluations = read_jsonl(Path(args.public_evaluations))
    tokenizer, model, device = load_model(args.model_path, args.adapter_path)
    selected: dict[str, dict[str, dict]] = defaultdict(dict)
    rows_out: list[dict] = []

    for evaluation in evaluations:
        problem_id = str(evaluation["problem_id"])
        problem = problems[problem_id]
        candidates = evaluation["selection"]["candidates"]
        enriched: list[dict] = []
        for candidate in candidates:
            item = dict(candidate)
            code = item.get("code")
            item["neural_score"] = score_candidate(problem, str(code), tokenizer, model, device, args.max_length, args.score_activation) if code else float("-inf")
            enriched.append(item)
        eligible = [item for item in enriched if item.get("code")]
        public_choice = max(eligible, key=lambda item: (float((item.get("public") or {}).get("pass_rate", 0.0)), -int(item["candidate_index"]))) if eligible else None
        neural_choice = max(eligible, key=lambda item: (float(item["neural_score"]), -int(item["candidate_index"]))) if eligible else None
        public_neural_choice = max(eligible, key=lambda item: (float((item.get("public") or {}).get("pass_rate", 0.0)), float(item["neural_score"]), -int(item["candidate_index"]))) if eligible else None
        choices = {"public": public_choice, "neural": neural_choice, "public_neural": public_neural_choice}
        for rule, choice in choices.items():
            if choice:
                selected[rule][problem_id] = choice
        rows_out.append({"problem_id": problem_id, "candidates": enriched, "selected_candidate_indices": {rule: (choice["candidate_index"] if choice else None) for rule, choice in choices.items()}})

    private_cache: dict[str, dict] = {}
    private_rows: dict[str, dict[str, dict]] = defaultdict(dict)
    for rule, by_problem in selected.items():
        for problem_id, choice in by_problem.items():
            code = str(choice["code"])
            code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
            if code_hash not in private_cache:
                private_cache[code_hash] = evaluate_split(code, problems[problem_id], "private", args.timeout, args.candidate_timeout)
            private_rows[rule][problem_id] = private_summary(private_cache[code_hash])

    metrics: dict[str, dict] = {}
    for rule, by_problem in private_rows.items():
        values = list(by_problem.values())
        metrics[rule] = {
            "problems": len(values),
            "selected_private_pass_rate_mean": sum(value["pass_rate"] for value in values) / len(values) if values else 0.0,
            "selected_private_all_pass": sum(value["all_pass"] for value in values),
            "selected_private_pass_at_1": sum(value["all_pass"] for value in values) / len(values) if values else 0.0,
        }

    output = {
        "model_path": args.model_path,
        "adapter_path": args.adapter_path,
        "public_evaluations": str(Path(args.public_evaluations)),
        "apps_path": str(Path(args.apps_path)),
        "private_fields_used_for_selection": [],
        "score_activation": args.score_activation,
        "candidate_count": sum(len(row["candidates"]) for row in rows_out),
        "private_evaluations": len(private_cache),
        "metrics": metrics,
        "selection_rows": rows_out,
        "private_rows": private_rows,
        "interpretation": "FunPRM-style derived function-node scorer; function boundary mapping is derived from complete candidates and is not the authors' original trajectory.",
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"metrics": metrics, "private_evaluations": len(private_cache)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
