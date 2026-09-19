# `.codebuddy/` —— 项目级 AI 助手配置目录

建立时间：2026-09-19
用途：存放本项目专用的 WorkBuddy / CodeBuddy 项目级配置（规则、技能）。

> **为什么是 `.codebuddy` 而不是 `.workbuddy`？**
> WorkBuddy 的**用户级**数据目录叫 `~/.workbuddy`，但**项目级**配置目录沿用 CodeBuddy Code 的
> `.codebuddy`，目录名恒为 `.codebuddy`。依据：WorkBuddy Desktop `app.asar` 中
> `packages/workbuddy-server/src/config/paths.ts` 的注释与常量
> `PROJECT_CONFIG_DIR_NAME = ".codebuddy"`（源码原话："目录名恒为 `.codebuddy`（**不是** `.workbuddy`）"）。
> 这是读取程序本体得到的结论，不是猜测。

## 目录内容

```text
.codebuddy/
├── README.md                                   ← 本文件
├── rules/
│   └── 00-通俗完整汇报协议.md                   ← 常驻规则，每会话首轮自动注入
└── skills/
    └── plain-language-debrief/
        ├── SKILL.md                            ← 技能正文（四段式汇报协议）
        └── references/术语大白话对照表.md        ← 约 60 条项目术语的通俗解释
```

## `rules/` 的生效机制（已验证）

- 项目级规则路径：`<cwd>/.codebuddy/rules/*.md`（递归收集所有 `.md`）；
- 判定规则（与 agent-cli 的 `MemoryParserImpl` / `MemoryValidatorImpl` 逐条对齐）：

  | frontmatter | 结果 |
  | --- | --- |
  | 无 `paths`、无 `alwaysApply` | `type = always`（裸规则默认常驻） |
  | `alwaysApply: true` | `type = always` |
  | `alwaysApply: false` 且无 `paths` | **整条丢弃**（永远不命中的死规则） |
  | `paths: <glob>` | `type = manual`，需运行时触发信号 |

- 注入方式：`type === "always"` 的规则在**会话首轮**（`stage = first_turn`）以
  `<project_rules description="...">Contents of <path>: <content></project_rules>` 形式
  注入系统提示；**不做缓存**，按当前 cwd 现算。
- **重要限制**：Desktop 侧只注入 `type === "always"` 的规则；带 `paths` 的 `manual` 规则
  当前**不会**被注入（其触发信号在 cbc 进程内，daemon 侧拿不到）。

## 如何临时关闭

- 关掉汇报协议：把 `rules/00-通俗完整汇报协议.md` 的 frontmatter 改成 `enabled: false`
  （`enabled: false` 时整条规则不加载）；
- 只改效果不删文件：把 `alwaysApply` 改成 `false` 且**不加** `paths` → 该规则被丢弃，不生效；
- 关闭技能：在 settings 的 `skillOverrides` 里把 `plain-language-debrief` 设为 `off`。

## 与其他约定的关系

- 本目录**不参与**研究数据流，不存放实验数据、报告或切分；
- 汇报协议的完整背景见 `~/.workbuddy/MEMORY.md`（用户级偏好）与 `~/.workbuddy/SOUL.md`；
- 同名用户级技能副本位于 `~/.workbuddy/skills/plain-language-debrief/`，两份内容需保持同步。
