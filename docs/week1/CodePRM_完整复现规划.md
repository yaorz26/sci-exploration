# CodePRM 完整复现规划

## 0. 项目定位

### 0.1 项目名称

面向代码生成的执行反馈增强过程奖励模型复现

### 0.2 复现对象

论文：**CodePRM: Execution Feedback-enhanced Process Reward Model for Code Generation**

论文提出一种面向代码生成的过程奖励模型。它同时利用：

```text
题目 + 思路 + 生成代码 + 代码执行反馈
```

来评价每个中间思路，并在推理阶段使用 Generate-Verify-Refine（生成-验证-修正，简称 GVR）流程定位和修正错误思路。

### 0.3 复现目标

本项目不要求一开始完全复现论文中的全部数字，而是分阶段验证论文的核心结论：

1. 只输入“题目 + 思路”的普通 PRM，对代码思路的判断效果较弱。
2. 加入代码和执行反馈后，CodePRM 能更准确地评价思路质量。
3. 使用通过率作为连续标签，比简单的 0/1 标签能提供更丰富的监督。
4. CodePRM 可以在搜索过程中找出低质量思路，并通过 GVR 流程修正它们。
5. CodePRM-GVR 能提升代码生成的 pass rate 和 pass@1。

最终目标是复现论文 Table 1 的主要趋势，并形成一份可以向导师汇报的实验报告。

## 1. 为什么先复现 CodePRM

导师给出的方向包括：

- 把代码生成任务拆成多个子任务；
- 分析代码的词法、语法、AST 等结构。

CodePRM 与第一个方向直接相关：它把自然语言思路拆成多个步骤，并结合代码执行反馈进行评价。先完成 CodePRM，可以建立以下基础：

- 了解代码生成的搜索流程；
- 学会运行代码并收集测试反馈；
- 学会构造过程奖励标签；
- 学会训练和使用一个代码 PRM；
- 为后续加入函数、AST 或静态分析信息打基础。

因此，当前阶段暂时不同时研究 FunPRM、AST 和约束解码。

## 2. 复现分层目标

为了避免一开始任务过大，把复现分成四个层级。

### Level 0：论文理解

目标：能够用自己的话解释论文。

必须回答：

- CodePRM 解决了什么问题？
- 为什么普通 PRM 不适合直接评价代码思路？
- CodePRM 输入了哪些信息？
- pass rate 标签是怎么获得的？
- GVR 的三个阶段分别做什么？

产出：一页论文理解笔记和方法流程图。

### Level 1：最小流程复现

目标：在 20 道 APPS Introductory 题目上跑通完整数据流。

流程：

```text
读取题目
→ 生成多个候选代码
→ 执行候选代码
→ 统计测试通过率
→ 选择候选代码
→ 输出结果
```

产出：

- 能运行的代码执行器；
- 候选代码生成结果；
- pass rate 和 pass@1 统计；
- 随机选择与通过率选择的对比表。

### Level 2：CodePRM 最小复现

目标：在小规模数据上训练一个简化版 CodePRM，并验证执行反馈的作用。

对比两个模型：

| 模型 | 输入 |
|---|---|
| 普通 PRM | 题目 + 思路 |
| CodePRM | 题目 + 思路 + 代码 + 执行反馈 |

产出：

- 训练数据；
- PRM 模型或评分器；
- 不同输入信息的消融实验；
- Best-of-N 选择结果。

### Level 3：论文规模复现

目标：尽量按照论文设置复现主要实验。

包括：

- APPS 三种难度；
- Codeforces 三种难度；
- GPT-4o-mini 和 DeepSeek-Coder-V2-Lite-Instruct；
- Best-of-N 和 MCTS；
- GVR-MCTS；
- 与 RethinkMCTS、LATS 等方法比较。

产出：接近论文 Table 1 的实验表、误差分析和复现报告。

## 3. 论文设置记录

下面的配置来自论文，应当在代码中集中保存，避免参数散落在脚本里。

### 3.1 数据集

#### APPS

- 难度：Introductory、Interview、Competition；
- 论文测试：每个难度 100 道正式题；
- 论文训练：使用 600 道 APPS 题目训练 CodePRM；
- 训练题和测试题不能重叠；
- 每道题的测试用例平均分为 public tests 和 private tests。

#### Codeforces

- 难度：rating 1200、1500、1700；
- 每个难度评估 100 道题；
- 同样把测试用例分成 public 和 private 两部分。

### 3.2 模型

论文中涉及以下模型：

- CodePRM 训练骨干：Qwen2.5-Coder-7B-Instruct；
- 代码生成模型：GPT-4o-mini、DeepSeek-Coder-V2-Lite-Instruct；
- 论文使用 MCTS 进行主要 GVR 实验。

实际复现时应根据可用显卡、模型文件和 API 情况选择模型。模型无法完全一致时，应在报告中明确写出替代模型，不要把替代实验称为严格复现。

### 3.3 搜索配置

- 每个搜索节点生成 3 个子节点；
- 最大 rollout 数量为 16；
- Best-of-N 中每条思路链最多 4 步；
- 每个节点对应一份由当前思路生成的代码；
- 使用 public tests 提供过程中的反馈；
- 使用 private tests 计算最终结果。

### 3.4 评价指标

#### Pass rate

代码通过的 private tests 数量除以 private tests 总数，再在所有题目上求平均。

#### Pass@1

生成结果完全通过某一道题全部 private tests 的题目比例。

#### 其他建议指标

- 代码生成成功率；
- 候选选择准确率；
- 修正前后的通过率变化；
- 每道题的生成次数；
- 每道题的执行次数；
- 总推理时间；
- GPU 显存占用；
- API 调用次数和成本（如果使用 API）。

## 4. 总体实验流程

```text
准备环境和数据
        ↓
实现代码执行器
        ↓
实现基础代码生成器
        ↓
实现随机选择和通过率选择
        ↓
收集思路、代码和执行反馈
        ↓
训练普通 PRM 和 CodePRM
        ↓
实现 Best-of-N 选择
        ↓
实现 GVR 流程
        ↓
实现 GVR-MCTS
        ↓
扩大数据规模
        ↓
整理表格、曲线和复现报告
```

## 5. 分阶段实施计划

### 第 1 阶段：环境和资源检查

### 目标

确认当前机器能否运行最小实验，避免在不了解资源的情况下直接开始大规模训练。

### 需要检查的内容

- Python 版本；
- PyTorch 是否安装；
- Transformers 是否安装；
- 是否有 NVIDIA GPU；
- GPU 显存大小；
- 是否能加载一个小型代码模型；
- 是否有 Hugging Face 或其他模型下载权限；
- 是否有可用的 API；
- 是否能运行 Python 子进程；
- 是否能安全限制代码的运行时间。

### 产出

建立一份环境记录：

```text
Python：
PyTorch：
GPU：
显存：
可用本地模型：
可用 API：
数据集状态：
主要限制：
```

### 完成标准

至少能够运行：

```python
print("hello")
```

并能确认一个模型是否可以正常生成文本。

### 第 2 阶段：实现代码执行器

### 目标

给定题目、候选代码和测试用例，能够自动执行代码并返回结构化结果。

### 执行器需要完成的工作

1. 写入临时代码文件；
2. 注入测试输入；
3. 运行候选程序；
4. 设置超时时间；
5. 捕获标准输出和错误输出；
6. 判断每个测试用例是否通过；
7. 统计 public pass rate 和 private pass rate；
8. 保存错误信息。

### 反馈格式

建议统一保存为：

```json
{
  "passed": 8,
  "total": 10,
  "pass_rate": 0.8,
  "error_type": "wrong_answer",
  "message": "expected ..., got ...",
  "timeout": false
}
```

### 必须防止的问题

- 无限循环；
- 运行时间过长；
- 访问不应该访问的文件；
- 生成代码覆盖原始数据；
- 不同题目的临时文件互相污染；
- 只执行 public tests，导致误把 public pass rate 当成最终成绩。

### 完成标准

人工准备 2-3 个简单程序：

- 一个完全正确；
- 一个输出错误；
- 一个超时。

执行器必须能正确区分三种情况。

### 第 3 阶段：实现基础代码生成和候选选择

### 目标

每道题生成多个候选代码，并建立最基础的对照实验。

### 最小规模设置

- 数据：APPS Introductory 20 道题；
- 每题候选数：4；
- 每个候选代码都执行 public 和 private tests；
- 固定随机种子；
- 保存完整生成结果。

### 需要实现的选择策略

#### 随机选择

从 4 个候选代码中随机选择一个，作为随机基线。

#### 第一个候选

直接使用模型生成的第一个候选，作为基础模型基线。

#### Public pass rate 选择

选择 public pass rate 最高的候选。若有多个候选分数相同，使用固定的平局处理规则。

#### 理想上界，仅用于分析

使用 private pass rate 最高的候选。该方法不能作为正式推理基线，因为实际推理阶段不能看到 private tests；它只能帮助判断候选池本身是否包含正确答案。

### 结果表

| 方法 | 候选数 | Pass rate | Pass@1 | 平均执行次数 |
|---|---:|---:|---:|---:|
| 第一个候选 | 4 |  |  |  |
| 随机选择 | 4 |  |  |  |
| Public pass rate | 4 |  |  |  |
| Private 上界 | 4 |  |  |  |

### 完成标准

- 20 道题全部完成或明确记录失败原因；
- 结果可以自动生成；
- 重新运行可以得到相同的实验配置和相近结果；
- 能区分“模型没有生成正确代码”和“选择器没有选出正确代码”。

### 第 4 阶段：收集 CodePRM 训练数据

### 目标

构造论文所需的思路-代码-执行反馈数据。

### 每条数据应包含

```json
{
  "problem_id": "apps_0001",
  "problem": "题目描述",
  "thoughts": [
    "思路步骤 1",
    "思路步骤 2",
    "思路步骤 3"
  ],
  "code": "完整代码",
  "public_feedback": {
    "pass_rate": 0.75,
    "message": "..."
  },
  "private_feedback": {
    "pass_rate": 0.60,
    "message": "..."
  },
  "label": 0.60,
  "generator_model": "...",
  "random_seed": 42
}
```

### 标签生成

论文的思想是：一个中间思路的标签由该思路后续生成的多个代码的平均 private pass rate 决定。

例如：

```text
思路 1 产生 3 个代码
代码通过率：1.0、0.8、0.6
思路 1 标签 = (1.0 + 0.8 + 0.6) / 3 = 0.8
```

不能只保存最终代码的结果，还要保存思路链和思路对应的代码。

### 小规模设置

先使用：

- 20 道题；
- 每道题 4 条思路链；
- 每条思路链 3-4 个步骤；
- 每个思路节点生成 2-4 份代码。

### 完成标准

- 每条思路都能对应到代码；
- 每份代码都有执行反馈；
- 每个思路都有标签；
- 标签的计算过程可以人工抽查；
- 训练集与测试集没有题目重叠。

### 第 5 阶段：训练普通 PRM 和 CodePRM

### 目标

验证“执行反馈是否是必要输入”。

### 普通 PRM

输入：

```text
题目 + 思路链
```

输出：每个思路步骤的质量分数。

### CodePRM

输入：

```text
题目 + 思路链 + 代码 + 执行反馈
```

输出：每个思路步骤的质量分数。

### 标签

第一版使用连续 pass rate 作为标签：

```text
label ∈ [0, 1]
```

训练损失使用均方误差：

```text
MSE = (预测分数 - 真实 pass rate)^2
```

### 标签消融

再训练一个使用 0/1 标签的版本：

| 版本 | 标签 |
|---|---|
| Soft-label CodePRM | private pass rate，例如 0.6、0.8 |
| Binary-label CodePRM | 通过为 1，否则为 0 |

### 资源受限时的替代方案

如果暂时无法微调 7B 模型，按以下顺序降级：

1. 使用更小的本地模型验证数据格式和训练流程；
2. 使用预训练模型提取文本表示，再训练一个简单回归器；
3. 使用规则评分器验证 GVR 的数据流；
4. 等环境确认后再进行正式 CodePRM 微调。

降级实验只能说明流程可行，不能宣称完全复现论文模型。

### 完成标准

- 普通 PRM 和 CodePRM 都能输出分数；
- 训练损失能够下降；
- 能在未见过的题目上进行评分；
- 能比较有无执行反馈时的候选选择效果。

### 第 6 阶段：实现 Best-of-N 评价

### 目标

使用 PRM 对多个候选进行排序，验证 PRM 是否比随机选择更有效。

### 流程

```text
同一道题生成 N 个候选思路链和代码
→ PRM 对每个步骤打分
→ 聚合一条思路链的分数
→ 选择总分最高的候选
→ 运行 private tests
```

### 分数聚合

第一版采用平均分：

```text
trajectory_score = 所有步骤分数的平均值
```

后续可以比较：

- 平均分；
- 最低步骤分数；
- 最后一条思路分数；
- 平均分与最低分的加权组合。

### 实验矩阵

| 选择方法 | 是否使用执行反馈 | 是否训练 PRM |
|---|---|---|
| 随机选择 | 否 | 否 |
| 第一个候选 | 否 | 否 |
| Public pass rate | 是 | 否 |
| 普通 PRM | 否 | 是 |
| CodePRM | 是 | 是 |

### 完成标准

在同样的候选数量和生成预算下，得到每种方法的：

- pass rate；
- pass@1；
- 选择时间；
- 每题选择结果。

### 第 7 阶段：实现 Generate-Verify-Refine

### 目标

验证 CodePRM 能否定位错误思路，并帮助模型重新生成代码。

### Generate

生成器提出多条思路，并根据思路生成代码。

### Verify

运行代码，读取执行反馈。对于没有通过全部 public tests 的代码，CodePRM 对每个思路步骤评分。

### Refine

选择低质量思路，要求生成器只修改该思路，再重新生成代码。

### 第一版使用最低分策略

```text
找出分数最低的步骤
→ 只修改该步骤
→ 重新生成完整代码
→ 再次执行测试
```

### 对比策略

#### 不修正

代码第一次生成后直接结束。

#### 随机修正

随机选择一个思路步骤进行重写。

#### 最低分修正

选择 CodePRM 分数最低的思路步骤进行重写。

#### 阈值修正

所有分数低于阈值的思路都进行重写。

第一轮阈值可以设置为 0.5，后续再比较 0.2、0.5、0.7、0.9。

### 完成标准

至少回答：

- 修正后 public pass rate 是否提高？
- 修正后 private pass rate 是否提高？
- CodePRM 选择的步骤是否比随机选择更值得修改？
- 修改过多思路是否会导致原本正确的思路被破坏？

### 第 8 阶段：实现 GVR-MCTS

### 目标

尽量复现论文的主要推理算法。

### MCTS 的四个阶段

1. Selection：选择当前最有希望的节点；
2. Expansion：生成新的思路节点；
3. Simulation：根据当前思路生成代码并执行；
4. Backpropagation：把结果奖励回传到路径上的节点。

### 第一版简化实现

为了降低复杂度，先实现固定宽度和固定深度：

- 每个节点 2-3 个子节点；
- 思路深度 3-4 步；
- 总 rollout 不超过 8；
- 使用 CodePRM 分数和 public pass rate 作为奖励；
- 代码通过所有 public tests 时停止搜索。

### 论文设置

简化版跑通后，再调整为：

- 每节点 3 个子节点；
- 最大 16 次 rollout；
- 使用 P-UCB 选择节点；
- 使用 CodePRM 评价中间思路；
- 失败节点触发思路修正。

### 对比方法

至少比较：

- Base：直接生成一份代码；
- Best-of-N：生成多个候选并筛选；
- MCTS：不使用 CodePRM 的搜索；
- GVR-MCTS：使用 CodePRM 验证和修正。

## 6. 核心实验矩阵

小规模实验先使用 20 道 APPS Introductory 题；扩大实验后再使用论文规模。

### 实验 E0：执行器正确性

目的：确认测试执行和指标计算没有问题。

输出：正确代码、错误代码、超时代码的执行结果。

### 实验 E1：候选池质量

目的：确认生成多个候选是否有意义。

比较：1、2、4、8 个候选。

指标：候选池中至少包含一个完全正确代码的比例。

### 实验 E2：选择方法

目的：比较随机选择、通过率选择和 PRM 选择。

比较：

- Random；
- First candidate；
- Public pass rate；
- Normal PRM；
- CodePRM。

### 实验 E3：执行反馈消融

目的：验证执行反馈的作用。

比较：

```text
题目 + 思路
题目 + 思路 + 代码
题目 + 思路 + 代码 + 执行反馈
```

### 实验 E4：标签消融

目的：比较连续 pass rate 标签与 0/1 标签。

比较：

- Binary label；
- Soft pass-rate label。

### 实验 E5：修正策略

目的：比较不同思路定位策略。

比较：

- 不修正；
- 随机修正；
- Locate-minimum；
- Threshold-based。

### 实验 E6：GVR 效果

目的：验证搜索中的动态修正是否有效。

比较：

- Base；
- Best-of-N；
- MCTS；
- GVR-MCTS。

### 实验 E7：模型和难度泛化

目的：验证方法是否只对某一模型或简单题有效。

比较：

- GPT-4o-mini；
- DeepSeek-Coder-V2-Lite-Instruct；
- APPS 三种难度；
- Codeforces 三种难度。

## 7. 推荐的实验顺序

不要一次实现所有实验，按下面顺序推进：

```text
E0 执行器
→ E1 候选池
→ E2 基础选择
→ E3 执行反馈消融
→ E4 标签消融
→ E5 修正策略
→ E6 GVR-MCTS
→ E7 扩大实验
```

如果某一步没有跑通，不要跳到下一步。下一步依赖前一步的数据和代码。

## 8. 推荐的项目目录

```text
codeprm-reproduction/
├── README.md
├── requirements.txt
├── configs/
│   ├── minimal.yaml
│   ├── apps.yaml
│   └── codeforces.yaml
├── data/
│   ├── raw/
│   ├── processed/
│   └── splits/
├── src/
│   ├── data_loader.py
│   ├── generator.py
│   ├── executor.py
│   ├── feedback.py
│   ├── metrics.py
│   ├── prm.py
│   ├── best_of_n.py
│   ├── gvr.py
│   └── mcts.py
├── scripts/
│   ├── check_environment.py
│   ├── run_one_problem.py
│   ├── collect_data.py
│   ├── train_prm.py
│   ├── evaluate_bon.py
│   └── evaluate_gvr.py
├── outputs/
│   ├── generations/
│   ├── executions/
│   ├── checkpoints/
│   └── results/
└── reports/
    ├── experiment_log.md
    ├── tables/
    └── figures/
```

## 9. 配置文件应记录的内容

每次实验都要保存配置，至少包括：

```yaml
dataset: apps
split: introductory
num_problems: 20
num_candidates: 4
max_rollouts: 8
thought_depth: 4
generator_model: "model-name"
prm_model: "model-name"
use_code: true
use_execution_feedback: true
label_type: pass_rate
verification_strategy: locate_minimum
random_seed: 42
timeout_seconds: 10
```

同一组结果必须能通过配置文件重新运行。

## 10. 数据记录规范

### 10.1 每道题的记录

```json
{
  "problem_id": "...",
  "dataset": "APPS",
  "difficulty": "introductory",
  "method": "CodePRM-GVR",
  "num_candidates": 4,
  "selected_candidate": 2,
  "public_pass_rate": 1.0,
  "private_pass_rate": 0.8,
  "pass_at_1": 0,
  "num_refinements": 1,
  "execution_time_seconds": 2.3,
  "error": null,
  "seed": 42
}
```

### 10.2 每轮修正的记录

```json
{
  "problem_id": "...",
  "round": 1,
  "thought_scores": [0.82, 0.31, 0.74],
  "selected_step": 1,
  "before_public_pass_rate": 0.5,
  "after_public_pass_rate": 1.0,
  "before_private_pass_rate": 0.4,
  "after_private_pass_rate": 0.8,
  "refinement_success": true
}
```

不要只保存最后的平均结果。原始生成结果、执行反馈和每次选择都要保留，方便定位问题。

## 11. 结果分析方法

### 11.1 先看趋势，再看数字

由于模型版本、提示词、数据集版本和随机种子可能不同，复现结果不一定与论文完全一致。首先判断以下趋势是否出现：

- CodePRM 是否超过随机选择；
- CodePRM 是否超过普通 PRM；
- 执行反馈是否带来收益；
- pass rate 标签是否优于 0/1 标签；
- GVR 是否比不修正更好；
- 修正更多思路是否不一定更好。

### 11.2 分析失败类型

把失败分成：

- 语法错误；
- 运行时错误；
- 超时；
- 输出格式错误；
- 边界条件错误；
- 算法复杂度过高；
- 思路正确但代码实现错误；
- 代码基本正确但测试覆盖不足。

### 11.3 区分三个问题

对于生成失败，要区分：

1. 候选池中没有正确代码；
2. 候选池有正确代码，但 PRM 没选出来；
3. PRM 找到了错误步骤，但生成器没有正确修正。

这三个问题分别对应生成能力、评分能力和修正能力，不能混在一起分析。

## 12. 验收标准

### Level 1 验收

- 可以读取 APPS 题目；
- 可以生成候选代码；
- 可以执行测试；
- 可以计算 public pass rate 和 private pass rate；
- 可以输出一个结果表。

### Level 2 验收

- 可以构造带思路和执行反馈的数据；
- 可以训练一个评分模型；
- 可以使用评分模型选择候选代码；
- 可以完成执行反馈消融实验。

### Level 3 验收

- 可以完成 GVR 流程；
- 可以比较最低分修正和随机修正；
- 可以观察修正前后的通过率变化；
- 可以解释失败案例。

### Level 4 验收

- 可以完成 GVR-MCTS；
- 可以在 APPS 和 Codeforces 上评估；
- 可以对比论文 Table 1 的主要趋势；
- 可以形成完整复现报告。

## 13. 时间规划

以下按每周有若干连续时间投入估计，实际时间取决于模型下载、GPU 和 API 情况。

### 第 1 周：跑通最小流程

- 完成环境检查；
- 准备 20 道 APPS 题；
- 实现代码执行器；
- 运行 2-3 道题；
- 完成 E0 和 E1。

周末产出：

- 环境记录；
- 执行器；
- 20 道题的候选生成结果；
- 初步 pass rate 表。

### 第 2 周：完成基础选择实验

- 完成随机选择；
- 完成 public pass rate 选择；
- 完成候选数量对比；
- 整理 E1 和 E2；
- 开始收集 PRM 训练数据。

周末产出：

- 基础选择实验表；
- 训练数据样例；
- 生成和执行失败日志。

### 第 3 周：训练简化版 PRM

- 完成普通 PRM 数据格式；
- 完成 CodePRM 数据格式；
- 训练普通 PRM；
- 训练加入执行反馈的 CodePRM；
- 完成 E3。

周末产出：

- 两个模型或评分器；
- 执行反馈消融结果；
- 对导师可展示的初步结论。

### 第 4 周：实现 GVR

- 实现最低分策略；
- 实现随机修正；
- 实现阈值策略；
- 完成 E4 和 E5；
- 分析修正成功和失败案例。

周末产出：

- GVR 流程；
- 修正策略对比表；
- 3-5 个具体案例。

### 第 5-6 周：扩大实验

- 增加题目数量；
- 增加 APPS 难度；
- 尝试 Codeforces；
- 实现简化版 MCTS；
- 完成 GVR-MCTS。

周末产出：

- 主要实验表；
- 失败类型统计；
- 复现报告初稿。

## 14. 资源不足时的降级路线

### 没有 GPU

先完成：

- 论文流程复现；
- 数据格式设计；
- 代码执行器；
- API 生成候选代码；
- 规则评分器和 GVR 流程。

暂时不做 7B 模型微调。

### 没有 API

使用可以本地运行的小型代码模型，但必须记录：

```text
论文模型：GPT-4o-mini / DeepSeek-Coder-V2-Lite
实际模型：本地替代模型
```

### 显存不足

按以下顺序降低成本：

1. 减少题目数量；
2. 减少每题候选数；
3. 减少 rollout 数量；
4. 使用 LoRA；
5. 使用 4-bit 量化；
6. 使用更小的模型验证流程。

### 数据集无法完整下载

先使用 10-20 道公开题目进行流程测试，不能把小样本结果当成论文规模结果。

## 15. 常见风险和处理方式

### 风险 1：生成代码不能运行

处理：先把问题分为模型生成问题和执行器问题，使用人工构造的正确/错误代码单独测试执行器。

### 风险 2：普通 PRM 和 CodePRM 都没有效果

可能原因：

- 训练数据太少；
- 思路标签错误；
- 思路和代码没有正确对应；
- 模型没有真正读取执行反馈；
- 候选数量太少；
- 测试反馈格式不统一。

处理：先抽查 20 条训练样本，再检查模型输入文本和标签。

### 风险 3：GVR 修正后反而变差

这并不一定说明实验失败。论文也指出，修正过多思路可能破坏正确内容。应记录：

- 修正前后得分；
- 修正前后测试通过率；
- 被修改的思路；
- 生成器修改后的内容。

### 风险 4：结果和论文不一致

优先检查：

- 数据集版本；
- 模型版本；
- prompt；
- public/private 测试划分；
- 最大 rollout 数；
- 随机种子；
- pass rate 计算方式。

复现报告中应区分：

- 严格复现；
- 缩小规模复现；
- 替代模型复现；
- 概念验证实验。

## 16. 给导师的阶段性汇报方式

每次联系导师都准备三部分：

### 进展

```text
我完成了什么？
得到什么结果？
和论文结论是否一致？
```

### 问题

```text
我具体卡在哪里？
我尝试过什么？
现在有哪两个选择？
```

### 下一步

```text
如果采用方案 A，我下一步做什么？
如果采用方案 B，我下一步做什么？
```

### 第一次汇报模板

> 老师，我准备先复现 CodePRM。第一阶段使用 APPS Introductory 的 20 道题，每题生成 4 个候选代码，先完成执行器、随机选择和 public pass rate 选择。第二阶段再比较普通 PRM 和加入代码执行反馈的 CodePRM。请问您建议我先使用 API 模型完成流程验证，还是直接准备本地 Qwen2.5-Coder-7B-Instruct 的微调环境？

### 有初步结果后的汇报模板

> 老师，我在 20 道 APPS Introductory 题上跑通了候选生成和代码执行。当前第一个候选的 pass@1 是 X，随机选择是 Y，public pass rate 选择是 Z。下一步我想收集思路、代码和执行反馈，训练一个简化版 CodePRM。现在主要不确定的是思路标签应该使用单个代码的通过率，还是多个后续代码的平均通过率；论文采用的是后者，我准备按论文设置实现。

## 17. 复现报告结构

最终报告建议按照下面结构写：

```text
1. 研究问题
2. CodePRM 方法概述
3. 论文实验设置
4. 复现环境和模型
5. 数据集与数据划分
6. 实现细节
7. 最小流程实验
8. 执行反馈消融实验
9. 标签消融实验
10. GVR 修正实验
11. GVR-MCTS 实验
12. 与论文结果对比
13. 失败案例分析
14. 复现结论
15. 后续研究方向
```

## 18. 复现完成后的后续研究

只有完成 CodePRM 基线后，再考虑加入 AST 或函数结构信息。

推荐的后续实验顺序：

```text
CodePRM
→ CodePRM + 函数划分
→ CodePRM + AST 摘要
→ CodePRM + 类型检查结果
→ CodePRM + 静态分析结果
→ 比较哪类结构信息最有帮助
```

后续可以形成一个更具体的研究问题：

> 在相同生成预算下，将 AST 或静态分析信息加入代码过程奖励模型，能否更准确地识别错误思路，并提升 pass@1？

但这个问题必须建立在 CodePRM 基线已经跑通的前提下。

## 19. 当前最优先的三件事

本节原来描述的是启动阶段。启动阶段已经完成，当前优先级应更新为：

1. 固定真实 APPS 数据版本、public/private 测试划分和数据路径；
2. 用本地 `qwen2.5-coder:3b` 在真实 APPS Introductory 子集上生成并执行候选代码；
3. 在真实反馈记录上训练可学习的 CodePRM，并把现有 NumPy Ridge 结果作为回归测试基线。

完成这三件事后，才适合讨论论文级的 GVR-MCTS 数字。当前已经完成的离线 fixture、执行器和 Ollama 冒烟实验保留为流程验收证据，不应当被表述为论文规模复现。

## 20. 当前阶段的完成定义

Level 1 的完成定义已经满足：

```text
能读取题目
能生成代码
能执行代码
能得到 public/private 测试反馈
能比较不同选择方法
能解释结果为什么这样
```

Level 2 还需要补齐真实 APPS 数据和可学习的神经评分器。后续每个阶段以第 21 节的验收门槛为准，不以“得到论文同样的数字”为单独完成标准。

## 21. 2026-09-04 实施版任务分解与可行性检查

本节是当前执行版本，状态优先于第 13 节的周计划。可行性等级含义如下：

```text
A：当前机器和现有代码可以直接完成；
B：可以完成，但需要数据、依赖、较长运行时间或明确的降级方案；
C：在当前配置下不建议承诺，需要外部 GPU/API、Linux/WSL 或更换实验范围。
```

### 21.1 资源基线与已验证事实

| 项目 | 当前事实 | 对计划的影响 |
| --- | --- | --- |
| 操作系统/解释器 | Windows 11，Python 3.13.7 | 运行现有脚本没有问题；部分深度学习依赖在 Windows/Python 3.13 上兼容性较差 |
| GPU | RTX 4060 Laptop，8188 MiB | 适合 1.5B/3B 推理和小型回归模型；不适合直接微调 7B |
| PyTorch | 已安装 | 可继续做推理和 NumPy/PyTorch 验证 |
| Transformers/Datasets | 未安装 | 真实 Hugging Face 数据读取和神经 PRM 训练尚未具备 |
| Ollama | `http://127.0.0.1:11434` 可用 | 无需 API key 即可做本地候选生成 |
| 已下载模型 | `qwen2.5-coder:1.5b`、`qwen2.5-coder:3b`，另有 Dolphin3 | 3B 是主实验生成器，1.5B 用于快速冒烟，Dolphin3 仅作对照 |
| 数据 | 已有 20 题离线 fixture；已获取 20 题真实 APPS train Introductory 子集；官方 test 路径未配置 | 当前 train 子集可推进缩小规模闭环；严格论文评估仍需官方 test split |
| 执行安全 | 临时目录 + 超时 + 隔离导入 | 足够开发验收；真实不可信代码仍需要容器或 OS 级沙箱 |

### 21.2 任务矩阵

| ID | 任务 | 当前状态 | 主要产物 | 依赖 | 估计 | 可行性 |
| --- | --- | --- | --- | --- | ---: | :---: |
| T00 | 环境和版本冻结 | 已完成 | `reports/environment.json`、配置文件、随机种子 | 无 | 0.5 天 | A |
| T01 | 项目骨架和数据契约 | 已完成 | `codeprm-reproduction/`、JSON/JSONL schema | T00 | 0.5 天 | A |
| T02 | 执行器 E0 回归 | 已完成 | `scripts/test_executor.py`、四类错误断言 | T01 | 0.5 天 | A |
| T03 | 离线 20 题 E1/E2 | 已完成 | baseline、feedback、selection 表 | T02 | 0.5 天 | A |
| T04 | Ollama 候选生成 | 已完成 | 1.5B/3B/Dolphin3 结果、原始响应 | T02 | 1 天 | A |
| T05 | 真实 APPS 数据获取与标准化 | 已完成首个 train 子集；test 待获取 | 固定版本数据、split manifest、5 题人工抽查 | T01/T02 | 已用约 1 天 | B |
| T06 | 真实题目 prompt 和生成协议 | 部分完成；已完成函数题适配和 1 候选 smoke | prompt 版本、seed、temperature、生成日志 | T04/T05 | 0.5-1 天 | B |
| T07 | 真实反馈数据收集 | 已完成 20×4 批量 | 每题多候选的 thoughts/code/public/private 记录 | T05/T06 | 已用约 1 天 | B |
| T08 | 可学习 CodePRM 训练环境 | 未完成神经版；已有 Ridge 替身 | Transformers/PEFT 训练脚本、checkpoint、loss 曲线 | T07 | 1-3 天（替身）；3-7 天（神经） | B/C |
| T09 | Level 2 输入/标签消融 | 已完成真实数据 Ridge 版 | normal/code-only/CodePRM、soft/binary 表 | T07/T08 | 已用约 1 天 | B |
| T10 | GVR 模型驱动修正 | 已完成池替换版和 20 题 Qwen3B 一次重写；更强定位待做 | failure localization、修正前后对比、案例集 | T06/T08/T09 | 已用约 1 天 | B |
| T11 | MCTS/GVR-MCTS | 已完成真实 8-rollout 简化搜索 | 固定 rollout、选择/扩展/回传日志 | T09/T10 | 已用约 0.5 天 | B/C |
| T12 | APPS Introductory 扩大实验 | 未开始 | 20/50/100 题分规模表和置信区间 | T05-T10 | 1-3 天 | B |
| T13 | APPS Interview/Competition | 未开始 | 难度分层结果、失败类型统计 | T12 | 3-7 天 | B/C |
| T14 | Codeforces 适配 | 未开始 | checker/输入格式适配及独立结果表 | T02/T05 | 3-7 天 | C |
| T15 | 论文 Table 1 对照 | 未开始 | 同协议对照表、差异说明 | T12/T13 | 2-5 天 | C |
| T16 | AST/FunPRM 扩展 | 延后 | 结构特征消融和新增研究问题 | T12 通过 | 1-2 周 | C |
| T17 | 可复现打包与报告 | 持续进行 | README、环境快照、命令、失败案例 | 各阶段 | 0.5-1 天/阶段 | A |

### 21.3 任务卡和验收标准

#### T05：真实 APPS 数据获取与标准化（首个子集已完成）

输入是一个明确版本的 APPS 导出或等价 JSON/JSONL；每道题至少要有题面、输入输出说明、public 测试和 private 测试。执行内容：

- 记录来源、commit/tag、下载日期、许可证和题目数量；
- 使用 `src/data_loader.py` 的 APPS `input_output` 适配器转换为统一 schema；
- 先抽查 5 道题，分别确认输入可读、期望输出可解析、public/private 不重复；
- 通过后再生成 `data/splits/apps_introductory.json`，禁止运行时隐式改变 split。

当前已完成 `data/raw/apps_train_introductory20.json` 和 `data/splits/apps_train_introductory20.json`，固定 revision 为 `21e74ddf8de1a21436da12e3e653065c5213e9d1`，20 道题包含 71 个 public 测试和 82 个 private 测试，SHA-256 为 `2fef66b2119b160ae90375485d34cb7190586bd053803efc37f98d4d79039d84`。5 题字段抽查和重复运行一致性已通过。

这份数据来自 `train` split，public/private 是按 `input_output` 前半/后半样例的自定义划分；它足以推进缩小规模训练闭环，但不能替代官方 test split 的严格论文评估。

#### T06：真实生成协议冻结

主生成器使用 `qwen2.5-coder:3b`；`qwen2.5-coder:1.5b` 只用于成本/速度对照。每个候选必须保存模型名、prompt 版本、seed、temperature、原始响应、解析后的 thoughts/code。标准输入题继续强制 stdin 一次性读取、answer-only 输出、禁止文件和交互式提示；函数式题必须保留 `starter_code` 签名、只返回函数实现、禁止自行读 stdin。这样可以避免把题型/IO 不匹配误判为 PRM 失败。

验收门槛：同一配置重跑可定位到同一个 `problem_id/candidate_id`；解析失败率单独统计，不能静默丢弃候选；至少保留 20 题 × 4 候选的原始响应。

#### T07：执行反馈和标签收集

对每个候选分别运行 public 和 private 测试，记录每个测试的 `passed/wrong_answer/syntax_error/runtime_error/timeout`、stdout/stderr 摘要和耗时。soft label 定义为 private pass rate（0、0.5、1 等连续值），binary label 仅作为消融。public 反馈只能用于选择/训练输入，private 反馈只能用于标签和最终评估。

验收门槛：无 private 泄漏；每个候选都有完整记录；随机抽查 20 条记录能由执行结果重新计算 label；超时和异常不会中断整批任务。

#### T08：可学习 CodePRM

当前 `src/learned_prm.py` 的 NumPy Ridge 是数据契约和实验回归替身，不是论文中的 Transformer PRM。短期先完成真实 APPS 上的 Ridge/轻量 MLP，验证输入字段、标签和 train/test split；正式神经版本再安装 `transformers`、`datasets`、`peft`，选小型 backbone 做 LoRA/QLoRA。

验收门槛：训练集和测试集按题目划分，不能按候选随机打散造成泄漏；保存配置、checkpoint、训练曲线和最佳验证点；与 code-only、normal PRM 的输入消融都能一键重跑。

可行性判断：8GB 显存适合 1.5B/3B 推理，不适合在 Windows 上直接全量微调论文级 7B。若要做 7B LoRA，应改用 Linux/WSL、4-bit 量化并确认 `bitsandbytes`/CUDA 兼容，或使用外部 GPU；否则应把结果标为“轻量替身”。

#### T09：Level 2 消融

固定同一候选池和 split，至少比较：题目+思路（normal）、题目+思路+代码（code-only）、题目+思路+代码+public 执行反馈（CodePRM）；CodePRM 再比较 soft 与 binary 标签。所有模型使用相同候选和训练预算。

验收门槛：报告 train MSE、test MSE/相关性、选择后的 pass rate 和 pass@1，并附 95% bootstrap 置信区间或明确说明样本过小无法估计。离线 fixture 的 1.0 结果只能作为管线回归，不作为结论。

#### T10：GVR

先用 public 反馈定位最低质量思路步骤，再让生成器仅重写该步骤并重新生成代码；池替换版只作为无模型的上限/回归对照。每次修正保存原思路、新思路、代码、执行反馈和是否接受。

验收门槛：同时报告修正前后 pass rate、pass@1、平均修正次数和“修正导致退化”的比例；至少整理 3 个成功和 3 个失败案例。若修正预算或接受阈值改变，必须产生新的结果文件名。

#### T11/T12：搜索和扩大规模

先在 20 题真实 APPS 上固定 8/16 rollout 做搜索壳回归，再扩至 50/100 题；每次只改变一个变量（候选数、rollout、阈值或模型）。扩大实验前先确认单题失败不会导致整批中断，并保存中间结果以便断点续跑。

验收门槛：每个规模至少 3 个随机种子，输出均值、标准差和失败类型；不能只报告最好的 seed。当前 3B 推理在 8GB 显存内已验证，故 Introductory 20-100 题属于 B 级可行；Interview/Competition 和 Codeforces 因题面复杂度、checker 和运行成本列为 B/C。

### 21.4 依赖关系和执行顺序

```text
T00 → T01 → T02 → T03
             └→ T04
T04 + T05 → T06 → T07 → T08 → T09 → T10 → T11 → T12
                                                        ├→ T13
                                                        ├→ T14
                                                        └→ T15
T12 通过后再做 T16；T17 随每个阶段同步更新
```

关键路径是 `T05 → T06 → T07 → T08 → T09`。其中 T05（真实数据）和 T08（神经训练环境）是目前的两个硬门槛；继续优化离线 fixture 或下载更多生成模型不会替代它们。

### 21.5 分阶段执行安排

**阶段 A：数据闭环（1-2 天，目标 T05-T07）**

- 固定 APPS Introductory 20 题，先不追求 100 题；
- 用 3B 生成每题 4 个候选，完整保存响应和执行反馈；
- 生成第一份真实 `feedback_records`，完成 5 题人工审计。

**阶段 B：评分器和选择（2-4 天，目标 T08-T10）**

- 先跑 Ridge/轻量 MLP，复现输入与标签消融；
- 在相同候选池上接入 GVR，记录修正退化率；
- 若依赖安装顺利，再开一个独立的神经 PRM 实验，不覆盖替身结果。

**阶段 C：规模和搜索（3-7 天，目标 T11-T13）**

- 20 → 50 → 100 题逐级扩大，采用 3 个 seed；
- 先固定 8 rollout，再评估 16 rollout 的收益/耗时；
- 只有 Introductory 结果稳定后才进入更难难度。

**阶段 D：论文对照和扩展（条件满足后，目标 T14-T16）**

- 需要数据、评测 checker、模型/接口和计算预算全部记录；
- 7B 微调、Codeforces、AST/FunPRM 不纳入当前阶段完成承诺；
- 对照论文数字时明确写“严格复现、缩小规模、替代模型、概念验证”四种标签。

### 21.6 可行性结论和反馈

当前已有的可重跑结果如下。这里的 `pass rate` 是被选候选在 private 测试上的平均通过率，`pass@1` 是题目级至少选出一个完全通过候选的比例；所有行都属于缩小规模验证。

| 候选生成器/数据 | First（pass rate / pass@1） | Random（pass rate / pass@1） | Public selection（pass rate / pass@1） | Oracle（pass rate / pass@1） | 结果性质 |
| --- | ---: | ---: | ---: | ---: | --- |
| 离线 fixture（模板） | 0.325 / 0.30 | 0.225 / 0.15 | 1.00 / 1.00 | 1.00 / 1.00 | 数据流回归，不是 benchmark |
| Dolphin3（20 题） | 0.85 / 0.85 | 0.85 / 0.85 | 0.95 / 0.95 | 0.95 / 0.95 | 本地替代生成器对照 |
| Qwen2.5-Coder 1.5B（20 题） | 0.60 / 0.60 | 0.65 / 0.65 | 0.80 / 0.80 | 0.80 / 0.80 | 快速本地对照 |
| Qwen2.5-Coder 3B（20 题） | 0.95 / 0.95 | 0.85 / 0.85 | 1.00 / 1.00 | 1.00 / 1.00 | 当前主生成器冒烟结果 |

这些数字说明执行器、候选保存和 public 选择链路已经工作；它们不能说明 PRM 已经学会跨题泛化，因为 fixture 只有 20 题、每题 1 个 public + 2 个 private 测试，且当前评分器仍是 Ridge 替身。

1. **当前工作目录和最小流程可行且已经完成。** E0、离线 E1/E2、简化 Level 2/GVR/MCTS、真实 APPS train 子集获取，以及 Ollama 的 1.5B/3B 真实生成均有可重跑产物。
2. **本地小模型适合做生成器，不等于已经有 CodePRM。** 当前 PRM 是 NumPy Ridge 替身；Ollama 只解决候选代码生成，不能替代过程奖励模型训练。一次 Qwen3B 模型驱动 GVR 已完成，但只接受 public 严格提升的 2/20 次修正，说明定位和改写仍是瓶颈。
3. **最现实的主线是“真实 APPS Introductory + Qwen2.5-Coder 3B + 轻量 CodePRM”。** 这条路线在现有 8GB 显存和 Windows 环境下为 B 级可行，足以产生可信的阶段性实验，但不能宣称复现论文 Table 1。
4. **论文级 7B 神经 PRM、完整 Codeforces 和外部模型对照目前是条件任务。** 需要 Linux/WSL 或外部 GPU、额外依赖、固定数据版本和更多运行预算；在这些条件未满足前应标为 C 级，不把时间消耗在无效调参上。
5. **首份真实 APPS 数据已经补齐，但仍需区分 train 子集和官方 test 评估。** 当前 train 子集可以沿 T06→T10 推进；要做严格论文比较，仍需获取并固定官方 test split，新增模型下载的优先级低于这一数据工作。

## 22. 更新后的阶段汇报口径

对导师汇报时建议使用下面的准确表述：

> 我已经在 Windows + RTX 4060 8GB 上完成 CodePRM 的执行器、候选选择、执行反馈数据契约、简化 PRM/GVR/MCTS，以及 Ollama 本地 Qwen2.5-Coder 3B 的生成验证。当前结果是缩小规模的流程复现，不是论文数字复现。下一步固定 APPS Introductory 数据版本，收集真实 public/private 反馈，再训练轻量 CodePRM；7B 微调和论文级 Table 1 对照需要单独的 Linux/外部 GPU 预算。
