"""P48：构建另池公开候选，冻结12个新锚点后做36次有界执行。"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from bounded_execution import evaluate

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_discrete_candidate_boundary_v1_20261009"
SOURCE = ROOT / "data/raw/d1_project_v1_20261008/repositories/boltons/boltons/statsutils.py"
LICENSE = SOURCE.parents[1] / "LICENSE"
SOURCE_SHA = "0c4d05a17b14244a880e5047c1823d1e1e522e6c5ee76c6b47f54d8bde791e68"

# 逐值解析，既不由Counter生成预期，也不从参考执行中抄答案。
CASES = [
    {"case_id": "mixed_integer_first", "input": {"data": [1, "1", 1, "1"]}, "expected": {"value": {"count": 4, "mode": 1}}, "reason": "整数1和字符串1各两次，整数先出现"},
    {"case_id": "mixed_string_first", "input": {"data": ["1", 1, "1", 1]}, "expected": {"value": {"count": 4, "mode": "1"}}, "reason": "各两次，字符串先出现"},
    {"case_id": "empty_bool_default", "input": {"data": [], "default": False}, "expected": {"value": {"count": 0, "mode": False}}, "reason": "空数量0，众数返回False原类型"},
    {"case_id": "empty_null_default", "input": {"data": [], "default": None}, "expected": {"value": {"count": 0, "mode": None}}, "reason": "空数量0，众数返回null"},
    {"case_id": "empty_string_default", "input": {"data": [], "default": "空"}, "expected": {"value": {"count": 0, "mode": "空"}}, "reason": "空数量0，众数返回显式字符串"},
    {"case_id": "single_string", "input": {"data": ["solo"]}, "expected": {"value": {"count": 1, "mode": "solo"}}, "reason": "唯一值频数1，无需default"},
    {"case_id": "reject_bool_item", "input": {"data": [True]}, "expected": {"error": "TypeError"}, "reason": "bool虽为int子类，契约要求精确int或str"},
    {"case_id": "reject_float_item", "input": {"data": [1.0]}, "expected": {"error": "TypeError"}, "reason": "浮点元素不在输入域"},
    {"case_id": "reject_list_item", "input": {"data": [[]]}, "expected": {"error": "TypeError"}, "reason": "列表元素不在输入域"},
    {"case_id": "reject_non_list", "input": {"data": "x"}, "expected": {"error": "TypeError"}, "reason": "data必须是列表"},
    {"case_id": "reject_missing_data", "input": {}, "expected": {"error": "ValueError"}, "reason": "缺data按本次显式适配契约拒绝"},
    {"case_id": "reject_object_default", "input": {"data": [], "default": {}}, "expected": {"error": "TypeError"}, "reason": "default只允许有限JSON标量"},
]

GUARD = '''import math

def _validate(payload):
    if type(payload) is not dict:
        raise TypeError("payload must be a plain dictionary")
    if "data" not in payload:
        raise ValueError("missing data")
    if set(payload) - {"data", "default"}:
        raise ValueError("unexpected field")
    values = payload["data"]
    if type(values) is not list:
        raise TypeError("data must be a list")
    if len(values) > 128:
        raise ValueError("data exceeds 128 items")
    if any(type(value) not in (int, str) for value in values):
        raise TypeError("data items must have exact type int or str")
    default = payload.get("default", None)
    if default is not None and type(default) not in (bool, str, int, float):
        raise TypeError("default must be a JSON scalar")
    if type(default) is float and not math.isfinite(default):
        raise ValueError("default must be finite")
    return values, default
'''

PROGRAMS = {
    "whole": GUARD + '''
def solve(payload):
    values, default = _validate(payload)
    frequencies = {}
    for value in values:
        frequencies[value] = frequencies.get(value, 0) + 1
    mode = default
    if values:
        highest = max(frequencies.values())
        for value in values:
            if frequencies[value] == highest:
                mode = value
                break
    return {"count": len(values), "mode": mode}
''',
    "helpers": GUARD + '''
from collections import Counter

def _count(values):
    return len(values)

def _mode(values, default):
    if not values:
        return default
    counts = Counter(values)
    highest = max(counts.values())
    return next(value for value in values if counts[value] == highest)

def solve(payload):
    values, default = _validate(payload)
    return {"count": _count(values), "mode": _mode(values, default)}
''',
    "source_adapter": GUARD + '''
import importlib.util
from pathlib import Path

_source = Path(__file__).resolve().parent / "sources" / "statsutils.py"
_spec = importlib.util.spec_from_file_location("d1_eb09_statsutils", _source)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

def solve(payload):
    values, default = _validate(payload)
    # 数量空域固定0；众数空域按题面default。不是单一上游对象的原契约。
    return {"count": _module.Stats(values, default=0).count,
            "mode": _module.Stats(values, default=default).mode}
''',
}

REQUIREMENTS = """# E_B09：同时报告数量与众数（另池公开候选）

在Python函数solve(payload)中，对一组离散观测同时提供两个用途不同的统计：数量用于规模检查，众数用于代表值选择。内部函数与计算次序自由，不要求先算数量，也不要求拆成helper。

payload须为普通字典，仅含必需的data和可选default。data须为列表，最多128项；每项精确类型只能是int或str，允许混合；bool、float、容器元素不允许。default省略时为None；显式值可以是有限JSON标量（None/bool/str/int/有限float），不能是数组或对象。

返回正好两个字段：count是列表长度（整数）；mode是频数最高的原值，并列时选择原列表中首次出现的值。整数1与字符串"1"分别计频数。空列表返回count=0、mode=default。输入不得改变，含列表次序、类型和字典键次序。

异常优先级：payload非普通字典抛TypeError；缺data抛ValueError；额外字段抛ValueError；data非列表抛TypeError；长度超128抛ValueError；data元素类型无效抛TypeError；default类型无效抛TypeError；default浮点非有限抛ValueError。无需固定异常消息。

适配声明：任务借鉴固定boltons Stats的count/mode用途。数量空域0和众数可选default用两个独立来源对象包装；长度上限、精确元素类型及异常是本候选明确增加的适配。不能称上游全部API原样复现。

本目录诊断全部公开，不构成隐藏确认集；目前仅12个新边界得到三结构实测，未覆盖上述全部无效组合/长度上限。正式标签、切分、人工复核未冻结；不并入原20题，不称模型效果。原评分器把1与1.0视为相等，但bool与数值区分，不能声称它强制count整数输出类型。
"""


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def main():
    if sha(SOURCE) != SOURCE_SHA:
        raise ValueError("固定来源哈希改变")
    OUT.mkdir(exist_ok=False)
    candidate = OUT / "candidate"
    (candidate / "sources").mkdir(parents=True)
    shutil.copy2(SOURCE, candidate / "sources/statsutils.py")
    shutil.copy2(LICENSE, candidate / "sources/LICENSE")
    (candidate / "requirements.md").write_text(REQUIREMENTS, encoding="utf-8")
    for name, source in PROGRAMS.items():
        (candidate / (name + ".py")).write_text(source, encoding="utf-8")
    write_json(candidate / "public_diagnostics.json", CASES)
    write_json(candidate / "task.json", {
        "task_id": "E_B09", "title": "离散数量与众数报告", "status": "研究池候选，全部诊断公开，未正式冻结",
        "entry": "solve(payload)", "requirements": "requirements.md", "diagnostics": "public_diagnostics.json",
        "source": {"repository": "mahmoud/boltons", "commit": "4e5faa3d7e4008d89e0d8bf1ea87b6d9a061a16d",
                   "upstream_module": "boltons/statsutils.py", "module_sha256": SOURCE_SHA,
                   "license": "BSD-3-Clause", "license_file": "sources/LICENSE", "license_sha256": sha(LICENSE)},
        "structural_labels": {"dependency": None, "state_scope": None, "independent_testability": None},
        "related_candidate": "E_B08", "family_note": "同Stats模块/同来源，不是新的独立来源或新增独立样本",
        "adaptation": "count/default分离；域与异常由候选显式规定；三程序共享校验guard不是三个独立oracle",
        "human_reviews": 0, "formal_split": None, "source_contamination": "未知",
    })
    write_json(OUT / "cases_and_programs_frozen.json", {
        "created_at": datetime.now(timezone.utc).isoformat(), "cases": CASES,
        "expected_provenance": "本次执行前逐值解析/显式异常；非人类真值，非参考输出导出",
        "program_hashes": {name: sha(candidate / (name + ".py")) for name in PROGRAMS},
        "comparator_sha256": sha(ROOT / "scripts/d1/evaluate_candidate.py"),
        "source_sha256": SOURCE_SHA, "public_diagnostics_only": True,
        "budget": {"task_calls": 36, "model_calls": 0, "API_calls": 0, "hidden_reads": 0, "old_case_reruns": 0},
    })
    results = {}
    for name in PROGRAMS:
        result = evaluate(candidate / (name + ".py"), candidate / "public_diagnostics.json")
        write_json(OUT / (name + "_bounded_result.json"), result)
        results[name] = result
    write_json(OUT / "summary.json", {
        "created_at": datetime.now(timezone.utc).isoformat(), "task_id": "E_B09",
        "results": results, "new_task_calls": sum(result["cases"] for result in results.values()),
        "all_36_pass": all(result["all_pass"] and result["cases"] == 12 for result in results.values()),
        "valid_inputs": 6, "invalid_inputs": 6, "new_old_six_calls": 0,
        "scope": "三结构共有边界guard；有效域算法不同，上游适配提供有限来源一致性；未证全域/人工/模型效果",
        "model_calls": 0, "API_calls": 0, "hidden_reads": 0, "initial20_modified": False,
        "candidate_files": {str(path.relative_to(candidate)): sha(path) for path in candidate.rglob("*") if path.is_file() and "__pycache__" not in path.parts},
    })
    print(json.dumps({name: {key: result[key] for key in ("cases", "passed", "all_pass")} for name, result in results.items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
