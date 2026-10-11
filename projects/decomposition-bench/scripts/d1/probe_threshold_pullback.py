"""P62：原树先选、删除后路径与浮点除法逆谓词。"""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_threshold_pullback_v1_20261009"
TASK = ROOT / "data/processed/d1_project_initial20_v5_20261008/public/D1_B05/task.json"
CASES = [
    {"id": "positive_drop", "input": {"tree": [None, 3, 1], "factor": 2, "threshold": 5, "drop_null": True},
     "expected": {"tree": [6, 2], "matches": [{"path": [0], "value": 6}]}, "selected_original_paths": [[1]]},
    {"id": "negative_factor", "input": {"tree": [None, -2, 1, 3], "factor": -2, "threshold": -2, "drop_null": True},
     "expected": {"tree": [4, -2, -6], "matches": [{"path": [0], "value": 4}, {"path": [1], "value": -2}]},
     "selected_original_paths": [[1], [2]]},
    {"id": "zero_inclusive_bool", "input": {"tree": {"z": [None, -3, True, 5]}, "factor": 0, "threshold": 0, "drop_null": True},
     "expected": {"tree": {"z": [0, True, 0]}, "matches": [{"path": ["z", 0], "value": 0}, {"path": ["z", 2], "value": 0}]},
     "selected_original_paths": [["z", 1], ["z", 3]]},
    {"id": "zero_exclusive", "input": {"tree": [1, -2], "factor": 0, "threshold": 1},
     "expected": {"tree": [0, 0], "matches": []}, "selected_original_paths": []},
    {"id": "rounded_multiply_boundary", "input": {"tree": [None, 3], "factor": 0.1, "threshold": 0.30000000000000004, "drop_null": True},
     "expected": {"tree": [0.30000000000000004], "matches": [{"path": [0], "value": 0.30000000000000004}]},
     "selected_original_paths": [[1]], "division_prediction": "0.30000000000000004/0.1向上得到3.0000000000000004，除法谓词漏整数3"},
    {"id": "binary_exact_control", "input": {"tree": {"k": [None, 3, False]}, "factor": 0.5, "threshold": 1.5, "drop_null": True},
     "expected": {"tree": {"k": [1.5, False]}, "matches": [{"path": ["k", 0], "value": 1.5}]},
     "selected_original_paths": [["k", 1]]},
]
MATERIALIZE = '''def solve(payload):
    factor, threshold = payload.get("factor", 1), payload["threshold"]
    drop = payload.get("drop_null", False)
    def transform(node):
        if type(node) is dict:
            return {key: transform(value) for key, value in node.items() if not (drop and value is None)}
        if type(node) is list:
            return [transform(value) for value in node if not (drop and value is None)]
        return node * factor if type(node) in (int, float) else node
    tree, matches = transform(payload["tree"]), []
    def visit(node, path):
        if type(node) is dict:
            for key, value in node.items():
                visit(value, path + [key])
        elif type(node) is list:
            for index, value in enumerate(node):
                visit(value, path + [index])
        elif type(node) in (int, float) and node >= threshold:
            matches.append({"path": path, "value": node})
    visit(tree, [])
    return {"tree": tree, "matches": matches}, {"selected_result_paths": [m["path"] for m in matches]}
'''
ORIGINAL = '''def solve(payload):
    factor, threshold = payload.get("factor", 1), payload["threshold"]
    drop = payload.get("drop_null", False)
    selected = []
    def predicate(value):
        {predicate_body}
    def select(node, path):
        if type(node) is dict:
            for key, value in node.items():
                select(value, path + [key])
        elif type(node) is list:
            for index, value in enumerate(node):
                select(value, path + [index])
        elif type(node) in (int, float) and predicate(node):
            selected.append(path)
    select(payload["tree"], [])
    mappings, products = {{}}, {{}}
    def transform(node, old_path, new_path):
        if type(node) is dict:
            result = {{}}
            for key, value in node.items():
                if not (drop and value is None):
                    result[key] = transform(value, old_path + [key], new_path + [key])
            return result
        if type(node) is list:
            result = []
            for index, value in enumerate(node):
                if not (drop and value is None):
                    result.append(transform(value, old_path + [index], new_path + [len(result)]))
            return result
        if type(node) in (int, float):
            key = tuple(old_path)
            mappings[key], products[key] = new_path, node * factor
            return products[key]
        return node
    tree = transform(payload["tree"], [], [])
    matches = [{{"path": mappings[tuple(path)], "value": products[tuple(path)]}} for path in selected]
    return {{"tree": tree, "matches": matches}}, {{"selected_original_paths": selected,
            "selected_result_paths": [m["path"] for m in matches],
            "selection_happened_before_tree_transformation": True}}
'''
PRODUCT = "return value * factor >= threshold"
DIVIDE = '''if factor > 0:
            return value >= threshold / factor
        if factor < 0:
            return value <= threshold / factor
        return 0 >= threshold'''
PROGRAMS = {"materialize_then_scan": MATERIALIZE,
            "original_product_predicate": ORIGINAL.format(predicate_body=PRODUCT),
            "original_division_predicate": ORIGINAL.format(predicate_body=DIVIDE)}


def save(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def worker():
    frozen = json.loads((OUT / "six_anchors_and_three_programs_frozen.json").read_text(encoding="utf-8"))
    rows = []
    for name, program in frozen["programs"].items():
        scope = {}
        exec(compile(program, name + ".py", "exec"), scope)
        for case in frozen["cases"]:
            payload = copy.deepcopy(case["input"])
            before = copy.deepcopy(payload)
            output, trace = scope["solve"](payload)
            rows.append({"program": name, "id": case["id"], "output": output, "trace": trace,
                         "diagnostic_pass": output == case["expected"], "input_unchanged": payload == before})
    boundary = frozen["cases"][4]["input"]
    print(json.dumps({"rows": rows, "solve_calls": len(rows),
                      "boundary_arithmetic": {"product": 3 * boundary["factor"],
                                              "inverse_threshold": boundary["threshold"] / boundary["factor"],
                                              "product_predicate": 3 * boundary["factor"] >= boundary["threshold"],
                                              "division_predicate": 3 >= boundary["threshold"] / boundary["factor"]}}, ensure_ascii=False))


def main():
    if "--worker" in sys.argv:
        worker()
        return
    OUT.mkdir(exist_ok=False)
    save("six_anchors_and_three_programs_frozen.json", {
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "cases": CASES,
        "programs": PROGRAMS, "predicted_scores": {"materialize_then_scan": 6, "original_product_predicate": 6, "original_division_predicate": 5},
        "predicted_division_failure": "rounded_multiply_boundary",
        "source_hashes": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in (TASK, Path(__file__))},
        "contract_origin": "原B05公开乘后谓词/删除后的结果路径；程序角色独立登记",
        "necessity_scope": "外部乘法数值和输出路径必须符合，未限定先物化后筛选算法",
        "limits": "六新手算诊断；两原树方案共享变换/映射，只换谓词；非独立oracle/模型结果/原评分"})
    proc = subprocess.run([sys.executable, "-B", "-X", "utf8", str(Path(__file__).resolve()), "--worker"],
                          cwd=ROOT, capture_output=True, timeout=20)
    with (OUT / "worker.stdout.txt").open("xb") as handle:
        handle.write(proc.stdout)
    with (OUT / "worker.stderr.txt").open("xb") as handle:
        handle.write(proc.stderr)
    if proc.returncode or len(proc.stdout) > 1048576:
        raise RuntimeError("新诊断失败/过限，原输出保留")
    result = json.loads(proc.stdout.decode("utf-8"))
    save("three_execution_results.json", result)
    scores = {name: sum(r["diagnostic_pass"] for r in result["rows"] if r["program"] == name) for name in PROGRAMS}
    selected_matches = sum(r["trace"].get("selected_original_paths") == case["selected_original_paths"]
                           for r in result["rows"] if r["program"] == "original_product_predicate"
                           for case in CASES if r["id"] == case["id"])
    summary = {"new_inputs": 6, "new_solve_calls": result["solve_calls"], "scores_out_of_six": scores,
               "original_product_selection_trace_matches": [selected_matches, 6],
               "division_failed_ids": [r["id"] for r in result["rows"] if r["program"] == "original_division_predicate" and not r["diagnostic_pass"]],
               "boundary_arithmetic": result["boundary_arithmetic"], "input_unchanged": all(r["input_unchanged"] for r in result["rows"]),
               "predictions_all_match": scores == {"materialize_then_scan": 6, "original_product_predicate": 6, "original_division_predicate": 5},
               "model_calls": 0, "private_reads": 0, "original_test_runs": 0,
               "conclusion": "原树先选用实际乘积谓词与原—新路径映射可以满足本六例；浮点除法阈值逆变换不普遍等价",
               "limits": "手工构造/同助手有限诊断，不推模型失败根因/所有逆变换/最优拆法，不改旧标签/评分"}
    save("summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
