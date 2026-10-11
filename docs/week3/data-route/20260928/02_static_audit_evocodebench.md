# WP2 静态审计：EvoCodeBench-2403

日期：2026-09-28 ｜ 结论：**暂缓（优先级 2）**——不是不合适，而是"还没验证能不能在本机跑通"
审计方式：HF API + GitHub API + 官方仓库 README + 文件清单。**未下载完整数据、未运行任何代码**。

## 一、来源与许可证

| 项目 | 内容 |
| --- | --- |
| 数据集 | `LJ0815/EvoCodeBench`（Hugging Face） |
| 代码仓库 | https://github.com/seketeam/EvoCodeBench |
| 论文 | EvoCodeBench: An Evolving Code Generation Benchmark Aligned with Real-World Code Repositories，[arXiv:2404.00599](https://arxiv.org/abs/2404.00599) |
| 仓库许可证 | **Apache-2.0**（GitHub API 一手核实） |
| 数据集许可证 | **HF 元数据无 license tag** ⚠ |
| 最后更新 | 数据集 2024-06-24；仓库 2024-08-15 |

**许可证风险（WP2 硬性核查项）**：数据集不含 275 个样本本身，而是**25 个真实开源仓库的源码打包**（`Source_Code.tar.gz`）+ 依赖数据。仓库的 Apache-2.0 只覆盖**评测代码**，**数据里那 25 个上游仓库各自的许可证必须逐仓库核查**，否则不能确认可再分发。此项**未完成**。

## 二、数据文件与体积（HF 实测）

| 文件 | 体积 |
| --- | --- |
| `EvoCodeBench-2403/Source_Code.tar.gz` | 995.61 MiB |
| `EvoCodeBench-2403/Dependency_Data.tar.gz` | 152.48 MiB |
| `EvoCodeBench-2403/data.tar.gz` | 0.08 MiB |
| 合计 | **约 1.15 GB** |

## 三、任务结构与字段（来自官方 README，未下载核实）

每题字段：`namespace`（如 `benedict.utils.type_util.is_bool`）、`type`（function / method）、`completion_path`、`signature_position`、`body_position`、`dependency`（`intra_class` / `intra_file` / `cross_file`）、`indent`、**`tests`**（测试函数列表）、`requirement`（`Functionality` + `Arguments`）、`domain`。

- **任务单元：单个函数体**（替换 `body_position` 处代码后跑测试）；
- 275 题 / 25 仓库；评测时**同一仓库不能并行跑**（README 明确警告，否则结果不可信）。

**可拆分性判断**：`【推断】` 中等。题目带跨文件依赖（说明需要理解项目），但**交付单位是单个函数体**，题内没有"多阶段接口"。按五项判据第 1--3 条只能算部分满足。

## 四、环境与运行（官方要求，未实测）

- README 原文：**"强烈建议在 Ubuntu 下评测，并使用 conda 建虚拟环境"**；
- `conda create --name EvoCodeBench --python=3.10` + `pip install numpy func-timeout tqdm textwrap psutil tiktoken`；
- 需要修改 `envir_setup.sh` 中的 Root 变量后运行 `bash setup_env`。

**本机含义**：需要 WSL2（已装 Ubuntu-22.04）或 Windows 上自行拼环境；WSL 内的网络曾受限（此前记录 HF 被阻断，用户开代理后**WSL 是否自动走代理未验证**）。**这是本候选最大的未验证点。**

## 五、落盘与清理方案

- 落盘：`D:\yaorz\research\decomposition-bench\data\raw\evocodebench\EvoCodeBench-2403\`（D 盘，约 1.15 GB）；
- 环境：若走 WSL，conda 环境需显式指定到 `/mnt/d/...`，避免写入 WSL 根文件系统（其 VHDX 虽在 D 盘，但内部路径仍建议外挂）；
- 清理：删除上述目录 + 对应 conda env 即可；无 Docker 依赖（若不用容器）。

## 六、评分表（15 项，0/1/2；`?`＝未核实）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 来源与许可证清晰度 | **1** | 仓库 Apache-2.0 清楚，但数据集无 tag + 25 个上游仓库逐仓许可未查 |
| 需求描述完整度 | **2** | 有 Functionality + Arguments 两段 |
| 项目上下文真实性 | **2** | 真实仓库 + 跨文件依赖 |
| 可执行测试完整度 | **2** | `tests` 字段随数据给出 |
| 公开/私有可分离性 | **1** | 官方只有一套测试，需自行在不泄漏前提下切分 |
| 五项可拆分判据匹配度 | **1** | 有跨文件依赖，但交付单位是单函数体 |
| 本机运行可行性 | **?** | 需 Ubuntu + conda，未实测 |
| Python 子集可用规模 | **2** | 全 Python，275 题 |
| 按仓库隔离切分可行性 | **2** | 数据带仓库路径，天然可按仓库切分 |
| 污染与重复风险可审计性 | **1** | 有跨仓库复制风险；训练边界未知 |
| Windows/WSL2/Docker 依赖与稳定性 | **1** | 官方建议 Ubuntu + conda |
| 体积与 D 盘落盘可控性 | **2** | 1.15 GB，方案已定 |
| 网络可达性 | **2** | HF 经代理可达 |
| 是否确有至少两个自然阶段且能分阶段测试 | **1** | 单函数体交付，阶段划分靠外部推断 |
| 判据与既有文献定义的对应程度 | **1** | 未逐篇建立映射 |

**总分：约 20--21 / 30（1 项未核实）**。硬性否决条件：**目前未命中**，但第 1 条（许可证）处于"未完成核查"状态。

## 七、结论与下一步

**结论：暂缓，保留为优先级 2。** 它有真实仓库上下文与可执行测试，是"项目式"方向的主要备选；但存在两个未验证的关键点：**25 个上游仓库的许可证** 与 **WSL/conda 能否在本机装成**。

**下一步（若继续）**：① 逐仓库查 25 个源仓库许可证；② 在 WSL 内做一次最小安装试验（约 1.15 GB 下载）；③ 抽 1 题跑通参考实现。三项都过才进入 WP3。
