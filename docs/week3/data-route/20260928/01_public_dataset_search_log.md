# WP1-1：公开数据集检索日志（第一轮）

日期：2026-09-28
工作包：WP1（执行依据 `docs/week3/9.28数据集路线_分步执行与Agent移交文档.md` §六）
状态：**第一轮，未完成**。已完成"按候选名定向核查"与"既有答案核查"两条主线；**逐会议、逐年的系统性检索尚未做**（见第五节"未完成项"）。
本轮未下载任何数据集（除 FAST-0 的 BigCodeBench 原始文件）；未调用生成模型；未修改既有产物。

## 一、检索方式与工具

> **2026-09-28 补充（同日稍后）**：用户开启了本机代理（`C:\...\Internet Settings` 中 `ProxyEnable=1`、`ProxyServer=127.0.0.1:7890`）。实测结果：
> - `github.com` / `api.github.com` / `raw.githubusercontent.com` / `codeload.github.com`：**可达**（经代理与直连都通）；
> - `huggingface.co`：**经代理可达**（0.41 s），直连仍超时；
> - `hf-mirror.com`、`pypi.org`：仍可达。
>
> 因此**本轮引用的许可证已改为经 GitHub API 与 Hugging Face API 一手核实**，结果汇总在 `docs/week3/公开数据集与论文链接清单.md`；本文件第三节原先"多数许可证未取一手文件"的说明**部分作废**（以链接清单为准）。同时做了两处更正：
> 1. **Commit0 的 arXiv 编号应为 `2412.01769`**（原记录 `2412.1769` 是错号，已核对 arXiv 页面标题）；
> 2. **DevEval / DevBench 存在至少三个不同工作**（`seketeam/DevEval` ACL 2024、`open-compass/DevEval` 全生命周期案例研究、2026 年 telemetry 版 DevBench），不得统称。

| 项 | 说明 |
| --- | --- |
| 检索工具 | Web 搜索（针对主题词）+ 定向抓取官方页面/arXiv/HF 元数据接口 |
| HF 元数据 | 经 `hf-mirror.com/api/datasets/<id>` 查询许可证、最后修改时间、下载量与文件体积（本机 huggingface.co 直连不可达，镜像可达，见 FAST-0 报告 §2.4） |
| 本机可达性 | `pypi.org` 可达；`hf-mirror.com` 可达；`huggingface.co` 与 `github.com` 从本机**不可达**（抓取工具走的是另一条网络路径，能读到 GitHub 页面，**这不代表本机能 clone**） |
| 检索日期 | 全部为 2026-09-28 |

## 二、本轮实际使用的检索式（逐条记录）

1. `paper comparing modular decomposition code generation versus direct monolithic generation equal budget repository-level evaluation`
2. `repository-level code generation benchmark comparison SWE-bench Commit0 DevBench Long Code Arena ClassEval RepoBench license task unit tests`
3. `DevEval benchmark github repository Fsoft license how to evaluate docker unit tests EvoCodeBench official repo`
4. `MASAI modular architecture software engineering AI agents SWE-bench sub-agents versus monolithic baseline comparison results`

HF 元数据定向查询的数据集 ID：
`bigcode/bigcodebench`、`princeton-nlp/SWE-bench`、`princeton-nlp/SWE-bench_Verified`、`SWE-bench/SWE-bench_Lite`、`FudanSELab/ClassEval`、`tianyang/repobench_python_v1.1`、`AWS-CodeWhisperer/CrossCodeEval`、`Fsoft-AIC/DevEval`、`Fsoft-AIC/EvoCodeBench-2403`、`livecodebench/code_generation_lite`、`xlangai/DS-1000`、`JetBrains-Research/lca-bug-fixing`、`commit-0/commit0`、`bigcode/the-stack`

## 三、HF 元数据查询的原始结果（可复核）

| 数据集 ID | 许可证（HF 元数据） | 最后修改 | 下载量 | 结果 |
| --- | --- | --- | --- | --- |
| `bigcode/bigcodebench` | **apache-2.0** | 2025-04-30 | 128,664 | 成功；数据文件 2.25 MiB（v0.1.4） |
| `princeton-nlp/SWE-bench` | **未标注（空）** | 2025-03-03 | 46,753 | 成功；但**许可证缺失** |
| `princeton-nlp/SWE-bench_Verified` | **未标注（空）** | 2025-02-18 | 244,376 | 成功；**许可证缺失** |
| `SWE-bench/SWE-bench_Lite` | **未标注（空）** | 2026-08-16 | 46,899 | 成功；**许可证缺失** |
| `FudanSELab/ClassEval` | **mit** | 2024-08-26 | 2,234 | 成功 |
| `tianyang/repobench_python_v1.1` | `cc`（未细分） | 2024-02-27 | 1,240 | 成功 |
| `livecodebench/code_generation_lite` | `cc`（未细分） | 2025-06-05 | 99,380 | 成功；主分支合计 **4.28 GiB** |
| `xlangai/DS-1000` | **cc-by-sa-4.0** | 2024-09-19 | 15,842 | 成功；3.28 MiB |
| `bigcode/the-stack` | `other` | 2026-08-03 | 10,557 | 成功（非本题所需，仅作对照） |
| `AWS-CodeWhisperer/CrossCodeEval` | — | — | — | **HTTP 401**，经镜像无法读取元数据 |
| `Fsoft-AIC/DevEval` | — | — | — | **HTTP 401**；后续查明官方仓库在 `seketeam/DevEval`，HF 组织名不对 |
| `Fsoft-AIC/EvoCodeBench-2403` | — | — | — | **HTTP 401**；后续查明 HF 上为 `LJ0815/EvoCodeBench`（页面显示总文件体积 1.2 GB） |
| `JetBrains-Research/lca-bug-fixing` | — | — | — | **HTTP 401** |
| `commit-0/commit0` | — | — | — | **HTTP 401**（ID 待核实） |

**说明**：401 可能表示数据被 gating（需要 HF 账号与 token），也可能只是镜像侧限制。由于本机 HF 直连不可达，**"gated 数据集能否在本机取得"目前是未解风险**，必须在 WP2 逐一确认。

## 四、定向核查得到的页面级事实（含来源）

| 事实 | 来源 | 性质 |
| --- | --- | --- |
| SWE-bench 2294 条真实 issue，来自 12 个 Python 仓库，生成补丁、用单元测试判定；有 Lite / Verified / Multilingual / Multimodal 等变体 | 综述 ar5iv 2510.04905；SWE-bench-Live 官方页 | 二手+官方页，**未核对原始论文** |
| Commit0：54 个 Python 库，从零实现整个库；给 spec PDF + 含单元测试的 starter 仓库；只用单元测试通过率计分；明确限制联网取原仓库 | arXiv 2412.1769（HTML 版） | 论文原文页面 |
| CoderEval：460 题（230 Python + 230 Java），六档上下文依赖，**Docker 环境自动评测** | 综述 2510.04905 引述 | 二手，未核对论文 |
| DevEval：1874 题 / 117 仓库 / 10 领域；任务=给签名+需求+仓库上下文生成函数体；评测=替换 body 后跑测试；官方建议 Ubuntu + conda | 官方仓库 `github.com/seketeam/DevEval` | 一手（仓库 README） |
| EvoCodeBench-2403：275 题 / 25 仓库；字段含 requirement、tests、dependency（intra_class / intra_file / cross_file）；评测=替换 body 后跑测试；需 Ubuntu + conda + 自带 `setup_env` 脚本 | 官方仓库 `github.com/seketeam/EvoCodeBench` | 一手（仓库 README） |
| ClassEval：100 题、类级生成、含多个相互依赖方法（手工构造）；HF 元数据许可证 MIT | 综述 2510.04905 引述 + HF 元数据 | 二手 + 一手元数据 |
| RepoBench-R/C/P、RepoEval、CrossCodeEval：行/片段级**补全**基准，非整段生成 | 综述 2510.04905 | 二手 |
| Long Code Arena：6 个不同任务（含 bug fixing、commit message 等），不适合按单一规模统计 | 综述 2510.04905 | 二手 |
| BigCodeBench：1140 题、单函数 `task_func`、依赖 723 个函数调用来自 139 个库、7 个领域 | DevBench(2026) 对比表 + FAST-0 实测 | 二手 + 一手实测 |

## 五、本轮未完成项（必须在下一轮补齐，不得当作已检索）

1. **逐会议检索未做**：NeurIPS / ICML / ICLR / AAAI / IJCAI / ACL / EMNLP / NAACL / ICSE / FSE / ASE / ISSTA / MSR / ICSME 的会议论文集**没有逐届翻阅**。本轮是"按已知候选名定向核查"，召回是否完整**未验证**。
2. **venue_year 未核实**：候选表的会议与年份字段多数尚未回到论文首页确认，暂标"待核"。
3. **许可证未拿一手文件**：SWE-bench 家族 HF 元数据里没有许可证；Commit0 / DevEval / EvoCodeBench / CoderEval 的 LICENSE 文件**未取原文**。
4. **污染与训练时间边界未查**：Qwen2.5-Coder 官方训练数据截止时间**未查**，因此 `contamination_risk` 一律为"未知"。
5. **环境可运行性未验**：EvoCodeBench / DevEval 官方要求 Ubuntu + conda；本机 Docker 守护进程未运行、WSL 内 HF 被阻断，**这些候选能否在本机跑通尚未验证**（属 WP3）。
6. **2021--2023 早期数据集**只覆盖了综述提到的名字，未系统补齐。
7. **未确认 gated 数据集能否下载**（见第三节说明）。

## 六、下一步

1. 补齐第 5.1--5.4 项，重点是**逐会议检索**与**许可证一手核对**；
2. 对短名单（见 `01_public_dataset_landscape.md`）做 WP2 静态审计；
3. G1 前必须把"公开数据能同时满足五项判据的比例"变成有证据的判断，而不是印象。
