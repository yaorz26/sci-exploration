"""Train a small QLoRA sequence scorer on CodePRM step records.

The script trains a scalar sequence-classification head with LoRA and MSE
labels. It supports both the historical candidate-level proxy records and the
continuation-level records, with the latter selected by ``--label-field
step_label``.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from torch.utils.data import DataLoader
from transformers import AutoModelForSequenceClassification, AutoTokenizer, BitsAndBytesConfig


def read_records(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def format_text(row: dict) -> str:
    return (
        "<problem>\n" + str(row.get("problem", "")) + "\n</problem>\n"
        "<thought>\n" + str(row.get("thought_prefix", row.get("thought_step", ""))) + "\n</thought>\n"
        "<code>\n" + str(row.get("code", "")) + "\n</code>\n"
        "<public_feedback>\n" + json.dumps(row.get("public_feedback", {}), ensure_ascii=False) + "\n</public_feedback>"
    )


def make_split(records: list[dict], train_fraction: float) -> tuple[list[dict], list[dict]]:
    problem_ids = []
    for row in records:
        if row["problem_id"] not in problem_ids:
            problem_ids.append(row["problem_id"])
    cutoff = max(1, int(len(problem_ids) * train_fraction))
    train_ids = set(problem_ids[:cutoff])
    return [row for row in records if row["problem_id"] in train_ids], [row for row in records if row["problem_id"] not in train_ids]


class TextDataset(torch.utils.data.Dataset):
    def __init__(self, records: list[dict], tokenizer, max_length: int, label_field: str):
        self.records = records
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.label_field = label_field

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        row = self.records[index]
        encoded = self.tokenizer(
            format_text(row),
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt",
        )
        return {
            "input_ids": encoded["input_ids"].squeeze(0),
            "attention_mask": encoded["attention_mask"].squeeze(0),
            "labels": torch.tensor(float(row[self.label_field]), dtype=torch.float32),
        }


def predict_scores(logits: torch.Tensor, activation: str) -> torch.Tensor:
    return torch.sigmoid(logits) if activation == "sigmoid" else logits


def evaluate(model, loader, device, activation: str) -> dict[str, float]:
    model.eval()
    values = []
    with torch.no_grad():
        for batch in loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            logits = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"]).logits.squeeze(-1)
            logits = predict_scores(logits, activation)
            labels = batch["labels"]
            values.extend((logits.float().cpu() - labels.float().cpu()).tolist())
    model.train()
    if not values:
        return {"mse": 0.0, "mae": 0.0}
    return {"mse": sum(value * value for value in values) / len(values), "mae": sum(abs(value) for value in values) / len(values)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--max-steps", type=int, default=0)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--label-field", default="label", choices=["label", "step_label", "binary_label", "binary_step_label"])
    parser.add_argument("--score-activation", default="linear", choices=["linear", "sigmoid"])
    parser.add_argument("--loss", default="mse", choices=["mse", "bce"])
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for the neural pilot")

    records = read_records(Path(args.data))
    train_records, test_records = make_split(records, 0.75)
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_path,
        local_files_only=True,
        num_labels=1,
        quantization_config=quantization,
        device_map="auto",
        dtype=torch.float16,
        trust_remote_code=True,
    )
    model.config.pad_token_id = tokenizer.pad_token_id
    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(
        model,
        LoraConfig(
            r=8,
            lora_alpha=16,
            lora_dropout=0.05,
            bias="none",
            task_type="SEQ_CLS",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
            modules_to_save=["score"],
        ),
    )
    model.train()
    device = next(model.parameters()).device
    train_loader = DataLoader(TextDataset(train_records, tokenizer, args.max_length, args.label_field), batch_size=args.batch_size, shuffle=True)
    test_loader = DataLoader(TextDataset(test_records, tokenizer, args.max_length, args.label_field), batch_size=args.batch_size, shuffle=False)
    optimizer = torch.optim.AdamW((parameter for parameter in model.parameters() if parameter.requires_grad), lr=args.learning_rate)
    steps = 0
    optimizer.zero_grad(set_to_none=True)
    for _ in range(args.epochs):
        for batch_index, batch in enumerate(train_loader):
            batch = {key: value.to(device) for key, value in batch.items()}
            logits = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"]).logits.squeeze(-1)
            if args.loss == "bce":
                loss = torch.nn.functional.binary_cross_entropy_with_logits(logits.float(), batch["labels"].float())
            else:
                scores = predict_scores(logits, args.score_activation)
                loss = torch.nn.functional.mse_loss(scores.float(), batch["labels"].float())
            loss = loss / args.gradient_accumulation
            loss.backward()
            if (batch_index + 1) % args.gradient_accumulation == 0:
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                steps += 1
                print(json.dumps({"step": steps, "loss": float(loss.detach().cpu())}), flush=True)
                if args.max_steps and steps >= args.max_steps:
                    break
        if args.max_steps and steps >= args.max_steps:
            break
    metrics = {"train_records": len(train_records), "test_records": len(test_records), "train_problems": len({row['problem_id'] for row in train_records}), "test_problems": len({row['problem_id'] for row in test_records}), "steps": steps, "label_field": args.label_field, "score_activation": args.score_activation, "loss": args.loss, "test_error": evaluate(model, test_loader, device, args.score_activation), "exact_step_label": args.label_field in {"step_label", "binary_step_label"}}
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    (output_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
