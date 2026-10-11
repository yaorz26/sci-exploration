"""Train a scalar QLoRA scorer on function-node records."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer, BitsAndBytesConfig


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def format_function_node(row: dict) -> str:
    return (
        "<problem>\n" + str(row.get("problem", "")) + "\n</problem>\n"
        "<completed_functions>\n" + str(row.get("completed_functions", "")) + "\n</completed_functions>\n"
        "<current_function>\n" + str(row.get("current_function", "")) + "\n</current_function>\n"
        "<prefix_code>\n" + str(row.get("prefix_code", "")) + "\n</prefix_code>\n"
        "<public_feedback>\n" + json.dumps(row.get("public_feedback", {}), ensure_ascii=False) + "\n</public_feedback>"
    )


def split_by_problem(rows: list[dict], fraction: float) -> tuple[list[dict], list[dict]]:
    problem_ids = sorted({str(row["problem_id"]) for row in rows})
    cutoff = max(1, min(len(problem_ids) - 1, int(len(problem_ids) * fraction)))
    train_ids = set(problem_ids[:cutoff])
    return [row for row in rows if str(row["problem_id"]) in train_ids], [row for row in rows if str(row["problem_id"]) not in train_ids]


class FunctionNodeDataset(Dataset):
    def __init__(self, rows: list[dict], tokenizer, max_length: int, label_field: str):
        self.rows = rows
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.label_field = label_field

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        row = self.rows[index]
        encoded = self.tokenizer(
            format_function_node(row),
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


def score_activation(logits: torch.Tensor, activation: str) -> torch.Tensor:
    return torch.sigmoid(logits) if activation == "sigmoid" else logits


def evaluate(model, loader, device, activation: str) -> dict[str, float]:
    model.eval()
    errors: list[float] = []
    with torch.no_grad():
        for batch in loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            logits = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"]).logits.squeeze(-1)
            values = score_activation(logits, activation).float().cpu()
            labels = batch["labels"].float().cpu()
            errors.extend((values - labels).tolist())
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
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--max-steps", type=int, default=0)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--label-field", choices=["step_label", "final_label", "binary_step_label", "binary_final_label"], default="step_label")
    parser.add_argument("--score-activation", choices=["linear", "sigmoid"], default="sigmoid")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for the FunPRM scorer pilot")
    rows = read_jsonl(Path(args.data))
    train_rows, test_rows = split_by_problem(rows, 0.75)
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
    train_loader = DataLoader(FunctionNodeDataset(train_rows, tokenizer, args.max_length, args.label_field), batch_size=args.batch_size, shuffle=True)
    test_loader = DataLoader(FunctionNodeDataset(test_rows, tokenizer, args.max_length, args.label_field), batch_size=args.batch_size, shuffle=False)
    optimizer = torch.optim.AdamW((parameter for parameter in model.parameters() if parameter.requires_grad), lr=args.learning_rate)
    steps = 0
    batches_since_step = 0
    optimizer.zero_grad(set_to_none=True)
    for _ in range(args.epochs):
        for batch in train_loader:
            batch = {key: value.to(device) for key, value in batch.items()}
            logits = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"]).logits.squeeze(-1)
            scores = score_activation(logits, args.score_activation)
            loss = torch.nn.functional.mse_loss(scores.float(), batch["labels"].float()) / args.gradient_accumulation
            loss.backward()
            batches_since_step += 1
            if batches_since_step >= args.gradient_accumulation:
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                steps += 1
                print(json.dumps({"step": steps, "loss": float(loss.detach().cpu())}), flush=True)
                batches_since_step = 0
                if args.max_steps and steps >= args.max_steps:
                    break
        if batches_since_step:
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)
            steps += 1
            batches_since_step = 0
        if args.max_steps and steps >= args.max_steps:
            break

    metrics = {
        "model_path": args.model_path,
        "train_records": len(train_rows),
        "test_records": len(test_rows),
        "train_problems": len({row["problem_id"] for row in train_rows}),
        "test_problems": len({row["problem_id"] for row in test_rows}),
        "steps": steps,
        "label_field": args.label_field,
        "score_activation": args.score_activation,
        "max_length": args.max_length,
        "exact_continuation_source": True,
        "function_node_mapping_derived": True,
        "test_error": evaluate(model, test_loader, device, args.score_activation),
    }
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    (output_dir / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
