"""Check the train/test split and selection numbers used by the frozen diagnostic report."""
import json
from pathlib import Path

ROOT = Path(r"D:\yaorz\research\decomposition-bench")
diag = ROOT / "reports/neural_codeprm_train50_seed42_diagnostic_2026-09-05.json"
data = json.loads(diag.read_text(encoding="utf-8"))


def walk(obj, prefix="", depth=0):
    if depth > 2:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            s = json.dumps(v, ensure_ascii=False)
            print(f"{'  '*depth}{k}: {type(v).__name__} len={len(s)} -> {s[:220]}")
            if isinstance(v, (dict, list)) and len(s) < 4000:
                walk(v, prefix + k + ".", depth + 1)
    elif isinstance(obj, list) and obj:
        print(f"{'  '*depth}[list len={len(obj)}] first -> {json.dumps(obj[0], ensure_ascii=False)[:220]}")


walk(data)
