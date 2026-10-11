# P5b 分层 60 题 Seed42 分析

## 范围

本报告覆盖冻结的 `experiments/decomp_strata_20260918/selection.json`：20 个
`simple_single_stage` 函数题、20 个 `medium_multi_stage` 函数题，以及 20 个
`hard_naturally_decomposable` 标准输入输出题。所有运行均使用 Qwen2.5-Coder 7B、seed42；M0/M1 每题两个候选，M2a/M2b 每题两个分解、每个函数两个实现、每个分解最多八种组合。

候选选择只使用公共测试。私有池 oracle 是选择完成后的诊断，遍历保存的每个唯一候选，不会影响候选选择。评测采用 `experiments/decomp_strata_20260918/evaluator_policy.md` 中冻结的本地策略；官方 APPS evaluator 未能取得，因此本结果不是官方 APPS 基准结果。

## 结果

所有全通过计数均以 20 题为分母。`候选题数` 表示至少有一个有效候选的题数，`公共全通过` 表示公共集选择结果，`私有全通过` 表示选择后私有评测结果，`池 oracle` 表示池中任一候选私有全通过。

| 分层 | 方法 | 候选题数 | 公共全通过 | 私有全通过 | 池 oracle | 生成/分解请求 | 实现请求 | 输入 token | 输出 token |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 简单 | M0 direct | 20 | 17 | 14 | 15 | 40 | - | 14,254 | 3,852 |
| 简单 | M1 plan | 19 | 15 | 12 | 14 | 40 | - | 15,014 | 7,397 |
| 简单 | M2a skeleton | 15 | 12 | 9 | 10 | 40 分解 | 210 | 133,998 | 23,362 |
| 简单 | M2b JSON | 13 | 8 | 7 | 7 | 40 分解 | 202 | 116,140 | 20,996 |
| 中等 | M0 direct | 19 | 6 | 3 | 3 | 40 | - | 25,156 | 8,292 |
| 中等 | M1 plan | 19 | 7 | 4 | 4 | 40 | - | 25,916 | 11,888 |
| 中等 | M2a skeleton | 13 | 4 | 2 | 2 | 40 分解 | 188 | 183,196 | 26,050 |
| 中等 | M2b JSON | 12 | 6 | 3 | 3 | 40 分解 | 210 | 203,242 | 29,013 |
| 困难 stdin | M0 direct | 20 | 1 | 1 | 1 | 40 | - | 30,996 | 9,909 |
| 困难 stdin | M1 plan | 20 | 0 | 0 | 0 | 40 | - | 31,756 | 13,148 |
| 困难 stdin | M2a skeleton | 15 | 0 | 0 | 0 | 40 分解 | 252 | 294,476 | 39,818 |
| 困难 stdin | M2b JSON | 13 | 0 | 0 | 0 | 40 分解 | 262 | 291,612 | 43,057 |

原始摘要和私有池 oracle 文件均位于 `data/processed/p5b_*_seed42_v1_*`。

## 解释

1. 在简单负对照层，M2a/M2b 在选择后私有正确率和池 oracle 上都落后于 M0/M1，同时输入 token 消耗约高一个数量级。
2. 在中等层，M1 是最强整题基线，私有全通过为 4/20；M2a 为 2/20，M2b 为 3/20。两种模块化协议均未超过基线，池 oracle 与选择后结果一致。
3. 在困难自然可分解 stdin 层，M0 私有全通过为 1/20；M1、M2a、M2b 均为 0/20，两个模块化池 oracle 也均为 0/20。在当前预算下没有模块化优势证据。M2 候选损失主要来自结构验证失败，而不是单纯执行器失败。

因此，在当前模型、提示、预算、数据切分和本地 evaluator 下，RL 继续保持 No-Go。预注册的双种子要求尚未完成：本报告只覆盖 seed42。seed43 复制实验的必要性与合理性已单独审查，见 `reports/p5b_seed43_experiment_preflight_review_20260918.md`；按当前决策门不启动该重复实验。

## 可复现入口

- 冻结成员：`experiments/decomp_strata_20260918/selection.json`
- 冻结切分清单：`data/splits/apps_stratified60_20260918.json`
- 正式摘要：`data/processed/p5b_*_summary.json`
- 池 oracle 脚本：`scripts/compute_private_pool_oracle.py`
- 池 oracle 输出：`data/processed/p5b_*_pool_oracle.json`
