"""Materialize the deterministic 20-problem fixture as JSON."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data_loader import make_offline_problems


def main() -> None:
    problems = make_offline_problems(20)
    output = ROOT / "data" / "raw" / "offline_introductory_20.json"
    output.write_text(json.dumps(problems, ensure_ascii=False, indent=2), encoding="utf-8")
    split_output = ROOT / "data" / "splits" / "offline_introductory.json"
    split_output.write_text(json.dumps({"dataset": "APPS", "difficulty": "introductory", "train_ids": [], "test_ids": [p["problem_id"] for p in problems], "note": "Pipeline fixture only; no training/test overlap."}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {output} ({len(problems)} problems)")
    print(f"wrote {split_output}")


if __name__ == "__main__":
    main()
