# classeval_v1（ClassEval 派生物）使用说明

**先读 `dataset_card.md`**（来源、许可、限制）。本目录只放派生产物；原始数据在 `../../raw/classeval/`。

## 重建

```bash
# 依赖：pyarrow（主环境 venv）
<repo>/.venvs/bigcodebench_fast0/Scripts/python.exe scripts/wp4a_classeval/build_dataset_and_freeze.py
<repo>/.venvs/bigcodebench_fast0/Scripts/python.exe scripts/wp4a_classeval/verify_split.py   # 校验公开/私有切分
```

- 回归（全 100 题参考实现）：`scripts/wp3_classeval/run_full_regression.py`
- 冒烟（10 题分层抽查）：`scripts/wp3_classeval/run_smoke.py`
- 切分模块与其测试：`src/classeval_split.py`、`tests/test_classeval_split.py`

## 运行环境（重要）

| 项 | 要求 |
| --- | --- |
| Python | 3.13（主环境）；依赖 `pyarrow`、`numpy`、`pandas`、`nltk`(+语料)、`gensim`、`beautifulsoup4`、`lxml`、`openpyxl`、`python-docx`、`pillow`、`PyPDF2`、`reportlab`、`pytz` |
| NumPy | 2.x；仓库内 venv 已带 `sitecustomize.py` 垫片补回 `np.mat`（ClassEval 建于 NumPy 1.x 时代） |
| nltk 语料 | `NLTK_DATA=D:\yaorz\research\.cache\nltk_data`（**避免写 C 盘**） |
| 网络 | 跑测试**不需要**联网 |
| 已知例外 | 依赖 NumPy 1.x 宽松语义的题已排除；如需复验，用 WSL py3.10 + `numpy<2`（脚本 `scripts/wp3_classeval/wsl_py310_run.sh`） |

## 红线

- `private/` 下的私有测试**不得**进入提示词、候选生成、候选选择或调参；
- 冻结清单 `data/splits/classeval_v1/frozen_manifest.json` 中的任何字段改动都必须生成新版本，**不得就地覆盖**。
