#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查明 RESEARCH_PLAN.md 里 '八之二' 的真实上下文，并把完成定义节可靠写入。"""
from pathlib import Path

PLAN = Path(r"D:\yaorz\research\codeprm-reproduction\.research-state\RESEARCH_PLAN.md")
text = PLAN.read_text(encoding="utf-8")

# 打印所有出现位置及上下文
positions = []
start = 0
while True:
    i = text.find("八之二", start)
    if i < 0:
        break
    positions.append(i)
    start = i + 1
print("出现次数:", len(positions))
for i in positions:
    print(f"  位置 {i}: …{text[max(0,i-40):i+40]!r}…")

# 检查是否已有独立小节标题
has_section = "\n## 八之二" in text
print("已有独立小节:", has_section)

if not has_section:
    note = """

## 八之二、本轮完成定义（决策 5b，2026-10-11）

本轮研究的**完成定义**确定为：**边界交付完成**。交付内容包括：

1. **真实项目研究池**：PR126、PR142、PR440、QUEUE_K2 四项真实项目功能（各有官方变更、父源码、项目调用入口、公开行为锚点、合法替代组织与遗漏控制），外加 URL_K3 一项**合成任务**（已按上游实测 6/18 降级，不计入真实项目功能）。
2. **适用边界结果**：哪些义务可由公开行为辨认、哪些只能相对接口或观察域说明、哪些因时点不可见或契约不完整而保持 unknown。
3. **主问题 A 的明确不可回答判定与恢复条件**：口径为"在当前资源、人工审查与完整候选条件下明确不可回答"，不是逻辑上永远不可回答。

**明确不包含**：正式数据集、正式结构标签（formal_labels）、正式切分（split）、主问题 A 的收益估计。这些仍受人工审查与资源条件约束，**不因本轮完成定义而放宽**。

同时确认：G3 的人工审查为**外部依赖未履行**（决策 3b）；G4 模型执行**暂缓**（决策 4），PROTOCOL.md 草案保留但不得当作 M0/M2 方法比较；审查工具改用**二值缺陷清单**（决策 1）；四个候选已完成上游保真度实测（决策 2）。
"""
    # 插到最后一个 "## 八" 标题之前，找不到就追加到文件末尾
    idx = text.rfind("\n## 八、")
    if idx >= 0:
        text = text[:idx] + note + text[idx:]
        action = "插入到「## 八、当前计划状态指针」之前"
    else:
        text = text.rstrip("\n") + note
        action = "追加到文件末尾"
    PLAN.write_text(text, encoding="utf-8")
    print("动作:", action)
else:
    print("动作: 无需修改")

final = PLAN.read_text(encoding="utf-8")
print("插入后字符数:", len(final))
print("包含 '## 八之二':", "\n## 八之二" in final)
