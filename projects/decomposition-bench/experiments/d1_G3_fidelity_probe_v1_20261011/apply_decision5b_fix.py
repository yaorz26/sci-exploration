#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补齐决策 5b 的两处未生效修改：阶段表 G3 行标注 + 八之二完成定义节。"""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
PLAN = HERE.parents[1] / ".research-state/RESEARCH_PLAN.md"
text = PLAN.read_text(encoding="utf-8")
original = text

# 1) 阶段表 G3 行标注（标题行在 ### G3 之后，取紧随其后的第一行表格）
import re
m = re.search(r"(### G3：真实盲审与数据切分门\n\n)([^\n]*目标是把“可研究候选”与“正式标签”分开)", text)
if m:
    text = text.replace(m.group(0), m.group(1) + m.group(2) +
                        "（人工审查已登记为外部依赖未履行；见八之二完成定义）")
    print("阶段表 G3 行：已标注")
else:
    print("阶段表 G3 行：未匹配到，跳过")

# 2) 在「## 八、当前计划状态指针」之前插入八之二
anchor = "## 八、当前计划状态指针"
note = """## 八之二、本轮完成定义（决策 5b，2026-10-11）

本轮研究的**完成定义**确定为：**边界交付完成**。交付内容包括

1. **真实项目研究池**：PR126、PR142、PR440、QUEUE_K2 四项真实项目功能（各有官方变更、父源码、项目调用入口、公开行为锚点、合法替代组织与遗漏控制），外加 URL_K3 一项**合成任务**（已按上游实测 6/18 降级，不计入真实项目功能）。
2. **适用边界结果**：哪些义务可由公开行为辨认、哪些只能相对接口或观察域说明、哪些因时点不可见或契约不完整而保持 unknown。
3. **主问题 A 的明确不可回答判定与恢复条件**：口径为"在当前资源、人工审查与完整候选条件下明确不可回答"，不是逻辑上永远不可回答。

**明确不包含**：正式数据集、正式结构标签（`formal_labels`）、正式切分（`split`）、主问题 A 的收益估计。这些仍受人工审查与资源条件约束，**不因本轮完成定义而放宽**。

同时确认：G3 的人工审查为**外部依赖未履行**（决策 3b）；G4 模型执行**暂缓**（决策 4），`PROTOCOL.md` 草案保留但不得当作 M0/M2 方法比较；审查工具改用**二值缺陷清单**（决策 1）；四个候选已完成上游保真度实测（决策 2）。

"""
if anchor in text and "八之二" not in text:
    text = text.replace(anchor, note + anchor, 1)
    print("八之二完成定义：已插入")
else:
    print("八之二完成定义：锚点缺失或已存在，跳过")

if text != original:
    PLAN.write_text(text, encoding="utf-8")
    print("已写入 RESEARCH_PLAN.md")
else:
    print("无改动")
