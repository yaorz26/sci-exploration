"""Generate the stage-2 manual-observation material file."""
import ast
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"D:\yaorz\research\decomposition-bench")
FB = ROOT / "data/processed/feedback_records_apps_train_intro50_qwen3b_seed42.jsonl"
OUT = Path(r"D:\yaorz\research\阶段2_手工观察素材.md")

SELECTED = ["apps-train-2653", "apps-train-2661", "apps-train-2662", "apps-train-2688", "apps-train-2671"]

records = [json.loads(line) for line in FB.open(encoding="utf-8")]
by_problem = defaultdict(list)
for rec in records:
    by_problem[rec["problem_id"]].append(rec)
for pid in by_problem:
    by_problem[pid].sort(key=lambda r: r["code"])


def funcs(code):
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return None, f"语法错误: {exc}"
    names = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    return names, None


def msg_head(fb):
    text = (fb.get("message") or "").strip().splitlines()
    return text[-1][:200] if text else ""


# ---------- baseline table ----------
first_rate, pub_rate, oracle_rate = [], [], []
first_p1 = pub_p1 = oracle_p1 = 0
for pid, recs in by_problem.items():
    pri = [r["private_feedback"]["pass_rate"] for r in recs]
    pub = [r["public_feedback"]["pass_rate"] for r in recs]
    pub_choice = max(range(len(recs)), key=lambda i: (pub[i], -i))
    first_rate.append(pri[0])
    pub_rate.append(pri[pub_choice])
    oracle_rate.append(max(pri))
    first_p1 += pri[0] == 1.0
    pub_p1 += pri[pub_choice] == 1.0
    oracle_p1 += max(pri) == 1.0

n = len(by_problem)
lines = []
lines.append("# 阶段 2 手工观察素材（train-50 seed42 冻结候选池）\n")
lines.append("生成日期：2026-09-10　数据源：`decomposition-bench/data/processed/feedback_records_apps_train_intro50_qwen3b_seed42.jsonl`\n")
lines.append("> 本文件只做机械整理：把代码、执行反馈、函数清单摊开。**判定列留空，由你手工填写。**\n")
lines.append("> 候选顺序按代码内容排序，保证可复现；与生成顺序无关。\n")

lines.append("\n## 0. 先验基线（用于对齐已有报告）\n")
lines.append("| 选择方法 | private pass rate 均值 | private pass@1 | 说明 |")
lines.append("| --- | ---: | ---: | --- |")
lines.append(f"| 首候选 | {statistics.fmean(first_rate):.3f} | {first_p1/n:.3f} | 不消耗任何评分 |")
lines.append(f"| public pass rate 最高者 | {statistics.fmean(pub_rate):.3f} | {pub_p1/n:.3f} | 直接执行反馈选择 |")
lines.append(f"| private oracle | {statistics.fmean(oracle_rate):.3f} | {oracle_p1/n:.3f} | 事后上限，仅分析用 |")
no_correct = sum(1 for pid, recs in by_problem.items() if max(r["private_feedback"]["pass_rate"] for r in recs) == 0.0)
lines.append(f"\n- private 全 0（候选池里没有正确答案）的题目：**{no_correct} / {n}**")
pub_incomplete = sum(
    1 for pid, recs in by_problem.items()
    if recs[max(range(len(recs)), key=lambda i: (recs[i]["public_feedback"]["pass_rate"], -i))]["private_feedback"]["pass_rate"] < 1.0
)
lines.append(f"- public 选择后最终仍未完全通过 private 的题目：**{pub_incomplete} / {n}**\n")

# ---------- per-problem sections ----------
lines.append("\n---\n")
lines.append("## 1. 五道观察题的原始素材\n")
lines.append("每道题结构相同：题面 → 候选代码 → 执行反馈 → 待填表。\n")

for pid in SELECTED:
    recs = by_problem[pid]
    lines.append(f"\n### {pid}\n")
    question = recs[0]["problem"]
    if len(question) > 1200:
        question = question[:1200] + "\n…（题面截断）"
    lines.append("<details><summary>题面（点击展开）</summary>\n")
    lines.append("```text\n" + question.strip() + "\n```\n")
    lines.append("</details>\n")

    lines.append("\n**候选总览（请先只看 public 列，再对照 private 列）**\n")
    lines.append("| 候选 | 顶层函数 | 函数个数 | public 通过 | private 通过 | private 错误类型 |")
    lines.append("| --- | --- | ---: | ---: | ---: | --- |")
    for i, r in enumerate(recs):
        names, err = funcs(r["code"])
        fn_disp = "解析失败" if names is None else (", ".join(f"`{x}`" for x in names) or "（无顶层函数）")
        nfn = "-" if names is None else len(names)
        pv = r["private_feedback"]
        et = pv.get("error_type") or "无（全部通过）"
        lines.append(f"| C{i} | {fn_disp} | {nfn} | {r['public_feedback']['pass_rate']:.2f} "
                     f"({r['public_feedback']['passed']}/{r['public_feedback']['total']}) | "
                     f"{pv['pass_rate']:.2f} ({pv['passed']}/{pv['total']}) | {et} |")
    lines.append("")

    for i, r in enumerate(recs):
        lines.append(f"\n#### {pid} / 候选 C{i}\n")
        lines.append("**模型的思路步骤（thoughts）**\n")
        for j, t in enumerate(r["thoughts"]):
            lines.append(f"{j+1}. {t.strip()}")
        lines.append("\n**生成的代码**\n")
        lines.append("```python\n" + r["code"].rstrip() + "\n```\n")
        pf, pv = r["public_feedback"], r["private_feedback"]
        lines.append("**执行反馈**\n")
        lines.append(f"- public: {pf['passed']}/{pf['total']} 通过，error_type = `{pf.get('error_type')}`")
        if pf.get("message"):
            lines.append(f"  - 末行信息：`{msg_head(pf)}`")
        lines.append(f"- private: {pv['passed']}/{pv['total']} 通过，error_type = `{pv.get('error_type')}`")
        if pv.get("message"):
            lines.append(f"  - 末行信息：`{msg_head(pv)}`")
        lines.append("")

    lines.append("\n**待你填写的标注表**\n")
    lines.append("| 候选 | 函数个数 | 我按语义切的 subtask | 函数与 subtask 是否一一对应 | 错误落在哪个 subtask | public 反馈能否指出该位置 | private 是否真的失败 |")
    lines.append("| --- | ---: | --- | --- | --- | --- | --- |")
    for i in range(len(recs)):
        lines.append(f"| C{i} |  |  |  |  |  |  |")
    lines.append("")

lines.append("\n---\n")
lines.append("## 2. 汇总表（全部填完后统计）\n")
lines.append("| 指标 | 数值 |")
lines.append("| --- | ---: |")
lines.append("| 观察题数 | 5 |")
lines.append("| 候选数 | 20 |")
lines.append("| 函数与语义 subtask 不一致的候选数 |  |")
lines.append("| 不一致率 |  |")
lines.append("| public 反馈能定位错误位置的候选数 |  |")
lines.append("| public 反馈误导（全过但 private 失败）的候选数 |  |")
lines.append("| 候选池内无正确答案的题数 |  |")
lines.append("")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("written:", OUT, len("\n".join(lines)), "chars")
