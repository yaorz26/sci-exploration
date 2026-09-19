# P5c k=8 实验恢复说明（中断用）

更新：2026-09-19 16:30 前后
用途：任何新会话读此文件即可恢复被中断的 P5c 实验，不需要本日对话上下文。

## 实验是什么（预注册）

- 预注册文件：`experiments/p5c_medium_k8_20260919/preregistration.md`（含附录 A 全部修订，先读它）
- 一句话：中等层 20 题、M2a skeleton、复用 P5b 冻结分解、k 从 2 提到 8、repair_v1 提示、**A1 开启（允许嵌套函数）**、每题随机采样 64 组合（seed 42）、配等生成预算 M0 对照。

## 执行到哪一步了

| 步骤 | 状态 |
| --- | --- |
| 1. 预注册 + A1 可行性 + 评测解释器修复 | ✅ 完成（提交 6daba51、e183a00） |
| 2. **k=8 实现生成** | ⏳ **被中断于此步**（见下） |
| 3. 组合重放 + 池 oracle | 未开始 |
| 4. 阳性对照检查 | 未开始（并入步骤 3） |
| 5. 等预算 M0 对照 | 未开始 |
| 6. 报告 | 未开始 |

## 恢复命令（全部在 `D:\yaorz\research\codeprm-reproduction` 目录下执行）

**一律使用系统 Python**：`D:\yaorz\tools\python_new\python.exe`（P5b 同源解释器；禁止用其他解释器做任何评测，原因见 `reports/p5b_full_space_recombination_replay_20260919.md` 复检记录节）。

### 步骤 2 恢复（生成，脚本自带断点续跑，命令与原命令完全相同即可续跑）

```
D:\yaorz\tools\python_new\python.exe scripts\generate_extra_implementations.py --decompositions data/processed/p5b_medium20_m2a_skeleton_qwen25coder_7b_d2_i2_c8_seed42_v1_decompositions.jsonl --implementations data/processed/p5b_medium20_m2a_skeleton_qwen25coder_7b_d2_i2_c8_seed42_v1_implementations.jsonl --output data/processed/p5c_medium_k8_repairv1_seed42_v1_implementations.jsonl --k 8 --retries 1 --allow-nested
```

- 脚本按 `(problem_id, decomposition_index, function_name, implementation_index)` 逐条写入并 flush，重启后自动跳过已完成项；
- 若上次中断切在半行，续跑会自动丢弃末尾截断行（2026-09-19 已加固）；
- 完成标志：输出目录出现 `p5c_medium_k8_repairv1_seed42_v1_implementations_summary.json`；
- 进度日志：`p5c_medium_k8_repairv1_seed42_v1_implementations_progress.log`。

### 步骤 3（生成完成后）

```
D:\yaorz\tools\python_new\python.exe scripts\replay_full_combination_space.py --decompositions data/processed/p5b_medium20_m2a_skeleton_qwen25coder_7b_d2_i2_c8_seed42_v1_decompositions.jsonl --implementations data/processed/p5c_medium_k8_repairv1_seed42_v1_implementations.jsonl --output data/processed/p5c_medium_k8_repairv1_seed42_v1_recombinations.jsonl --allow-nested-functions --sample 64 --sample-seed 42
```

注意：此步的 `--implementations` 要**同时包含 P5b 原有实现与新生成实现**。`replay_full_combination_space.py` 只接受单个文件——需要先把两个 JSONL 合并（`scripts/merge_jsonl.py` 可用，或 cat），或改脚本支持多输入。**这是恢复时最先要确认的接口细节。**

```
D:\yaorz\tools\python_new\python.exe scripts\compute_private_pool_oracle.py --data data/processed/apps_stratified60_20260918.json --input data/processed/p5c_medium_k8_repairv1_seed42_v1_recombinations.jsonl --output data/processed/p5c_medium_k8_repairv1_seed42_v1_pool_oracle.json --timeout 10 --candidate-timeout 10
```

### 步骤 4 阳性对照（强制）

apps-train-1642 与 apps-train-1649 在 P5b 中有已知全过候选；重放后这两个题的池 oracle 必须仍 ≥ P5b 水平（1642: 2 个全过候选、1649: 6 个）。若不满足，评测环境有问题，停止并排查（解释器 / 预算耗尽）。

### 步骤 5 等预算 M0 对照

按预注册第 4 节：先统计步骤 2+3 的实际 `model_output_tokens` 总量，用 P5b 中等层 M0 的"每程序平均输出 token"换算出 M0 每题候选数 N，冻结后再跑。M0 生成用 `scripts/run_baseline.py`（需核对其参数）或 `src/whole_program.py` 的 WholeProgramGenerator。

## 评测纪律（违反即结果作废）

1. 只用系统 Python 3.13.7 做评测；
2. 评测必须带阳性对照；
3. 必须报告预算耗尽（budget_exhausted）计数；
4. private 只用于选择冻结后的诊断与最终评测；
5. 不覆盖既有文件，一切新产物用新后缀。

## 相关文件

- 生成脚本：`scripts/generate_extra_implementations.py`（含断点续跑与 A1 恢复逻辑）
- 组合重放：`scripts/replay_full_combination_space.py`（含 --allow-nested-functions / --sample / --sample-seed）
- 穷举重放报告（含解释器缺陷与复检记录）：`reports/p5b_full_space_recombination_replay_20260919.md`
- 项目总入口：`D:\yaorz\research\当前情况总结.md`
