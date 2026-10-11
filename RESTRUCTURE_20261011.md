# 项目文件整改记录（2026-10-11）

分支：`restructure-20261011`　执行范围：方案 1（搬重物）+ 方案 3（更新引用）
本文件用途：**旧路径 → 新路径的唯一对照表**。任何"某文件现在在哪"的问题，先查这里。

---

## 一、这次做了什么

理由很简单：仓库里 33GB 的内容有 31GB 是模型权重、虚拟环境和本机缓存，**它们本来就不进 git**，但一直堆在代码目录里，把 `codeprm-reproduction/` 撑得没法看。这次把它们搬到独立分区，代码目录只留代码与证据。

| 原位置 | 新位置 | 体积 | 文件数 |
|---|---|---|---|
| `codeprm-reproduction/models/` | `runtime/models/qwen/` | 24,936.6 MB | 53 |
| `codeprm-reproduction/.venv_funprm/` | `runtime/venvs/.venv_funprm/` | 5,274.0 MB | 37,410 |
| `codeprm-reproduction/.venvs/` | `runtime/venvs/.venvs/` | 529.7 MB | 16,498 |
| `codeprm-reproduction/.venv_apps/` | `runtime/venvs/.venv_apps/` | 251.7 MB | 8,961 |
| `.cache/`（工作区根，pip/nltk 缓存） | `runtime/cache/.cache/` | 244.3 MB | 314 |

合计搬走 **约 31.2 GB**。全部为 `git` 未跟踪内容（搬迁前逐项验证：5 个目录的已跟踪文件数均为 **0**），因此**本次搬迁对 git 历史零影响**。

## 二、为什么旧路径还能用：junction 软链

关键取舍：代码里有 **169 处** `Path(__file__).resolve().parents[N]` 和 **12 处**写死的 `D:\yaorz\research\codeprm-reproduction\...`。如果真搬走，这些引用要全部重算重测，风险远大于收益。

所以采取"**搬家 + 留旧门牌**"：在旧位置建 Windows junction（目录软链，无需管理员权限），指向新位置。

```powershell
# 建链命令（已执行；如需在新机器重建，用绝对路径，不能用相对路径）
cmd /c mklink /J "D:\yaorz\research\codeprm-reproduction\models"       "D:\yaorz\research\runtime\models\qwen"
cmd /c mklink /J "D:\yaorz\research\codeprm-reproduction\.venvs"       "D:\yaorz\research\runtime\venvs\.venvs"
cmd /c mklink /J "D:\yaorz\research\codeprm-reproduction\.venv_apps"   "D:\yaorz\research\runtime\venvs\.venv_apps"
cmd /c mklink /J "D:\yaorz\research\codeprm-reproduction\.venv_funprm" "D:\yaorz\research\runtime\venvs\.venv_funprm"
cmd /c mklink /J "D:\yaorz\research\.cache"                            "D:\yaorz\research\runtime\cache\.cache"
```

**已验证可达**（`Test-Path` 实测）：

- `codeprm-reproduction/models/Qwen2.5-Coder-7B-Instruct/tokenizer.json` → True
- `codeprm-reproduction/models/Qwen2.5-Coder-3B-Instruct/config.json` → True
- `codeprm-reproduction/.venvs/bigcodebench_fast0/Scripts/python.exe` → True
- `codeprm-reproduction/.venv_funprm/Scripts/python.exe` → True
- `codeprm-reproduction/.venv_apps/Scripts/python.exe` → True
- `.cache/nltk_data` → True

**注意（重要）**：junction 的目标是**绝对路径**。如果整个工作区以后换盘符或换目录（例如从 `D:\yaorz\research` 改到别处），这 5 个软链会全部失效，必须按上表重建。

## 三、旧 → 新 路径映射（供查证与改写）

| 文档/脚本里写的旧路径 | 实际位置（新） | 是否仍可直接使用 |
|---|---|---|
| `codeprm-reproduction/models/...` | `runtime/models/qwen/...` | ✅ 经 junction 可用 |
| `codeprm-reproduction\.venvs\bigcodebench_fast0\...` | `runtime/venvs/.venvs/bigcodebench_fast0/...` | ✅ 经 junction 可用 |
| `codeprm-reproduction\.venv_funprm\...` | `runtime/venvs/.venv_funprm/...` | ✅ 经 junction 可用 |
| `codeprm-reproduction\.venv_apps\...` | `runtime/venvs/.venv_apps/...` | ✅ 经 junction 可用 |
| `D:\yaorz\research\.cache\{pip,uv,hf,nltk_data}` | `runtime/cache/.cache/{pip,uv,hf,nltk_data}` | ✅ 经 junction 可用 |
| `D:/yaorz/tools/ollamaModels/blobs/...`、`D:/yaorz/tools/ollama/lib/ollama` | **未变动**（在工作区之外） | ✅ 原样可用 |
| `/mnt/d/yaorz/research/codeprm-reproduction/.venvs/wsl_py310` | `runtime/venvs/.venvs/wsl_py310`（WSL 路径） | ⚠️ 见下 |

### 唯一未修的一类引用：WSL 路径

2 处 WSL 专用引用指向 `/mnt/d/...` 层面的旧路径，Windows junction 对 WSL **不生效**：

- `codeprm-reproduction/scripts/wp3_classeval/wsl_py310_check.py:12`
- `codeprm-reproduction/scripts/wp3_classeval/wsl_py310_run.sh:5`

（`VENV = "/mnt/d/yaorz/research/codeprm-reproduction/.venvs/wsl_py310"`）
WSL 里把该路径改成 `/mnt/d/yaorz/research/runtime/venvs/.venvs/wsl_py310` 即可。**本次未改**，因为无法在 Windows 侧验证 WSL 内是否可达。

## 四、引用更新的范围与"故意不改"的部分

全仓扫描结果：含 `codeprm-reproduction/...` 或 `.cache`、`.venvs` 字样的文件共 **122** 个，但它们的性质完全不同，处理方式也不同：

| 类别 | 处理 | 原因 |
|---|---|---|
| **运行路径**（脚本找虚拟环境、模型、缓存） | ✅ 已用 junction 保持可用，**零改动** | 改 15 个脚本的路径不如留门牌可靠 |
| **活文档**（`memory/artifact-map.md`、`docs/week3/data-route/*`） | ⚠️ 保留旧写法，以本文件映射表为准 | 它们是**当时的记录**，改了就变成"事后改写历史" |
| **冻结证据**（`experiments/*/summary.json`、`protocol_copy.json`、`pool_oracle.json` 等） | ❌ 故意不改 | 哈希冻结、`candidate_freeze_v2.json` 里 19 份材料哈希依赖原字节；改动即破坏证据 |
| **追加账本**（`codeprm-reproduction/.research-state/ledger.jsonl`） | ❌ 只增不改 | 账本是追加式，历史条目内的路径是当时事实 |
| **运行时日志中的路径**（`wp3/w4a` 的 stdout tail） | ❌ 不改 | 是机器原始输出，改了就不是原始输出 |

结论：**路径"事实"没有变，只是门牌号多了一个入口**。查旧路径能不能用 → 看本文件第三节；查某文件现在物理在哪 → 看第一节。

## 五、回滚方式

本次改动**全部可逆**，且不涉及 git 历史：

```powershell
# 1) 删软链（只删链接，不动 runtime 里的实体）
foreach ($p in @("codeprm-reproduction\models","codeprm-reproduction\.venvs",
                 "codeprm-reproduction\.venv_apps","codeprm-reproduction\.venv_funprm",".cache")) {
  cmd /c rmdir "$p"
}
# 2) 把实体搬回原位（同盘，秒级）
Move-Item runtime\models\qwen            codeprm-reproduction\models
Move-Item runtime\venvs\.venvs           codeprm-reproduction\.venvs
Move-Item runtime\venvs\.venv_apps       codeprm-reproduction\.venv_apps
Move-Item runtime\venvs\.venv_funprm     codeprm-reproduction\.venv_funprm
Move-Item runtime\cache\.cache           .cache
# 3) git 侧：本分支的提交可整体丢弃
git checkout main
git branch -D restructure-20261011
```

**删除链接时务必用 `rmdir`，不要用 `Remove-Item -Recurse`**——后者在旧版 PowerShell 上可能穿透 junction 删除真实内容。

## 六、本轮改动的文件（除搬迁外）

| 文件 | 改动 |
|---|---|
| `.gitignore` | 新增 `runtime/` 与 5 个 junction 路径的忽略规则；补 `.cache/`；此前已修 `Scripts/`、`/Scripts/` 误伤研究脚本的问题 |
| `RESTRUCTURE_20261011.md` | 本文件（新增） |

**未改动**：`AGENTS.md`、`.codebuddy/`、`.research-state/` 下任何文件。因此本轮**不触发**治理自检的强制重跑（如后续改动治理文件，仍需跑 `python scripts/check_governance_integrity.py`）。

## 七、尚未做（方案 2，需单独决策）

`codeprm-reproduction` 这个目录名已经名不副实（现在的内容是 D1 项目，不是 CodePRM 复现）。改名或提升层级会波及：

- **169 处** `parents[N]` 算术（`scripts/` 一层 `parents[1]`、`scripts/d1/` 两层 `parents[2]`）；
- **12 处**写死的 `D:\yaorz\research\codeprm-reproduction`；
- **122 个文件**里的路径字样；
- 以及 `codeprm-reproduction/.gitignore` 内所有相对规则。

在这些引用没有经过一次完整回归（至少：`scripts/d1/` 下任一脚本能跑通、`tests/` 通过）之前，**不建议动**。真要动，正确顺序是：先把 169 处相对路径改成"从环境变量或单一常量推导"，再改目录名。

## 八、验证命令（随时可复查本记录是否仍然成立）

```powershell
cd D:\yaorz\research
# 软链是否还有效
Test-Path codeprm-reproduction\models\Qwen2.5-Coder-7B-Instruct\tokenizer.json
# 链接目标
Get-Item codeprm-reproduction\models | Select-Object Name, LinkType, Target
# git 是否被 31GB 污染（应只有 runtime/ 一条未跟踪）
git status --porcelain
# runtime 体积
"{0:N1} MB" -f ((Get-ChildItem runtime -Recurse -File -Force | Measure-Object Length -Sum).Sum/1MB)
```
