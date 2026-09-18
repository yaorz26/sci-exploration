# 下一阶段研究计划：神经 CodePRM 与结构化执行反馈扩展

更新时间：2026-09-05  
工作目录：`D:\yaorz\research\codeprm-reproduction`

## 1. 研究定位

当前缩小规模复现已经得到三个可靠观察：

1. 在固定 APPS train-50 子集、3 个 seed 上，public pass-rate 选择稳定优于首候选；
2. Ridge 替身中，soft CodePRM 的平均 private pass rate 高于 normal/code-only，但 pass@1 的标签结论不完全一致；
3. 模型驱动 GVR 有小幅净收益，主要瓶颈仍是错误步骤定位和重写质量。

因此下一阶段的核心问题不是继续堆搜索 rollout，而是验证：

> 学习到的执行反馈过程评分器，是否能超过直接使用 public pass rate 的选择器，并进一步提升 GVR 的定位和修正质量？

推荐研究题目：

> 面向函数式代码生成的结构化执行反馈过程奖励模型

主线采用“神经 CodePRM 基线 → GVR 误差分析 → 函数/AST/错误结构扩展 → 官方数据验证”的顺序。

## 2. 当前环境可行性

| 条目 | 检查结果 | 判断 |
| --- | --- | --- |
| GPU | RTX 4060 Laptop，8188 MiB，约 6.5GB 可用 | 3B 4-bit/LoRA 可行；7B 需严格 QLoRA 设置 |
| WSL | Ubuntu 22.04，Python 3.10.12，CUDA `nvidia-smi` 可见 | 训练环境可建立 |
| Windows 主环境 | Python 3.13，Transformers/PEFT 未安装，PyTorch 为 CPU 版 | 不作为神经训练环境 |
| WSL 训练依赖 | 已安装 torch 2.6.0+cu124、transformers 4.57.6、datasets 3.6.0、peft 0.20.0、accelerate 1.14.0、bitsandbytes 0.50.2 | T01 smoke 已通过 |
| 磁盘 | D 盘约 167GB 可用，WSL 根文件系统约 939GB 可用 | 3B 权重、缓存和数据可容纳；需保留清理策略 |
| 本地生成模型 | Ollama 已有 Qwen2.5-Coder 1.5B/3B | 继续作为候选生成器 |
| 真实数据 | APPS train Introductory 20/50 已固定 | 可直接复用；官方 test 仍需单独获取 |
| 执行器 | 函数式 APPS 已支持，E0 全部通过 | 研究闭环可运行；安全隔离仍需加强 |

结论：

- **A 级可行**：WSL 环境、3B 小型 LoRA/QLoRA、APPS train-50/100、PRM 消融、GVR 分析；
- **B 级条件可行**：官方 APPS test、APPS 600 题；
- **本项目明确跳过**：7B QLoRA/全量训练、Codeforces、对抗代码执行。它们不进入当前主线的指标和结论。

## 3. 研究问题与假设

### RQ1：执行反馈是否让学习评分器超过直接 public 选择？

- H1：题目 + 思路 + 代码 + public 执行反馈的神经 CodePRM，在 held-out problems 上超过题目 + 思路和题目 + 思路 + 代码；
- 比较对象必须使用相同候选池、相同训练题/测试题划分和相同随机种子；
- 直接 public pass-rate 选择器作为上限参考，不把它误称为 PRM。

### RQ2：soft label 与 binary label 的优势分别体现在哪里？

- H2：soft label 更有利于 pass-rate 和排序相关性；
- binary label 可能在 pass@1 上更强；
- 需要同时报告 Spearman、pairwise accuracy、pass rate、pass@1，避免只看单一指标。

### RQ3：GVR 的瓶颈是定位还是重写？

- H3：PRM 选错步骤时，重写模型质量提升也很有限；
- 分离记录定位正确率、重写接受率、接受后退化率和 public/private 不一致率；
- 比较固定阈值、最低分、adaptive stop 和错误类型条件化策略。

### RQ4：函数/AST/错误结构能否带来额外收益？

- H4：在函数式任务上，函数签名、AST 摘要、异常类别和失败测试摘要能改善步骤定位；
- 只有在基础神经 CodePRM 跑通后加入结构特征，避免混淆收益来源。

## 4. 任务分解与验收标准

### T00：冻结当前复现基线

输入：train-50 固定数据、3 seed baseline、Level-2、GVR、MCTS、model-GVR。  
产物：结果索引、环境快照、数据 SHA-256、统一指标表。  
验收：所有结果均能从 checkpoint 重新定位；不覆盖已有输出。

### T01：建立 WSL 神经训练环境（已完成）

环境：Ubuntu 22.04、Python 3.10、独立 virtualenv。  
依赖：CUDA PyTorch、Transformers、Datasets、PEFT、Accelerate、bitsandbytes。  
验收：

1. `torch.cuda.is_available()` 为真；
2. 单 batch 3B 4-bit 模型能完成 forward/backward；
3. 显存峰值低于 7.5GB；
4. 保存一个最小 checkpoint 并能重新加载。

结果：Qwen2.5-Coder 3B 本地 4-bit 加载、LoRA 注入和单 batch backward 均通过；训练参数约 3.69M，memory reserved 约 4.43GB。模型通过 Windows 宿主机下载后从 `/mnt/d` 加载，因为 WSL 直连 Hugging Face 不可用。复现脚本为 `scripts/neural_smoke.py`，依赖清单为 `requirements-neural-wsl.txt`，结果为 `reports/t01_neural_smoke_2026-09-05.json`。

降级路径：3B 正式训练出现 OOM 时使用 1.5B；仍 OOM 时先运行冻结 backbone + 线性/MLP head，保留数据和评测结论。

### T02：构造论文风格训练记录（首个严格小样本已完成）

当前记录是候选级反馈；神经 CodePRM 需要步骤级样本：

```text
problem
→ thought step i
→ code continuation / generated code
→ public execution feedback
→ private pass-rate label
```

产物：

- `data/processed/codeprm_step_records_train50.jsonl`；
- soft label 与 binary label 两套目标；
- 题目分组 split manifest；
- 每条记录的 prompt、代码、反馈、标签和模型版本。

当前结果：三个 seed 已生成 proxy 步骤记录；train-20 的三个 seed 已生成严格 continuation-level 记录：seed42 为 118 个思路节点/236 条记录，seed43 和 seed44 各为 120 个节点/240 条记录。设置均为 2 个候选、最多 3 步、每节点 2 个 continuation。每个节点标签都经过 continuation private pass rate 均值校验，并写入 `exact_step_label=true`。proxy 记录仍保留作流程回归，不与严格标签结果混用。

验收：同一题的候选不能跨 train/test；private 内容只用于 label 和最终评估；随机抽查 50 条可由执行记录重算。

### T03：3B 神经 CodePRM pilot（首轮已完成）

设置：

- backbone：Qwen2.5-Coder 3B；
- 4-bit load + LoRA/QLoRA；
- sequence length 1024 起步，batch size 1，gradient accumulation；
- train 37 problems，test 13 problems，至少 3 seed；
- 先训练 soft label，再训练 binary label。

对照：

1. normal PRM：问题 + 思路；
2. code-only PRM：问题 + 思路 + 代码；
3. CodePRM：问题 + 思路 + 代码 + public feedback。

当前结果：严格 continuation 标签的 train-20 三种子首轮 1 epoch 已完成（每次 15/5 题、45/44 optimizer steps）。线性 head 的神经选择 private pass rate 分别为 `0.533/0.400/0.200`，首候选分别为 `0.467/0.400/0.333`；三种子均值为 `0.378 +/- 0.168` 对 `0.400 +/- 0.067`，平均选择增益为 `-0.022`。步骤 Spearman 为 `-0.152/-0.173/-0.262`，均值 `-0.196 +/- 0.059`。随后修正为 sigmoid 输出并训练 3 epoch：独立三种子 step MSE 为 `0.217 +/- 0.006`，Spearman 为 `-0.030 +/- 0.160`；将 716 条三种子记录合并训练后，在三个候选池上的 neural 选择均值为 `0.456 +/- 0.069`，仍低于 public 选择的 `0.633`。因此严格标签、sigmoid 校准和 pooled 训练链路均可用，但 train-20 尚未证明神经评分器能够超过直接执行反馈；结构化特征消融暂缓到 train-50/100 数据扩展之后。汇总文件为 `reports/neural_pilot_exact_train20_3seed_sigmoid_epoch3_2026-09-05.json`，pooled 评估位于 `outputs/neural_pilot/train20_allseeds_sigmoid_epoch3/`。

train-50 seed42 严格标签扩展已完成：50 题、598 节点、1196 条 continuation 记录，标签重算校验 `bad_nodes=0`。在固定 37/13 题目划分上，soft label、binary BCE、以及与部署时原始候选代码/public feedback 对齐的 soft label 均未通过门槛。最佳原始候选评分为 `0.514` private pass rate，低于首候选 `0.533`，更低于 public 选择 `0.683`；public+neural 并列决策为 `0.626`，同样退化。当前配置因此标记为 **No-Go**，不投入 seed43/44 的同配置 continuation 采集。下一轮必须先增加每个节点的 continuation 重复数，并扩展问题级训练规模；结构化特征消融继续暂缓。诊断报告为 `reports/neural_codeprm_train50_seed42_diagnostic_2026-09-05.json`。

正式验收：loss 下降、checkpoint 可加载、无 private 泄漏、输出四类指标和 95% bootstrap 或明确的小样本说明。

### T03.5：标签重复数修复（下一步）

目标：降低每节点仅 2 条 continuation 所带来的标签方差，而不改变 APPS、模型、候选池、题目切分或 private-test 使用边界。

1. 在现有 train-50 seed42 的 598 节点上，从 2 条增加到 4 条 continuation；前两条保留，补充第 3/4 条，并将所有同一节点记录的 `step_label` 重算为 4 条 private pass rate 均值；
2. 继续使用 source candidate 的 thought prefix，private tests 只在生成后执行，绝不写入 prompt；
3. 使用部署对齐输入（原始候选 code + public feedback）和 soft sigmoid MSE，固定 37/13 problem split；
4. 同时报原始候选选择、public 选择、public+neural tie-break、步骤排序和 bootstrap 区间；
5. 仅当原始候选选择不低于首候选，且 public+neural tie-break 不低于 public 选择时，才为 seed43/44 重复该协议；否则停止神经 CodePRM 主线并保留负结果。

可行性：本机已验证 3B QLoRA 和断点采集；所需新增约 1,196 次本地 continuation 生成及执行。采集器已经具备按题目 checkpoint/resume，扩展前需将其改为支持“已有 2 条节点继续补到 4 条”的增量标签重算。

预期作用：该任务不承诺提高指标；它用于区分“标签估计方差过大”与“当前学习目标本身不适合候选选择”。

### T04：扩大到 100/600 题

顺序：`train-50 → train-100 → APPS 600`。  
每个规模至少 3 seed；每次只改变题目数，不同时改变模型、候选数和温度。  
优先使用 APPS Introductory；Interview/Competition 在执行器审计后单独加入。7B、Codeforces 和对抗代码执行不纳入本项目范围。

验收：问题级 split、断点恢复、单题失败不中断、候选解析率和执行状态完整记录。

前置条件更新：在 train-50 seed42 No-Go 后，T04 不直接重复当前训练配置。先将每节点 continuation 从 2 增至至少 4，并在 train-50 上确认原始候选选择不低于首候选且不损害 public 选择，再扩大到 train-100。

### T05：GVR 定位与重写分析

在神经 PRM 上比较：

- minimum-score step；
- fixed threshold；
- adaptive threshold；
- public score 无提升时停止；
- 错误类型条件化修正。

必须报告：accepted rewrites、定位准确率、private gain、degradation、平均调用次数和成功/失败案例。

### T06：结构化 CodePRM 扩展

逐项加入特征，避免一次改动过多：

1. 函数签名与参数/返回值摘要；
2. AST 节点和控制流摘要；
3. runtime error 类型；
4. 失败测试输入/输出摘要；
5. 测试覆盖或失败位置摘要。

每项只在固定候选池上做 ablation。主评价为 held-out pass@1 和 GVR 净收益；辅助评价为步骤排序指标。

### T07：官方 APPS 协议验证

条件满足后获取官方 APPS test split，保留当前 train custom split 作为开发集。  
该任务只验证 APPS 官方协议，不扩展到 Codeforces。

验收：数据版本、模型、seed、超时和硬件全部记录；结果表明确区分 custom split 与 official split。

## 5. 推荐执行顺序和时间预算

| 周期 | 任务 | 结果 |
| --- | --- | --- |
| 第 1 周 | T00、T01、单 batch GPU smoke | 训练环境和显存边界 |
| 第 2 周 | T02、T03 | 3B 神经 PRM pilot |
| 第 3 周 | T03 三 seed、T05 初版 | neural PRM 与 Ridge 对照 |
| 第 4 周 | T04 train-100、T05 完整分析 | 稳定性与 GVR 误差报告 |
| 第 5-6 周 | T06 结构化特征 ablation | 第一版研究创新结果 |
| 后续 | T07 官方 APPS | 外部协议验证 |

若仅使用本机，3B pilot、train-100、APPS 600 的分阶段实验可行；7B、Codeforces 和对抗代码执行已经从本项目范围移除。

## 6. Go/No-Go 门槛

### Go

- 3B 单 batch forward/backward 成功；
- neural CodePRM 在 held-out ranking 或 pass@1 上超过 Ridge baseline；
- 三 seed 方向一致；
- GVR 接受后退化率低且定位指标可解释；
- 结构化特征至少有一个维度获得稳定增益。

### 暂停并修协议

- train/test 题目重叠；
- public/private 泄漏；
- PRM 只在训练集有效；
- GVR 退化率高；
- 结构化特征与候选质量、模型版本同时变化，无法归因。

## 7. 预期论文/报告产出

1. 复现报告：论文设置、当前设置、差异和完整结果；
2. 神经 CodePRM checkpoint 与训练配置；
3. soft/binary、normal/code-only/CodePRM 消融表；
4. GVR 定位与重写失败案例集；
5. 函数/AST/错误结构扩展的 ablation；
6. official/custom split 分离的最终结论。

当前最稳妥的研究主张是：

> 执行反馈对代码候选选择具有稳定价值；进一步的研究重点是让学习型过程评分器超过直接测试反馈，并通过结构化程序信息提升错误定位和 GVR 修正质量。

## 8. 明确跳过的任务及影响

### 8.1 7B CodePRM

跳过后，研究结论定位为 3B 资源约束下的神经 CodePRM 研究，不报告论文 7B 数字，也不对 Table 1 做绝对值复现。当前主问题“执行反馈是否改善学习型过程评分”仍可在 3B 上检验。

### 8.2 Codeforces

跳过后，结论范围限定为 APPS 函数式任务。研究重点转为函数签名、程序结构和测试反馈，避免引入 checker/语言适配变量。

### 8.3 对抗代码执行

跳过后，实验仅运行固定 APPS 候选和受控测试；不把当前执行器描述为安全沙箱，也不运行恶意或来源不明的对抗样本。
