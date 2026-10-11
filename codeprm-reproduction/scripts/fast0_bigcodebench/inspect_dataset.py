"""FAST-0：BigCodeBench v0.1.4 原始数据静态检查（只读，不运行生成模型）。

用途：核实字段结构、任务数量、依赖库分布，为 5--10 题参考实现抽查选定样本。
运行：<venv>/Scripts/python.exe inspect_dataset.py

注：`libs` 字段是单引号 Python 字面量（如 ['random', 'itertools']），不是 JSON，
必须用 ast.literal_eval 解析；第一版用 json.loads 解析失败后已修正。
"""
import ast
from collections import Counter
import json
import pathlib

import pyarrow.parquet as pq

RAW = pathlib.Path(
    r"D:\yaorz\research\codeprm-reproduction\data\raw\bigcodebench\v0.1.4\bigcodebench_v0.1.4_full.parquet"
)


def parse_libs(s):
    try:
        return list(ast.literal_eval(s))
    except Exception:
        return []


def main() -> None:
    table = pq.read_table(RAW)
    print("rows:", table.num_rows)
    print("columns:", table.column_names)
    d = table.to_pylist()

    print("\n--- task_id 前缀分布 ---")
    print(Counter(x["task_id"].rsplit("/", 1)[0] for x in d))

    print("\n--- libs 分布（每题依赖库，前 20 组） ---")
    lib_counter: Counter = Counter()
    for x in d:
        lib_counter[tuple(sorted(parse_libs(x["libs"])))] += 1
    for k, v in lib_counter.most_common(20):
        print(f"  {v:4d}  {list(k)}")

    print("\n--- 第一个样例的字段（截断显示） ---")
    s = d[0]
    for k, v in s.items():
        text = str(v).replace("\n", "\\n")
        print(f"  [{k}] len={len(str(v))} :: {text[:180]}")

    print("\n--- 含测试的题比例 ---")
    has_test = sum(1 for x in d if x.get("test"))
    print(f"  {has_test}/{len(d)}")

    print("\n--- 依赖库种类数 ---")
    all_libs = set()
    for x in d:
        all_libs.update(parse_libs(x["libs"]))
    print("  共", len(all_libs), "种")
    print("  ", sorted(all_libs))

    print("\n--- 只依赖标准库的题数 ---")
    stdlib = set(__import__("sys").stdlib_module_names)
    only_std = [x["task_id"] for x in d if set(parse_libs(x["libs"])) <= stdlib]
    print("  共", len(only_std), "题；前 20 个：", only_std[:20])

    print("\n--- prompt / 解 / 测试长度统计 ---")
    import statistics as st
    for key in ["complete_prompt", "canonical_solution", "test", "code_prompt"]:
        lens = [len(str(x[key])) for x in d]
        print(f"  {key}: median={st.median(lens):.0f} mean={st.mean(lens):.0f} max={max(lens)}")


if __name__ == "__main__":
    main()

