"""Inspect the structure of the existing reproduction records (read-only)."""
import json
from pathlib import Path

ROOT = Path(r"D:\yaorz\research\decomposition-bench")

fb = ROOT / "data/processed/feedback_records_apps_train_intro50_qwen3b_seed42.jsonl"
gen = ROOT / "outputs/generations/baseline_candidates_apps_train_intro50_qwen3b_seed42.json"

print("=== feedback jsonl ===")
with fb.open(encoding="utf-8") as fh:
    first = json.loads(fh.readline())
print("keys:", list(first.keys()))
for k, v in first.items():
    s = json.dumps(v, ensure_ascii=False)
    print(f"  {k}: {type(v).__name__} len={len(s)} -> {s[:160]}")

n = sum(1 for _ in fb.open(encoding="utf-8"))
print("lines:", n)

print("\n=== generations json ===")
data = json.loads(gen.read_text(encoding="utf-8"))
print("type:", type(data).__name__)
if isinstance(data, dict):
    print("top keys:", list(data.keys())[:10])
    sample_key = next(iter(data))
    sample = data[sample_key]
    print("sample key:", sample_key, "type:", type(sample).__name__)
    if isinstance(sample, dict):
        print("sample keys:", list(sample.keys()))
        for k, v in sample.items():
            s = json.dumps(v, ensure_ascii=False)
            print(f"  {k}: {type(v).__name__} len={len(s)} -> {s[:160]}")
    elif isinstance(sample, list):
        print("len:", len(sample))
        print("elem keys:", list(sample[0].keys()))
