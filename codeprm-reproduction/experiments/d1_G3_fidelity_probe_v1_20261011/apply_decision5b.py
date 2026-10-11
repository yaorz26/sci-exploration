#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""决策 5b：修订宏观计划——把 G3 人工审查登记为外部依赖，并写入"边界交付完成"。

只改 RESEARCH_PLAN.md 中与 G3 门槛有关的段落；其余阶段顺序、资源与红线不动。
修订前原文先快照。
"""
from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
STATE = REPO / ".research-state"
PLAN = STATE / "RESEARCH_PLAN.md"

stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
snap = STATE / "snapshots" / f"RESEARCH_PLAN_before_decision5b_{stamp}.md"
snap.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(PLAN, snap)

text = PLAN.read_text(encoding="utf-8")

OLD_G3 = """退出条件：两位审查者均完成且分歧得到记录，才生成 formal_labels 和 split；任一审查者不可得、审查不盲或分歧无法追溯时，继续交付 research_pool_only，但不得自封正式数据集。

投入上限：本地只做材料冻结、盲审包和一致性记录；外部审查是前置依赖，不以助手自审冒充。审查不可得时不进入 G4 模型执行。"""

NEW_G3 = """退出条件（2026-10-11 按决策 5b 修订）：**真实人工双审登记为外部依赖未履行**。本地可完成的部分已全部完成——任务版本冻结、材料哈希、盲审包与一致性脚本齐备、并已用 AI 隔离审查做过三轮内部缺陷质检（不计入人工一致率）。

- 若两位真实审查者以后可得：以**新版本**补做人工审查，届时再谈 formal_labels/split。
- 若不可得：**允许交付当前研究池与适用边界**，并按下列限制交付——不得宣布正式数据集、不得生成正式标签、不得声称主问题 A 已有收益估计。
- 主问题 A 的口径固定为：**在当前资源、人工审查与完整候选条件下明确不可回答**；不是逻辑上永远不可回答。

投入上限：本地只做材料冻结、盲审包、一致性记录与 AI 内部缺陷质检；不以助手自审冒充人工审查。**审查不可得不再是硬门槛**，但 G4 模型执行仍需单独的资源与协议批准（见决策 4：暂缓）。"""

if OLD_G3 not in text:
    raise SystemExit("未找到 G3 退出条件原文，未做修改")

text = text.replace(OLD_G3, NEW_G3)

# 在计划的阶段表里同步 G3 一行的退出依据
OLD_ROW = "| G3：真实盲审与数据切分门 | 目标是把“可研究候选”与“正式标签”分开"
if OLD_ROW in text:
    text = text.replace(
        "| G3：真实盲审与数据切分门 | 目标是把“可研究候选”与“正式标签”分开",
        "| G3：真实盲审与数据切分门（人工审查已登记为外部依赖未履行） | 目标是把“可研究候选”与“正式标签”分开")

marker = "\n\n## 九、当前状态指针"
note = """

## 八之二、本轮完成定义（决策 5b，2026-10-11）

本轮研究的**完成定义**确定为：**边界交付完成**。即交付
①真实项目研究池（PR126/PR142/PR440/QUEUE_K2 四项真实项目功能 + URL_K3 一项合成任务）、
②适用边界结果（哪些义务可由公开行为辨认、哪些只能相对接口说明、哪些保持 unknown）、
③主问题 A 的明确不可回答判定与恢复条件。

**不包含**：正式数据集、正式结构标签、正式切分、主问题 A 的收益估计。这些仍受人工审查与资源条件的约束，不因本轮完成定义而放宽。

决策 5b 同时确认：G3 的人工审查为外部依赖未履行；G4 模型执行暂缓（决策 4）；PROTOCOL.md 草案保留但不得当作 M0/M2 方法比较（决策 4）。
"""
if marker in text and "本轮完成定义（决策 5b" not in text:
    text = text.replace(marker, note + marker)

PLAN.write_text(text, encoding="utf-8")

print("宏观计划已按决策 5b 修订")
print("修订前快照:", snap.name)
changed = ["G3 退出条件 → 外部依赖未履行 + 边界交付允许" ,
           "阶段表 G3 行标注" ,
           "新增八之二：本轮完成定义＝边界交付完成"]
for c in changed:
    print("  -", c)
