# WP2 补充核查：许可证、训练边界、WSL 实测、LCA 评测方式

日期：2026-09-28 ｜ 性质：对 `02_static_audit_summary_and_shortlist_update.md` 的补充与更正
本轮**未运行任何代码生成模型**（LLM 调用 0 次）；未安装任何软件；未修改任何系统设置。

---

## 一、EvoCodeBench 的上游仓库许可证：链条不成立

做法：下载该数据集仅 0.08 MiB 的元数据包（`data.tar.gz`，实测 84,579 字节），取出 275 题、识别出 **25 个上游仓库**，再用 GitHub 搜索 + 仓库 API 逐个查 `license.spdx_id`。

**结果（25 个仓库，逐个实测）**：

| 许可证类型 | 仓库数 | 仓库名 |
| --- | --- | --- |
| Apache-2.0 | 7 | litData、camp_zipnerf、searcharray、nlm-ingestor、XAgent、UHGEval、contrastors |
| MIT | 8 | UniRef、microagents、open-iris、ollama-python、tanuki.py、microsearch、fast-stable-diffusion、Python-Type-Challenges |
| BSD-3-Clause | 1 | skfolio |
| **AGPL-3.0** | **2** | stable-diffusion-webui-forge、Simulated_Scepter |
| **GPL-3.0** | **1** | deluder |
| NOASSERTION（有协议但 GitHub 无法归类） | 4 | EasyVolcap、AutoRAG、openai-testing-agent-demo、gaussian-splatting-lightning |
| **无许可证** | **2** | Generalizable-BEV、openlogprobs |

**结论：EvoCodeBench 的许可链条不成立**，理由三条：

1. 混入 **AGPL-3.0 / GPL-3.0 三个强传染性许可**，把它们的代码打进数据包再分发会带来额外义务；
2. **两个仓库没有许可证**（默认保留全部权利），不应再分发；
3. **四个 NOASSERTION 需要人工读 LICENSE 原文**，且本轮仓库映射靠"按名字搜索"，其中 `stable-fast`、`Test-Agent`、`scepter`、`deluder` 等**可能是同名错配**（例如 `Test-Agent` 命中的是 `openai/openai-testing-agent-demo`）。

**处理建议**：若仍要走 EvoCodeBench，只能①人工确认每个仓库映射；②把任务集限制在"上游仓库为 MIT/Apache-2.0/BSD"的子集；③对 AGPL/GPL/无许可的仓库任务剥离。**这会显著缩小可用题量**（275 题中至少 3 题必删、6 题待定）。当前状态：**暂缓，且比第一轮审计时风险更高**。

## 二、Qwen2.5-Coder 的训练数据时间边界：官方未披露

- 官方模型卡（`Qwen/Qwen2.5-Coder-7B-Instruct` 的 README）只写"5.5 万亿 token、含源码/文本-代码对齐/合成数据"，**没有任何训练数据截止时间**；
- 技术报告（[arXiv:2409.12186](https://arxiv.org/abs/2409.12186)）摘要同样未披露截止时间。

**按执行文档 §6.4 第 11 条，此项必须明确记为"未知"，不得凭记忆填写日期。**

**由此得到一个对全部候选都成立的结论**：Qwen2.5-Coder 于 **2024-09 发布**，而本轮候选数据的发布时间全部早于它——ClassEval（2023-08）、EvoCodeBench（2024-03/06）、DevEval（2024-05）、BigCodeBench（2024-06）、Commit0（2024-12）、LCA（2024-06）。因此**"优先选择模型发布之后提交的代码来降低污染"这一手段，在本轮候选上全部失效**；污染风险只能保持"未知"，不能声称已控制。

## 三、WSL 实测（决定 EvoCodeBench 的 Ubuntu+conda 路线可行性）

2026-09-28 实测（只读探测，未安装任何软件）：

| 项目 | 实测结果 |
| --- | --- |
| 发行版 | `Ubuntu-22.04`（版本 2，本次探测时由 Stopped 启动）；另有 `docker-desktop` 发行版 |
| Python | **3.10.12**（符合 EvoCodeBench 要求的 3.10） |
| conda | **未安装**（`which conda` 无输出） |
| pip | 22.0.2（系统 pip） |
| 磁盘 | `/dev/sdd 1007G 总、23G 已用、934G 可用` |
| 直连网络 | **pypi 可达（200）**；**huggingface.co 不可达**（`Network is unreachable`） |
| 走 Windows 代理 | **失败**：`127.0.0.1:7890` 返回 `Connection refused`；WSL 自己的提示是"检测到 localhost 代理配置，但未镜像到 WSL。NAT 模式下的 WSL 不支持 localhost 代理" |

**两条可用的结论**：

1. **939 GiB 之谜解决（实测证据）**：WSL 内看到的是 `/dev/sdd` **1007 G 的虚拟磁盘**（已用 23 G、可用 934 G），即 WSL2 虚拟磁盘的**容量上限约 1 TB**。**物理 D 盘实际只剩 120.3 GiB**，所以 WSL 侧读写最终受物理盘限制——**磁盘预算必须用物理剩余量**（此前的 `【推断】` 现已被实测证实）。
2. **EvoCodeBench 的路线可行但要多绕一步**：数据必须在 **Windows 侧下载后经 `/mnt/d` 载入 WSL**（HF 在 WSL 内不可达）；WSL 内无 conda，**改用 `python3 -m venv` 即可**；pip 装包在 WSL 内直连 pypi 正常。
   - 另有可选方案：在 `.wslconfig` 开 `networkingMode=mirrored` 让 WSL 直接用 Windows 的代理——这属于**系统级配置改动**，本轮**未做**，需用户明确同意后才考虑。

## 四、Long Code Arena（library-based code generation）审计结论：排除作为主评测集

| 项目 | 结果 |
| --- | --- |
| 许可证 | 数据集 **apache-2.0**；卡片明确写"所有仓库均为宽松许可（MIT / Apache-2.0 / BSD-3-Clause / BSD-2-Clause）"✔ **许可链条清楚，是本轮候选里最好的之一** |
| 规模 | **150 条**人工撰写指令，来自 **62 个 Python 仓库**；核心数据 `data/test-*.parquet` **4.37 MiB** |
| 目录结构 | 另有 `repos/*.tar.gz`（45+ 个库的快照，合计 **1,361 MiB**），用于"给模型构建上下文"，**可选** |
| 字段 | `instruction`、`reference`、`clean_reference`、`path_to_reference_file`、`n_unique_apis`、`unique_apis`、`project_defined_elements`、`api_calls`、`internal_apis` 等 |
| **评测方式** | 官方 `lca-baselines/library_based_code_generation` 的 README 明确：计算 **`ChrF` 与 `API Recall`** 两个指标——**文本相似度 + API 召回，不是执行测试** |

**判定：排除作为主评测集。** 理由：我们的判定必须"可执行、可自动、可复现"，而 ChrF/API Recall 衡量的是"像不像参考程序、有没有用到该库的 API"，**没有 pass/fail 的正确性判定**，命中执行文档 §7.3 硬性否决第 3 条（无法形成稳定的自动判定）。

**保留价值**：它的"给模型项目上下文"做法、宽松许可的仓库快照、以及 45+ 个真实库的代码，可以作为**自建任务（WP4B）的素材与上下文来源**；也可作为"生成代码是否真的用上了项目内部 API"的辅助观察指标（不能替代测试判定）。

## 五、更新后的候选状态（覆盖前一份汇总中的相应行）

| 候选 | 更新后状态 | 变化原因 |
| --- | --- | --- |
| ClassEval | 进入试运行（优先级 1） | 不变 |
| EvoCodeBench-2403 | **暂缓，风险上调** | 上游仓库许可链条不成立（AGPL×2、GPL×1、无许可×2、NOASSERTION×4）；WSL 路线需绕行 |
| DevEval | 排除 | 不变（仓库无 LICENSE） |
| Commit0 | 排除 | 不变（需 Docker/Modal） |
| BigCodeBench | 保留为可运行对照 | 不变 |
| LCA library-based code generation | **排除（主评测集）** | 评测为 ChrF/API Recall，非执行测试 |
| LCA 其他任务（bug localization / project-level completion / module summarization 等） | 未审 | 本轮只审了 library-based 一个 |

## 六、本轮仍未完成（承接 Task #8）

1. **WP1 逐会议检索**（NeurIPS / ICML / ICLR / AAAI / IJCAI / ACL / EMNLP / NAACL / ICSE / FSE / ASE / ISSTA / MSR / ICSME）——召回完整性仍未被验证；
2. **通读 Revisiting Modularity（2407.11406）、GenSE-Scheduler、MASAI 原文**核对数字；
3. LCA 其余 5 个任务是否与"拆分"相关，未审；
4. EvoCodeBench 的上游仓库**映射确认**（本轮是名字搜索，可能有错配）。

## 七、产物

- 本文件 `03_wp2_supplement_licenses_cutoff_wsl_lca.md`
- 机器产物：`codeprm-reproduction/data/raw/evocodebench/data_extracted/data.jsonl`（275 题元数据）、`upstream_repo_licenses.json`（25 个仓库的许可核查记录）
- 脚本：`codeprm-reproduction/scripts/fast0_bigcodebench/wp2_evocodebench_repo_licenses.py`、`wp2_evocodebench_upstream_licenses.py`、`wp2_cutoff_and_lca.py`、`wp2_wsl_probe.py`
