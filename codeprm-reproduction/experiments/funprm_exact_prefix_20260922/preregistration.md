# FunPRM 真实函数前缀续写与生成式 PRM：开发阶段协议

创建时间：2026-09-22  
状态：**已完成确认；412 次采集、unit-test-only 重标、7B 生成式 PRM 训练和一批全新30题确认均已完成**。

## 1. 目标

把当前“完整候选标签复制到各函数边界”的代理监督，替换为 FunPRM 原论文定义的函数前缀 Monte Carlo 续写标签；随后训练使用 `+/-` 下一 token 概率的 7B 生成式 PRM。此阶段只做训练和旧开发集选择，不读取新的确认集来调参。

## 2. 数据与源轨迹

- 问题：`apps_train_introductory50_private_safe.json`，仅训练用途；
- 源候选：现有 7B functionized 训练池；每题按候选序号取第一个结构有效、代码唯一的候选，不按 public/private 成绩选择；
- 节点：源候选按顶层函数切分，对每个非最终函数边界保留从文件开头到该函数结尾的真实代码前缀；
- 最终完整候选的 private 全通过值作为 clean final reward，与 partial reward 分开保存。

## 3. Monte Carlo 标签

- 续写模型：Ollama `qwen2.5-coder:7b`；temperature 0.7；
- 每个 partial prefix 独立续写 4 次；seed 由 problem/source candidate/function index/rollout index 确定；
- prompt 包含题面、starter API 和代码前缀，不包含 public/private 测试、执行结果或标签；
- 模型只补齐剩余顶层函数，原前缀不得修改；结构或执行无效的续写按失败计；
- 节点标签为 4 次续写中 private 全通过的比例，只使用训练 split private；
- 最大 600 次请求；预计请求数在第一调用前计算，超过上限则停止。

## 4. 生成式 PRM

- 基座：本地 `Qwen2.5-Coder-7B-Instruct`，4-bit QLoRA；
- 提示与论文一致地要求只输出 `+` 或 `-`；分数为 `p(+) / (p(+) + p(-))`；
- partial 使用 soft Monte Carlo 标签训练；clean final 数据只用于明确标注的最终监督或后续 meta correction，不把普通混合训练冒充论文的双层元学习；
- LoRA：r=8、alpha=16、dropout=0.05，目标 q/k/v/o projection；训练/验证按 problem 划分。
- 训练前 token 长度审计发现 103 个节点中 46 个超过 512 token、15 个超过 768 token，因此本次冻结 `max_length=768`；这是在看到开发集结果前作出的输入完整性修正。

## 5. 开发门槛

- 旧留出 30 题已降级为开发集；比较只使用 neural-only，不使用 public/private 执行反馈选候选；
- 当前 neural-only 基线为 17/30，固定首候选为 14/30，随机单候选期望为 10.8/30；
- 新模型达到至少 17/30 且相对随机单候选保持正向，才允许在 skip110 后另取全新确认集；达到 18/30 及以上视为开发改进；
- 未过门槛则停止该实现，不在开发集反复试权重；RL 始终不由本阶段触发。

## 6. 实际结果回填

- 训练重标：`113/412` 个 rollout 标签因旧结构门禁被纠正；成功 rollout=`160/412`，正节点=`54/103`，split-half Pearson=`0.8080`。
- 训练：Qwen2.5-Coder-7B-Instruct 4-bit QLoRA，10 epochs、99 steps、`max_length=768`；问题切分留出 MSE=`0.13485`、MAE=`0.24357`。
- 旧开发30题：neural-only=`17/30`，固定首候选=`14/30`，随机期望=`10.8/30`。达到确认准入门槛，但未达到预注册的18/30开发改进门槛。
- 全新确认30题：neural-only=`15/30`（覆盖15/27），固定首候选=`8/30`，随机期望=`9/30`，pool oracle=`18/30`；相对首候选8胜1负，精确双侧符号检验`p=0.0391`，随机 bootstrap CI=`[0.0767,0.3333]`。
- 结论：保留为“论文机制的本地正向复现信号”，停止确认集调参；由于本地教师为7B且源轨迹仍helper-first，不称为论文逐字完整复现。RL继续No-Go。
