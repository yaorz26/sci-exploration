"""Audit untruncated token lengths for frozen generative FunPRM training rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from transformers import AutoTokenizer

from scripts.funprm_generative_common import render_prompt


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def percentile(values: list[int], probability: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(ordered[lower])
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    data_path = Path(args.data)
    output_path = Path(args.output)
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite {output_path}")
    rows = read_jsonl(data_path)
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True, trust_remote_code=True)
    lengths = [
        len(tokenizer(render_prompt(tokenizer, str(row["problem"]), str(row["prefix_code"])), add_special_tokens=False)["input_ids"])
        for row in rows
    ]
    output = {
        "data": str(data_path),
        "data_sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
        "model_path": args.model_path,
        "records": len(rows),
        "minimum": min(lengths),
        "median": percentile(lengths, 0.5),
        "p75": percentile(lengths, 0.75),
        "p90": percentile(lengths, 0.9),
        "p95": percentile(lengths, 0.95),
        "maximum": max(lengths),
        "over_512": sum(length > 512 for length in lengths),
        "over_768": sum(length > 768 for length in lengths),
        "over_1024": sum(length > 1024 for length in lengths),
        "lengths": lengths,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: output[key] for key in [
        "records", "minimum", "median", "p75", "p90", "p95", "maximum", "over_512", "over_768", "over_1024",
    ]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
