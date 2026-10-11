# WP1 收口：会议导向检索结果与既有答案更新

日期：2026-09-28 ｜ 性质：WP1 遗留项的补齐 + **对 `01_prior_answer_and_research_gap.md` 的重要更正**
本轮未运行任何代码生成模型；检索与核对均为只读。

---

## 一、本轮做了什么（口径可复核）

| 动作 | 具体做法 |
| --- | --- |
| 会议导向检索 | 用"会议 + 年份 + 代码生成/基准/数据集"组合式检索（2024--2026），定向找**新发布的基准与数据集**；检索式与命中见第二节 |
| 原文核对 | 读本地已有抽取文本 `archive/pdftext/09_MoT.txt`（77,908 字符），确认它到底是哪一篇 |
| 仓库核对 | 查 EvoCodeBench 官方仓库内容，确认是否存在官方仓库映射表 |
| 其余任务核对 | 读 `lca-baselines` 其余 5 个任务的 README，确认各自评测指标 |

**未做（不得当作已做）**：没有逐届翻阅 ICSE/FSE/ASE/NeurIPS/ICML/ICLR/ACL 等会议论文集，因此**召回仍可能有遗漏**；本轮是"会议导向的关键词检索 + 官方页面核对"，不是穷举。

## 二、会议导向检索命中的新基准（2025--2026）

| 工作 | 会议/年份 | 任务单元 | 与我们的关系 |
| --- | --- | --- | --- |
| **RepoMasterEval** | **ASE 2025** | 代码**补全**（在真实仓库文件里挖空一段） | 用**变异测试**衡量测试用例有效性、对低变异分的用例人工补充——这是"测试能不能区分候选"的方法论参考，可直接借用 |
| **RealisticCodeBench** | **ASE 2025** | 函数级（376 题，Python 361 + JS/TS/Java/C++），题源是"GitHub 上被 ChatGPT/Copilot 生成过的代码" | 与我们问题形态不符（补全/函数级），但说明"真实化"是当前基准的趋势 |
| **HumanEvo** | **ICSE 2025** | **仓库级**代码生成，强调"未来上下文泄漏"与"有用上下文缺失" | 需要 conda + 逐实例克隆仓库与运行时环境 → 与本机条件冲突（同 Commit0/SWE-bench 一类） |
| **DevBench（2026，telemetry 版）** | arXiv 2601.11895 | 实例级补全，1800 题 | 已在候选表中，维持"不进短名单" |
| **软件工程 LLM 基准基础设施综述** | AI Foundation Models & SE 2026 | 综述 | 见第三节引用的事实 |

## 三、从综述与官方页面取得的、对判断有直接影响的事实

1. **EvoCodeBench 的污染控制**：该综述称 EvoCodeBench"把数据泄漏从 **41.47% 降到 2.18%**"，且"最好的模型 Pass@1 只有 **20.74%**"（二手引述，未见原文核对）。
   - 读法：它的泄漏控制设计确实比 APPS 类更好；但**最好的模型只有两成通过率**，对我们来说意味着候选池可能更空——这与执行文档要求的前置探针（P0）用途一致。
2. **LiveCodeBench 的污染证据**：模型在"训练截止时间之后发布的问题"上性能**下降 15--20%**（二手引述）。这为"污染会实质影响分数"提供了直接证据，也说明**我们候选全部早于 Qwen2.5-Coder 发布**这件事不是小事。
3. **SWE-bench 的规模—难度落差**：同一综述称"在 SWE-bench Verified 上超过 70% 的模型，到 SWE-bench Pro（私有商业代码库、近期 issue）只有 23%"——**下降 47 个百分点**，作者据此判断是记忆而非真实修复能力。
4. **社区对小题量基准的定性**（研讨会结论，直接支持我们的标签上限）："约 200 条的小基准适合当**冒烟测试**，但**不足以**做微调或综合能力评估。"
   - 这句话与执行文档"20--30 题只能称探索性"的判断方向一致，可作为外部依据引用。

## 四、对既有答案的重要更正：项目里的"MoC/MoT"是两篇不同论文

**更正内容**：`archive/pdftext/09_MoT.txt` 的正文标题是 **"MoT: Modularization-of-Thought Prompting for Effective Code Generation"**（Ruwei Pan, Hongyu Zhang, 重庆大学），即 **arXiv 2503.12483**，被 **ISSTA 2026** 接收（Proc. ACM Softw. Eng., Vol.3, ISSTA, Article ISSTA082, DOI 10.1145/3832173）。它是**纯提示词方法**，不做任何训练。

而 `01_prior_answer_and_research_gap.md` 第一组里写的"**MoTCoder / MoT**（SFT，APPS +5.8%、CodeContests +5.9%）"指的是**另一篇**：arXiv 2312.15960 的 **MoTCoder（Module-of-Thought 指令微调）**。

**两篇都叫 MoT，必须分开写**：

| | MoT（2503.12483，ISSTA 2026） | MoTCoder（2312.15960） |
| --- | --- | --- |
| 手段 | **纯提示词**（Modularization-of-Thought + MLR 图） | **指令微调（SFT）** |
| 模型 | GPT-4o-mini、DeepSeek-V3-671B、DeepSeek-R1 | Qwen2.5-Coder-7B-Instruct（1 epoch，最大输入 2048 token） |
| 基准 | HumanEval / HumanEval-ET / HumanEval+ / MBPP / MBPP-ET / MBPP+ / LiveCodeBench / RAL-Bench | APPS、CodeContests |
| 结果 | HumanEval Pass@1 **92.1**、HumanEval+ **83.5**、HumanEval-ET **91.5**；相对 6 个基线平均提升 **0.03%--32.85%** | 报告提升 **APPS / CodeContests 约 5.8--5.9 个百分点**（两处来源对调 APPS 与 CodeContests 的具体数值，**待核**） |
| 是否重组 | **不重组** | 不重组 |
| 是否等预算 | 未报告等预算对照（报 Pass@1） | 未报告 |

## 五、这对本项目"研究增量"的影响（必须诚实写清）

**负面**：MoT（ISSTA 2026）是**纯提示词的模块化方法，并且报告了正结果**。这**削弱**了"只靠提示词做分解没有价值"的说法，也削弱了我们原来"没人做过 prompt-only 拆分对照"的表述。

**但差异仍然清楚**，我们与 MoT 的配置有六处不同：

1. **任务域**：MoT 用的是 HumanEval/MBPP 家族（函数级单点）与竞赛题；我们是**多方法/多阶段**的类级与项目式任务；
2. **模型**：MoT 用 GPT-4o-mini / DeepSeek-R1/V3（API 大模型）；我们是**本地 7B、8GB 单机**；
3. **是否重组**：MoT 不重组；我们 M2 的核心机制是**跨候选重组**；
4. **预算口径**：MoT 报 Pass@1，无等预算对照；我们要求**等预算**并单独报告候选池上限；
5. **任务结构分层**：MoT 没有"高可拆分层 vs 低可拆分负对照层"的**交互检验**；
6. **判定指标**：MoT 用题目 Pass@1 汇总；我们要求**题目级成对差异**与分环节失败归因。

**因此修订后的可主张增量（比上一版更窄）**：

> 在**本地 7B、等预算、零训练**条件下，**带跨候选重组**的分解生成在**多阶段任务**上是否优于直接生成，并且这个差异是否**随任务可拆分性变化**——这是 MoT（不重组、无分层、用大模型 API）、MoTCoder（需 SFT）、DecompRL（需 RL 与 80×H100）三条路线都未覆盖的组合。

**同时保留两条限制**：① MoT 的正结果说明这条路上**存在**可行的方法，我们的路线**有可能**得到正信号（这比上一版乐观一点）；② 但 MoT 的收益是否来自"分解"本身、还是来自"更长的中间推理 + 多一次调用"，其消融（RQ2/RQ4）需进一步细读才能判断——本轮只读了摘要与结果段落。

## 六、LCA 其余 5 个任务的评测方式（补齐上一轮）

| 任务 | 评测指标 | 是否可执行判定 |
| --- | --- | --- |
| bug_localization | 文件级匹配（notebook 中计算） | 否（非执行） |
| **ci-builds-repair** | **把仓库推回 GitHub，请求真实 GitHub CI 结果** | **否，且依赖外部服务**（命中硬性否决第 8 条） |
| commit_message_generation | 文本指标（BLEU 类） | 否 |
| module_summarization | **LLM-as-assessor**（用大模型判断生成文档与真值谁更好） | 否 |
| project_level_code_completion | **困惑度（perplexity）** + 单行补全 | 否 |

**结论：LCA 六个任务全部没有执行型判定**，整体排除作为主评测集（与上一轮对 library-based 的结论一致）。

## 七、EvoCodeBench 仓库映射：官方仓库里没有映射表

查 `seketeam/EvoCodeBench` 仓库内容：只有代码（`LM_inference.py`、`pass_k.py`、`setup_env.sh`、`prompt/`、`parser/` 等）、LICENSE、README 与 `croissant_metadata.json`，**没有任何仓库清单文件**。因此 25 个上游仓库的映射**只能从源码包或论文附录确认**；上一轮"按名字搜索"得到的 25 条许可核查结果**仍需人工复核**（其中 4--5 条疑似错配）。

## 八、WP1 状态

| 验收项 | 状态 |
| --- | --- |
| 三类会议来源都被实际检索 | **部分**：做了会议导向的关键词检索，未逐届翻阅论文集 |
| 短名单有一手来源 | 完成 |
| 区分保留/待定/排除并留理由 | 完成（见 WP2 与补充文档） |
| 形成 3--5 个静态审计候选 | 完成（4 个，另 1 个 LCA 已审并排除） |
| 逐一证实或推翻既有初筛线索 | 完成（BigCodeBench 证实可运行但结构不符；SWE-bench/Commit0 证实本机不可行；DevBench 证实为三个不同工作） |
| 明确回答同类研究是否已回答主问题 | 完成（本节第四、五节） |
| 模型训练数据时间边界有官方证据或标未知 | 完成（标为**未知**，官方未披露） |

## 九、产物

- 本文件 `04_wp1_venue_search_and_gap_update.md`
- 脚本 `codeprm-reproduction/scripts/fast0_bigcodebench/wp1_evocodebench_repos_and_lca_metrics.py`
- 依据的本地文本：`archive/pdftext/09_MoT.txt`
