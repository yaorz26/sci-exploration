"""P63：第二来源上下界功能的公开研究池候选；不读取来源测试。"""
from __future__ import annotations

import ast
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = ROOT / "data/raw/d1_project_v1_20261008/repositories/more_itertools"
SOURCE_MANIFEST = ROOT / "data/raw/d1_project_v1_20261008/manifests/more_itertools.json"
OUT = ROOT / "experiments/d1_second_source_extrema_v1_20261009"
CASES = [
    {"id": "lower0_upper2", "input": {"data": [0, 2]}, "expected": {"value": {"minimum": 0, "maximum": 2}}},
    {"id": "lower1_upper2", "input": {"data": [1, 2, 2]}, "expected": {"value": {"minimum": 1, "maximum": 2}}},
    {"id": "lower0_upper3", "input": {"data": [3, 0, 2]}, "expected": {"value": {"minimum": 0, "maximum": 3}}},
    {"id": "lower1_upper3", "input": {"data": [1, 3, 2]}, "expected": {"value": {"minimum": 1, "maximum": 3}}},
    {"id": "single_negative", "input": {"data": [-4]}, "expected": {"value": {"minimum": -4, "maximum": -4}}},
    {"id": "empty_rejection", "input": {"data": []}, "expected": {"error": "ValueError"}},
]
PROGRAMS = {
    "one_pass": '''def solve(payload):
    iterator = iter(payload["data"])
    try:
        low = high = next(iterator)
    except StopIteration:
        raise ValueError("空数据") from None
    for value in iterator:
        if value < low:
            low = value
        if value > high:
            high = value
    return {"minimum": low, "maximum": high}
''',
    "two_pass": '''def solve(payload):
    data = payload["data"]
    return {"minimum": min(data), "maximum": max(data)}
''',
    "source_adapter": '''import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / "sources"))
import more_itertools

def solve(payload):
    low, high = more_itertools.minmax(payload["data"])
    return {"minimum": low, "maximum": high}
''',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    with (OUT / name).open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def worker():
    import copy
    import importlib.util
    cases = json.loads((OUT / "candidate/public_diagnostics.json").read_text(encoding="utf-8"))
    rows = []
    for name in PROGRAMS:
        spec = importlib.util.spec_from_file_location("p63_" + name, OUT / "candidate" / (name + ".py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for case in cases:
            payload = copy.deepcopy(case["input"])
            before = copy.deepcopy(payload)
            try:
                value = module.solve(payload)
                actual = {"value": json.loads(json.dumps(value, ensure_ascii=False, allow_nan=False))}
            except Exception as exc:
                actual = {"error": type(exc).__name__}
            expected = case["expected"]
            if "value" in expected:
                passed = ("value" in actual and type(actual["value"]) is dict
                          and set(actual["value"]) == {"minimum", "maximum"}
                          and all(type(v) is int for v in actual["value"].values())
                          and actual == expected)
            else:
                passed = actual == expected
            rows.append({"program": name, "id": case["id"], "actual": actual,
                         "diagnostic_pass": passed and payload == before, "input_unchanged": payload == before})
    print(json.dumps({"rows": rows, "solve_calls": len(rows), "source_minmax_calls": 6}, ensure_ascii=False))


def main():
    if "--worker" in sys.argv:
        worker()
        return
    OUT.mkdir(exist_ok=False)
    candidate = OUT / "candidate"
    candidate.mkdir()
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    source = SOURCE_ROOT / "more_itertools/more.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "minmax")
    save("public_source_and_integer_domain_frozen.json", {
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repository": manifest["repository"], "commit": manifest["commit"],
        "module_sha256": sha(source), "license_sha256": sha(SOURCE_ROOT / "LICENSE"),
        "public_function_source": ast.get_source_segment(source.read_text(encoding="utf-8"), node),
        "public_contract": "同时返回比较意义上的最小/最大；空且无default抛ValueError；key/default为上游可选；max并列未承诺first",
        "candidate_domain": "JSON精确整数列表长度<=128，不暴露key/default；空域ValueError，其他输入保证在域内",
        "implementation_vs_obligation": "来源记载单遍/少比较为实现特征；候选不把次数/复杂度作为输出要求",
        "new_solve_calls_so_far": 0, "model_calls": 0, "private_reads": 0})
    for name in ("more_itertools/more.py", "more_itertools/recipes.py", "more_itertools/__init__.py", "LICENSE"):
        origin, target = SOURCE_ROOT / name, candidate / "sources" / name
        expected = manifest["source_hashes"][name]
        if sha(origin) != expected:
            raise ValueError("固定源码与原获取manifest不同")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origin, target)
    for name, program in PROGRAMS.items():
        (candidate / (name + ".py")).write_text(program, encoding="utf-8")
    requirements = '''# E_M07：整数观测的下界与上界（研究池候选）

实现solve(payload)，payload含data精确整数列表（bool不在域内），长度至多128；字段与类型保证符合声明域。分别报告最小值minimum和最大值maximum，用于下界/上界两个用途；返回正好这两个字段，值为原整数。空列表抛ValueError，不固定消息。输入与列表次序不得改变。

内部实现、helper数量及计算次序自由，可以一遍扫描或两遍计算。这里不暴露key/default，不要求一次遍历、比较次数或渐近复杂度；这些是固定minmax实现的特征，不作为本候选义务。输入是可重复读JSON列表，不是只能消费一次的流，不能据本候选推广流语义。

来源为固定more-itertools minmax，MIT许可原文保留。转换tuple为命名JSON字段及整数域限制是显式适配；上下界用途由候选表述，不冒称完整库API/项目集成。六诊断全部公开，来源/两个手写结构不是三独立oracle；结构标签/正式切分null，人工0/未正式冻结/未发布，不并入原20题。
'''
    (candidate / "requirements.md").write_text(requirements, encoding="utf-8")
    task = {"task_id": "E_M07", "title": "整数上下界报告", "requirements": "requirements.md",
            "diagnostics": "public_diagnostics.json", "entry": "solve(payload)",
            "source": {"repository": manifest["repository"], "commit": manifest["commit"], "module_sha256": sha(source),
                       "license": "MIT", "license_sha256": sha(SOURCE_ROOT / "LICENSE"), "license_file": "sources/LICENSE"},
            "labels": {"dependency": None, "state_scope": None, "testability": None}, "formal_split": None,
            "human_reviews": 0, "source_contamination": "未知", "status": "研究池公开候选，未正式冻结/不改原储备",
            "family_relation": "同more-itertools来源及迭代工具关联，不是第五独立来源；未称与E_M06统计独立"}
    for name, value in (("task.json", task), ("public_diagnostics.json", CASES)):
        with (candidate / name).open("x", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
    save("six_cases_and_three_programs_frozen.json", {
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "cases": CASES, "programs": PROGRAMS,
        "predictions_out_of_six": {name: 6 for name in PROGRAMS}, "solve_upper_limit": 18,
        "hashes": {str(path.relative_to(ROOT)): sha(path) for path in (source, SOURCE_MANIFEST, Path(__file__))},
        "valid_use_grid": "minimum0/1与maximum2/3四格；极值共同使用同一有效列表，非算法/统计独立"})
    proc = subprocess.run([sys.executable, "-B", "-X", "utf8", str(Path(__file__).resolve()), "--worker"],
                          cwd=ROOT, capture_output=True, timeout=20)
    with (OUT / "worker.stdout.txt").open("xb") as handle:
        handle.write(proc.stdout)
    with (OUT / "worker.stderr.txt").open("xb") as handle:
        handle.write(proc.stderr)
    if proc.returncode or len(proc.stdout) > 1048576:
        raise RuntimeError("新来源诊断失败/过限，输出保留")
    result = json.loads(proc.stdout.decode("utf-8"))
    save("three_execution_results.json", result)
    scores = {name: sum(row["diagnostic_pass"] for row in result["rows"] if row["program"] == name) for name in PROGRAMS}
    summary = {"new_inputs": 6, "new_solve_calls": result["solve_calls"], "source_minmax_calls": result["source_minmax_calls"],
               "scores_out_of_six": scores, "predictions_all_match": all(value == 6 for value in scores.values()),
               "source_hash_matches_original_manifest": True, "model_calls": 0, "private_reads": 0, "human_reviews": 0,
               "candidate": "E_M07另池公开候选，标签/切分null、不改原20或储备",
               "conclusion": "第二来源公开上下界契约允许两遍与一遍算法，非缓存/非操作历史任务机会获六锚点支持",
               "limits": "共同输入域/有限公开例/同助手预期；不证明比较支撑解除或新独立来源，不支持单次流输入",
               "next": "公开docstring的key并列不承诺first，检验若扩key=abs是否会将合法输出差异误记错误"}
    save("summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
