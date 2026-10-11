"""P90调用完成契约的公开API评价；不固定Cache基类的存储所有权。"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

SCENARIOS = [
    {"name": "empty", "puts": [], "time": 4, "returns": [[]], "stored": []},
    {"name": "boundary_mixed", "puts": [[0, "a", 1], [2, "b", 2]], "time": 4, "returns": [[["a", 1]]], "stored": [["b", 2]]},
    {"name": "repeat", "puts": [[0, "a", 1]], "time": 4, "returns": [[["a", 1]], []], "stored": []},
    {"name": "same_deadline", "puts": [[0, "a", 1], [0, "b", 2]], "time": 4, "returns": [[["a", 1], ["b", 2]]], "stored": []},
    {"name": "insertion_cleanup", "puts": [[0, "a", 1], [4, "b", 2]], "time": 4, "returns": [[]], "stored": [["b", 2]]},
]


def evaluate(workspace):
    sys.path.insert(0, str(workspace))
    import cachetools
    from cachetools import TTLCache
    if not Path(cachetools.__file__).resolve().is_relative_to(workspace):
        raise RuntimeError("目标工作区导入错误")
    class Clock:
        value = 0
        def __call__(self):
            return self.value
    rows = []
    for scenario in SCENARIOS:
        clock = Clock()
        row = {"case": scenario["name"], "calls": [], "return_pass": False,
               "call_complete_state_pass": False, "after_consumption_state_pass": False, "pass": False}
        try:
            cache = TTLCache(maxsize=20, ttl=4, timer=clock, getsizeof=lambda value: 2)
            for when, key, value in scenario["puts"]:
                clock.value = when
                cache[key] = value
            expected = {"items": scenario["stored"], "length": len(scenario["stored"]),
                        "size": 2 * len(scenario["stored"])}
            def snapshot():
                keys = list(cache)
                return {"items": sorted([[key, cache[key]] for key in keys]),
                        "length": len(cache), "size": cache.currsize}
            for expected_pairs in scenario["returns"]:
                result = cache.expire(scenario["time"])
                before = snapshot()
                pairs = sorted([[key, value] for key, value in result])
                after = snapshot()
                row["calls"].append({"observation_timer": clock.value, "explicit_expire_time": scenario["time"],
                    "before_consumption": before, "after_consumption": after,
                    "returned_pairs": pairs, "expected_pairs": expected_pairs,
                    "return_pass": pairs == expected_pairs, "call_complete_state_pass": before == expected,
                    "after_consumption_state_pass": after == expected})
            for field in ("return_pass", "call_complete_state_pass", "after_consumption_state_pass"):
                row[field] = all(call[field] for call in row["calls"])
            row["pass"] = all(row[field] for field in ("return_pass", "call_complete_state_pass", "after_consumption_state_pass"))
        except Exception as exc:
            row.update(exception=type(exc).__name__, message=str(exc))
        rows.append(row)
    return {"cases": rows, "passed": sum(row["pass"] for row in rows), "total": len(rows),
            "all_pass": all(row["pass"] for row in rows),
            "return_passed": sum(row["return_pass"] for row in rows),
            "call_complete_state_passed": sum(row["call_complete_state_pass"] for row in rows),
            "scope": "原五公开输入/P90时点规范；公开API状态观察，不约束存储位置；非全域物理证明/隐藏确认"}


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
    if args.output is None or args.output.exists():
        raise ValueError("需要独占新output")
    proc = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(Path(__file__)),
                          "--worker", "--workspace", str(workspace)], capture_output=True,
                          text=True, encoding="utf-8", timeout=10)
    result = json.loads(proc.stdout) if proc.returncode == 0 else {"environment_error": True,
                "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps({key: result.get(key) for key in ("passed", "total", "all_pass", "environment_error")}, ensure_ascii=False))
    if result.get("environment_error"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
