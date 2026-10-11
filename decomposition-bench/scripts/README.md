# 脚本索引

脚本按用途理解，不按文件名逐个试跑。所有命令默认在 `decomposition-bench/` 根目录执行。

## 当前主线

| 用途 | 脚本 |
|---|---|
| 函数前缀候选节点 | `build_funprm_function_nodes.py`, `build_funprm_candidate_nodes.py` |
| 函数前缀续写采集 | `collect_funprm_function_prefix_rollouts.py` |
| 真实测试重标 | `relabel_funprm_prefix_rollouts.py` |
| 标签审计 | `analyze_funprm_prefix_labels.py` |
| 生成式 PRM 训练 | `train_funprm_generative.py` |
| 生成式 PRM 选择与私有后评测 | `evaluate_funprm_generative.py` |
| 无执行反馈统计 | `analyze_funprm_no_execution.py` |
| 候选池上限 | `analyze_funprm_pool_oracle.py`, `compute_private_pool_oracle.py` |
| 结构化 top-down 冒烟 | `run_structured_topdown_experiment.py` |
| 结构化冒烟事后机械装配审计 | `analyze_structured_topdown_smoke.py` |

## 旧主线

- `run_whole_program_experiment.py`：直接生成/计划基线。
- `run_modular_smoke.py`：分解、独立实现和组合。
- `train_neural_prm.py`, `train_funprm_scorer.py`：较早的神经评分器路线。
- `analyze_p5_results.py`, `analyze_p5d_confirmation.py`：P5/P5d 结果分析。

运行前先确认输入数据、输出前缀、seed 和是否会调用 Ollama。高成本脚本不应在确认集上临时改参数重跑。
