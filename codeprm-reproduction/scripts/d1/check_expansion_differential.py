"""补充来源适配的确定性差分诊断；不计入数据集案例或模型成绩。"""
import argparse
import copy
import json
import random
from pathlib import Path
import task_specs
from evaluate_candidate import json_equal

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    rng = random.Random(20261008)
    cases = []
    for i in range(600):
        items = list(range(rng.randrange(0, 8)))
        operations = []
        for j in range(18):
            op = {"op": rng.choice(["next", "peek", "seek", "relative_seek", "elements"])}
            if op["op"] == "seek": op["index"] = rng.randrange(0, 12)
            if op["op"] == "relative_seek": op["offset"] = rng.randrange(-10, 11)
            if op["op"] == "peek" and rng.choice([False, True]): op["default"] = None
            operations.append(op)
        cases.append(("D1_M03", {"items": items, "operations": operations}))
    def tree(depth):
        if depth == 0 or rng.random() < .5:
            return rng.choice([None, True, False, -2, 0, 1, 1.5, "x"])
        children = [tree(depth-1) for j in range(rng.randrange(0, 5))]
        return children if rng.choice([False, True]) else {str(j): child for j, child in enumerate(children)}
    for i in range(600):
        value = tree(4)
        if not isinstance(value, (dict, list)): value = [value]
        cases.append(("D1_B05", {"tree": value, "factor": rng.choice([-2, 0, 1, 2.5]),
                                   "threshold": rng.choice([-1, 0, 2]), "drop_null": rng.choice([False, True])}))
        sources = [tree(3) for j in range(rng.randrange(1, 5))]
        sources = [v if isinstance(v, dict) else {"x": v} for v in sources]
        cases.append(("D1_F03", {"sources": sources}))
    for i in range(600):
        value = {"name": rng.choice(["x", "", None, 1])}
        if rng.random() < .7: value["retries"] = rng.choice([None, True, 2.9, -2.9, "2", 0])
        if rng.random() < .7: value["scores"] = rng.choice([None, [], [True], [1.9, -2.9], ["1"], {}])
        if rng.random() < .7: value["options"] = rng.choice([None, {}, {"limit": 1.9}, {"mode": "fast"}, {"limit": None}, {"mode": 0}])
        cases.append(("D1_F04", {"value": value, "default_retries": rng.choice([0, 3, 10])}))
    specs = {spec["id"]: spec for spec in task_specs.TASKS}
    failures, counts = [], {}
    for index, (tid, payload) in enumerate(cases):
        spec = specs[tid]
        reference = task_specs.outcome(spec["reference"], payload)
        alternate = task_specs.outcome(spec["alternate"], payload)
        counts[tid] = counts.get(tid, 0) + 1
        if not json_equal(reference, alternate):
            failures.append({"index": index, "task_id": tid, "input": payload, "reference": reference, "alternate": alternate})
    summary = {"seed":20261008,"case_count":len(cases),"counts":counts,"disagreement_count":len(failures),
               "scope":"4项来源适配的补充差分；不属于305案例，不是独立人工真值或完全覆盖", "failures":failures}
    (args.output/"summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print({key: value for key, value in summary.items() if key != "failures"})
    if failures: raise SystemExit(1)

if __name__ == "__main__":
    main()
