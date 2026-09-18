# 项目状态

最后更新：2026-09-18T08:44:09.958299Z
状态：进行中
文档语言：中文。后续报告、汇报、结果文档默认使用中文；代码标识、路径、模型名和原始 JSON 字段保持原样。

## 任务契约

- 目标：在本地 8GB/Qwen2.5-Coder 7B 条件下，判断模块化代码生成在任何 RL 训练前是否具有可靠优势。
- 交付和成功标准：可预注册、无泄漏、三分层确认实验；候选、成本、公共选择和私有后评测均可追溯。
- 约束：只使用自定义 APPS 切分；冻结的 P5 结果不可调参；私有测试不影响成员资格、提示或选择；RL 保持暂停。

## 已验证发现

- P5 Interview function25 未发现模块化方法相对 M1 在选择后私有全通过或池 oracle 上的稳定自动优势。
- M2 协议会拒绝实现签名不符、未声明的额外函数、嵌套函数和额外顶层语句；直接整题回退默认关闭并单独计数。
- 已评分的 Interview-25 和 development-20 不得进入新的确认性切分。
- P5b 60 题切分已冻结，本地 evaluator 策略已明确；官方 APPS evaluator 未取得。
- seed42 三层四方法共 12 个正式运行已完成，私有池 oracle 已在选择后计算。
- 困难层 seed42：M0 选择后私有全通过 1/20、池 oracle 1/20；M1/M2a/M2b 均为 0/20。

## 工作假设和预测

- H1：模块化生成不会在简单单阶段任务上超过 M1，但在有明确独立阶段的困难任务上可能改善选择后私有全通过和池 oracle。
- 证伪条件：困难层 M2 在两个 seed 上不能同时超过 M1 的两个主要指标，或收益来自未报告的直接回退/额外预算。

## 当前工作

- 最近完成：完成 seed42 全部正式运行、私有池 oracle、中文结果报告，以及 seed43 实验必要性与合理性审查；新增 M2 错误归因审计。
- 当前判断：seed42 困难层没有模块化正向信号，M2 候选结构失败率高且生成成本显著更大。
- 当前审计结论：六个正式 M2 分解记录集均已逐条复核；仅空文档错误记录为 0。实现语法解析总体通过，但嵌套函数、额外函数和缺失目标函数仍导致实现池/组合淘汰；困难层已形成候选的 M2a/M2b 私有池 oracle 均为 0/20。
- 离线 API 重验证结论：困难层 M2a/M2b 候选数、公共选择、私有通过值均未改变；选中候选 ID 20/20 一致。因此 API 门控不是当前 No-Go 的主要解释。
- 协议修复 pilot 结论：repair_v1 将未评分 5 题的候选形成率从 3/5 提高到 4/5，实现有效率从 13/14 提高到 14/14；拓扑排序补生成消除了单题结构阻塞，但公共全通过候选仍为 0/5，未达到扩展门槛。
- 语义归因结论：已形成候选的失败均为 wrong_answer，主要是算法理解、阶段契约或全局构造错误，而不是 composer/evaluator 故障。
- 静态契约审计结论：正式困难层实现池中发现 53 条辅助函数 I/O 违规（M2a 18、M2b 35）；简单/中等层为 0。声明依赖未调用在 skeleton 中受自动前置依赖规则放大，不能直接当作语义错误。
- helper I/O 硬门控反事实结论：离线拒绝违规实现使候选覆盖从 M2a `15/20` 降至 `12/20`、M2b `13/20` 降至 `7/20`，选择后私有全通过仍为 `0/20`；硬门控不是可接受的直接修复。
- 下一步：不扩大 repair_v1，不启动 seed43 或 RL。若继续研究，只应围绕“阶段契约改善算法正确率”提出新假设；否则保持当前 No-Go 并整理交付。

## 实验前审查结论

- seed43 对当前 RL 决策不是必要的：负结果只会重复 No-Go，正结果若与 seed42 方向不一致也不能通过“两个 seed 方向一致”的预注册门槛。
- 继续原样重复会产生很高模型调用成本，但不能修复已观察到的 M2 结构协议瓶颈。
- 当前结论强度：在 seed42、当前模型/提示/预算/切分/本地 evaluator 下 No-Go；双 seed 稳定性未估计。

## 开放问题和风险

- 自适应路由仍只有代码级验证，没有模型运行证据。
- 当前自定义 APPS 公共和私有切分支持本地机制研究，不等同于官方 APPS 基准。
- 若未来要研究稳定性，应先明确新的信息需求；不能为了形式上的双 seed 数量直接复用同一协议。

## 关键产物

- `reports/p5_interview_function25_analysis_20260917.md`：冻结 P5 结果
- `experiments/decomprl_20260914/manifest.json`：P0-P5 来源
- `experiments/decomp_strata_20260918/selection.json`：冻结成员资格
- `experiments/decomp_strata_20260918/README.md`：中文实验协议
- `experiments/decomp_strata_20260918/evaluator_policy.md`：中文评测策略
- `reports/p5b_stratified60_seed42_analysis_20260918.md`：中文 seed42 结果
- `reports/p5b_seed43_experiment_preflight_review_20260918.md`：seed43 实验前审查
- `reports/p5b_seed42_error_attribution_20260918.md`：M2 错误归因审计
- `reports/p5b_hard_seed42_offline_api_revalidation_20260918.md`：困难层离线 API 重验证
- `reports/p5b_protocol_repair_pilot_plan_20260918.md`：协议修复 pilot 计划
- `reports/p5b_protocol_repair_pilot_result_20260918.md`：协议修复 pilot 结果
- `reports/p5b_protocol_repair_semantic_attribution_20260918.md`：协议修复 pilot 语义归因
- `reports/p5b_contract_audit_20260918.md`：实现阶段静态契约审计
- `reports/p5b_helper_io_gate_counterfactual_20260918.md`：helper I/O 硬门控反事实重放
- `scripts/compute_private_pool_oracle.py`：选择后池诊断
