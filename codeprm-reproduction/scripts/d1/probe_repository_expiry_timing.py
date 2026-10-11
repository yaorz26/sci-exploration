"""只检验生成器报告与实际清理时点，一fresh场景两组织。"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "experiments/d1_cache_expiry_repository_task_v1_20261009/feature/src"
OUT = ROOT / "experiments/d1_repository_expiry_timing_v1_20261009"
OUT.mkdir(exist_ok=False)
worker = OUT / "run_one.py"
worker.write_text('''import json
from pathlib import Path
import sys

sys.path.insert(0, sys.argv[1])
from cachetools import Cache, TTLCache
original = TTLCache.expire

class Clock:
    def __call__(self):
        return 0

def immediate(self, time=None):
    pairs = original(self, time)
    return (pair for pair in pairs)

def deferred(self, time=None):
    def consume():
        yield from original(self, time)
    return consume()

cache = TTLCache(maxsize=10, ttl=4, timer=Clock())
cache['a'] = 1
TTLCache.expire = immediate if sys.argv[2] == 'immediate' else deferred
returned = cache.expire(4)
before = [[key, Cache.__getitem__(cache, key)] for key in Cache.__iter__(cache)]
pairs = [[key, value] for key, value in returned]
after = [[key, Cache.__getitem__(cache, key)] for key in Cache.__iter__(cache)]
print(json.dumps({'organization':sys.argv[2], 'returned_type':type(returned).__name__, 'stored_after_call_before_consumption':before, 'returned_pairs':pairs, 'stored_after_consumption':after, 'post_consumption_observation_accepts':pairs == [['a',1]] and after == []}, ensure_ascii=False))
''', encoding="utf-8")
with (OUT / "freeze_before_execution.json").open("x", encoding="utf-8") as handle:
    json.dump({"created_at": datetime.now(timezone.utc).isoformat(), "worker_sha256": hashlib.sha256(worker.read_bytes()).hexdigest(), "source_sha256": hashlib.sha256((SOURCE / "cachetools/__init__.py").read_bytes()).hexdigest(), "input": {"timer": 0, "ttl": 4, "put": ["a",1], "expire_time": 4}, "prediction": {"immediate": "调用后空，消费后空，返回a", "deferred": "调用后a仍在，消费后空，返回a"}, "scope": "生成器类型相同，仅清理时点不同；不追溯改旧规范/分母"}, handle, ensure_ascii=False, indent=2)
rows = []
for name in ("immediate", "deferred"):
    proc = subprocess.run([sys.executable,"-I","-B",str(worker),str(SOURCE),name], capture_output=True, text=True, encoding="utf-8", timeout=30)
    if proc.returncode:
        raise RuntimeError(proc.stderr)
    row = json.loads(proc.stdout)
    with (OUT / (name + "_actual.json")).open("x", encoding="utf-8") as handle:
        json.dump(row, handle, ensure_ascii=False, indent=2)
    rows.append(row)
with (OUT / "summary.json").open("x", encoding="utf-8") as handle:
    json.dump({"rows": rows, "unique_new_inputs": 1, "programs": 2, "model_calls": 0, "human_reviews": 0, "conclusion": "消费后观察接纳两者，但调用后真实存储不同；原需求时点未明确，不能直接认延迟版为原题错误"}, handle, ensure_ascii=False, indent=2)
print(json.dumps(rows, ensure_ascii=False, indent=2))
