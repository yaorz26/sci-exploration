# 配置文件来源的相对路径（修订版 v2）

修订说明（v2，2026-10-11）：依据独立审查意见补齐四处——① 给出**完整调用序列**与真实目录形态，不再只给结果形态；② 定义"应用配置目录/源文件目录/cwd/relative_to"四个术语分别属于哪个对象；③ 把优先级写成**有序判定表**并在源文件内附最小判定例；③ 说明公开诊断内嵌于评价器。修订前的 v1 已快照保存。

在给定项目包源码中实现源文件目录相对路径功能，保持现有外部 API 和默认行为。Python 3，依赖 PyYAML。通过修改现有项目代码交付功能，不要求特定内部拆法。

## 一、术语定义（每个开关挂在哪个对象上）

| 术语 | 含义 | 挂在哪个对象 |
| --- | --- | --- |
| 源文件目录 | 当前 `ConfigSource`/`YamlSource` 所用配置文件的所在目录（由该来源的 `filename` 决定） | 由来源的 `filename` 决定 |
| 应用配置目录 | `Configuration` 对象的应用配置根目录（由 `Configuration('appname')` 的名字与 `app_dir` 决定） | `Configuration` |
| `base_for_paths` | 开关：相对路径是否以**源文件目录**为基准 | 源级：`ConfigSource` / `YamlSource` 的构造参数 |
| `in_source_dir` | 开关：模板是否明确选择**源文件目录** | 模板级：`Filename(...)` 的构造参数 |
| `in_app_dir` | 开关：模板是否强制回到**应用配置目录** | 模板级：`Filename(...)` 的构造参数 |
| `set_file(..., base_for_paths=...)` | 载入文件的入口，可把源级开关传给该来源 | `Configuration.set_file` |
| `cwd`（模板级） | **模板级**显式基准目录：`Filename(cwd=<绝对路径>)` 的构造参数；给出时作为相对路径的基准 | 模板级：`Filename(...)` 的构造参数 |
| 进程当前工作目录 | 操作系统层面的 cwd；**只在既无源文件、模板也未给 `cwd` 时**作为兜底 | 进程环境（不直接作为模板参数） |
| `relative_to` | 现有行为：模板可指定相对于某个视图键解析；**在判定表中排在源级/模板级开关之后** | 模板级 |

## 二、调用序列（评价按此序列调用，公开例即此形态）

```python
# 真实目录在测试运行时创建，形态如下（<...> 为实际绝对路径）
# <project>/settings/config.yaml   内容: path: assets/a.txt
# <app>/                           应用配置目录（Configuration 的 app_dir）

config = confuse.Configuration('appname', read=False)          # 构造时不自动加入任何来源
config.set_file('<project>/settings/config.yaml')              # 或带 base_for_paths=True
value = config['path'].get(confuse.Filename(cwd=<app>))        # 或 Filename(cwd=<app>, in_source_dir=True)
                                                               # 或 Filename(cwd=<app>, in_app_dir=True)
```

## 三、有序判定表（自上而下第一条命中者生效）

依据：合并版 `confuse/templates.py` 的 `Filename` 类 docstring 原文——
"Relative paths are relative to the template's `cwd` argument **when it is specified**. Otherwise, if the paths come from a file, they will be relative to the configuration directory by default or to the base directory of the config file if either the source has `base_for_paths` set to True or the template has `in_source_dir` set to True. Paths from sources without a file are relative to the current working directory."

对"值为相对路径的模板求值"这一动作，按下列顺序判定基准目录。**本表与第四节判定例必须一致；冲突时以本表为准。**

1. 若路径为**绝对路径** → 原样返回。
2. 否则若模板给了 `cwd` → 以该 `cwd` 为基准。**（`cwd` 指定时无条件优先，压过 `base_for_paths`、`in_source_dir`、`relative_to` 与默认行为；这是上游 docstring 的明文语义）**
3. 否则若模板 `in_app_dir=True` → 以**应用配置目录**为基准（即使该值不来自文件）。
4. 否则若该来源有 `filename` → 以**源文件目录**为基准；此条覆盖两种触发方式：源级 `base_for_paths=True`，或模板 `in_source_dir=True`。
5. 否则若模板给了 `relative_to` → 保持现有 `relative_to` 行为。
6. 否则若该来源有 `filename` → 以**应用配置目录**为基准（默认行为）。
7. 否则 → 以**当前工作目录**为基准。

两条补充：源级 `base_for_paths=True` 但该来源**没有** `filename` 时该开关无效（落回第 6/7 条）；模板 `in_source_dir=True` 但该来源没有 `filename` 时同样无效。

## 四、最小判定例（已按上游合并版实测校正）

假定应用目录 `<app>`、配置文件 `<project>/settings/config.yaml`、文件内值为 `assets/a.txt`。
下列期望值全部由上游合并版真实运行得到（证据见 `experiments/d1_G3_fidelity_probe_v1_20261011/fidelity_PR126.json`）。

| 调用 | 期望输出 | 依据判定表 |
| --- | --- | --- |
| `set_file(path)` + `Filename(cwd=<app>)` | `<app>/assets/a.txt` | 第 2 条 |
| `set_file(path)` + `Filename(cwd=<app>, in_source_dir=True)` | `<app>/assets/a.txt` | 第 2 条（`cwd` 压过 `in_source_dir`） |
| `set_file(path, base_for_paths=True)` + `Filename(cwd=<app>)` | `<app>/assets/a.txt` | 第 2 条（`cwd` 压过 `base_for_paths`） |
| `set_file(path)` + `Filename()`（不给 cwd） | `<app>/assets/a.txt` | 第 6 条（默认＝应用配置目录） |
| `set_file(path, base_for_paths=True)` + `Filename()` | `<project>/settings/assets/a.txt` | 第 4 条（源级开关生效） |
| `set_file(path)` + `Filename(in_source_dir=True)` | `<project>/settings/assets/a.txt` | 第 4 条（模板级开关生效） |
| 文件内值为绝对路径（如 `<tmp>/x.txt`）+ 任意开关 | `<tmp>/x.txt`（保持不变） | 第 1 条 |

## 五、公开诊断的位置

本任务的公开诊断（公开用例）**内嵌在评价器脚本中**，不单独提供用例文件；未来模型可见输入只有本需求、父包源码与公开例形态。

该任务为研究池候选，公开诊断用于说明功能义务。没有正式结构标签、人工双审或模型效果结论。
