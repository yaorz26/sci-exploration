"""只静态读取STRUCTURE_V2声明和复制节点，不执行任务模块。"""
from __future__ import annotations

import ast
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "experiments/d1_testability_label_provenance_v1_20261008"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    frozen = read(OUT / "inputs_and_ast_locator_frozen.json")
    extension = read(OUT / "scope_extension_frozen.json")
    for record in frozen["sources"] + extension["sources"]:
        if digest(ROOT / record["path"]) != record["sha256"]:
            raise ValueError("前置源码/行表改变，停止")
    source_path = ROOT / "scripts/d1/task_specs_expansion.py"
    source = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    nodes = [node for node in tree.body if isinstance(node, ast.Assign)
             and any(isinstance(target, ast.Name) and target.id == "STRUCTURE_V2" for target in node.targets)]
    if len(nodes) != 1 or not isinstance(nodes[0].value, ast.Dict):
        raise ValueError("不是单一静态字典，不能用literal_eval复现")
    table = ast.literal_eval(nodes[0].value)
    manifest = read(ROOT / "data/processed/d1_project_initial20_v5_20261008/manifest.json")
    comparisons = []
    groups = defaultdict(lambda: {"tasks": [], "testability": set()})
    for record in manifest["tasks"]:
        tid, label = record["task_id"], record["structure_v2"]
        state, scope, deps, testability, explanation = table[tid]
        copied = {"cross_operation_state": state, "state_scope": scope, "behavior_dependencies": deps,
                  "separate_behavior_testability": testability, "evidence": explanation}
        matches = {field: label[field] == value for field, value in copied.items()}
        comparisons.append({"task_id": tid, "all_five_fields_match": all(matches.values()), "fields": matches})
        group = groups[tuple(sorted(deps))]
        group["tasks"].append(tid)
        group["testability"].add(testability)
    result = {
        "status": "静态来源核对完成；排除当前构建程序从依赖标签计算可测字段",
        "origin": "task_specs_expansion.py的20任务ID静态五元组；task_specs导入；build_dataset逐字段复制",
        "target_declaration": {"path": str(source_path.relative_to(ROOT)), "line": nodes[0].lineno,
                               "end_line": nodes[0].end_lineno, "kind": "ast.Dict/ast.literal_eval",
                               "node_sha256": hashlib.sha256(ast.get_source_segment(source, nodes[0]).encode()).hexdigest()},
        "copied_fields": ["cross_operation_state", "state_scope", "behavior_dependencies", "separate_behavior_testability", "evidence"],
        "compared_tasks": len(comparisons), "all_fields_matched_tasks": sum(c["all_five_fields_match"] for c in comparisons),
        "comparisons": comparisons,
        "dependency_groups": [{"dependencies": list(deps), "tasks": data["tasks"],
                               "testability": sorted(data["testability"])} for deps,data in groups.items()],
        "competing_explanations": {
            "构建时testability由依赖集合直接算出": "当前静态代码排除：两字段各自作为字面量存储并复制",
            "构建时两字段共同从legacy类别映射": "当前静态复制路径未支持，legacy描述仅附存",
            "作者逐题指定的表中存在样本/判断对应": "支持；不能据此证明作者判断彼此独立或语义正确",
        },
        "decision": "保留样本对应/支撑不足与人工0；不把它错误归因于构建器。P42查非缓存多统计公开功能能否提供不同用途的独立契约而不要求有序转换。",
        "model_calls": 0, "API_calls": 0, "task_evaluations": 0, "hidden_reads": 0,
        "limits": ["只查当前静态来源，不解释最初作者心理/先后或生成历史", "逐字段字面量不等真实独立人类标注", "20/20复制一致不等语义正确或主A成立", "原初标/切分/测试保持"]
    }
    with (OUT / "source_copy_comparison.json").open("x", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps({"tasks": len(comparisons), "matched": result["all_fields_matched_tasks"],
                      "origin": result["origin"], "dependency_groups": len(groups), "hidden_reads": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
