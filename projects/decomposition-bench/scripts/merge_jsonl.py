"""Merge JSONL files while preserving record order and UTF-8 content."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    lines = []
    for item in args.inputs:
        source = Path(item)
        lines.extend(line for line in source.read_text(encoding="utf-8").splitlines() if line.strip())
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print({"output": str(target), "records": len(lines), "inputs": args.inputs})


if __name__ == "__main__":
    main()
