# FAST-0 报告：BigCodeBench 参考实现可运行性抽查

日期：2026-09-28
工作包：FAST-0（半天最小可行路径）
依据：`docs/week3/9.28数据集路线_分步执行与Agent移交文档.md` §四（FAST-0 定义）、§5--§8
产物：
- 本报告 `docs/week3/data-route/20260928/00a_fast0_bigcodebench_smoke_report.md`
- 机器产物 `codeprm-reproduction/experiments/fast0_bigcodebench/fast0_smoke_manifest.json`（v1，装 pytz 前）
- 机器产物 `codeprm-reproduction/experiments/fast0_bigcodebench/fast0_smoke_manifest_v2_pytz.json`（v2，装 pytz 后）
- 脚本 `codeprm-reproduction/scripts/fast0_bigcodebench/inspect_dataset.py`、`run_reference_tests.py`
- 原始数据 `codeprm-reproduction/data/raw/bigcodebench/v0.1.4/bigcodebench_v0.1.4_full.parquet`

**本轮未做的事**：没有调用任何代码生成模型（LLM 调用数 = 0）、没有拉取 Docker 镜像、没有安装官方 `bigcodebench` 评测包、没有修改任何既有冻结产物、没有解除实验暂停。

> **2026-09-28 同日后补（网络条件变化，影响本报告 §2.4）**：用户开启了本机代理（注册表 `ProxyEnable=1`、`ProxyServer=127.0.0.1:7890`）。重新实测：`github.com`、`api.github.com`、`raw.githubusercontent.com`、`codeload.github.com` **均可达**；`huggingface.co` **经代理可达**（直连仍超时）；`hf-mirror.com` 与 `pypi.org` 仍可达。
> 因此本报告 §2.4 与 §五第 6 条中"GitHub 从本机不可达"的结论**已不成立，以本条为准**；"HF 直连不可达、需走镜像或代理"仍然成立。许可证亦已改为一手核实，见 `docs/week3/公开数据集与论文链接清单.md`。

---

## 一、一句话结果

**FAST-0 通过。** BigCodeBench v0.1.4 可以在本机（Windows 原生 + D 盘隔离环境）完整下载、加载并跑通参考实现测试：抽 5 题 × 3 次全部通过且结果稳定；总下载量约 2.3 MB，远低于 2 GiB 额度。**但同一轮检查发现一个对研究问题更重要的结构事实：BigCodeBench 的任务单元是"单个函数"，不满足本项目五项可拆分判据中的前三条**——这正是复审预告的"好跑的都不够可拆分"矛盾，需要在 G1 认真处理。

---

## 二、可核查事实

### 2.1 来源与许可证

| 项目 | 结果 |
| --- | --- |
| 数据集 | `bigcode/bigcodebench`（Hugging Face） |
| 版本 | v0.1.4（另有 v0.1.0 / 0.1.0_hf / 0.1.1 / 0.1.2 / 0.1.3） |
| 许可证 | **apache-2.0**（来自 HF 数据集元数据 tag `license:apache-2.0` 与 cardData） |
| 最后修改 | 2025-04-30T17:34:50Z（HF 记录） |
| 论文 | arXiv:2406.15877（HF 元数据 tag） |
| 下载量记录 | 128,664（HF 记录） |
| 原始文件 | `data/v0.1.4-00000-of-00001.parquet`，**2,362,110 字节（2.25 MiB）** |
| 本次落盘 | `codeprm-reproduction/data/raw/bigcodebench/v0.1.4/bigcodebench_v0.1.4_full.parquet` |
| 文件 SHA-256 | `d9a4965821c9507ebdfb551c288656b2d5fe553234f5183044333ca8a4018267` |
| 下载时间（UTC） | 2026-09-28T06:31:05Z |

许可证核对**仅依据 HF 元数据**；未取得仓库内的 LICENSE 原文（GitHub 在本机不可达，见 2.4）。**此项在 WP2 仍需以官方 LICENSE 文件复核**，不得当成已完全核实。

### 2.2 数据结构（1140 题）

字段：`task_id`、`complete_prompt`、`instruct_prompt`、`canonical_solution`、`code_prompt`、`test`、`entry_point`、`doc_struct`、`libs`。

| 观察 | 数值 |
| --- | --- |
| 题数 | 1140（前缀全部为 `BigCodeBench/`） |
| 带测试的题 | **1140/1140（100%）**，形式为 `unittest` 测试类 |
| 任务单元 | **单函数**，入口固定为 `task_func`（`entry_point` 字段） |
| prompt 长度（字符） | 中位 1030 / 均值 1112 / 最大 3590 |
| 参考解长度 | 中位 414 / 均值 466 / 最大 1811 |
| 测试长度 | 中位 2116 / 均值 2361 / 最大 14791 |
| 依赖库种类 | 139 种 |
| **只依赖标准库的题** | **324/1140（28.4%）** |

重依赖示例（需注意本机安装成本）：`tensorflow`、`keras`、`cv2`、`django`、`flask`、`gensim`、`librosa`、`geopandas`、`shapely`、`wordcloud`、`nltk`、`sympy`、`statsmodels`。

### 2.3 参考实现测试结果

抽样规则（在看结果之前冻结）：抽样池 = 只依赖标准库的 324 题；`random.seed(20260928)` 从池中等量抽样 5 题；每题连续跑 3 次；判定 = 退出码 0。

抽中：`BigCodeBench/24`、`/256`、`/464`、`/670`、`/999`。

| 版本 | 环境 | 结果 |
| --- | --- | --- |
| v1 | 只有 pyarrow | **3/5 通过**；`/256`、`/464` 报 `ModuleNotFoundError: No module named 'pytz'`，且 3 次都稳定失败 |
| v2 | 追加 `pytz` | **5/5 通过，3 次全部一致，全部稳定** |

单题 3 次耗时：0.60--1.12 秒（无网络依赖、无随机性漂移）。环境实测明细与每次运行的输出尾部保存在两个 manifest JSON 中。

### 2.4 环境与网络（本次实测，2026-09-28）

| 项目 | 结果 |
| --- | --- |
| 工作目录 | `D:\yaorz\research\codeprm-reproduction\.venvs\bigcodebench_fast0`（**D 盘**） |
| Python | 3.13.14（venv 内），pyarrow 25.0.1，pytz 2026.4，pip 26.2.1 |
| PIP_CACHE_DIR | `D:\yaorz\research\.cache\pip`（**D 盘**） |
| HF_HOME | `D:\yaorz\research\.cache\hf`（**D 盘**） |
| `pypi.org` | **可达**（直连 0.36 s；沙箱代理也可达） |
| `huggingface.co` | **不可达**（直连超时；经沙箱代理返回 502） |
| `hf-mirror.com` | **可达**（直连 0.42 s）——本次下载即通过它完成 |
| `github.com` / `raw.githubusercontent.com` | **不可达**（直连与代理均超时） |
| Docker | 未使用（守护进程状态未复核） |
| 新增下载总量 | 数据 2.25 MiB + pip 包（pyarrow/pytz/pip 等，含缓存）——量级远小于 2 GiB |

---

## 三、观察与推断分离

**观察到的事实**

1. 数据可下载、可加载，许可证元数据为 apache-2.0；
2. 1140 题全部自带 unittest 测试，参考解可稳定复现通过（5/5，3 次一致）；
3. 每题运行时间在 1 秒量级；
4. `libs` 字段**少报依赖**：`/256`、`/464` 实际 import `pytz`，但 `libs` 只列了标准库名；
5. 任务入口统一是单函数 `task_func`，题内没有多函数接口或模块边界；
6. 只有 28.4% 的题不依赖第三方库，其余题的依赖跨度很大（含 tensorflow、django、cv2 等重型库）。

**由此作出的推断（不是事实）**

1. 【推断】BigCodeBench 作为**本机可稳定判分**的评测材料是可行的，至少对标准库子集成立；
2. 【推断】按五项可拆分判据第 1--3 条（多个自然阶段 / 阶段间接口清楚 / 子功能可独立验证），BigCodeBench **结构上不适合回答本项目的拆分问题**——它测的是"单个函数写对没有"，不是"多阶段任务拆分后组合得好不好"。**注意：这是基于任务字段结构的整体判断，不是逐题标注结果**；逐题打标属 WP2/WP3，且不排除少数题内部含多步流程；
3. 【推断】若坚持用 BigCodeBench，本路线大概率只能得到"方法主效应"的描述，无法检验"任务结构 × 方法"的交互——这与复审第四节预判一致；
4. 【推断】`libs` 字段不可单独作为依赖清单，环境预检必须实际试跑才能暴露缺失依赖（本次已实证）。

---

## 四、FAST-0 门槛对照

| 门槛 | 要求 | 实测 | 判定 |
| --- | --- | --- | --- |
| 许可与来源可核 | 有官方来源 | HF 元数据 + arxiv 编号；LICENSE 原文未取得 | **条件通过** |
| 下载可行 | ≤2 GiB | 2.25 MiB | 通过 |
| 环境可装 | 隔离环境、D 盘 | venv + 缓存均在 D 盘 | 通过 |
| 参考测试可跑 | 5--10 题 | 5 题，装 pytz 后 5/5 通过 | 通过 |
| 结果稳定 | 重复一致 | 3 次全一致 | 通过 |
| 不拉 Docker 镜像 | 禁止 | 未使用 | 通过 |
| 不运行生成模型 | 禁止 | LLM 调用 0 次 | 通过 |

---

## 五、失败与限制（如实记录，不因结论积极而省略）

1. **v1 失败已保留**：装 pytz 前 2 题稳定失败，manifest v1 未删除，未用其他题补齐。
2. **抽样带筛选偏差**：5 题是从"仅标准库"的 324 题里抽的。**全体 1140 题的参考测试可运行率未测**，不能把 5/5 当成"BigCodeBench 全体可跑"。
3. **官方评测链路未验证**：没有安装官方 `bigcodebench` 包，没有验证官方 evaluator 的判分逻辑（含依赖安装、超时、输出上限处理）。本机验证的是"参考解 + 官方测试能跑通"，不等于"官方评测管线在本机可用"。
4. **LICENSE 原文未取得**（github.com 不可达）；apache-2.0 目前只是元数据结论。
5. **重度依赖题（约 71.6%）未试**，其本机可行性仍未知；其中 tensorflow / cv2 / geopandas 类依赖在 8GB 机器上可能显著增加体积与时间成本。
6. **网络前提**：HF 直连不可达，后续下载必须走镜像（`hf-mirror.com`）或主机中转；GitHub 不可达会影响自建路线（WP4B）的仓库获取，需另找路径。
7. **未做公开/私有测试切分**：BigCodeBench 每题只有一套测试，切分方案尚未设计与验证。

---

## 六、对后续工作包的直接输入

- **WP1**：BigCodeBench 的"功能级单点任务"定位已由本轮**部分证实**（原初筛把它列为可用候选，本轮证实其可运行，但削弱其适配拆分问题的能力）；需要在 WP1 一并核实是否有更贴合"多阶段 + 可自动测试"的候选。
- **WP2**：BigCodeBench 的静态审计可复用本报告字段表；必须补 LICENSE 原文、官方 evaluator 行为、公开/私有切分可行性与污染风险（模型训练时间边界）。
- **WP3**：环境预检已有可用模板（D 盘 venv + 环境变量）；**不得**只依据 `libs` 字段判断依赖。
- **G1**：有了一个明确的"工程可用但研究适配性弱"样本，正是 G1 需要正面回答的那类矛盾。

---

## 七、下一个工作包

**WP1：系统检索 AI / SE 顶会公开数据集 + 既有答案核查**（`01_*` 系列四个产物）。
