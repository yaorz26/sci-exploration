# 项目整改记录（2026-10-11）

分支：`restructure-20261011`
本文件用途：**旧路径 → 新路径的唯一对照表**。任何"某文件现在在哪"的问题，先查这里。

---

## 一、这次改了什么（两件事）

### 1. 项目目录改名（git 层面）

| 旧 | 新 |
|---|---|
| `codeprm-reproduction/` | `decomposition-bench/` |

理由：`codeprm-reproduction` 这个名字早已名不副实——里面装的是"面向项目功能级代码生成的任务分解评测"这条线（D1），不是 CodePRM 复现。

**git 识别为 8750 个 rename（R100，内容 100% 未变）**，因此仓库内所有 SHA-256 校验值（`candidate_freeze_v2.json` 的 19 份材料哈希、`ledger.jsonl` 的记录等）**全部继续成立**。改名不改文件内容，这是它比"新建项目再搬"更安全的地方。

### 2. 运行时资产移出代码目录

代码目录里 33GB 有 31GB 是模型权重、虚拟环境和本机缓存——**它们本来就不进 git**，但堆在项目里把目录撑得没法看。

| 原位置 | 新位置 | 体积 | 文件数 |
|---|---|---|---|
| `codeprm-reproduction/models/` | `runtime/models/qwen/` | 24,936.6 MB | 53 |
| `codeprm-reproduction/.venv_funprm/` | `runtime/venvs/.venv_funprm/` | 5,274.0 MB | 37,410 |
| `codeprm-reproduction/.venvs/` | `runtime/venvs/.venvs/` | 529.7 MB | 16,498 |
| `codeprm-reproduction/.venv_apps/` | `runtime/venvs/.venv_apps/` | 251.7 MB | 8,961 |
| `.cache/`（工作区根，pip/nltk 缓存） | `runtime/cache/.cache/` | 244.3 MB | 314 |

合计 **约 31.2 GB**。搬迁前逐项验证：这 5 个目录的已跟踪文件数均为 **0**，因此搬迁对 git 历史零影响。

## 二、路径引用怎么处理的

**先说结论：没有用软链（junction）。** 中途曾建过 junction 保留旧门牌，用户明确要求彻底整理后**已全部拆除**，改用直接改名 + 改引用。

引用分三类，处理方式不同：

| 类别 | 例子 | 规模 | 处理 |
|---|---|---|---|
| **相对深度引用** | `ROOT = Path(__file__).resolve().parents[1]` | 151 处 | ✅ **无需改动**。`parents[N]` 的 N 只由目录**深度**决定（深度 1 用 `parents[1]`，深度 2 用 `parents[2]`），与目录名无关；改名不改深度 |
| **写死目录名的引用** | `D:\yaorz\research\codeprm-reproduction\...`、`ROOT / "codeprm-reproduction/..."` | 219 个文件、961 处 | ✅ **已逐处替换**为 `decomposition-bench`（用 Python 逐行替换，见第五节事故记录） |
| **冻结证据与历史存档内的路径字样** | `decomposition-bench/experiments/**`、`.research-state/**`（ledger、snapshots、archive） | 未统计 | ❌ **故意不改**。它们是"当时的记录"；改了等于改写历史，且可能破坏冻结哈希 |

替换范围与排除规则（脚本逻辑，可复查）：

```
排除目录：decomposition-bench/experiments/、decomposition-bench/.research-state/、runtime/
排除路径片段：/ORIGINALS/、/state_before_、/interrupt_、/snapshots/、/archive/
处理扩展名：.py .md .json .jsonl .txt .sh .ps1 .yaml .yml .cfg .ini .toml 及 .gitignore
```

替换后复查：**仍有旧名的活文件 = 0**。

### 新目录名与旧路径对照

| 文档里可能看到的旧写法 | 现在实际位置 |
|---|---|
| `codeprm-reproduction/scripts/...` | `decomposition-bench/scripts/...` |
| `codeprm-reproduction/data/...` | `decomposition-bench/data/...` |
| `codeprm-reproduction/experiments/...` | `decomposition-bench/experiments/...` |
| `codeprm-reproduction/.research-state/...` | `decomposition-bench/.research-state/...` |
| `codeprm-reproduction/models/Qwen2.5-Coder-*` | `runtime/models/qwen/Qwen2.5-Coder-*` |
| `codeprm-reproduction/.venvs/bigcodebench_fast0` | `runtime/venvs/.venvs/bigcodebench_fast0` |
| `codeprm-reproduction/.venv_funprm` | `runtime/venvs/.venv_funprm` |
| `codeprm-reproduction/.venv_apps` | `runtime/venvs/.venv_apps` |
| `D:\yaorz\research\.cache\{pip,uv,hf,nltk_data}` | `runtime/cache/.cache/{pip,uv,hf,nltk_data}` |
| `D:/yaorz/tools/ollamaModels/...`、`D:/yaorz/tools/ollama/lib/ollama` | **未变动**（在工作区之外） |

## 三、虚拟环境没有搬，是重新定位

`.venv_funprm/pyvenv.cfg` 里写死了绝对路径：

```
executable = D:\yaorz\research\codeprm-reproduction\.venv_apps\Scripts\python.exe
```

所以 Python 虚拟环境**不能靠改名复用**。当前状态：`runtime/venvs/` 下三个环境都在，但**其 pyvenv.cfg 仍指向旧路径**，直接调用可能失败。

**要恢复某个环境时的正确做法**（不依赖旧路径）：

```powershell
cd D:\yaorz\research\runtime\venvs
py -3.12 -m venv .venvs\classeval_new          # 或复用现有环境并修复 pyvenv.cfg
.\.venvs\classeval_new\Scripts\python.exe -m pip install -r D:\yaorz\research\decomposition-bench\requirements.txt
```

【未验证】本次**没有**实测旧环境在改名后能否正常启动——没有做这项测试，不写"应该没问题"。

## 四、回归验证结果（改名后实测）

| 检查 | 命令 | 结果 |
|---|---|---|
| 单元测试 | `cd decomposition-bench && python -m pytest tests -q -p no:cacheprovider` | **92 passed**，exit=0 |
| 治理自检 | `python scripts/check_governance_integrity.py` | **全部通过**，exit=0，账本事件数 452 |
| 导入链 | `python decomposition-bench/scripts/d1/run_repository_patch_probe.py` | 成功执行到 `main()`（报 `FileExistsError` 因输出目录已存在，属预期） |
| 工作区完整性 | `git ls-files --deleted` | **0**（无文件因改名丢失） |

注意：从工作区根跑 `pytest decomposition-bench/tests` **会报 13 个收集错误**，原因是 `.pytest_cache` 里残留旧路径。这不是改名造成的：进项目目录内跑就 92/92 通过，或加 `-p no:cacheprovider` 忽略缓存。

## 五、必须记录的两次事故（本轮真实发生）

诚实交代，避免以后误判。

**事故 1：`git mv` 改名被拒 → 改用 robocopy。**
`git mv codeprm-reproduction decomposition-bench` 报 `Permission denied`（codex 相关进程占用该目录），`Move-Item` 也失败并在目标目录留下**半搬状态**（`data/`、`.gitignore` 已过去，`scripts/` 等仍在旧目录）。改用 `robocopy /E /MOVE /R:0 /W:0` 一次搬完（退出码 3 = 正常），随后删除空目录。

**事故 2：批量替换脚本内存溢出，污染了 140 个文件。**
用 PowerShell 整文件读入 + `-replace` 替换时触发 `OutOfMemoryException`，并把错误内容写进了 **140 个文件**（含 `configs/*.json`、`data/processed/*.json`、`docs/**/*.md`、`scripts/**/*.py` 等）。

- **发现方式**：`git status` 出现大量异常 `D`，抽查文件首行发现内容被替换成别的文件内容。
- **恢复方式**：`git checkout -- .` 从 **git 索引**还原（索引里保存的是替换前的正确内容，因为替换结果从未 `git add`）。还原后复查污染特征串：**0**。
- **教训**：批量文本替换必须逐行处理并做编码保护，不能整文件读入内存；已改用 Python 逐行版本，成功替换 219 个文件、961 处，无污染。

事故 2 的副作用：`git checkout -- .` 把工作区还原成索引状态（即改名**前**的路径），所以改名必须重新 `git add -A` 一次——本次记录的这一版就是重新暂存后的结果。

## 六、`.gitignore` 的变化

| 变化 | 原因 |
|---|---|
| 新增 `runtime/` | 31.2GB 运行时资产现在集中在此，必须整目录排除 |
| 保留 `decomposition-bench/models/` 等作为安全网 | 万一这些目录又出现在项目里 |
| 删除 `*.log` 规则 | `decomposition-bench/data/processed/` 下有多份 `*_progress.log` **已被 git 跟踪**，忽略规则会让它们从 `git status` 里消失 |
| 删除 `tmp/` 无锚定规则 | 会连带忽略 `decomposition-bench/tmp/` 下的文件 |
| 新增说明：不要写裸的 `Scripts/`、`lib/`、`include/` | Windows 上 git 路径匹配**大小写不敏感**，`/Scripts/` 会吞掉 `scripts/check_governance_integrity.py` 和 `decomposition-bench/scripts/`（本轮已踩过） |

## 七、遗留项（未做，需要时再决定）

1. **255 个"已跟踪但被忽略"的文件**：242 个是上游第三方仓库（`data/raw/.../repositories/` 下的 boltons/cachetools/confuse/more_itertools），12 个是超过 50MB 的评测转储，1 个是 `archive/decomprl-source.tar`。它们仍在 git 跟踪中（忽略规则对已跟踪文件无效），**本次未做 `git rm --cached`**。若要真正移出，需单独确认——注意其中有文件曾触发 GitHub 的"建议使用 LFS"警告。
2. **虚拟环境未实测**（见第三节）。
3. **WSL 路径未改**：`decomposition-bench/scripts/wp3_classeval/wsl_py310_check.py` 与 `wsl_py310_run.sh` 指向 `/mnt/d/yaorz/research/...` 下的旧路径。替换只在 Windows 路径语义下做了字面替换，**WSL 内是否可达未验证**。
4. **两个 57MB 文件仍在 git 历史中**（`p5b_hard20_m1_plan_..._pool_oracle.json`、`..._evaluations.jsonl`）。要瘦身需 `git filter-repo` 重写历史，会让旧提交哈希全部改变。

## 八、验证命令（随时可复查本记录）

```powershell
cd D:\yaorz\research
Test-Path decomposition-bench                          # True
Test-Path codeprm-reproduction                          # False
"runtime 体积 MB: " + ("{0:N1}" -f ((Get-ChildItem runtime -Recurse -File -Force | Measure-Object Length -Sum).Sum/1MB))
git ls-files --deleted | Measure-Object -Line           # 0
git log --oneline -3
cd decomposition-bench; python -m pytest tests -q -p no:cacheprovider   # 92 passed
```
