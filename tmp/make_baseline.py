import hashlib, json
from pathlib import Path
ROOT = Path(r"D:\yaorz\research")
d = ROOT / "docs" / "basic-require"
base = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(d.rglob("*")) if p.is_file()}
out = ROOT / "scripts" / "human_only_baseline.json"
out.write_text(json.dumps(base, ensure_ascii=False, indent=2), encoding="utf-8")
print("基线已写入:", out.name)
for k, v in base.items():
    print(f"  {k}  {v[:16]}…")
