"""Run no-execution FunPRM Best-of-N selection with a generative +/- scorer."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.funprm_generative_common import (  # noqa: E402
    function_prefixes,
    positive_probability,
    render_prompt,
    reward_logits,
    reward_token_ids,
)
from src.data_loader import load_problems  # noqa: E402
from src.modular import evaluate_split  # noqa: E402


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def private_summary(value: dict[str, Any]) -> dict[str, Any]:
    total = int(value.get("total", 0))
    passed = int(value.get("passed", 0))
    return {"passed": passed, "total": total, "pass_rate": float(value.get("pass_rate", 0.0)), "all_pass": bool(total and passed == total)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--adapter-path", required=True)
    parser.add_argument("--candidate-evaluations", required=True)
    parser.add_argument("--apps-path", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument(
        "--defer-private",
        action="store_true",
        help="Score candidates and freeze selections without running private tests.",
    )
    args = parser.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.truncation_side = "left"
    plus_id, minus_id = reward_token_ids(tokenizer)
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    base = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        local_files_only=True,
        quantization_config=quantization,
        device_map="auto",
        dtype=torch.float16,
        trust_remote_code=True,
    )
    model = PeftModel.from_pretrained(base, args.adapter_path)
    model.eval()
    device = next(model.parameters()).device
    problems = {str(row["problem_id"]): row for row in load_problems(args.apps_path)}
    source_rows = read_jsonl(Path(args.candidate_evaluations))
    score_cache: dict[tuple[str, str], tuple[float, list[float]]] = {}
    selection_rows = []

    for source in source_rows:
        problem_id = str(source["problem_id"])
        candidates = source["selection"]["candidates"]
        enriched = []
        for candidate in candidates:
            code = candidate.get("code")
            if not code:
                continue
            code_hash = str(candidate.get("code_hash") or hashlib.sha256(str(code).encode()).hexdigest())
            cache_key = (problem_id, code_hash)
            if cache_key not in score_cache:
                try:
                    prefixes = function_prefixes(str(code), include_final=True)
                except (SyntaxError, TypeError, ValueError):
                    prefixes = []
                scores = []
                for prefix in prefixes:
                    prompt = render_prompt(tokenizer, str(problems[problem_id].get("question", "")), prefix)
                    encoded = tokenizer(prompt, truncation=True, max_length=args.max_length, return_tensors="pt")
                    encoded = {key: value.to(device) for key, value in encoded.items()}
                    with torch.no_grad():
                        score = positive_probability(reward_logits(model, encoded["input_ids"], encoded["attention_mask"], plus_id, minus_id))[0]
                    scores.append(float(score.cpu()))
                score_cache[cache_key] = (sum(scores) / len(scores) if scores else 0.0, scores)
            aggregate, node_scores = score_cache[cache_key]
            enriched.append({
                "candidate_index": int(candidate["candidate_index"]),
                "code": str(code),
                "code_hash": code_hash,
                "neural_score": aggregate,
                "node_scores": node_scores,
            })
        choice = max(enriched, key=lambda item: (item["neural_score"], -item["candidate_index"])) if enriched else None
        selection_rows.append({
            "problem_id": problem_id,
            "candidates": enriched,
            "selected_candidate_indices": {"neural": choice["candidate_index"] if choice else None},
        })

    private_cache: dict[tuple[str, str], dict[str, Any]] = {}
    private_rows: dict[str, dict[str, Any]] = defaultdict(dict)
    if not args.defer_private:
        for selection in selection_rows:
            problem_id = str(selection["problem_id"])
            selected_index = selection["selected_candidate_indices"]["neural"]
            choice = next((row for row in selection["candidates"] if row["candidate_index"] == selected_index), None)
            if choice is None:
                continue
            code_hash = choice["code_hash"]
            cache_key = (problem_id, code_hash)
            if cache_key not in private_cache:
                private_cache[cache_key] = evaluate_split(choice["code"], problems[problem_id], "private", args.timeout, None)
            private_rows["neural"][problem_id] = private_summary(private_cache[cache_key])

    values = list(private_rows["neural"].values())
    total_problems = len(selection_rows)
    covered_problems = sum(
        row.get("selected_candidate_indices", {}).get("neural") is not None
        for row in selection_rows
    )
    all_pass_count = sum(int(value["all_pass"]) for value in values)
    output = {
        "model_path": args.model_path,
        "adapter_path": args.adapter_path,
        "selection_rule": "highest mean generative +/- score across cumulative function prefixes; candidate index tie-break",
        "private_fields_used_for_selection": [],
        "private_evaluation_deferred": bool(args.defer_private),
        "total_problems": total_problems,
        "covered_problems": covered_problems,
        "candidate_count": sum(len(row["candidates"]) for row in selection_rows),
        "unique_scored_codes": len(score_cache),
        "private_evaluations": len(private_cache),
        "metrics": {
            "neural": {
                "problems": len(values),
                "selected_private_pass_rate_mean": sum(value["pass_rate"] for value in values) / len(values) if values else 0.0,
                "selected_private_all_pass": all_pass_count,
                "selected_private_pass_at_1_covered": all_pass_count / len(values) if values else 0.0,
                "selected_private_pass_at_1_all_problems": all_pass_count / total_problems if total_problems else 0.0,
            }
        },
        "selection_rows": selection_rows,
        "private_rows": private_rows,
        "interpretation": (
            "Paper-aligned no-execution Best-of-N selector using generative +/- token probabilities. "
            + ("Selections are frozen; private evaluation is deferred." if args.defer_private else "Private tests follow the frozen selection only.")
        ),
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"metrics": output["metrics"], "private_evaluations": len(private_cache)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
