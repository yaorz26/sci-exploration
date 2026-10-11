# WP2 静态审计：ClassEval

日期：2026-09-28 ｜ 结论：**进入试运行（优先级 1）**
审计方式：HF API + 下载原始文件（0.48 MiB）+ 本地结构分析 + 参考实现可运行性抽查（3 题 × 3 次）。**未运行任何代码生成模型（LLM 调用 0 次）**。

---

## 一、来源与许可证（一手核实）

| 项目 | 内容 |
| --- | --- |
| 数据集 | `FudanSELab/ClassEval`（Hugging Face） |
| 代码仓库 | https://github.com/FudanSELab/ClassEval |
| 论文 | ClassEval: A Manually-Crafted Benchmark for Evaluating LLMs on Class-level Code Generation，[arXiv:2308.01861](https://arxiv.org/abs/2308.01861) |
| 仓库许可证 | **MIT**（GitHub API `license.spdx_id`，2026-09-28 核实） |
| 数据集许可证 | **mit**（HF 元数据） |
| 最后更新 | 数据集 2024-08-26；仓库 2024-10-24 |
| 原始文件 | `data/test-00000-of-00001-5c45fa6e45572491.parquet`，**499,568 字节（0.48 MiB）** |
| 本地落盘 | `D:\yaorz\research\decomposition-bench\data\raw\classeval\data\...` |
| SHA-256 | `ac2f490a8fa0ca63d8b6d166821ca430a382dc04611209e2067a2714cc89df2a` |
| 下载时间（UTC） | 2026-09-28T07:0x |

许可证清晰、体积可忽略、来源可追溯。**无许可证风险。**

## 二、数据结构（100 题，410 个方法）

题目级字段：`task_id`、`skeleton`、`test`、`solution_code`、`import_statement`、`class_description`、**`methods_info`**、`class_name`、`test_classes`、`class_constructor`、`fields`。

**关键字段 `methods_info`（这是本数据集对我们最有价值的部分）**：每题一个列表，每个元素是一个方法，字段为

| 子字段 | 含义 |
| --- | --- |
| `method_name` | 方法名 |
| `method_description` | 方法的完整 docstring（含参数、返回值、doctest 示例） |
| `solution_code` | **该方法的参考实现**（逐方法给出） |
| `test_class` | 该方法的测试类名 |
| `test_code` | **该方法的测试代码**（逐方法给出） |
| `dependencies` | 该方法依赖的其他方法（**方法级依赖关系**） |

结构统计（本地实测）：

| 指标 | 数值 |
| --- | --- |
| 题数 | 100 |
| 方法总数 | 410 |
| 每题方法数 | 最少 2，中位 4，最多 10 |
| 每题测试类数 | 最少 2，中位 5，最多 11 |
| skeleton 长度中位 | 2104 字符 |
| test 长度中位 | 5686 字符 |
| 有 `fields` 字段的题 | 77/100 |
| skeleton 中含 `pass` 占位的题 | 11/100 |

**判定：每一项任务天然包含多个方法 + 方法级依赖 + 方法级测试**，即"多个自然阶段、阶段间有明确接口、子功能可独立测试"三条判据**在数据层面直接成立**（这是本项目五项判据第一次在公开数据上被结构性满足，而不是靠人工标注推断）。

## 三、一个真实样例（完整链路，题 `ClassEval_0`）

- **类**：`AccessGatewayFilter`（访问网关过滤器，4 个方法）
- **给模型看的骨架**（`skeleton`，节选）：
  ```python
  import logging
  import datetime

  class AccessGatewayFilter:
      """
      This class is a filter used for accessing gateway filtering, primarily for authentication and access log recording.
      """

      def __init__(self):
          pass

      def filter(self, request):
          """
          Filter the incoming request based on certain rules and conditions.
          :param request: dict, the incoming request details
          :return: bool, True if the request is allowed, False otherwise
          >>> filter = AccessGatewayFilter()
          >>> filter.filter({'path': '/login', 'method': 'POST'})
          True
          """
  ```
- **参考实现**：`solution_code` 给出整类实现；`methods_info[i].solution_code` 给出**单个方法**的实现；
- **测试**：`test` 是 unittest 文件；`methods_info[i].test_code` 是**单个方法**的测试；`test_class` 给出类名（例如方法 `filter` ↔ `AccessGatewayFilterTestFilter`）。
- **链路完整性**：需求（方法 docstring）→ 骨架 → 参考实现：✔；测试：✔；**公开/私有可切分**：见下。

## 四、测试机制与公开/私有切分（本审计最重要的发现）

1. **每个方法都有自己的测试类**，因此切分可以**按方法**做：例如把方法 A、B 的测试公开给模型做自检，把方法 C、D 的测试留作私有判定——这正好满足执行文档"公开测试与私有测试严格隔离"的要求，而 BigCodeBench 每题只有一套测试、切分困难。
2. 实测运行方式：`solution_code + test + unittest.main()`，用隔离 venv 直接跑，**无需安装任何第三方库即可运行抽到的 3 题**；
3. **注意反向风险：`skeleton` 里已经给出全部方法签名和 docstring，等于把"怎么拆"直接告诉了模型。** 若直接拿 skeleton 当输入，M2 的分解环节就被泄漏了（这与执行文档 §11.2 步骤 E 的"解法形状泄漏"是同一类问题，只是发生在公开数据集上）。**研究"如何拆分"时必须显式设计对照**：
   - 输入 A：只给类描述（`class_description`），让模型自己决定拆成哪些方法（真实分解任务）；
   - 输入 B：给完整 skeleton（等于给定分解），只考"实现"环节；
   - 两者之差正好可以把"分解环节的价值"与"实现环节的价值"分开——这是本数据集能直接支撑的核心实验。

## 五、参考实现可运行性抽查（可复核）

规则在看结果前冻结：`random.seed(20260928)`，从 100 题中抽 3 题，每题连续 3 次，判定=退出码 0。

| 任务 | 3 次结果 | 单次耗时 |
| --- | --- | --- |
| `ClassEval_35` | 3/3 通过 | 3.94 / 5.03 / 4.01 秒 |
| `ClassEval_70` | 3/3 通过 | 0.61 / 0.62 / 0.62 秒 |
| `ClassEval_87` | 3/3 通过 | 0.73 / 0.69 / 0.64 秒 |

**汇总：3/3 题全部通过、3 次全一致。** 机器产物：`decomposition-bench/experiments/wp2_classeval/classeval_smoke_manifest.json`。

## 六、环境、网络、落盘

| 项目 | 结果 |
| --- | --- |
| 环境模式 | **Windows 原生 Python 即可**（官方 README 建议 conda + Python 3.8+，本次实测用既有 3.13 venv 直接跑通；若正式使用建议按官方建议单独建环境） |
| 现有环境 | `decomposition-bench/.venvs/bigcodebench_fast0/`（复用；正式立项时另建 `classeval` 专用 venv） |
| 新增下载 | **0.48 MiB**（数据） |
| 是否需要 Docker | **否** |
| 网络 | 仅下载时需要；运行测试不需要联网（实测） |
| 落盘路径 | `D:\yaorz\research\decomposition-bench\data\raw\classeval\`（D 盘） |
| 清理方法 | 删除该目录即可；无外部服务、无容器 |

## 七、可拆分性、污染、限制

- **可拆分性**：满足（见第二节，方法级依赖与测试均随数据给出）。
- **污染风险**：`【未知】`。ClassEval 2023-08 发布、数据来自开源仓库，可能出现在 Qwen2.5-Coder 的训练数据中；**Qwen2.5-Coder 的官方训练数据截止时间本轮仍未核实**，因此不能声称无污染。数据集本身提供 100 道手工构造的题（非直接抓 GitHub 文件），污染风险相对可控但未验证。
- **限制（必须写明）**：
  1. **只有 100 题**，规模是短名单里最小的；分层（高/低可拆分）后每层可能不足 8--10 题，需要评估；
  2. **单文件、无仓库上下文**：没有跨文件依赖，与"项目式代码"仍有距离（这是它相对 Commit0/EvoCodeBench 的短板）；
  3. **题风偏"教科书式"**：类小而完整、方法文档齐全，与真实项目里"上下文缺失、接口模糊"的情况有差距；
  4. **skeleton 会泄漏分解**（见第四节），设计输入时必须处理。

## 八、评分表（执行文档 §7.4 的 15 项，各项 0/1/2；`?`＝未核实）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 来源与许可证清晰度 | **2** | 仓库 MIT + 数据集 mit，均一手核实 |
| 需求描述完整度 | **2** | 类描述 + 逐方法 docstring（含参数/返回值/示例） |
| 项目上下文真实性 | **1** | 单文件、自包含，无仓库上下文 |
| 可执行测试完整度 | **2** | 逐方法 unittest，实测可跑通 |
| 公开/私有可分离性 | **2** | 可按方法切分（方法↔测试类一一对应） |
| 五项可拆分判据匹配度 | **2** | 多方法 + 依赖 + 逐方法测试，1--3 条成立 |
| 本机运行可行性 | **2** | Windows 原生、0.48 MiB、秒级 |
| Python 子集可用规模 | **1** | 全 Python，但仅 100 题 |
| 按仓库隔离切分可行性 | **?** | 数据无仓库信息；若需仓库级隔离需另找来源标注 |
| 污染与重复风险可审计性 | **1** | 可审计但未做；训练边界未知 |
| Windows/WSL2/Docker 依赖与稳定性 | **2** | 无容器依赖 |
| 体积与 D 盘落盘可控性 | **2** | 0.48 MiB |
| 网络可达性 | **2** | HF 经代理可达 |
| 是否确有至少两个自然阶段且能分阶段测试 | **2** | 每题 2--10 个方法，逐方法测试 |
| 判据与既有文献定义的对应程度 | **1** | 类级/方法级分解与 MoT、Revisiting Modularity 的定义可对应，但未逐篇建立映射 |

**总分：26 / 30（含 1 项未核实）**。硬性否决条件：**未命中任何一条**。

## 九、结论与建议

**结论：进入试运行（优先级 1）。** 它是目前唯一同时满足"多方法结构 + 逐方法测试 + 公开/私有可按方法切分 + 本机零成本运行 + 许可证清晰"的候选，且直接支持"如何拆分"的三类对照（是否给分解、按方法拆 vs 整体写、分解环节 vs 实现环节）。

**必须同时接受的三条限制**：100 题规模小；单文件无仓库上下文；skeleton 会泄漏分解（必须靠输入设计解决）。

**下一步（WP3）**：抽 10 题做可运行性试验（按执行文档 §8.2 的 4/3/3 分层），并**实测按方法切分公开/私有测试**是否真的不影响参考实现通过。
