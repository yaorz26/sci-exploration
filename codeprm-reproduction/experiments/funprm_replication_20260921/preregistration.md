# FunPRM 风格评分器复现：7B 留出实验协议

创建时间：2026-09-21  
状态：下载 7B 权重前冻结。训练集、留出集、选择规则和停止门槛固定后，不根据留出集私有结果改提示或改阈值。

## 1. 研究问题

在完整函数化候选已经存在的前提下，函数级评分器能否比只看 public pass rate 更好地选出 private 正确程序？这一步只研究选择器，不重新讨论 M2a 独立重组，也不启动 RL。

## 2. 论文机制的可复现范围

本地复现保留 FunPRM 的核心链条：

1. 候选是完整程序，但要求由多个顶层函数组成；
2. 把完整程序按顶层函数切成前缀节点；
3. 训练一个 QLoRA 评分器，输入题目、函数前缀、当前函数和已有 public 反馈；
4. 用训练集里的 continuation-level 标签做函数节点的 noisy supervision，用完整候选 private pass rate 做 clean final supervision；
5. 在新留出题上只用模型分数或 public+模型分数选择，最后一次性读取 private 评测。

由于本地没有论文作者的原始训练集、原始函数续写轨迹和原始 7B checkpoint，本实验不把“由完整候选派生函数前缀”冒充论文的逐函数 Monte Carlo 数据；报告中会单独标明这是受控的 FunPRM 风格缩小复现。

## 3. 数据隔离

- 训练材料：`data/processed/codeprm_continuation_train50_seed42_deployment_aligned.jsonl`，50 个问题、1196 个 continuation-level step records。只用于训练和训练集内诊断。
- 留出题：`data/raw/apps_train_new_intro_after50_function30.json`，30 个问题。该切分不进入训练、prompt 调整、候选预算或阈值选择。
- 留出候选：使用 `qwen2.5-coder:7b`、seed 42、每题 10 个 `functionized` 完整候选，沿用已冻结的 public/private evaluator。候选生成不读 private。
- private 只允许在 public 或模型选择完成后评估，禁止进入输入文本、训练标签、路由阈值或调参。

## 4. 固定模型和训练参数

- 基座：`Qwen/Qwen2.5-Coder-7B-Instruct`，本地 HF 目录 `models/Qwen2.5-Coder-7B-Instruct`；
- 训练：4-bit NF4、LoRA `r=8`、`alpha=16`、dropout `0.05`，目标模块 `q_proj/k_proj/v_proj/o_proj`，保存 `score` 头；
- tokenizer max length：512；batch size：1；gradient accumulation：4；learning rate：`1e-4`；epoch：1；seed：42；
- 标签：主运行使用 `step_label` 和 sigmoid MSE；另保存一个 candidate-level proxy 作为负对照，不把它称为 exact FunPRM；
- 候选评分：对每个候选的函数前缀节点取平均分；整题选择按最高平均分，分数相同按候选序号升序；另报告 `public pass rate -> neural tie-break` 的混合选择器。

### 4.1 预注册的奖励校正消融

为对应论文中“中间 noisy reward + 最终 clean reward/meta correction”的差异，固定再训练一个同结构 adapter，只把节点标签改为完整候选的 `final_label`。它不读取留出 private，不改变候选池；若它优于主运行，只能说明 clean-final supervision 在本地派生数据上更合适，不能声称已复现作者的 meta reward correction。

## 5. 预先判读规则

- 主门槛：在 30 个留出题上，模型选择的 private 全通过题数必须超过当前 public-only/F1 基线 11/19 的方向性门槛；这只是与既有 P5d 机制诊断的参照，不把不同题集直接做显著性检验。
- 主要可接受信号：在同一 30 题留出集上，`neural-only` 或 `public+neural tie-break` 的 selected private pass@1 高于 public-only，并且不使用 private 选择。
- 如果模型分数不如 public-only：记录为评分器未兑现候选池潜力，不启动 RL；优先检查标签、函数边界和训练/留出分布。
- 如果训练 loss 下降但留出选择不提升：视为测量失败或过拟合，不报告为正向结果。
- 只跑一个 seed 的 30 题结果是机制 pilot，不升级为稳定性结论；若通过门槛，再预注册第二个独立留出集和多 seed。

## 6. 成本与停止

- 7B HF 权重下载上限：20 GB；本机 D 盘剩余空间约 82 GB；
- 留出生成预算：30 题 × 10 候选，沿用既有 F1 预算；
- 评分器训练资源上限：单卡 RTX 4060 8GB，先跑 50 个 optimizer steps 冒烟，再跑 1 epoch；若 OOM，固定改为 max length 256、gradient accumulation 8，不改变数据或标签；
- 若 7B HF 权重无法下载或无法加载，3B 只做工程冒烟，不能替代正式 7B 结论。

## 7. 输出

- 候选：`data/processed/funprm_holdout30_f1_qwen25coder_7b_n10_seed42_v1_*`；
- 函数级训练记录：`data/processed/funprm_train50_function_nodes_v1.jsonl`；
- adapter：`outputs/models/funprm_qwen25coder_7b_function_v1/`；
- 选择评测：`data/processed/funprm_holdout30_selection_v1.json`；
- 报告：`reports/funprm_replication_20260921.md`。
