"""Train a QLoRA generative FunPRM using soft +/- reward-token targets."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

import torch
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from scripts.funprm_generative_common import (
    positive_probability,
    render_prompt,
    reward_logits,
    reward_token_ids,
    soft_binary_loss,
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def split_by_problem(rows: list[dict[str, Any]], fraction: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    problem_ids = sorted({str(row["problem_id"]) for row in rows})
    cutoff = max(1, min(len(problem_ids) - 1, int(len(problem_ids) * fraction)))
    train_ids = set(problem_ids[:cutoff])
    return [row for row in rows if str(row["problem_id"]) in train_ids], [row for row in rows if str(row["problem_id"]) not in train_ids]


class RewardDataset(Dataset):
    def __init__(self, rows: list[dict[str, Any]], tokenizer: Any, max_length: int):
        self.rows = rows
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        row = self.rows[index]
        prompt = render_prompt(self.tokenizer, str(row.get("problem", "")), str(row.get("prefix_code", "")))
        encoded = self.tokenizer(
            prompt,
            truncation=True,
            max_length=self.max_length,
            # Batch size is one, so fixed-length padding only wastes compute.
            padding=False,
            return_tensors="pt",
        )
        return {
            "input_ids": encoded["input_ids"].squeeze(0),
            "attention_mask": encoded["attention_mask"].squeeze(0),
            "labels": torch.tensor(float(row["label"]), dtype=torch.float32),
        }


def evaluate(model: Any, loader: DataLoader, device: torch.device, plus_id: int, minus_id: int) -> dict[str, float]:
    model.eval()
    errors: list[float] = []
    with torch.no_grad():
        for batch in loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            scores = positive_probability(reward_logits(model, batch["input_ids"], batch["attention_mask"], plus_id, minus_id)).cpu()
            labels = batch["labels"].float().cpu()
            errors.extend((scores - labels).tolist())
    model.train()
    return {
        "mse": sum(error * error for error in errors) / len(errors) if errors else 0.0,
        "mae": sum(abs(error) for error in errors) / len(errors) if errors else 0.0,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--max-steps", type=int, default=0)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for generative FunPRM training")
    rows = read_jsonl(Path(args.data))
    train_rows, test_rows = split_by_problem(rows, 0.75)
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    tokenizer.truncation_side = "left"
    plus_id, minus_id = reward_token_ids(tokenizer)
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        local_files_only=True,
        quantization_config=quantization,
        device_map="auto",
        dtype=torch.float16,
        trust_remote_code=True,
    )
    model.config.pad_token_id = tokenizer.pad_token_id
    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(model, LoraConfig(
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    ))
    model.train()
    device = next(model.parameters()).device
    train_loader = DataLoader(RewardDataset(train_rows, tokenizer, args.max_length), batch_size=args.batch_size, shuffle=True)
    test_loader = DataLoader(RewardDataset(test_rows, tokenizer, args.max_length), batch_size=args.batch_size, shuffle=False)
    optimizer = torch.optim.AdamW((parameter for parameter in model.parameters() if parameter.requires_grad), lr=args.learning_rate, weight_decay=1e-3)
    optimizer.zero_grad(set_to_none=True)
    steps = 0
    batches_since_step = 0
    stop = False
    for _ in range(args.epochs):
        for batch in train_loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            logits = reward_logits(model, batch["input_ids"], batch["attention_mask"], plus_id, minus_id)
            loss = soft_binary_loss(logits, batch["labels"]) / args.gradient_accumulation
            loss.backward()
            batches_since_step += 1
            if batches_since_step >= args.gradient_accumulation:
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                steps += 1
                print(json.dumps({"step": steps, "loss": float(loss.detach().cpu())}), flush=True)
                batches_since_step = 0
                if args.max_steps and steps >= args.max_steps:
                    stop = True
                    break
        if stop:
            break
    if batches_since_step and not stop:
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)
        steps += 1

    metrics = {
        "model_path": args.model_path,
        "data": args.data,
        "train_records": len(train_rows),
        "test_records": len(test_rows),
        "train_problems": len({row["problem_id"] for row in train_rows}),
        "test_problems": len({row["problem_id"] for row in test_rows}),
        "train_positive_label_mean": sum(float(row["label"]) for row in train_rows) / len(train_rows),
        "test_positive_label_mean": sum(float(row["label"]) for row in test_rows) / len(test_rows),
        "steps": steps,
        "epochs": args.epochs,
        "max_length": args.max_length,
        "reward_tokens": {"plus": plus_id, "minus": minus_id},
        "objective": "soft cross entropy over normalized +/- next-token logits",
        "test_error": evaluate(model, test_loader, device, plus_id, minus_id),
    }
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    (output_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
