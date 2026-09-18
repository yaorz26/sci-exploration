"""Run the minimal local 3B QLoRA forward/backward smoke test."""

from __future__ import annotations

import os
import sys

import torch
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


def main() -> None:
    model_id = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("MODEL_PATH")
    if not model_id:
        raise SystemExit("usage: neural_smoke.py MODEL_PATH")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available")

    tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=True, trust_remote_code=True)
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        local_files_only=True,
        quantization_config=quantization,
        device_map="auto",
        dtype=torch.float16,
        trust_remote_code=True,
    )
    model = prepare_model_for_kbit_training(model)
    model = get_peft_model(
        model,
        LoraConfig(
            r=8,
            lora_alpha=16,
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        ),
    )
    model.train()
    text = (
        "<problem>Write a function that returns the sum of two integers.</problem>\n"
        "<thoughts>Read the two arguments and add them.</thoughts>\n"
        "<code>def solve(a, b): return a + b</code>"
    )
    batch = tokenizer(text, return_tensors="pt").to(model.device)
    output = model(**batch, labels=batch["input_ids"])
    output.loss.backward()
    print({
        "status": "passed",
        "model_path": model_id,
        "torch": torch.__version__,
        "cuda": torch.cuda.get_device_name(0),
        "loss": float(output.loss.detach().cpu()),
        "trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad),
        "memory_allocated": torch.cuda.memory_allocated(),
        "memory_reserved": torch.cuda.memory_reserved(),
        "memory_free_total": torch.cuda.mem_get_info(),
    })


if __name__ == "__main__":
    main()
