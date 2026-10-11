# `.codebuddy/` 项目配置说明

更新时间：2026-10-11。D1 实验已结束并归档。

## 当前生效配置

本项目当前没有强制加载的科研 skill，也没有研究循环常驻规则。`plain-language-debrief` 只在用户要求解释、报告或“看不懂”时按需使用。

原研究循环 skill 的正文、发现入口和常驻规则已移到：

`decomposition-bench/.research-state/archive/governance_20261011/`

该目录是历史留档，不属于生效配置；不得从那里调用或自动恢复旧实验。

## 当前生效目录

```text
.codebuddy/
├── README.md
└── skills/
    └── plain-language-debrief/
        ├── SKILL.md
        └── references/
            └── 术语大白话对照表.md
```

`.agents/skills/` 中没有本项目的科研循环跳转壳；`.codebuddy/rules/` 中没有该实验的常驻规则。

## 研究状态入口

| 内容 | 唯一位置 |
|---|---|
| 人类可读最终说明 | `PROJECT_ENTRY.md` |
| 题目与红线 | `decomposition-bench/.research-state/RESEARCH_TARGET.md` |
| 已结束的计划 | `decomposition-bench/.research-state/RESEARCH_PLAN.md` |
| 最终状态 | `decomposition-bench/.research-state/PROJECT_STATE.md` |
| 历史证据 | `decomposition-bench/.research-state/ledger.jsonl` |

## 维护规则

- 不覆盖原始实验输出、失败记录和冻结材料。
- 当前 D1 已结束，不能按旧计划自动开始新任务。
- 若用户未来明确开启新研究，先创建新的实验名称和新计划。
- 改动治理文件或研究状态后运行 `python scripts/check_governance_integrity.py`。

