# FunPRM 真实函数前缀生成式 PRM：结果报告

日期：2026-09-22  
阶段：`funprm_exact_prefix_20260922`  
状态：确认集完成；RL 仍保持 No-Go。

## 结论先说

这次按论文机制重做的本地 7B 生成式 PRM，在此前未触碰的 30 题确认集上得到 **15/30** 的 neural-only 私有全通过，旧版本同口径基线为 **11/30**，固定首候选为 **8/30**，均匀随机单候选期望为 **9/30**。

因此得到一个可观但有限的正向结果：

- 相对旧 neural-only 基线：`+4` 题，pass@1 从 `11/30` 到 `15/30`；
- 相对固定首候选：`8` 胜、`1` 负，精确双侧符号检验 `p=0.0390625`；
- 相对随机单候选期望：`+6` 题，bootstrap 95% CI 为 `[0.0767, 0.3333]`；
- 候选池 private oracle 为 `18/30`，新 PRM 兑现其中 `15` 题，仍有 `3` 题 headroom 未兑现。

选择时没有使用 public/private 测试字段；private 评测只在候选选择冻结后运行。

## 实验链条

1. 从训练 50 题的真实函数前缀出发，得到 48 题、103 个非最终函数前缀节点。
2. 每个节点用本地 `qwen2.5-coder:7b` 独立续写 4 次，共 412 次已缓存 rollout。
3. 发现旧结构门禁错误要求入口函数位于最后；按真实 private unit-test 结果离线重标后，成功 rollout 从 `47/412` 改为 `160/412`，正节点 `54/103`，split-half Pearson 从 `0.488` 升到 `0.808`。
4. 用本地 `Qwen2.5-Coder-7B-Instruct` 做 4-bit QLoRA，soft `+/-` token 目标，10 epochs、99 steps、`max_length=768`。按问题切分的 24 节点留出 MSE=`0.13485`、MAE=`0.24357`。
5. 旧开发 30 题得到 `17/30`，满足确认准入最低门槛但没有达到预注册的 `18/30` 开发改进门槛。
6. 不调参、不重新生成候选，直接在此前未触碰的 after80 30 题候选池上确认，得到本报告的 `15/30`。

## 关键文件

- 训练标签审计：`data/processed/funprm_exact_prefix_train50_k4_seed42000_20260922_unit_reward_audit.json`
- 训练 adapter 与误差：`outputs/models/funprm_qwen25coder_7b_generative_exact_prefix_k4_v1/metrics.json`
- 旧开发选择：`data/processed/funprm_holdout30_generative_exact_prefix_k4_v1.json`
- 旧开发审计：`data/processed/funprm_holdout30_generative_exact_prefix_k4_v1_audit.json`
- 确认选择：`data/processed/funprm_confirm_after80_generative_exact_prefix_k4_v1.json`
- 确认审计：`data/processed/funprm_confirm_after80_generative_exact_prefix_k4_v1_audit.json`
- 确认候选池上限：`data/processed/funprm_confirm_after80_pool_oracle_20260922.json`

## 限定与下一步

这不是论文的逐字完整复现：本地教师是 7B 而非论文级更强模型，训练源候选仍是 helper-first，而 FunPRM 的 CoF 轨迹强调 main/high-level function first；数据量也只有 48 个训练问题。因此应把结果称为“论文机制的本地正向复现信号”，不能宣称普遍性能提升。

当前最合理的停止点是：保留这条 neural-only 正向结果，停止在确认集继续调参；RL 仍 No-Go。若要继续，应先按论文顺序重新生成 top-down CoF 轨迹，再做独立多切分确认，而不是在本确认集上迭代。
