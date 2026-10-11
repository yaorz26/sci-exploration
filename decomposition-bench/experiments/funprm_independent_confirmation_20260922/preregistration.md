# FunPRM 同分布 7B 评分器：独立确认实验

创建时间：2026-09-22  
状态：**已完成；预注册主指标方向反转，事后论文口径 neural-only 为正**。

## 1. 研究问题

上一批留出题中，`public pass rate + 7B 函数评分器打破同分` 从 `17/28` 提高到 `18/28`，但净收益只来自一题。本实验检验：在完全未参与训练、调参和上一轮留出评测的新题上，这个方向能否重复。

## 2. 冻结数据规则

- 数据源：`codeparrot/apps`，revision `21e74ddf8de1a21436da12e3e653065c5213e9d1`；
- split：`train`；difficulty：`introductory`；
- 按固定源顺序跳过前 80 个有至少两个测试的可用题，取接下来 30 题；
- 只接受带可解析 Python `def` starter API 的题；若少于 25 题满足该条件，模型调用前停止并新建协议，不临时补题；
- 在任何模型调用前运行 prompt-visible private 清理：若 private 测试的非空 input 和 output 同时出现在题面，删除该 private case；删除后无 private case 的题移出确认集；
- 成员资格不使用模型输出、public 成绩或 private 成绩。

前 50 个题已用于同分布训练；接下来的 30 个题已用于探索性留出。本实验从第 81 个可用题开始，题目不重叠。

## 3. 冻结模型与生成协议

- 候选生成器：Ollama `qwen2.5-coder:7b`，seed 42；
- 方法：`functionized` 完整程序，同一响应生成 2-5 个顶层函数；
- 每题 10 个候选；private 延后；每个测试超时 10 秒；
- 评分基座：HF `Qwen2.5-Coder-7B-Instruct` 4-bit；
- adapter：`outputs/models/funprm_qwen25coder_7b_function_samedist_v2/adapter_model.safetensors`；
- adapter SHA-256：`ee3aa919a606e9e8e8971debf95d7aabf8ea38a15e7a65f34deb1807adeada90`；
- 训练节点：`data/processed/funprm_train50_7b_function_nodes_v2.jsonl`；
- 训练节点 SHA-256：`d2161d75c089d0666127db278b14d897c01b616bbd47910fc7252cd63c5c4aa4`；
- 不重训、不调整 learning rate、epoch、label、prompt、候选数或选择权重。

## 4. 冻结选择规则

对每个结构有效候选，计算顶层函数节点得分的平均值。

- `public-only`：先按 public pass rate 降序，再按候选序号升序；
- `neural-only`：先按函数节点平均分降序，再按候选序号升序；
- `public+neural`：先按 public pass rate 降序，再按神经分数降序，最后按候选序号升序；
- private 在三个选择索引全部冻结后才执行；private 不进入 prompt、神经输入、候选过滤或 tie-break。

## 5. 指标与判读

主要指标：`public+neural` 相对 `public-only` 的选择后 private 全通过题数差，分母同时报告全部确认题和有有效候选的覆盖题。

次要指标：平均 private pass rate 差、改选题数、hybrid wins/losses、候选覆盖、结构有效率、pool oracle 和成本。

预先判读：

- 净增至少 `2` 题，且 hybrid losses 不超过 wins：记为“独立确认出现正向机制信号”；
- 净增 `1` 题：记为“弱重复，仍不足以称为可观或稳定”；
- 净增 `0` 题：记为“未独立复现”；
- 净增为负：记为“方向反转”；
- 无论结果如何，本轮后不在该确认集上调参；若正向，再另行决定是否做生成 seed 稳定性；若未复现，停止当前评分器分支；
- 本实验本身不触发 RL。RL 需要至少两个独立数据切分方向一致，并单独预注册训练目标。

## 6. 预算与停止条件

- 最大模型调用：30 题 × 10 候选 = 300 次 Ollama 请求；
- 评分：只使用冻结的一个 adapter；
- 数据抓取最多重试 2 次；模型请求沿用 runner 的单请求超时，不手工补生成失败候选；
- 出现题目重叠、adapter hash 不一致、private 提前读取或选择规则变化时，立即作废；
- 输出使用 `funprm_confirm_after80_..._20260922` 前缀，不覆盖已有结果。

## 7. 冻结后结果

- 生成：300/300 请求；177 个结构有效、159 个唯一候选；27/30 题有有效候选；生成阶段 private 评测为 0。
- public-only：18/30 全通过；public+neural：17/30 全通过；净变化 `-1`。
- 评分器改选 10 题，wins/losses=`0/1`；预注册正向门槛未通过，结果属于“方向反转”。
- 事后 pool oracle 为 18/30，且可全通过的题与 public-only 的 18 题完全相同；本候选池没有 pass@1 上升空间。
- 预注册主指标决策：不在该确认集调参，停止 public-assisted 路由，RL 不启动。事后论文口径审计保留 neural-only 为下一阶段基线。详见 `reports/funprm_independent_confirmation_20260922.md`。

事后论文口径补充（不替代上面的预注册判定）：FunPRM 原论文推理时不使用 public 测试。按 neural-only Best-of-10 对单次生成比较，本独立集为 11/30，对固定首候选 8/30、对随机单候选期望 9/30，分别为 `+3` 和 `+2` 题。该方向与旧开发集一致，但独立集区间仍包含 0，记为正向机制信号而非确认成功。
