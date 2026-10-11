"""P42：从已固定boltons源码抽取公开Stats行为并做小域独立契约探针。"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/raw/d1_project_v1_20261008/repositories/boltons/boltons/statsutils.py"
DOC = ROOT / "data/raw/d1_project_v1_20261008/repositories/boltons/docs/statsutils.rst"
OUT = ROOT / "experiments/d1_noncache_stats_testability_v1_20261008"

ANCHORS = [
    {"id": "a01", "data": [1, 2, 3]},
    {"id": "a02", "data": [1, 1, 5]},
    {"id": "a03", "data": []},
    {"id": "a04", "data": [-2, 0, 2]},
    {"id": "a05", "data": [1.5, 2.5]},
    {"id": "a06", "data": [100, 101, 102]},
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mean_ref(values):
    return sum(values, 0.0) / len(values) if values else 0.0


def variance_ref(values):
    if not values:
        return 0.0
    m = mean_ref(values)
    return sum((value - m) ** 2 for value in values) / len(values)


def load_module():
    spec = importlib.util.spec_from_file_location("d1_statsutils_frozen", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def main():
    if OUT.exists():
        raise FileExistsError("原始机器输出不得覆盖")
    OUT.mkdir()
    source_hash, doc_hash = sha(SOURCE), sha(DOC)
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    stats = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Stats")
    method_docs = {}
    for node in stats.body:
        if isinstance(node, ast.FunctionDef) and node.name in {"_calc_mean", "_calc_variance"}:
            method_docs[node.name] = {"line": node.lineno, "end_line": node.end_lineno,
                                      "docstring": ast.get_docstring(node) or ""}
    frozen = {"created_at": datetime.now(timezone.utc).isoformat(), "source": str(SOURCE.relative_to(ROOT)),
              "source_sha256": source_hash, "docs": str(DOC.relative_to(ROOT)), "docs_sha256": doc_hash,
              "methods": method_docs, "anchors": ANCHORS, "scope": "公开源码/文档，未读取测试文件或private案例",
              "model_calls": 0, "API_calls": 0, "hidden_reads": 0, "task_evaluations": 0}
    (OUT / "source_and_anchors_frozen.json").write_text(json.dumps(frozen, ensure_ascii=False, indent=2), encoding="utf-8")
    module = load_module()
    rows = []
    for anchor in ANCHORS:
        data = anchor["data"]
        obj = module.Stats(data)
        got_mean, got_variance = obj.mean, obj.variance
        exp_mean, exp_variance = mean_ref(data), variance_ref(data)
        rows.append({"anchor": anchor["id"], "input": data, "mean": {"observed": got_mean, "expected": exp_mean,
                    "pass": math.isclose(got_mean, exp_mean, rel_tol=0.0, abs_tol=1e-12)},
                    "variance": {"observed": got_variance, "expected": exp_variance,
                    "pass": math.isclose(got_variance, exp_variance, rel_tol=0.0, abs_tol=1e-12)}})
    result = {
        "status": "公开Stats两个不同用途统计量的有限契约探针完成",
        "source_sha256": source_hash, "docs_sha256": doc_hash, "anchors": rows,
        "behavior_contracts": [
            {"name": "mean", "purpose": "中心位置", "input": "有限数值序列/空序列", "output": "数值/默认0.0", "observable_unit": "单个数值"},
            {"name": "variance", "purpose": "离散程度", "input": "有限数值序列/空序列", "output": "数值/默认0.0", "observable_unit": "单个数值"},
        ],
        "pass_counts": {"mean": sum(row["mean"]["pass"] for row in rows), "variance": sum(row["variance"]["pass"] for row in rows)},
        "interpretation": "两个统计量有不同用途和可分开的输出契约，但variance实现语义依赖mean；它们共享同一数据对象，故是部分独立可测而非无耦合。Stats属性缓存提供方案级共享状态，不能由此抹掉任务侧两个输出机会。",
        "competing_explanations": {
            "同一整体多字段无独立契约": "被有限输入的中心位置/离散程度不同输出契约削弱，但未被全域证明排除",
            "两个用途可分别验证": "六个公开小域锚点的mean和variance均6/6符合独立参考",
            "有效域/默认值使机会只局部成立": "空序列使用默认0.0且保留为单独域；未覆盖非数值/NaN/大数全域"
        },
        "limits": ["6手算式公开锚点/非人工审查，不是全域语义真值", "仅一个固定来源功能，不能填回原20可测标签或声称跨来源", "没有比较模型拆分收益、没有新增private/原测试读取", "mean与variance共享数据且variance调用mean，不能宣称无依赖"],
        "model_calls": 0, "API_calls": 0, "new_downloads": 0, "hidden_reads": 0, "task_evaluations": 0,
    }
    (OUT / "summary.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": result["status"], "mean_pass": result["pass_counts"]["mean"],
                      "variance_pass": result["pass_counts"]["variance"], "anchors": len(rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
