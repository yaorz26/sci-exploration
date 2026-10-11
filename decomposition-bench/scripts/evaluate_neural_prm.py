"""Evaluate a saved scalar QLoRA scorer on exact step records and candidates."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
import sys

import torch
from peft import PeftModel
from scipy.stats import spearmanr
from transformers import AutoModelForSequenceClassification, AutoTokenizer, BitsAndBytesConfig

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from train_neural_prm import format_text, predict_scores


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_model(base_path: str, adapter_path: str):
    tokenizer = AutoTokenizer.from_pretrained(adapter_path, local_files_only=True, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    quantization = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)
    base = AutoModelForSequenceClassification.from_pretrained(base_path, local_files_only=True, num_labels=1, quantization_config=quantization, device_map="auto", dtype=torch.float16, trust_remote_code=True)
    base.config.pad_token_id = tokenizer.pad_token_id
    model = PeftModel.from_pretrained(base, adapter_path, local_files_only=True)
    model.eval()
    return tokenizer, model, next(model.parameters()).device


def score_rows(rows: list[dict], tokenizer, model, device, max_length: int, activation: str) -> list[float]:
    scores = []
    with torch.no_grad():
        for row in rows:
            encoded = tokenizer(format_text(row), truncation=True, max_length=max_length, padding="max_length", return_tensors="pt")
            encoded = {key: value.to(device) for key, value in encoded.items()}
            logits = model(**encoded).logits.squeeze()
            scores.append(float(predict_scores(logits, activation).float().cpu()))
    return scores


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--adapter-path", required=True)
    parser.add_argument("--step-data", required=True)
    parser.add_argument("--feedback-path", required=True)
    parser.add_argument("--apps-path", required=True)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--score-activation", default="linear", choices=["linear", "sigmoid"])
    parser.add_argument("--label-field", default="step_label", choices=["label", "step_label", "binary_label", "binary_step_label"])
    parser.add_argument("--candidate-thought-steps", type=int, default=0, help="0 keeps all thoughts; positive values retain only this prefix length")
    parser.add_argument("--num-candidates", type=int, default=2)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    tokenizer, model, device = load_model(args.model_path, args.adapter_path)
    exact_rows = read_jsonl(Path(args.step_data))
    test_problems = []
    for row in exact_rows:
        if row["problem_id"] not in test_problems:
            test_problems.append(row["problem_id"])
    test_problems = test_problems[int(len(test_problems) * 0.75):]
    exact_rows = [row for row in exact_rows if row["problem_id"] in set(test_problems)]
    exact_scores = score_rows(exact_rows, tokenizer, model, device, args.max_length, args.score_activation)
    labels = [row[args.label_field] for row in exact_rows]
    errors = [score - label for score, label in zip(exact_scores, labels)]
    node_scores = defaultdict(list)
    node_labels = defaultdict(list)
    for row, score in zip(exact_rows, exact_scores):
        key = (row["problem_id"], row["source_candidate_index"], row["step_index"])
        node_scores[key].append(score)
        node_labels[key].append(row["step_label"])
    continuation_candidate_score_rows = []
    for problem_id in test_problems:
        for candidate_index in range(args.num_candidates):
            values = [sum(node_scores[key]) / len(node_scores[key]) for key in node_scores if key[0] == problem_id and key[1] == candidate_index]
            continuation_candidate_score_rows.append({"problem_id": problem_id, "candidate_index": candidate_index, "score": sum(values) / len(values) if values else 0.0})
    original = read_jsonl(Path(args.feedback_path))
    by_problem = defaultdict(list)
    for row in original:
        by_problem[row["problem_id"]].append(row)
    original_candidate_rows = []
    original_candidate_meta = []
    for problem_id in test_problems:
        for candidate_index, candidate in enumerate(by_problem[problem_id][: args.num_candidates]):
            original_candidate_rows.append({
                "problem_id": problem_id,
                "candidate_index": candidate_index,
                "problem": candidate["problem"],
                "thought_prefix": candidate.get("thoughts", [])[: args.candidate_thought_steps] if args.candidate_thought_steps else candidate.get("thoughts", []),
                "code": candidate.get("code", ""),
                "public_feedback": candidate.get("public_feedback", {}),
            })
    original_scores = score_rows(original_candidate_rows, tokenizer, model, device, args.max_length, args.score_activation)
    for row, score in zip(original_candidate_rows, original_scores):
        original_candidate_meta.append({"problem_id": row["problem_id"], "candidate_index": row["candidate_index"], "score": score})

    continuation_selected_rates = []
    original_selected_rates = []
    public_selected_rates = []
    public_neural_tiebreak_rates = []
    baseline_rates = []
    selection_rows = []
    for problem_id in test_problems:
        continuation_scored = [row for row in continuation_candidate_score_rows if row["problem_id"] == problem_id]
        original_scored = [row for row in original_candidate_meta if row["problem_id"] == problem_id]
        continuation_selected = max(continuation_scored, key=lambda row: (row["score"], -row["candidate_index"]))["candidate_index"]
        original_selected = max(original_scored, key=lambda row: (row["score"], -row["candidate_index"]))["candidate_index"]
        candidates = by_problem[problem_id]
        public_selected = max(
            range(min(args.num_candidates, len(candidates))),
            key=lambda index: (candidates[index]["public_feedback"]["pass_rate"], -index),
        )
        original_score_by_index = {row["candidate_index"]: row["score"] for row in original_scored}
        public_neural_tiebreak = max(
            range(min(args.num_candidates, len(candidates))),
            key=lambda index: (
                candidates[index]["public_feedback"]["pass_rate"],
                original_score_by_index[index],
                -index,
            ),
        )
        continuation_selected_rates.append(candidates[continuation_selected]["private_feedback"]["pass_rate"])
        original_selected_rates.append(candidates[original_selected]["private_feedback"]["pass_rate"])
        public_selected_rates.append(candidates[public_selected]["private_feedback"]["pass_rate"])
        public_neural_tiebreak_rates.append(candidates[public_neural_tiebreak]["private_feedback"]["pass_rate"])
        baseline_rates.append(candidates[0]["private_feedback"]["pass_rate"])
        selection_rows.append({
            "problem_id": problem_id,
            "continuation_prefix_candidate_index": continuation_selected,
            "original_candidate_index": original_selected,
            "public_candidate_index": public_selected,
            "public_neural_tiebreak_candidate_index": public_neural_tiebreak,
            "first_private_pass_rate": candidates[0]["private_feedback"]["pass_rate"],
            "continuation_prefix_private_pass_rate": candidates[continuation_selected]["private_feedback"]["pass_rate"],
            "original_candidate_private_pass_rate": candidates[original_selected]["private_feedback"]["pass_rate"],
            "public_selected_private_pass_rate": candidates[public_selected]["private_feedback"]["pass_rate"],
            "public_neural_tiebreak_private_pass_rate": candidates[public_neural_tiebreak]["private_feedback"]["pass_rate"],
        })
    output = {
        "test_problems": test_problems,
        "step_records": len(exact_rows),
        "score_activation": args.score_activation,
        "label_field": args.label_field,
        "candidate_thought_steps": args.candidate_thought_steps,
        "step_mse": sum(error * error for error in errors) / len(errors) if errors else 0.0,
        "step_mae": sum(abs(error) for error in errors) / len(errors) if errors else 0.0,
        "step_spearman": float(spearmanr(exact_scores, labels).statistic) if len(set(labels)) > 1 else 0.0,
        "candidate_selected_private_pass_rate": sum(continuation_selected_rates) / len(continuation_selected_rates) if continuation_selected_rates else 0.0,
        "continuation_prefix_selected_private_pass_rate": sum(continuation_selected_rates) / len(continuation_selected_rates) if continuation_selected_rates else 0.0,
        "original_candidate_selected_private_pass_rate": sum(original_selected_rates) / len(original_selected_rates) if original_selected_rates else 0.0,
        "public_selected_private_pass_rate": sum(public_selected_rates) / len(public_selected_rates) if public_selected_rates else 0.0,
        "public_neural_tiebreak_private_pass_rate": sum(public_neural_tiebreak_rates) / len(public_neural_tiebreak_rates) if public_neural_tiebreak_rates else 0.0,
        "first_candidate_private_pass_rate": sum(baseline_rates) / len(baseline_rates) if baseline_rates else 0.0,
        "candidate_selected_pass_at_1": sum(rate == 1.0 for rate in continuation_selected_rates) / len(continuation_selected_rates) if continuation_selected_rates else 0.0,
        "continuation_prefix_selected_pass_at_1": sum(rate == 1.0 for rate in continuation_selected_rates) / len(continuation_selected_rates) if continuation_selected_rates else 0.0,
        "original_candidate_selected_pass_at_1": sum(rate == 1.0 for rate in original_selected_rates) / len(original_selected_rates) if original_selected_rates else 0.0,
        "public_selected_pass_at_1": sum(rate == 1.0 for rate in public_selected_rates) / len(public_selected_rates) if public_selected_rates else 0.0,
        "public_neural_tiebreak_pass_at_1": sum(rate == 1.0 for rate in public_neural_tiebreak_rates) / len(public_neural_tiebreak_rates) if public_neural_tiebreak_rates else 0.0,
        "first_candidate_pass_at_1": sum(rate == 1.0 for rate in baseline_rates) / len(baseline_rates) if baseline_rates else 0.0,
        "selection_rows": selection_rows,
        "interpretation": "exact-label QLoRA held-out evaluation; report as exploratory unless backed by larger multi-seed data"
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
