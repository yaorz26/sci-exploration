# 报告索引

`reports/` 保存正式报告、环境记录和机器可读摘要。报告文件保留原有名称，避免破坏历史引用；按研究线阅读即可。

## 目前最重要的报告

| 研究线 | 先读什么 | 结论 |
|---|---|---|
| FunPRM 扩量双确认 | `funprm_helperfirst_scale_confirmation_ab_20260926.md` | 两批各30题均为正，合并`12/60`对首候选`7/60`，冻结门槛通过；同池上限`14/60`，RL仍不自动启动 |
| FunPRM 函数前缀 | `funprm_exact_prefix_generative_result_20260922.md` | 新确认集 `15/30`，相对旧 neural-only `11/30` 有正向信号；RL 不因此启动 |
| FunPRM top-down 冒烟 | `funprm_topdown_phase1_smoke_20260922.md` | 单轮提示修复后仅覆盖 `6/10`，未过 `8/10` 门槛，停止扩量 |
| FunPRM 结构化 top-down | `funprm_topdown_structured_phase1b_20260922.md` | 契约覆盖 `9/10`，正式合规程序仅 `1/10`；事后机械装配为 `8/10`，不能翻案 |
| FunPRM 旧评分器 | `funprm_independent_confirmation_20260922.md` | public-assisted 路由不稳定，neural-only 更值得保留 |
| DecompRL 分层实验 | `p5b_stratified60_seed42_analysis_20260918.md` | prompt-only 模块化在困难层 No-Go |
| P5c 等预算对照 | `p5c_medium_k8_vs_equal_budget_m0_20260920.md` | 增加模块化搜索仍被直接生成超过 |
| P5d 函数化对照 | `p5d_functionized_vs_recombination_confirm19_20260920.md` | 完整函数化有探索性 +1，但未达到正向门槛 |
| 早期 CodePRM 基线 | `experiment_log.md` | 执行反馈选择有效，神经 PRM 当时没有超过 public 选择 |

## 目录约定

- `*_analysis_*.md`：结果解释和统计。
- `*_audit_*.json`：机器可读逐题审计。
- `checkpoint_*.json` / `environment.json`：运行环境和阶段快照。
- `run_log_*.md`：命令、成本和过程记录。

不要把只在一次对话里生成的临时截图或未引用草稿放进这里；它们应放在工作区 `archive/` 或 `tmp/`。
