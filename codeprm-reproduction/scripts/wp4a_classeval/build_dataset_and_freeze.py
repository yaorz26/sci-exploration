"""WP4A + WP5：把 ClassEval 转成统一字段、按方法切分公开/私有测试、并冻结清单。

输入：`data/raw/classeval/data/*.parquet`（原始，只读）
       `experiments/wp4a_classeval_regression/full100_regression.json` + `rerun_failed_round2.json`（参考实现回归结果）
输出：
  - `data/processed/classeval_v1/tasks_public.jsonl`   模型可读部分（不含私有测试）
  - `data/processed/classeval_v1/private/private_tests.jsonl`  私有测试（物理分离，不进入模型可读目录）
  - `data/processed/classeval_v1/provenance.json`      来源与哈希
  - `data/processed/classeval_v1/dataset_card.md`      数据卡（派生物声明）
  - `data/splits/classeval_v1/frozen_manifest.json`     冻结清单（探索集、预算、seed、选择规则）
  - `data/processed/classeval_v1/excluded_tasks.json`   被排除题及理由（不静默消失）

规则（预注册，见 docs/week3/data-route/20260929/）：
  - 可用性：参考实现在主环境连续 3 次通过；否则排除并记原因；
  - 分层：方法数 ≥5 目标层 / ==3 边界层 / ==2 负对照层；其余（==4）不进探索集；
  - 公开/私有：按 methods_info 顺序，前 ⌈n/2⌉ 个方法的测试为公开，其余（含无法映射的测试类）为私有；
  - 探索集：每层抽 8 题（seed 20260929），共 24 题；其余可用题留作储备。
本脚本不调用生成模型。
"""
import ast
import hashlib
import json
import pathlib
import random
import re
import statistics
import sys

import pyarrow.parquet as pq

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))
from classeval_split import split_public_private  # noqa: E402

ROOT = pathlib.Path(r"D:\yaorz\research\codeprm-reproduction")
RAW = ROOT / "data/raw/classeval/data/test-00000-of-00001-5c45fa6e45572491.parquet"
RAW_SHA = "ac2f490a8fa0ca63d8b6d166821ca430a382dc04611209e2067a2714cc89df2a"
REG1 = ROOT / "experiments/wp4a_classeval_regression/full100_regression.json"
REG2 = ROOT / "experiments/wp4a_classeval_regression/rerun_failed_round2.json"
OUT = ROOT / "data/processed/classeval_v1"
PRIV = OUT / "private"
SPLITS = ROOT / "data/splits/classeval_v1"
SEED = 20260929
N_PER_LAYER = 8
CHARS_PER_TOKEN = 3.2

EXCLUDED_REASONS = {
    "ClassEval_14": "非确定性：首次运行失败、随后两次通过（状态/顺序相关）",
    "ClassEval_17": "时间相关：断言依赖“当前日期”的日历事件",
    "ClassEval_31": "浮点精度：断言与高精度浮点常量严格相等，跨 NumPy 版本不稳定",
    "ClassEval_48": "宿主机相关：断言硬编码主机名",
    "ClassEval_50": "操作系统语义：Unix 文件权限测试在 Windows 上行为不同（PermissionError）",
    "ClassEval_51": "NumPy 2.x 语义变化：依赖 float(数组) 的宽松转换（NumPy 1.x 可通过，WSL py3.10 已复验）",
    "ClassEval_58": "非确定性：断言依赖随机数（扫雷随机布雷）",
    "ClassEval_60": "非确定性：断言依赖跨调用累积状态（票务数量）",
    "ClassEval_99": "操作系统语义：目录非空错误在 Windows 上语义不同（WinError 145）",
}

LAYER_RULE = "方法数 ≥5 → target；==3 → boundary；==2 → negative；==4 → 不入探索集（reserve_only）"

# 第二轮之后补齐依赖才通过的题（有独立复验记录，单独登记以免遗漏）
LATE_FIXES = {"ClassEval_69": "补装 reportlab 后连续 3 次通过（2026-09-29 复验）"}


def parse(v):
    return ast.literal_eval(v) if isinstance(v, str) else v


def layer_of(n: int) -> str:
    if n >= 5:
        return "target"
    if n == 3:
        return "boundary"
    if n == 2:
        return "negative"
    return "reserve_only"


def split_tests(test_code: str, methods_info):
    """统一改用 src/classeval_split.py（2026-09-29 修复拼接换行与空公开集两处缺陷）。"""
    return split_public_private(test_code, methods_info)


def sha256_text(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    PRIV.mkdir(parents=True, exist_ok=True)
    SPLITS.mkdir(parents=True, exist_ok=True)

    reg1 = json.loads(REG1.read_text(encoding="utf-8"))
    reg2 = json.loads(REG2.read_text(encoding="utf-8"))
    usable = {t["task_id"] for t in reg1["tasks"] if t.get("stable") and t["ok"]}
    usable |= {x["task_id"] for x in reg2["results"] if x["ok"]}
    usable |= {k for k in LATE_FIXES if k not in EXCLUDED_REASONS}
    all_ids = [t["task_id"] for t in reg1["tasks"]]
    excluded = [i for i in all_ids if i not in usable]

    rows = pq.read_table(RAW).to_pylist()
    public_records, private_records, index = [], [], []
    for r in rows:
        tid = r["task_id"]
        if tid not in usable:
            continue
        mi = parse(r["methods_info"])
        sp = split_tests(r["test"], mi)
        pub_test, priv_test, split_info = sp["public_tests"], sp["private_tests"], {
            "mode": sp["mode"],
            "public_available": sp["public_available"],
            "public_classes": sp["public_classes"],
            "private_classes": sp["private_classes"],
            "split_rule": sp.get("split_rule", ""),
        }
        subtasks = [
            {"name": m.get("method_name"), "description": m.get("method_description"),
             "dependencies": m.get("dependencies"), "test_class": m.get("test_class")}
            for m in mi
        ]
        free_input = f"{r['class_description']}\n\n# 可用导入：\n" + "\n".join(parse(r["import_statement"]))
        rec = {
            "task_id": tid,
            "source": {
                "dataset": "FudanSELab/ClassEval",
                "dataset_url": "https://huggingface.co/datasets/FudanSELab/ClassEval",
                "repo_url": "https://github.com/FudanSELab/ClassEval",
                "license": "MIT",
                "raw_file": str(RAW).replace("\\", "/"),
                "raw_file_sha256": RAW_SHA,
                "task_index": int(tid.split("_")[-1]),
            },
            "class_name": r["class_name"],
            "inputs": {
                "decompose_free": free_input,
                "decompose_given": r["skeleton"],
                "imports": parse(r["import_statement"]),
            },
            "reference_impl": r["solution_code"],
            "public_tests": pub_test,
            "private_test_ref": f"private/private_tests.jsonl#{tid}",
            "decomposition": {"should_decompose": None, "subtasks": subtasks,
                              "dependencies": {m.get("method_name"): m.get("dependencies") for m in mi}},
            "metadata": {
                "language": "python",
                "n_methods": len(mi),
                "n_methods_with_deps": sum(1 for m in mi if m.get("dependencies")),
                "layer": layer_of(len(mi)),
                "context_tokens_est": round((len(r["skeleton"]) + len(r["test"])) / CHARS_PER_TOKEN),
                "solution_chars": len(r["solution_code"]),
                "test_chars": len(r["test"]),
                "contamination_risk": "unknown",
                "env_note": "主环境 Python 3.13 + NumPy 2.x（含 np.mat 垫片）+ nltk 数据在 D 盘",
            },
            "split": split_info,
            "hashes": {"public_tests_sha256": sha256_text(pub_test), "private_tests_sha256": sha256_text(priv_test),
                       "reference_impl_sha256": sha256_text(r["solution_code"])},
        }
        public_records.append(rec)
        private_records.append({"task_id": tid, "private_tests": priv_test})
        index.append({"task_id": tid, "layer": rec["metadata"]["layer"], "n_methods": len(mi)})

    (OUT / "tasks_public.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in public_records), encoding="utf-8")
    (PRIV / "private_tests.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in private_records), encoding="utf-8")
    (OUT / "excluded_tasks.json").write_text(
        json.dumps({"excluded": [{"task_id": t, "reason": EXCLUDED_REASONS.get(t, "未归类")} for t in excluded],
                    "n_excluded": len(excluded), "n_usable": len(usable)}, ensure_ascii=False, indent=2), encoding="utf-8")

    pools = {}
    for x in index:
        pools.setdefault(x["layer"], []).append(x["task_id"])
    # 探索集抽样（预注册）：每层按 seed 打乱后取前 8 题；若某题公开测试不可用（public_available=False），
    # 顺位取下一题并在清单中记录替换。替换规则写在冻结清单里。
    avail = {t["task_id"]: t["split"]["public_available"] for t in public_records}
    rng = random.Random(SEED)
    exploratory, replacements = [], []
    for layer in ["target", "boundary", "negative"]:
        pool = sorted(pools.get(layer, []))
        shuffled = pool[:]
        rng.shuffle(shuffled)
        taken = []
        for cand in shuffled:
            if len(taken) >= N_PER_LAYER:
                break
            if not avail.get(cand, False):
                replacements.append({"layer": layer, "skipped": cand, "reason": "公开测试不可用（public_available=False）"})
                continue
            taken.append(cand)
        exploratory += sorted(taken)
    exploratory.sort(key=lambda t: int(t.split("_")[-1]))

    provenance = {
        "dataset": "FudanSELab/ClassEval",
        "license": "MIT",
        "raw_file_sha256": RAW_SHA,
        "usable_tasks": len(usable),
        "excluded_tasks": len(excluded),
        "layer_counts_usable": {k: len(v) for k, v in sorted(pools.items())},
        "outputs": {},
    }
    for p in [OUT / "tasks_public.jsonl", PRIV / "private_tests.jsonl", OUT / "excluded_tasks.json"]:
        provenance["outputs"][p.name] = hashlib.sha256(p.read_bytes()).hexdigest()

    manifest = {
        "dataset": "ClassEval（派生物：字段统一 + 公开/私有按方法切分）",
        "frozen_at": "2026-09-29",
        "seed_exploratory": SEED,
        "layer_rule": LAYER_RULE,
        "n_usable": len(usable),
        "n_excluded": len(excluded),
        "exploratory_set": {"n": len(exploratory), "task_ids": exploratory,
                            "replacements": replacements,
                            "per_layer": {l: [t for t in exploratory if dict((x["task_id"], x["layer"]) for x in index)[t] == l] for l in ["target", "boundary", "negative"]}},
        "reserve_pool": {"n": len(index) - len(exploratory),
                         "by_layer": {k: len(v) - len([t for t in exploratory if t in v]) for k, v in pools.items()}},
        "model": {"name": "qwen2.5-coder:7b（Ollama）", "quantization": "Q4（Ollama 默认 4.7 GB）",
                  "context_limit_tokens": 8192, "note": "WP3 实测最大上下文估算 4102 token，低于上限"},
        "arms": {
            "M0": "直接生成整个类（输入 decompose_free）",
            "M1": "先写自然语言计划，再生成整个类",
            "M2": "先给出分解（方法签名+docstring），再逐方法实现并组合",
            "M2_given": "输入 decompose_given（骨架已给 = 分解已给），只考实现环节（决策单第 10 项：作为对照臂）",
        },
        "decision_rules": {"selection_public": "按公开测试通过数选最优；并列时取更早生成的候选",
                           "private_use": "只在候选与选择规则冻结后运行"},
        "budget": {"per_task_candidates": 3, "timeout_seconds_per_test": 60, "max_output_tokens": 2048,
                   "disk_cap_gib": 20},
        "metrics": ["private_all_pass（题目级）", "M2-M0 成对差异", "候选池上限", "部分测试通过率",
                    "有效候选率", "接口类错误率", "双零题比例"],
        "stop_conditions": ["总请求数超预算", "单题超时", "磁盘超限"],
        "minimum_meaningful_improvement": "净值 ≥4 题且 bootstrap 95% 区间下界 >0",
        "hazard_notes": ["private 测试与模型可读文件物理分离", "非确定性题已排除（见 excluded_tasks.json）",
                         "污染风险为 unknown（Qwen 训练边界未披露）"],
        "artifact_hashes": provenance["outputs"],
    }
    (SPLITS / "frozen_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")

    print("可用题:", len(usable), "| 排除:", len(excluded))
    print("可用题分层:", provenance["layer_counts_usable"])
    print("探索集:", len(exploratory), exploratory)
    print("储备:", manifest["reserve_pool"])
    print("产物:", OUT, "|", SPLITS / "frozen_manifest.json")


if __name__ == "__main__":
    main()
