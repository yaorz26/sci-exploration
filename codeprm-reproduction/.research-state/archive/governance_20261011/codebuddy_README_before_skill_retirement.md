# `.codebuddy/` —— 项目级 AI 助手配置目录

建立时间：2026-09-19；最近修订：**2026-10-11（取消通俗汇报与项目记忆的强制加载）**
用途：存放本项目专用的项目级配置（常驻规则、技能正文），并登记**每一类内容的唯一权威位置**。

## 一、技能与规则的加载规则（2026-10-11 用户要求）

| 项目 | 加载方式 | 位置 |
| --- | --- | --- |
| 研究工作规程（原名"研究贡献循环"） | **每轮强制**（唯一一个）。**默认单步交付**；**用户明确授权"持续工作"后转持续模式**：连续推进直到目标达成或明确失败，每完成一项或每 2—3 轮交一次五件事简报，用户随时可叫停 | `.codebuddy/skills/research-contribution-loop/SKILL.md` |
| 通俗表达 | **按需**：用户要求"报告/解释/讲解"结果、过程、研究，或说"看不懂/这是什么意思/为什么"时才加载 | `.codebuddy/skills/plain-language-debrief/SKILL.md` |
| 研究问题循环协议 | 常驻，每会话首轮自动注入 | `.codebuddy/rules/02-研究问题循环协议.md` |

**研究工作规程承载的限制（2026-10-11 用户要求，写入技能第 1—10 节）**：事实只认原始证据（找不到就写"未知"，不靠记忆补全）；每项工作先写可见结果（只增文件/报告/检查数就不执行）；宏观计划锁定、局部任务不得改题（普通失败只换下一条已批准路径）；每项工作建立"问题—验证—判定"表（一个未知＋竞争解释＋最低成本验证＋事前判据）；困难问题走有限降级路线（修环境→缩规模→换数据/工具，两次尝试或约 30 分钟无新证据即停支路，不得把"没做成"包装成"边界发现"）；区分研究风险与操作风险（可逆本地操作直接执行，付费/训练/发布/删除/外部写入/改宏观计划才需确认）；每次交付回答五件事（做了什么／新证据／改变了哪个判断／还缺什么／下一条具体命令）；**推进模式由用户指令决定**（默认单步；授权后持续模式，检查点必须交简报，失效条件包括连续两轮无判断变化）。

**本次变更（2026-10-11，用户明确要求）**：
- **取消**通俗汇报的强制加载，改为上述按需条件触发；技能正文保留，术语表保留。
- **移除**项目记忆维护技能：`.codebuddy/skills/project-memory-maintainer/`、`.agents/skills/project-memory-maintainer/`、常驻规则 `01-项目记忆维护协议.md`、根目录 `PROJECT_MEMORY.md` 均已删除，不再每轮读写记忆。
- 删除前的原文备份在 `tmp/removed_skills_rules_20261011/`（仅作可撤销留痕，不属于生效配置）。
- `memory/` 目录与其中的历史文档**保留**（那是数据路线与研究发现的记录，不依赖已删技能即可阅读）；但它不再由任何每轮流程维护。

> **为什么是 `.codebuddy` 而不是 `.workbuddy`？**
> WorkBuddy 的**用户级**数据目录叫 `~/.workbuddy`，但**项目级**配置目录沿用 CodeBuddy Code 的
> `.codebuddy`，目录名恒为 `.codebuddy`。依据：WorkBuddy Desktop `app.asar` 中
> `packages/workbuddy-server/src/config/paths.ts` 的常量 `PROJECT_CONFIG_DIR_NAME = ".codebuddy"`。

## 二、权威归属表（一个机制只有一个家）

| 内容 | 唯一权威位置 | 其他位置只能 |
| --- | --- | --- |
| 加载哪几个技能、推进纪律、自审义务、汇报底线 | 根 `AGENTS.md` | 规则与技能不复述 |
| 通俗表达的方法与自检（按需加载） | `.codebuddy/skills/plain-language-debrief/SKILL.md` | 不再有对应常驻规则 |
| 研究循环的审查判据 | `.codebuddy/skills/research-contribution-loop/SKILL.md` | 规则只留硬约束与指针 |
| 题目 / 主问题 A / 成果 / 红线 | `codeprm-reproduction/.research-state/RESEARCH_TARGET.md` | 计划与状态不复述 |
| 阶段顺序 / 纳入标准 / 资源与失败转向 | 同目录 `RESEARCH_PLAN.md` | 目标与状态不复述 |
| 当前状态与待决项 | 同目录 `PROJECT_STATE.md` | 只放现状，历史进账本 |
| 历史恢复点与阶段结论 | 同目录 `ledger.jsonl`（追加式，只增不改） | 不堆回任何快照文件 |

**分工原则**：`rules/` 是"什么时候必须做"的硬约束（首轮注入，长会话被截断也仍是最强兜底）；`skills/` 是"怎么做"的方法与判据；`AGENTS.md` 是每轮读取的导航与纪律。

## 三、目录内容（与实际磁盘一致）

```text
.codebuddy/
├── README.md                                       ← 本文件
├── rules/
│   └── 02-研究问题循环协议.md                        ← 唯一的常驻规则
└── skills/
    ├── plain-language-debrief/                     ← 按需加载
    │   ├── SKILL.md
    │   └── references/术语大白话对照表.md
    └── research-contribution-loop/                 ← 每轮强制
        └── SKILL.md
```

## 四、`rules/` 的生效机制（已验证）

- 项目级规则路径：`<cwd>/.codebuddy/rules/*.md`（递归收集所有 `.md`）。
- 判定规则：无 `paths` 且无 `alwaysApply` → `type = always`；`alwaysApply: true` → `always`；`alwaysApply: false` 且无 `paths` → **整条丢弃**；带 `paths` → `manual`（Desktop 侧当前**不会**注入）。
- 注入方式：`always` 规则在**会话首轮**以 `<project_rules>` 注入系统提示，不做缓存。

## 五、技能的调用机制

项目级技能（`.codebuddy/skills/*/SKILL.md`）会被扫描进可用技能列表，但**系统不会自行执行技能**：正文要真正加载，必须由模型发起技能调用，或按 `AGENTS.md` 指示去读取对应文件。三条链：

| 链条 | 机制 | 强度 |
| --- | --- | --- |
| 规则注入链 | `rules/*.md` 中 `always` 规则首轮注入 `<project_rules>` | 最强，不依赖模型判断 |
| 发现链 | 技能被扫描进可用技能列表，模型可随时调用 | 中，依赖模型主动发起 |
| 指令链 | 根 `AGENTS.md` 明文规定加载规则 | 中，属指令遵守 |

**按需技能的可靠性**：`plain-language-debrief` 不再有常驻规则兜底，完全依赖 `AGENTS.md` 的指令链与发现链，因此**用户不提要求时不会被加载**——这是用户 2026-10-11 明确要的行为。

## 六、与 Codex 的兼容

- Codex 的仓库级技能发现入口为 `.agents/skills/<技能名>/SKILL.md`，只是跳转壳，不保存第二份正文。
- 当前 `.agents/skills/` 下只有 `research-contribution-loop`（因为它是唯一每轮强制加载的技能）。
- 技能正文以 `.codebuddy/skills/<名>/` 为唯一项目级来源。
- Codex 侧没有 `alwaysApply` 注入机制，只能依赖 `AGENTS.md` 的指令遵守。

## 七、用户级副本

- 用户级同名技能位于 `~/.workbuddy/skills/`（跨项目生效），其中包括一份 `plain-language-debrief`。
- **本项目以 `.codebuddy` 版为准**；助手不改动用户级目录。
- 其余用户级技能（`codex-bridge`、`hustoj-ac-export`、`win-shell-and-headless-render`）与本项目无关。

## 八、维护纪律

- **新增技能**：正文放 `.codebuddy/skills/<名>/`；若该技能需要每轮强制加载，才在 `.agents/skills/<名>/` 加跳转壳并在 `AGENTS.md` 第一节登记。
- **修改任何机制**：先改唯一权威位置，再检查 `AGENTS.md`、本 README、对应规则是否需要同步指针；**不得把正文复制进第二处**。
- **改完必须跑自检**：在仓库根目录执行 `python scripts/check_governance_integrity.py`。退出码 0 才算改完。
- **已删除配置的复现限制**：`codeprm-reproduction/experiments/` 下有 3 个历史 checkpoint 脚本（`d1_G2_confuse_pr142_env_source_v1_20261009/save_stage_checkpoint.py`、`d1_G3_contract_integrity_v1_20261009/save_user_interrupt.py`、`d1_G5_candidate_delivery_v1_20261009/save_cycle_checkpoint.py`）会读写 `PROJECT_MEMORY.md`。它们**已经执行过**、属一次性留痕脚本，未作修改；若以后重跑会因主记忆已删除而报错，这是预期行为。
