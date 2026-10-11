"""调用完成时点的规范增量；允许生成器报告，拒绝延迟清理。"""

import argparse
import json
from pathlib import Path
import subprocess
import sys


def evaluate(workspace, organization):
    sys.path.insert(0, str(workspace))
    from cachetools import Cache, TTLCache
    import cachetools
    if not Path(cachetools.__file__).resolve().is_relative_to(workspace):
        raise RuntimeError("目标工作区导入错误")
    cache = TTLCache(maxsize=10, ttl=4, timer=lambda: 0)
    cache["a"] = 1
    original = TTLCache.expire

    def immediate(self, time=None):
        pairs = original(self, time)
        return (pair for pair in pairs)

    def deferred(self, time=None):
        def consume():
            yield from original(self, time)
        return consume()

    if organization != "candidate":
        TTLCache.expire = immediate if organization == "immediate" else deferred
    result = cache.expire(4)
    before = [[key, Cache.__getitem__(cache, key)] for key in Cache.__iter__(cache)]
    size_before = Cache.currsize.fget(cache)
    pairs = [[key, value] for key, value in result]
    after = [[key, Cache.__getitem__(cache, key)] for key in Cache.__iter__(cache)]
    return {"organization": organization, "returned_type": type(result).__name__, "stored_after_call": before, "size_after_call": size_before, "returned_pairs": pairs, "stored_after_consumption": after, "call_complete_cleanup_pass": before == [] and size_before == 0, "return_pass": pairs == [["a",1]], "pass": before == [] and size_before == 0 and pairs == [["a",1]], "scope": "新时点条款的公开增量，不追溯原任务，不证明全域"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--organization", choices=("candidate", "immediate", "deferred"), default="candidate")
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    workspace = args.workspace.resolve(strict=True)
    if args.worker:
        print(json.dumps(evaluate(workspace, args.organization), ensure_ascii=False))
        return
    if args.output is None or args.output.exists():
        raise ValueError("需要尚不存在的结果路径")
    proc = subprocess.run([sys.executable,"-I","-B",str(Path(__file__).resolve()),"--worker","--workspace",str(workspace),"--organization",args.organization], capture_output=True, text=True, encoding="utf-8", timeout=30)
    if proc.returncode:
        result = {"environment_error":True,"stderr":proc.stderr}
    else:
        result = json.loads(proc.stdout)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x",encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False))
    if result.get("environment_error"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
