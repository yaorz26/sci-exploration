# WP2 静态审计汇总与短名单更新（供 G1 使用）

日期：2026-09-28
范围：对短名单 4 个候选（ClassEval、EvoCodeBench-2403、DevEval、Commit0）做完**第一轮**静态审计；另有 1 个新候选（Long Code Arena 的 library-based code generation）待审。
**本文件不替 G1 做决策**，只提供证据、代价与选项。G1 的正式结论须由用户/导师拍板。

---

## 一、审计结果一览

| 候选 | 结论 | 关键阻塞点 | 一手证据 |
| --- | --- | --- | --- |
| **ClassEval** | **进入试运行（优先级 1）** | 无硬性阻塞；限制是 100 题、单文件无仓库上下文、skeleton 会泄漏分解 | 仓库 MIT + 数据集 mit；0.48 MiB；**参考实现 3/3 题 × 3 次全部通过**；每题 2--10 个方法、逐方法测试与依赖随数据给出 |
| **EvoCodeBench-2403** | **暂缓（优先级 2）** | ① 25 个上游仓库许可证未逐一核查；② 需 Ubuntu + conda，本机未验证 | 仓库 Apache-2.0（HF 数据集无 license tag）；约 1.15 GB；275 题 / 25 仓库；单函数体交付 |
| **DevEval** | **排除** | **仓库无 LICENSE 文件**，数据集标 cc-by-4.0，而上游是 117 个真实仓库 → 许可证链条不成立（命中硬性否决第 1 条） | GitHub API `license=null`；HF 数据集 cc-by-4.0；约 1.5--2.4 GB；1874 题 |
| **Commit0** | **排除** | 跑测试**需 Docker 或 Modal**（本机守护进程未运行）；整库任务规模与 8192 token 输入上限不匹配（命中硬性否决第 4、9 条） | 仓库 MIT；HF 仅 0.02 MiB 元数据；README 明确要求 docker/modal；54 库 |
| **BigCodeBench**（已完成 FAST-0） | 保留为**可运行对照** | 任务单元是单函数，不满足五项判据前三条 | Apache-2.0；1140 题；参考测试 5/5 稳定通过 |
| **LCA library-based code generation**（新，未审） | **待审** | 测试机制未确认 | HF 数据集 apache-2.0；约 1.36 GB；字段含 `instruction`、`reference`、`clean_reference`、`internal_apis`、`n_unique_apis` |

## 二、"好跑的都不够可拆分"这条矛盾，现在有具体证据了

执行文档 §9.2 要求 G1 正面回答"同时满足『至少两个自然阶段、能分阶段测试、许可证清楚、本机稳定运行』的候选比例是多少"。第一轮审计给出的答案是：

| 候选 | 多自然阶段 | 分阶段可测 | 许可证清楚 | 本机稳定运行 |
| --- | --- | --- | --- | --- |
| ClassEval | ✔（2--10 方法） | ✔（逐方法测试） | ✔ | ✔（实测） |
| EvoCodeBench | ✘（单函数体） | 部分 | 未完成 | 未验证 |
| DevEval | ✘（单函数体） | 部分 | **✘** | 未验证 |
| Commit0 | ✔（整库） | ✔ | 部分 | **✘**（需容器） |
| BigCodeBench | ✘（单函数） | ✘ | ✔ | ✔（实测） |

**四项同时满足的只有 ClassEval 一个**，而它恰恰是"单文件、无仓库上下文、仅 100 题"的那一个。**结论（推断）：在当前条件下，公开数据里"结构够用 + 本机跑得动 + 许可干净"的交集非常薄，G1 很可能落在"有条件采用公开数据"或"公开主集 + 自建补充集"。**

## 三、对"如何拆分"这个主攻方向的直接影响

用户 2026-09-28 明确侧重是**拆分方法 / 是否拆分的判断 / 拆分—生成—组合的提示词工程**。按这个标准重排候选：

1. **ClassEval 是唯一能立刻开做的**：它每题的 `methods_info` 里逐方法给出 `method_name`、`method_description`、`solution_code`、`test_class`、`test_code`、**`dependencies`（方法级依赖）**——等于**自带一份"分解参考答案 + 分阶段测试"**。可以直接支撑三类对照：
   - **是否给分解**：只给类描述（让模型自己拆） vs 给完整 skeleton（分解已给定）；
   - **拆分粒度**：按方法逐个实现 vs 一次性写完整个类；
   - **分环节归因**：分解环节错（拆错方法/漏依赖）与实现环节错（方法写错）可分别统计。
   注意其中"给完整 skeleton"会**泄漏分解**，必须作为对照臂而非默认输入。
2. **EvoCodeBench / LCA** 提供"项目级上下文"，是补 SQL 短板的方向，但都还没验证能不能跑。
3. **Commit0 的价值转向"模板"**：它的库--模块结构可以作为**自建小规模任务（WP4B）的设计模板**，而不是直接使用。

## 四、给 G1 的三个选项（附代价）

| 选项 | 内容 | 代价 / 风险 | 适用条件 |
| --- | --- | --- | --- |
| **A. 只采用 ClassEval** | 用 100 题 + 逐方法测试做"如何拆分"的探索性对照 | 无仓库上下文；100 题分层后每层不足 8--10 题；结论只能到"探索性" | 接受"单文件类级任务"作为第一阶段边界 |
| **B. ClassEval 为主 + EvoCodeBench 补充** | 前者做分解策略对照，后者补项目级上下文 | 需先解决 EvoCodeBench 的 25 仓库许可 + WSL/conda 验证（约 1.15 GB 下载） | 愿意多花 1--2 天做环境与许可核查 |
| **C. 公开主集 + 自建小规模补充** | 公开数据做通用对照，自建 20--30 题按 Commit0 式"模块级"结构做拆分监督 | 自建需人工审核需求泄漏与测试隔离，成本最高；但能把"项目式"这条真正补上 | 导师认可"数据集本身也算成果"且愿意投入 |

## 五、本轮未完成项（不得当作已做）

1. 未核实 EvoCodeBench 的 25 个上游仓库许可证、未在 WSL/conda 内做任何安装试验；
2. 未审 LCA `lca-library-based-code-generation` 的测试机制（字段里没有测试列，需查评测代码）；
3. 未核实 Qwen2.5-Coder 的训练数据截止时间（污染判据仍为"未知"）；
4. 未做 WP1 的**逐会议检索**（召回完整性仍未被验证）；
5. 未通读 Revisiting Modularity / GenSE-Scheduler / MASAI 原文（既有答案核查仍有"只看摘要"的弱点）；
6. ClassEval 的评分表中"按仓库隔离切分可行性"仍为未核实——它没有仓库字段，若研究需要仓库级隔离，需要另想切分口径（例如按类名/领域做分组，或只按题号随机分组并如实标注）。

## 六、产物清单

- `02_static_audit_classeval.md`、`02_static_audit_evocodebench.md`、`02_static_audit_deveval.md`、`02_static_audit_commit0.md`
- 本文件 `02_static_audit_summary_and_shortlist_update.md`
- 机器产物：`decomposition-bench/experiments/wp2_classeval/classeval_smoke_manifest.json`
- 数据：`decomposition-bench/data/raw/classeval/data/test-00000-of-00001-5c45fa6e45572491.parquet`（SHA-256 `ac2f49…df2a`）
- 脚本：`decomposition-bench/scripts/fast0_bigcodebench/wp2_static_probe.py`、`wp2_classeval_smoke.py`
