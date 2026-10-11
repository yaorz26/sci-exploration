"""按候选清单中显式相关家族构造无向图；不推断未记录的语义关系。"""
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[2]
    manifest = root / "data/processed/d1_project_initial20_v5_20261008/manifest.json"
    tasks = json.loads(manifest.read_text(encoding="utf-8"))["tasks"]
    by_family = {}
    for task in tasks:
        by_family.setdefault(task["function_family"], []).append(task["task_id"])
    graph = {task["task_id"]: set() for task in tasks}
    unknown = []
    for task in tasks:
        for family in [task["function_family"]] + task.get("related_families", []):
            if family not in by_family:
                unknown.append({"task_id": task["task_id"], "family": family})
            for other in by_family.get(family, []):
                if other != task["task_id"]:
                    graph[task["task_id"]].add(other)
                    graph[other].add(task["task_id"])
    unseen, groups = set(graph), []
    while unseen:
        stack, found = [min(unseen)], set()
        while stack:
            node = stack.pop()
            if node not in found:
                found.add(node)
                stack.extend(graph[node] - found)
        unseen -= found
        groups.append(sorted(found))
    report = {"status": "pass" if not unknown else "revise", "tasks": len(tasks),
              "fine_grained_families": len(by_family), "explicit_link_components": len(groups),
              "components": groups, "unresolved_family_links": unknown,
              "limit": "连通分量仅用于显式相关性敏感分析，不是真实独立样本数；未标关系仍可能存在。每个细分家族一题不构成统计失效的充分理由。"}
    (root / "experiments/d1_family_link_audit_v1_20261008.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
