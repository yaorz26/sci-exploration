# 项目整改记录（2026-10-11）

分支：`restructure-20261011`
本文件用途：**旧路径 → 现在位置 的唯一对照表**。任何"某文件现在在哪"的问题，先查这里。

---

## 一、最终结构

整改后的工作区（本节是权威描述，下面各节的路径都以这里为准）：

```
D:\yaorz\research\
├── projects\
│   └── decomposition-bench\        项目代码与证据          10,494 文件 / 1,591.9 MB  ← 入库
├── runtime\                        本机运行时资产，不入库  31,867.1 MB
│   ├── models\qwen\                模型权重                 24,936.6 MB / 53 文件
│   ├── venvs\                      虚拟环境                  6,070.8 MB / 64,201 文件
│   │   ├── .venv_funprm\           训练环境（torch/peft/bnb）
│   │   ├── .venv_apps\             数据环境（datasets/requests）
│   │   └── .venvs\                 bigcodebench_fast0（隔离）、wsl_py310（WSL 用）
│   ├── cache\                      pip / uv / hf / nltk 缓存    244.3 MB
│   └── artifacts\                  训练产物 + 归档 + tmp        615.4 MB
│       ├── outputs\                原 projects/decomposition-bench/outputs（LoRA 等）
│       ├── tmp\                    原工作区 tmp/ 与项目 tmp/
│       ├── pdfs\ pdftext\ pdf-summary\  原 archive/
│       └── decomprl-source.tar     原 archive/
├── docs\                           研究文档（295 文件）——已并入项目原 docs\plans、docs\week3
├── articles\  memory\  scripts\
├── governance\                     PROJECT_ENTRY.md、README.md、本文件
├── AGENTS.md                       治理主文件（保留在根目录，见第七节）
├── .codebuddy\  .agents\           工具约定目录（保留在根目录，见第七节）
├── .gitignore
└── 当前情况总结.md
```

## 二、这次做了三件事

### 1. 项目改名（git 层面）

| 旧 | 新 |
|---|---|
| `codeprm-reproduction/` | `decomposition-bench/` |

理由：`codeprm-reproduction` 早已名不副实——里面装的是"面向项目功能级代码生成的任务分解评测"这条线（D1），不是 CodePRM 复现。

**git 识别为 rename（R100，内容 100% 未变）**，因此仓库内所有 SHA-256 校验值（`candidate_freeze_v2.json` 的 19 份材料哈希、`ledger.jsonl` 的记录等）**全部继续成立**。这正是"改名"优于"新建项目再搬"的地方：新建项目会切断追加账本与历史提交，改名不会。

### 2. 项目移入 `projects/`

| 旧 | 新 |
|---|---|
| `decomposition-bench/`（工作区根下） | `projects/decomposition-bench/` |

### 3. 运行时资产移出代码目录

代码目录里 33GB 有 31GB 是模型权重、虚拟环境和本机缓存——**它们本来就不进 git**，却堆在项目里把目录撑得没法看。

| 原位置 | 现在位置 | 体积 | 文件数 |
|---|---|---|---|
| `codeprm-reproduction/models/` | `runtime/models/qwen/` | 24,936.6 MB | 53 |
| `codeprm-reproduction/.venv_funprm/` | `runtime/venvs/.venv_funprm/` | 5,274.0 MB | 37,410 |
| `codeprm-reproduction/.venvs/` | `runtime/venvs/.venvs/` | 529.7 MB | 16,498 |
| `codeprm-reproduction/.venv_apps/` | `runtime/venvs/.venv_apps/` | 251.7 MB | 8,961 |
| `.cache/`（工作区根） | `runtime/cache/`（原 `.cache/.cache/` 已扁平化） | 244.3 MB | 314 |
| `archive/`（工作区根） | `runtime/artifacts/` | 8.4 MB | 33 |
| `lib/`（工作区根，本机依赖） | `runtime/venvs/lib/` | 15.4 MB | 1,331 |
| `decomposition-bench/outputs/` | `runtime/artifacts/outputs/` | 606.8 MB | 280 |
| `tmp/`（两处） | `runtime/artifacts/tmp/` | 0.2 MB | 56 |
| `decomposition-bench/docs/` | 并入工作区 `docs/` | 0.03 MB | 4 |
| `experiments/`（工作区根残留） | `projects/decomposition-bench/experiments/` | 0.03 MB | 3 |

搬迁前逐项验证：这些目录的已跟踪文件数均为 **0** 或极少（`outputs`、`docs`、根 `experiments`、两处 `tmp` 有跟踪文件，用 `git mv` / robocopy 保留跟踪状态），因此**对 git 历史零破坏**。

## 三、路径引用怎么处理的

**没有用软链（junction）。** 中途曾建 junction 保留旧门牌，用户要求彻底整理后**已全部拆除**。

### 关键：`parents[N]` 的换算方向（本轮踩过坑，务必看）

脚本用 `Path(__file__).resolve().parents[N]` 推导位置。项目从**工作区根**（1 层）移到 **`projects/decomposition-bench/`**（2 层）时，**N 不变**：

| 文件位置 | 推"项目根" | 推"工作区根" |
|---|---|---|
| 搬迁前 `decomposition-bench/scripts/run_baseline.py` | `parents[1]` | `parents[2]` |
| 搬迁后 `projects/decomposition-bench/scripts/run_baseline.py` | **`parents[1]`** | **`parents[2]`** |

原因：`parents[1]` 从 `scripts/` 退一层恰好是项目根（`projects/decomposition-bench`），搬迁没有改变"脚本与项目根之间"的相对层数。

**本轮曾误判为"多一层就要 +1"**，把 151 处改成 `parents[2]`/`parents[3]`，结果 ROOT 解析到 `projects/`、5 个测试收集失败（报 `FileNotFoundError: ...projects\scripts\build_stratified_slice.py`，少了项目那一层）。已改为 `-1` 并实测三处关键路径全部正确。**若将来再调整项目层级，先按"文件到目标的相对层数"重算，不要按"绝对层数"加。**

### 三类引用的处理

| 类别 | 规模 | 处理 |
|---|---|---|
| `parents[N]` 相对引用 | 151 处 / 143 文件 | ✅ 已按上表修正，实测正确 |
| 写死目录名的引用 | 219 文件 / 961 处（第一步改名时） | ✅ 已替换为 `decomposition-bench` |
| 项目根绝对路径 | 15 文件 | ✅ 已替换为 `D:\yaorz\research\projects\decomposition-bench` |
| **冻结证据与历史存档内的路径字样** | `experiments/**`、`.research-state/**`、少数 `data/processed/*.json` | ❌ **故意不改**——它们是"当时的记录"，改了等于改写历史 |

替换后复查：**仍有旧名的活文件 = 1**，即本文件自身的历史对照表（本节就是说明）。另 2 处是 `p5c_medium_k8_repairv1_*` 两份冻结摘要里的历史绝对路径，属故意保留。

### 旧 → 现在 路径对照（查证用）

| 文档里可能看到的旧写法 | 现在实际位置 |
|---|---|
| `codeprm-reproduction/scripts/...` | `projects/decomposition-bench/scripts/...` |
| `codeprm-reproduction/data/...` | `projects/decomposition-bench/data/...` |
| `codeprm-reproduction/experiments/...` | `projects/decomposition-bench/experiments/...` |
| `codeprm-reproduction/.research-state/...` | `projects/decomposition-bench/.research-state/...` |
| `codeprm-reproduction/.gitignore` | `projects/decomposition-bench/.gitignore` |
| `decomposition-bench/scripts/...`（过渡期的写法） | `projects/decomposition-bench/scripts/...` |
| `codeprm-reproduction/models/Qwen2.5-Coder-*` | `runtime/models/qwen/Qwen2.5-Coder-*` |
| `codeprm-reproduction/.venvs/bigcodebench_fast0` | `runtime/venvs/.venvs/bigcodebench_fast0` |
| `codeprm-reproduction/.venv_funprm` | `runtime/venvs/.venv_funprm` |
| `codeprm-reproduction/.venv_apps` | `runtime/venvs/.venv_apps` |
| `D:\yaorz\research\.cache\{pip,uv,hf,nltk_data}` | `runtime/cache/{pip,uv,hf,nltk_data}` |
| `D:\yaorz\research\archive\` | `runtime/artifacts/` |
| `decomposition-bench/outputs/` | `runtime/artifacts/outputs/` |
| `PROJECT_ENTRY.md` / `README.md`（根目录） | `governance/PROJECT_ENTRY.md` / `governance/README.md` |
| `D:/yaorz/tools/ollamaModels/...`、`D:/yaorz/tools/ollama/lib/ollama` | **未变动**（在工作区之外） |

## 四、虚拟环境：实测可用（不是推断）

**结论：搬迁没有破坏任何虚拟环境。** 三个 Windows 环境均实测启动，`prefix` 正确指向新位置，**没有一个包来自环境外**：

| 环境 | Python | 实测可用依赖 |
|---|---|---|
| `runtime/venvs/.venv_funprm` | 3.12.3 | torch 2.6.0+cu124、transformers 4.57.6、peft 0.20.0、bitsandbytes 0.50.2、datasets 3.6.0、numpy 2.4.6、pyarrow 25.0.1、yaml 6.0.3（9/11） |
| `runtime/venvs/.venv_apps` | 3.12.3 | datasets 2.21.0、requests 2.34.2、numpy 2.5.2、pyarrow 25.0.1、yaml 6.0.3（5/11） |
| `runtime/venvs/.venvs/bigcodebench_fast0` | 3.13.14 | numpy 2.5.3、bs4 4.15.0、pyarrow 25.0.1（3/11） |

未通过的那些是**本来就没装在该环境里**（`.venv_apps` 从未装 torch；`fast0` 是隔离环境；三个环境都没装 pytest，项目测试用系统 Python），不是搬迁造成的。

**WSL 环境也实测通过**：`/mnt/d/yaorz/research/runtime/venvs/.venvs/wsl_py310/bin/python` → Python 3.10.12 可执行。

**端到端实测**：用 `.venv_apps` 导入项目代码并加载真实数据 → `src.data_loader 导入成功`、`加载题目数: 20`。

### 已知残留（不影响运行，保留为历史记录）

`pyvenv.cfg` 里的元数据**仍是旧路径**，例如：

```
executable = D:\yaorz\research\codeprm-reproduction\.venv_apps\Scripts\python.exe
command    = ... -m venv D:\yaorz\research\codeprm-reproduction\.venv_funprm
```

- **不影响运行**（上表为实测结果），因为解释器靠 `home` 找基础 Python，而 `home` 指向的是环境外的基础安装，未变动；
- 唯一实际影响：`Scripts\activate` 里的 `VIRTUAL_ENV` 仍是旧路径。**建议直接用 `python.exe` 全路径调用**（项目脚本本来就这么调），或使用 `runtime\venvs\<环境>\Scripts\activate` 的完整路径激活；
- 另一个既有小问题（非本次造成）：`bigcodebench_fast0` 的 `home` 写 3.13.12、`version` 写 3.13.14、实测 3.13.14。

## 五、回归验证结果（全部实测）

| 检查 | 命令 | 结果 |
|---|---|---|
| 单元测试 | `cd projects/decomposition-bench && python -m pytest tests -q -p no:cacheprovider` | **92 passed**，exit=0 |
| 治理自检 | `python scripts/check_governance_integrity.py` | **全部通过**，exit=0，账本事件数 452 |
| 路径解析 | 模拟执行三个脚本取 `ROOT` / `EXPERIMENT_ROOT` / `SCRIPT` | 三处均指向正确文件 |
| 工作区完整性 | `git ls-files --deleted` | **0** |
| 大文件门 | `git ls-tree -r -l HEAD` 中 >100MB 的文件 | **无** |
| 虚拟环境 | 见第四节 | 三环境 + WSL 均可用 |

注意：从工作区根跑 `pytest projects/decomposition-bench/tests` 可能因 `.pytest_cache` 残留旧路径而报收集错误。进项目目录内跑，或加 `-p no:cacheprovider`。

## 六、`.gitignore` 的变化

| 变化 | 原因 |
|---|---|
| 新增 `runtime/` | 31.8GB 运行时资产集中在此，必须整目录排除 |
| 保留 `projects/decomposition-bench/models/` 等作为安全网 | 万一这些目录又出现在项目里 |
| 删除 `*.log` 规则 | `data/processed/` 下有多份 `*_progress.log` **已被 git 跟踪**，忽略规则会让它们从 `git status` 里消失 |
| 删除无锚定的 `tmp/` 规则 | 会连带忽略项目 `tmp/` 下的文件 |
| 新增说明：不要写裸的 `Scripts/`、`lib/`、`include/` | Windows 上 git 路径匹配**大小写不敏感**，`/Scripts/` 会吞掉 `scripts/check_governance_integrity.py`（本轮已踩过） |
| 逐条列出 >50MB 大文件 | GitHub 单文件硬上限 100MB。**改名会让这些规则失效**——本轮因此两次把 993MB 文件放进提交，均被 GitHub 拒绝后修正 |

## 七、遗留项（未做，需要时再决定）

1. **`AGENTS.md` 与 `.codebuddy/` 保留在工作区根目录**（本记录所在目录是 `governance/`，只放人类文档）。原因：治理自检脚本有 11 处写死 `ROOT/AGENTS.md`、`ROOT/.codebuddy/...`；且 `.codebuddy/` 是 AI 工具的约定读取位置，移走可能让工具找不到配置。要移入 `governance/`，需同步改脚本约 1（AGENTS）至 11（含 .codebuddy）处路径。
2. **253 个"已跟踪但被忽略"的文件**：242 个是上游第三方仓库（`data/raw/d1_project_v1_20261008/repositories/` 下的 boltons/cachetools/confuse/more_itertools），10 个是超过 50MB 的评测转储，1 个是归档 tar。忽略规则对已跟踪文件无效，**未做 `git rm --cached`**。
3. **两个 57MB 文件仍在 git 历史中**（`p5b_hard20_m1_plan_..._pool_oracle.json`、`..._evaluations.jsonl`）。已在远程，要瘦身需 `git filter-repo` 重写历史，会让旧提交哈希全部改变。
4. **WSL 专用脚本未改**：`projects/decomposition-bench/scripts/wp3_classeval/wsl_py310_check.py` 与 `wsl_py310_run.sh` 里的路径仍是旧写法。**环境本身实测可用**（第四节），但脚本里的路径常量需按需更新。
5. **分支未合并**：`restructure-20261011` 尚未合回 `main`。

## 八、两次事故（如实记录）

**事故 1：改名时 `git mv` 被拒。**
`git mv codeprm-reproduction decomposition-bench` 报 `Permission denied`（codex 相关进程占用该目录），`Move-Item` 也失败并在目标留下**半搬状态**（`data/`、`.gitignore` 已过去，`scripts/` 等仍在旧目录）。改用 `robocopy /E /MOVE /R:0 /W:0` 一次搬完，随后删空目录。此后 `projects/` 的搬迁同样用 robocopy。

**事故 2：批量替换脚本内存溢出，污染 140 个文件。**
用 PowerShell 整文件读入 + `-replace` 时触发 `OutOfMemoryException`，把错误内容写进了 **140 个文件**（含 `configs/*.json`、`data/processed/*.json`、`docs/**/*.md`、`scripts/**/*.py`）。

- **发现**：`git status` 出现大量异常 `D`，抽查文件首行发现内容变成了别的文件的内容。
- **恢复**：`git checkout -- .` 从 **git 索引**还原（索引里是替换前的正确内容，因为替换结果从未 `git add`）。复查污染特征串：**0**。
- **重做**：改用 Python 逐行替换，成功处理 219 个文件、961 处，无污染。
- **附带损失**：还原时有 3 个文件未回来，用 `git checkout HEAD --` 取回，**哈希与 HEAD 逐字节一致**（中途一次用 `>` 重定向写过，那是 UTF-16 带 BOM 的错误写法，已废弃重做）。
- **教训**：批量文本替换必须逐行处理 + 编码保护；改完全文类操作后，用 `git ls-files --deleted` 与哈希对比做完整性核对。

## 九、验证命令（随时可复查本记录）

```powershell
cd D:\yaorz\research
Test-Path projects\decomposition-bench            # True
Test-Path codeprm-reproduction                    # False
Test-Path decomposition-bench                     # False
"{0:N1} MB" -f ((Get-ChildItem runtime -Recurse -File -Force | Measure-Object Length -Sum).Sum/1MB)   # 约 31867
git ls-files --deleted | Measure-Object -Line     # 0
git log --oneline -4
cd projects\decomposition-bench; python -m pytest tests -q -p no:cacheprovider   # 92 passed
cd ..\..; python scripts/check_governance_integrity.py                           # 全部通过
# 虚拟环境自检（三环境之一）
.\runtime\venvs\.venv_funprm\Scripts\python.exe -c "import torch, transformers; print(torch.__version__, transformers.__version__)"
```
