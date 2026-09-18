"""Placeholder for learned PRM training; validates feedback labels for now."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/processed/feedback_records.jsonl")
    args = parser.parse_args()
    records = [json.loads(line) for line in Path(args.data).read_text(encoding="utf-8").splitlines() if line.strip()]
    labels = [float(record["label"]) for record in records]
    print({"status": "data_validated", "records": len(records), "label_min": min(labels, default=0.0), "label_max": max(labels, default=0.0), "note": "Install transformers and add a trainable backbone for learned CodePRM."})


if __name__ == "__main__":
    main()
