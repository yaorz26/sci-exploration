"""过期返回信息与底层清理的公开项目行为评价器。"""

import argparse
import json
from pathlib import Path
import platform
import subprocess
import sys


def evaluate(workspace):
    sys.path.insert(0, str(workspace))
    from cachetools import Cache, TTLCache
    import cachetools
    if not Path(cachetools.__file__).resolve().is_relative_to(workspace):
        raise RuntimeError("导入不属于目标工作区")

    class Clock:
        value = 0
        def __call__(self):
            return self.value

    scenarios = [
        {"name": "empty", "puts": [], "time": 4, "returns": [[]], "stored": []},
        {"name": "boundary_mixed", "puts": [[0, "a", 1], [2, "b", 2]], "time": 4, "returns": [[["a", 1]]], "stored": [["b", 2]]},
        {"name": "repeat", "puts": [[0, "a", 1]], "time": 4, "returns": [[["a", 1]], []], "stored": []},
        {"name": "same_deadline", "puts": [[0, "a", 1], [0, "b", 2]], "time": 4, "returns": [[["a", 1], ["b", 2]]], "stored": []},
        {"name": "insertion_cleanup", "puts": [[0, "a", 1], [4, "b", 2]], "time": 4, "returns": [[]], "stored": [["b", 2]]},
    ]
    rows = []
    for scenario in scenarios:
        clock = Clock()
        cache = TTLCache(maxsize=20, ttl=4, timer=clock, getsizeof=lambda value: 2)
        try:
            for time, key, value in scenario["puts"]:
                clock.value = time
                cache[key] = value
            outputs = []
            for unused in scenario["returns"]:
                returned = cache.expire(scenario["time"])
                try:
                    pairs = [[key, value] for key, value in returned]
                    pairs.sort(key=lambda pair: pair[0])
                    outputs.append(pairs)
                except (TypeError, ValueError) as exc:
                    outputs.append({"invalid_iterable": type(returned).__name__, "exception": type(exc).__name__})
            # 不触发TTL的len/items/currsize，基类公开接口观察实际存储。
            stored = sorted([[key, Cache.__getitem__(cache, key)] for key in Cache.__iter__(cache)], key=lambda pair: pair[0])
            currsize = Cache.currsize.fget(cache)
            expected_size = 2 * len(scenario["stored"])
            return_ok = outputs == scenario["returns"]
            state_ok = stored == scenario["stored"] and currsize == expected_size
            rows.append({"case": scenario["name"], "expected_returns": scenario["returns"], "actual_returns": outputs, "expected_stored": scenario["stored"], "actual_stored": stored, "expected_size": expected_size, "actual_size": currsize, "return_pass": return_ok, "state_pass": state_ok, "pass": return_ok and state_ok})
        except Exception as exc:
            rows.append({"case": scenario["name"], "exception": type(exc).__name__, "message": str(exc), "return_pass": False, "state_pass": False, "pass": False})
    return {"workspace": str(workspace), "python": platform.python_version(), "cases": rows, "passed": sum(row["pass"] for row in rows), "return_passed": sum(row["return_pass"] for row in rows), "state_passed": sum(row["state_pass"] for row in rows), "total": len(rows), "scope": "公开确定性项目诊断，不要求返回顺序/列表类型，非模型/人工/未见确认"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    workspace = args.workspace.resolve(strict=True)
    if args.worker:
        print(json.dumps(evaluate(workspace), ensure_ascii=False))
        return
    if args.output is None:
        parser.error("需要保存实际结果的新output路径")
    if args.output.exists():
        raise FileExistsError(args.output)
    proc = subprocess.run([sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--worker", "--workspace", str(workspace)], capture_output=True, text=True, encoding="utf-8", timeout=30)
    result = json.loads(proc.stdout) if proc.returncode == 0 else {"environment_error": True, "stderr": proc.stderr, "returncode": proc.returncode}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps({key: result.get(key) for key in ("passed", "return_passed", "state_passed", "total", "environment_error")}, ensure_ascii=False))
    if result.get("environment_error"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
