"""P57：整体排序、局部顺序契约与多重集合契约；全新公开诊断。"""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_range_local_observability_v1_20261009"
TASK = ROOT / "data/processed/d1_project_initial20_v5_20261008/public/D1_B01/task.json"
CASES = [
    {"id": "repeated_singletons", "input": {"text": "4,1,4"}, "expanded": [4, 1, 4], "expected": [1, 4, 4]},
    {"id": "descending_overlap", "input": {"text": "3-1,2"}, "expanded": [3, 2, 1, 2], "expected": [1, 2, 2, 3]},
    {"id": "empty_segments", "input": {"text": " ,2, 1-2,, "}, "expanded": [2, 1, 2], "expected": [1, 2, 2]},
    {"id": "multichar_separators", "input": {"text": " 4::2 || 3 ", "separator": "||", "range_separator": "::"},
     "expanded": [4, 3, 2, 3], "expected": [2, 3, 3, 4]},
    {"id": "empty_text", "input": {"text": ""}, "expanded": [], "expected": []},
    {"id": "zero_and_single_point", "input": {"text": "0,0,2-2"}, "expanded": [0, 0, 2], "expected": [0, 0, 2]},
    {"id": "invalid_middle", "input": {"text": "1,x,2"}, "expected_exception": "ValueError"},
    {"id": "invalid_range_tail", "input": {"text": "3-1,2-q"}, "expected_exception": "ValueError"},
]
BASE = '''def expand(payload):
    values = []
    separator = payload.get("separator", ",")
    range_separator = payload.get("range_separator", "-")
    for piece in payload["text"].split(separator):
        piece = piece.strip()
        if not piece:
            continue
        parts = piece.split(range_separator)
        if len(parts) == 1:
            values.append(int(parts[0]))
        elif len(parts) == 2:
            left, right = int(parts[0]), int(parts[1])
            step = 1 if right >= left else -1
            values.extend(range(left, right + step, step))
        else:
            raise ValueError("非法区间")
    {return_statement}

def solve(payload):
    return sorted(expand(payload))
'''
PROGRAMS = {
    "input_order": BASE.format(return_statement="return values"),
    "reversed_order": BASE.format(return_statement="return values[::-1]"),
    "deduplicate_wrong": BASE.format(return_statement="return list(dict.fromkeys(values))"),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def read(name):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def worker():
    frozen = read("eight_anchors_and_programs_frozen.json")
    rows = []
    for name, program in frozen["programs"].items():
        scope = {}
        exec(compile(program, name + ".py", "exec"), scope)
        target = scope["expand"].__code__
        for case in frozen["cases"]:
            payload = copy.deepcopy(case["input"])
            before = copy.deepcopy(payload)
            calls, returns = [], []

            def profile(frame, event, arg):
                if frame.f_code is target:
                    if event == "call":
                        calls.append("expand")
                    elif event == "return":
                        returns.append(copy.deepcopy(arg))

            output, error = None, None
            sys.setprofile(profile)
            try:
                output = scope["solve"](payload)
            except Exception as exc:
                error = type(exc).__name__
            finally:
                sys.setprofile(None)
            valid = "expected_exception" not in case
            if valid:
                local = returns[0] if len(returns) == 1 else None
                strong = local == case["expanded"]
                weak = isinstance(local, list) and all(type(v) is int for v in local) and sorted(local) == case["expected"]
                whole = error is None and isinstance(output, list) and all(type(v) is int for v in output) and output == case["expected"]
            else:
                strong = weak = None
                whole = error == case["expected_exception"]
            rows.append({"program": name, "id": case["id"], "valid_input": valid,
                         "output": output, "exception": error, "diagnostic_whole_pass": whole,
                         "strong_local_order_pass": strong, "weak_local_multiset_pass": weak,
                         "helper_calls": len(calls), "captured_helper_returns": returns,
                         "local_not_observable_due_to_exception": not valid and error is not None,
                         "input_unchanged": payload == before})
    print(json.dumps({"rows": rows, "solve_calls": len(rows),
                      "helper_calls": sum(r["helper_calls"] for r in rows),
                      "valid_local_returns": sum(r["valid_input"] and r["exception"] is None for r in rows)}, ensure_ascii=False))


def main():
    if "--worker" in sys.argv:
        worker()
        return
    OUT.mkdir(exist_ok=False)
    save("eight_anchors_and_programs_frozen.json", {
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "task_sha256": sha(TASK), "script_sha256": sha(Path(__file__)),
        "cases": CASES, "programs": PROGRAMS,
        "predictions": {"input_order": {"valid_whole": 6, "invalid_exception": 2, "strong": 6, "weak": 6},
                        "reversed_order": {"valid_whole": 6, "invalid_exception": 2, "strong": 3, "weak": 6},
                        "deduplicate_wrong": {"valid_whole": 1, "invalid_exception": 2, "strong": 1, "weak": 1}},
        "contracts": {"strong": "按原片段顺序与区间方向展开的具体序列，不是原任务规定的helper规则",
                      "weak": "与原区间/数值展开有相同整数多重集合，无顺序义务",
                      "whole": "手算诊断精确整数列表或ValueError，不调用原评分器/原测试"},
        "limits": "三结构共享解析基础，非独立oracle；八输入全部公开、初标未改、人工/模型0"})
    proc = subprocess.run([sys.executable, "-B", "-X", "utf8", str(Path(__file__).resolve()), "--worker"],
                          cwd=ROOT, capture_output=True, timeout=20)
    (OUT / "worker.stdout.txt").write_bytes(proc.stdout)
    (OUT / "worker.stderr.txt").write_bytes(proc.stderr)
    if proc.returncode or len(proc.stdout) > 1048576:
        raise RuntimeError("诊断进程失败或输出超过上限；原始输出已保留")
    result = json.loads(proc.stdout.decode("utf-8"))
    save("execution_result.json", result)
    summary = {"solve_calls": result["solve_calls"], "helper_calls": result["helper_calls"],
               "valid_local_returns": result["valid_local_returns"], "programs": {},
               "input_unchanged": all(r["input_unchanged"] for r in result["rows"]),
               "model_calls": 0, "private_reads": 0, "source_calls": 0,
               "whole_measurement": "新手算诊断，不是原数据集评分结果", "predictions_all_match": True}
    for name in PROGRAMS:
        rows = [r for r in result["rows"] if r["program"] == name]
        counts = {"valid_whole": sum(r["valid_input"] and r["diagnostic_whole_pass"] for r in rows),
                  "invalid_exception": sum(not r["valid_input"] and r["diagnostic_whole_pass"] for r in rows),
                  "strong": sum(r["strong_local_order_pass"] is True for r in rows),
                  "weak": sum(r["weak_local_multiset_pass"] is True for r in rows)}
        summary["programs"][name] = counts
        summary["predictions_all_match"] &= counts == read("eight_anchors_and_programs_frozen.json")["predictions"][name]
    summary["conclusion"] = "排序保留数值多重集合但隐藏展开顺序；强局部契约可拒整体合法方案，弱契约检出去重；异常例局部返回不可观察"
    save("summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
