# FunPRM 同分布 7B 评分器：留出结果审计

## 一句话结论

`public + 7B 函数评分器` 比只看 public 多做对了 1 题，但全部净收益来自同一道题；这是值得独立复验的正向线索，还不是可观或稳定的正向结果。

## 大白话解释

这次评分器在 28 道有有效候选的题里改选了 18 道。看起来动作很大，但 17 道换完以后最终对错没有变化：要么两个候选都全对，要么两个都没全对。

唯一真正有用的变化发生在 `apps-train-2723`：只看 public 选中的候选，private 通过率是 `0.6`；用评分器给 public 同分候选打破平局后，private 通过率变成 `1.0`。没有任何题从“全对”被换成“不全对”。因此总分从 `17/28` 变成 `18/28`。

可以把它理解成：评分器在 18 次换人里，有 1 次把正确替补换上场，其余 17 次没有改变胜负。方向是好的，但证据仍集中在一次成功上。

## 严谨口径

- 模型：`Qwen2.5-Coder-7B-Instruct`，4-bit QLoRA；
- 训练：50 个不重叠 APPS introductory 训练题，7B functionized 候选派生 1,154 个函数节点；
- 留出：30 题，28 题至少有一个结构有效候选；每题最多 10 个候选；seed 42；
- public-only：private 全通过 `17/28 = 60.71%`，平均 private pass rate `0.70744`；
- neural-only：private 全通过 `17/28 = 60.71%`，平均 private pass rate `0.68601`；
- public+neural：private 全通过 `18/28 = 64.29%`，平均 private pass rate `0.72173`；
- 配对净变化：全通过 `+1/28 = +3.57` 个百分点；平均 private pass rate `+0.01429`；
- 改选 18 题；全通过结局的 discordant pair 为 `1 win / 0 loss`；双侧精确符号检验 `p=1.0`；
- 100,000 次按题 bootstrap：全通过差值 95% 区间和平均 pass-rate 差值 95% 区间见机器可读审计输出；区间包含 0；
- 选择输入不含 private 字段；private 只在 public/neural 选择索引冻结后评测；
- 这是单一自定义切分、单 seed 的探索性结果，不能称为稳定复现或显著收益。

机器可读证据：

- `data/processed/funprm_holdout30_selection_samedist_v2.json`
- `data/processed/funprm_samedist_holdout_audit_20260922.json`
- `outputs/models/funprm_qwen25coder_7b_function_samedist_v2/metrics.json`

## 阶段与方向审查

阶段状态：`pass with weak positive signal`。流程、隔离和评测有效，但效应只由一题贡献。

方向选择：保持当前 adapter 和选择规则冻结，使用从未用于训练或调试的新题做一次独立确认。拒绝在当前 30 题上继续调超参数，因为那会把留出集变成训练集；拒绝直接启动 RL，因为当前正向证据太弱。
