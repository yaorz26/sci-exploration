"""Record the local runtime and optional ML dependencies."""

from __future__ import annotations

import importlib.util
import json
import platform
import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    gpu = "unavailable"
    try:
        gpu = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], capture_output=True, text=True, timeout=5).stdout.strip() or gpu
    except (FileNotFoundError, subprocess.SubprocessError):
        pass
    ollama_models = []
    try:
        tags = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=10)
        ollama_models = [line.split()[0] for line in tags.stdout.splitlines()[1:] if line.split()]
    except (FileNotFoundError, subprocess.SubprocessError):
        pass
    apps_subset = root / "data" / "raw" / "apps_train_introductory20.json"
    if apps_subset.exists():
        data_status = "real APPS train introductory20 available; custom public/private split; official test path not configured"
    else:
        data_status = "offline fixture available; external APPS path not configured"
    record = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "pytorch_installed": bool(importlib.util.find_spec("torch")),
        "transformers_installed": bool(importlib.util.find_spec("transformers")),
        "datasets_installed": bool(importlib.util.find_spec("datasets")),
        "gpu": gpu,
        "ollama_models": ollama_models,
        "api_keys_present": {name: bool(__import__("os").environ.get(name)) for name in ["HF_TOKEN", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"]},
        "data_status": data_status,
        "limitations": [
            item for item in [
                "No Transformers/Datasets package detected" if not (importlib.util.find_spec("transformers") and importlib.util.find_spec("datasets")) else None,
                "No model API key detected" if not any(record for record in {name: bool(__import__("os").environ.get(name)) for name in ["OPENAI_API_KEY", "DEEPSEEK_API_KEY"]}.values()) else None,
                "Executor is timeout-bounded but not an OS security sandbox",
            ] if item
        ],
    }
    output = root / "reports" / "environment.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
