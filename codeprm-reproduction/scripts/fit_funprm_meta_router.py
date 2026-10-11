"""Fit a train-only meta reward correction and evaluate it on a frozen holdout."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch
from peft import PeftModel
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from transformers import AutoModelForSequenceClassification, AutoTokenizer, BitsAndBytesConfig

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_funprm_function_nodes import _function_segments  # noqa: E402
from scripts.train_funprm_scorer import format_function_node, score_activation  # noqa: E402
from src.data_loader import load_problems  # noqa: E402
from src.modular import evaluate_split  # noqa: E402


FEATURE_NAMES = ["public_pass_rate", "neural_mean", "neural_min", "neural_max", "neural_std", "function_count", "code_chars"]


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


def score_node_rows(rows: list[dict], tokenizer, model, device, max_length: int, activation: str) -> list[float]:
    values: list[float] = []
    with torch.no_grad():
        for row in rows:
            encoded = tokenizer(format_function_node(row), truncation=True, max_length=max_length, padding="max_length", return_tensors="pt")
            encoded = {key: value.to(device) for key, value in encoded.items()}
            logits = model(**encoded).logits.squeeze(-1)
            values.append(float(score_activation(logits, activation).float().cpu()))
    return values


def training_candidate_rows(nodes: list[dict], scores: list[float]) -> list[dict]:
    grouped: dict[tuple[str, int], list[tuple[dict, float]]] = defaultdict(list)
    for row, score in zip(nodes, scores):
        grouped[(str(row["problem_id"]), int(row.get("source_candidate_index", 0)))].append((row, score))
    output: list[dict] = []
    for (problem_id, candidate_index), values in grouped.items():
        first = values[0][0]
        neural = np.asarray([score for _, score in values], dtype=float)
        public = first.get("public_feedback", {}) or {}
        code = str(first.get("prefix_code", ""))
        output.append({
            "problem_id": problem_id,
            "candidate_index": candidate_index,
            "features": [
                float(public.get("pass_rate", 0.0)),
                float(neural.mean()),
                float(neural.min()),
                float(neural.max()),
                float(neural.std()),
                float(len(values)),
                float(len(code)),
            ],
            "label": float(first.get("final_label", 0.0)),
        })
    return output


def holdout_features(candidate: dict) -> list[float]:
    code = str(candidate.get("code", ""))
    try:
        functions = _function_segments(code)
    except (SyntaxError, TypeError, ValueError):
        functions = []
    neural = float(candidate.get("neural_score", 0.0))
    public = candidate.get("public") or {}
    return [float(public.get("pass_rate", 0.0)), neural, neural, neural, 0.0, float(len(functions)), float(len(code))]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--adapter-path", required=True)
    parser.add_argument("--train-nodes", required=True)
    parser.add_argument("--holdout-selection", required=True)
    parser.add_argument("--apps-path", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--score-activation", choices=["linear", "sigmoid"], default="sigmoid")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    tokenizer, model, device = load_model(args.model_path, args.adapter_path)
    nodes = read_jsonl(Path(args.train_nodes))
    node_scores = score_node_rows(nodes, tokenizer, model, device, args.max_length, args.score_activation)
    train_candidates = training_candidate_rows(nodes, node_scores)
    x = np.asarray([row["features"] for row in train_candidates], dtype=float)
    y = np.asarray([row["label"] for row in train_candidates], dtype=float)
    groups = np.asarray([row["problem_id"] for row in train_candidates])

    cv_scores: dict[str, float] = {}
    for alpha in (0.01, 0.1, 1.0, 10.0, 100.0):
        fold_errors: list[float] = []
        splitter = GroupKFold(n_splits=5)
        for train_index, test_index in splitter.split(x, y, groups):
            estimator = make_pipeline(StandardScaler(), Ridge(alpha=alpha))
            estimator.fit(x[train_index], y[train_index])
            prediction = estimator.predict(x[test_index])
            fold_errors.extend((prediction - y[test_index]).tolist())
        cv_scores[str(alpha)] = sum(error * error for error in fold_errors) / len(fold_errors)
    best_alpha = min(cv_scores, key=cv_scores.get)
    estimator = make_pipeline(StandardScaler(), Ridge(alpha=float(best_alpha)))
    estimator.fit(x, y)

    selection_input = json.loads(Path(args.holdout_selection).read_text(encoding="utf-8"))
    problems = {str(row["problem_id"]): row for row in load_problems(args.apps_path)}
    private_cache: dict[str, dict] = {}
    private_rows: dict[str, dict] = {}
    selection_rows: list[dict] = []
    for row in selection_input["selection_rows"]:
        problem_id = str(row["problem_id"])
        enriched = []
        for candidate in row["candidates"]:
            item = dict(candidate)
            item["meta_features"] = holdout_features(item)
            item["meta_score"] = float(estimator.predict(np.asarray([item["meta_features"]], dtype=float))[0]) if item.get("code") else float("-inf")
            enriched.append(item)
        eligible = [item for item in enriched if item.get("code")]
        choice = max(eligible, key=lambda item: (float(item["meta_score"]), -int(item["candidate_index"]))) if eligible else None
        if choice:
            code = str(choice["code"])
            code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
            if code_hash not in private_cache:
                private_cache[code_hash] = evaluate_split(code, problems[problem_id], "private", args.timeout, None)
            private = private_cache[code_hash]
            private_rows[problem_id] = {
                "passed": int(private.get("passed", 0)),
                "total": int(private.get("total", 0)),
                "pass_rate": float(private.get("pass_rate", 0.0)),
                "all_pass": bool(private.get("total", 0) and private.get("passed", 0) == private.get("total", 0)),
            }
        selection_rows.append({"problem_id": problem_id, "candidates": enriched, "selected_candidate_index": choice["candidate_index"] if choice else None})

    values = list(private_rows.values())
    output = {
        "model_path": args.model_path,
        "adapter_path": args.adapter_path,
        "train_nodes": str(Path(args.train_nodes)),
        "holdout_selection": str(Path(args.holdout_selection)),
        "private_fields_used_for_fit": "training_split_only",
        "private_fields_used_for_holdout_selection": [],
        "feature_names": FEATURE_NAMES,
        "best_alpha": float(best_alpha),
        "cv_mse_by_alpha": cv_scores,
        "train_candidates": len(train_candidates),
        "holdout_problems": len(values),
        "selected_private_pass_rate_mean": sum(item["pass_rate"] for item in values) / len(values) if values else 0.0,
        "selected_private_all_pass": sum(item["all_pass"] for item in values),
        "selected_private_pass_at_1": sum(item["all_pass"] for item in values) / len(values) if values else 0.0,
        "private_evaluations": len(private_cache),
        "selection_rows": selection_rows,
        "private_rows": private_rows,
        "interpretation": "Train-only Ridge meta reward correction; holdout private is read only after meta selection.",
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({key: output[key] for key in ["best_alpha", "cv_mse_by_alpha", "holdout_problems", "selected_private_all_pass", "selected_private_pass_at_1", "selected_private_pass_rate_mean"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
