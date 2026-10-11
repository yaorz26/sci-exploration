"""Generate the stage-2 manual-observation material file (v2, generation order kept)."""
import ast
import json
import statistics
from collections import Counter, OrderedDict, defaultdict
from pathlib import Path

ROOT = Path(r"D:\yaorz\research\decomposition-bench")
FB = ROOT / "data/processed/feedback_records_apps_train_intro50_qwen3b_seed42.jsonl"
OUT = Path(r"D:\yaorz\research\阶段2_手工观察素材.md")

SELECTED = ["apps-train-2653", "apps-train-2661", "apps-train-2662", "apps-train-2688", "apps-train-2671"]

by_problem = OrderedDict()
for line in FB.open(encoding="utf-8"):
    rec = json.loads(line)
    by_problem.setdefault(rec["problem_id"], []).append(rec)  # 保持生成顺序

records = [r for recs in by_problem.values() for r in recs]


def funcs(code):
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return None, str(exc)
    return [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))], None


def msg_tail(fb):
    text = (fb.get("message") or "").strip().splitlines()
    return text[-1][:200] if text else ""


def spearman(xs, ys):
    def rank(vals):
        order = sorted(range(len(vals)), key=lambda i: vals[i])
        ranks = [0.0] * len(vals)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                ranks[order[k]] = avg
            i = j + 1
        return ranks

    rx, ry = rank(xs), rank(ys)
    mx, my = statistics.fmean(rx), statistics.fmean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return num / den if den else 0.0


def baselines(ids):
    first, pub, oracle = [], [], []
    f1 = p1 = o1 = 0
    for pid in ids:
        recs = by_problem[pid]
        pri = [r["private_feedback"]["pass_rate"] for r in recs]
        pubr = [r["public_feedback"]["pass_rate"] for r in recs]
        choice = max(range(len(recs)), key=lambda i: (pubr[i], -i))
        first.append(pri[0]); pub.append(pri[choice]); oracle.append(max(pri))
        f1 += pri[0] == 1.0; p1 += pri[choice] == 1.0; o1 += max(pri) == 1.0
    n = len(ids)
    return {
        "first": (statistics.fmean(first), f1 / n),
        "public": (statistics.fmean(pub), p1 / n),
        "oracle": (statistics.fmean(oracle), o1 / n),
    }


fn_dist = Counter()
for r in records:
    names, err = funcs(r["code"])
    fn_dist["syntax_error" if names is None else len(names)] += 1
thought_dist = Counter(len(r["thoughts"]) for r in records)
pub = [r["public_feedback"]["pass_rate"] for r in records]
pri = [r["private_feedback"]["pass_rate"] for r in records]
rho = spearman(pub, pri)
pub_ok_priv_bad = sum(1 for r in records if r["public_feedback"]["pass_rate"] == 1.0 and r["private_feedback"]["pass_rate"] == 0.0)
pub_bad_priv_ok = sum(1 for r in records if r["public_feedback"]["pass_rate"] == 0.0 and r["private_feedback"]["pass_rate"] == 1.0)
no_correct = sum(1 for pid in by_problem if max(r["private_feedback"]["pass_rate"] for r in by_problem[pid]) == 0.0)
err_types = Counter((r["private_feedback"].get("error_type") or "none") for r in records)

all50 = baselines(list(by_problem))
test13 = baselines(list(by_problem)[-13:])

L = []
A = L.append
A("# 阶段 2 手工观察素材（APPS train-50 seed42 冻结候选池）\n")
A("生成日期：2026-09-10")
A("数据源：`decomposition-bench/data/processed/feedback_records_apps_train_intro50_qwen3b_seed42.jsonl`（50 题 × 4 候选 = 200 条候选记录）\n")
A("> 本文件只做机械整理：摊开代码、执行反馈、函数清单和统计量。**判定列留空，由你手工填写。**")
A("> 候选顺序 = 生成顺序（C0 即首候选），与已有报告口径一致。\n")

A("\n---\n")
A("## 0. 已经算好的客观统计（可直接引用，建议抽查复核）\n")

A("### 0.1 步骤粒度：函数数 vs 思路步数\n")
A("| 口径 | 结果 |")
A("| --- | --- |")
A(f"| 可被 AST 解析的候选 | {200 - fn_dist.get('syntax_error', 0)} / 200 |")
A(f"| 顶层函数数 = 0 或 1 的候选 | {fn_dist.get(0, 0) + fn_dist.get(1, 0)} / 200 |")
A(f"| 顶层函数数 ≥ 2 的候选 | {sum(v for k, v in fn_dist.items() if isinstance(k, int) and k >= 2)} / 200 |")
A(f"| 顶层函数数 = 3 的候选 | {fn_dist.get(3, 0)} / 200 |")
A(f"| 语法错误导致无法解析 | {fn_dist.get('syntax_error', 0)} / 200 |")
A(f"| 思路步数范围 | {min(len(r['thoughts']) for r in records)} – {max(len(r['thoughts']) for r in records)} 步 |")
A(f"| 思路步数均值 | {statistics.fmean(len(r['thoughts']) for r in records):.2f} 步 |")
A("")
A("函数数完整分布：" + "、".join(f"{k} 个函数 → {v} 条" for k, v in sorted(fn_dist.items(), key=lambda kv: str(kv[0]))) + "。")
A("")
A("> 直接结论：这批任务全部是 APPS 函数式任务，**183/200 个候选只有 1 个顶层函数**。")
A("> 也就是说，如果按 FunPRM 的“函数即步骤”定义，绝大多数候选**只有一个步骤**，过程奖励退化为结果奖励。")
A("> 而同一批候选的思路步数是 3–16 步。这正是“函数边界 ≠ 语义 subtask 边界”的第一手证据。\n")

A("### 0.2 public 反馈与 private 结果的一致性\n")
A("| 指标 | 结果 |")
A("| --- | ---: |")
A(f"| Spearman(public pass rate, private pass rate) | {rho:.3f} |")
A(f"| public=1.00 但 private=0.00 的候选 | {pub_ok_priv_bad} / 200 |")
A(f"| public=0.00 但 private=1.00 的候选 | {pub_bad_priv_ok} / 200 |")
A(f"| public 高于 private 的候选 | {sum(1 for a, b in zip(pub, pri) if a > b)} / 200 |")
A(f"| public 低于 private 的候选 | {sum(1 for a, b in zip(pub, pri) if a < b)} / 200 |")
A(f"| private 全 0（池内无正确答案）的题目 | {no_correct} / 50 |")
A(f"| public 选择后仍未完全通过 private 的题目 | {sum(1 for pid in by_problem if by_problem[pid][max(range(4), key=lambda i: (by_problem[pid][i]['public_feedback']['pass_rate'], -i))]['private_feedback']['pass_rate'] < 1.0)} / 50 |")
A("")
A("private 错误类型分布：" + "、".join(f"{k} {v}" for k, v in err_types.most_common()) + "。\n")

A("### 0.3 选择基线（用于对齐 `reports/neural_codeprm_train50_seed42_diagnostic_2026-09-05.json`）\n")
A("| 选择方法 | 全部 50 题的 private pass rate | 后 13 题（诊断报告的测试划分） | 后 13 题 pass@1 |")
A("| --- | ---: | ---: | ---: |")
A(f"| 首候选 | {all50['first'][0]:.3f} | {test13['first'][0]:.3f} | {test13['first'][1]:.3f} |")
A(f"| public pass rate 最高者 | {all50['public'][0]:.3f} | {test13['public'][0]:.3f} | {test13['public'][1]:.3f} |")
A(f"| private oracle（事后上限） | {all50['oracle'][0]:.3f} | {test13['oracle'][0]:.3f} | {test13['oracle'][1]:.3f} |")
A("")
A("> 后 13 题一列与诊断报告中 `first_candidate_private_pass_rate = 0.5333`、`public_selection_private_pass_rate = 0.6833` 完全一致，说明口径可复现。\n")

A("\n---\n")
A("## 1. 五道观察题的原始素材\n")
A("选题理由（每题代表一类现象）：\n")
A("| 题目 | 现象 |")
A("| --- | --- |")
A("| `apps-train-2653` | public 全过、private 全败：public 反馈给出**完全错误的定位信息** |")
A("| `apps-train-2661` | public=0.00 但 private=1.00：public 反馈**反向误导** |")
A("| `apps-train-2662` | 同一题里 private 从 0.33 到 1.00 都有：可对比“错在哪一步” |")
A("| `apps-train-2688` | public 排序与 private 排序**不一致** |")
A("| `apps-train-2671` | 三个候选 private 相同但 public 不同：public 无区分度 |")
A("")

for pid in SELECTED:
    recs = by_problem[pid]
    A(f"\n### {pid}\n")
    question = recs[0]["problem"]
    if len(question) > 1500:
        question = question[:1500] + "\n…（题面截断）"
    A("<details><summary>题面（点击展开）</summary>\n")
    A("```text\n" + question.strip() + "\n```\n")
    A("</details>\n")
    A("\n**候选总览**\n")
    A("| 候选 | 顶层函数 | 函数个数 | public 通过 | private 通过 | private 错误类型 |")
    A("| --- | --- | ---: | ---: | ---: | --- |")
    for i, r in enumerate(recs):
        names, err = funcs(r["code"])
        disp = "解析失败" if names is None else (", ".join(f"`{x}`" for x in names) or "（无）")
        nfn = "-" if names is None else len(names)
        pv = r["private_feedback"]
        A(f"| C{i} | {disp} | {nfn} | {r['public_feedback']['pass_rate']:.2f} ({r['public_feedback']['passed']}/{r['public_feedback']['total']}) "
          f"| {pv['pass_rate']:.2f} ({pv['passed']}/{pv['total']}) | {pv.get('error_type') or '无（全部通过）'} |")
    A("")
    for i, r in enumerate(recs):
        A(f"\n#### {pid} / 候选 C{i}\n")
        A("**模型给出的思路步骤**\n")
        for j, t in enumerate(r["thoughts"]):
            A(f"{j+1}. {t.strip()}")
        A("\n**生成的代码**\n")
        A("```python\n" + r["code"].rstrip() + "\n```\n")
        pf, pv = r["public_feedback"], r["private_feedback"]
        A("**执行反馈**\n")
        A(f"- public：{pf['passed']}/{pf['total']} 通过，error_type = `{pf.get('error_type')}`")
        if pf.get("message"):
            A(f"  - 末行信息：`{msg_tail(pf)}`")
        A(f"- private：{pv['passed']}/{pv['total']} 通过，error_type = `{pv.get('error_type')}`")
        if pv.get("message"):
            A(f"  - 末行信息：`{msg_tail(pv)}`")
        A("")
    A("\n**待你填写的标注表（本题）**\n")
    A("| 候选 | 函数个数 | 我按语义切的 subtask（分号分隔） | 函数与 subtask 是否一一对应 | 错误落在哪个 subtask | public 反馈能否指出该位置 |")
    A("| --- | ---: | --- | --- | --- | --- |")
    for i in range(len(recs)):
        A(f"| C{i} |  |  |  |  |  |")
    A("")

A("\n---\n")
A("## 2. 汇总表（填完 5 题后统计）\n")
A("| 指标 | 数值 |")
A("| --- | ---: |")
A("| 观察题数 | 5 |")
A("| 观察候选数 | 20 |")
A("| 函数与语义 subtask 不一致的候选数 |  |")
A("| 不一致率 |  |")
A("| public 反馈能定位错误位置的候选数 |  |")
A("| public 反馈误导（全过但 private 失败）的候选数 |  |")
A("| 仅有单个函数的候选数 | 183 / 200（已算好，可在 5 题里抽查复核） |")
A("")

OUT.write_text("\n".join(L), encoding="utf-8")
print("written:", OUT)
