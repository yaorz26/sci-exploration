#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""精确插入八之二（带核对打印）。"""
from pathlib import Path

PLAN = Path(r"D:\yaorz\research\codeprm-reproduction\.research-state\RESEARCH_PLAN.md")
text = PLAN.read_text(encoding="utf-8")
print("文件字符数:", len(text))
print("包含 '八之二':", "八之二" in text)
print("包含 '## 八、当前计划状态指针':", "## 八、当前计划状态指针" in text)

note = """## 八之二、本轮完成定义（决策 5b，2026-10-11）

本轮研究的**完成定义**确定为：**边界交付完成**。交付内容包括：

1. **真实项目研究池**：PR126、PR142、PR440、QUEUE_K2 四项真实项目功能（各有官方变更、父源码、项目调用入口、公开行为锚点、合法替代组织与遗漏控制），外加 URL_K3 一项**合成任务**（已按上游实测 6/18 降级，不计入真实项目功能）。
2. **适用边界结果**：哪些义务可由公开行为辨认、哪些只能相对接口或观察域说明、哪些因时点不可见或契约不完整而保持 unknown。
3. **主问题 A 的明确不可回答判定与恢复条件**：口径为"在当前资源、人工审查与完整候选条件下明确不可回答"，不是逻辑上永远不可回答。

**明确不包含**：正式数据集、正式结构标签（formal_labels）、正式切分（split）、主问题 A 的收益估计。这些仍受人工审查与资源条件约束，**不因本轮完成定义而放宽**。

同时确认：G3 的人工审查为**外部依赖未履行**（决策 3b）；G4 模型执行**暂缓**（决策 4），PROTOCOL.md 草案保留但不得当作 M0/M2 方法比较；审查工具改用**二值缺陷清单**（决策 1）；四个候选已完成上游保真度实测（决策 2）。

"""

anchor = "## 八、当前计划状态指针"
if "八之二" in text:
    print("已存在，不修改")
elif anchor in text:
    text = text.replace(anchor, note + anchor, 1)
    PLAN.write_text(text, encoding="utf-8")
    print("已插入八之二；新字符数:", len(text))
else:
    print("锚点缺失，未修改")

after = PLAN.read_text(encoding="utf-8")
print("插入后包含 '八之二':", "八之二" in after)
idx = after.find("## 八之二")
print("位置:", idx, "| 片段:", after[idx:idx+60].replace("\n", " ") if idx >= 0 else "无")
