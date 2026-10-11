# 数据卡：ClassEval 派生物 v1（classeval_v1）

类型：**派生数据集**（不是新数据集）。来源数据集为 `FudanSELab/ClassEval`，本目录只是它的转换与切分结果。

## 来源与许可

| 项 | 内容 |
| --- | --- |
| 原数据集 | `FudanSELab/ClassEval`（Hugging Face），论文 [arXiv:2308.01861](https://arxiv.org/abs/2308.01861) |
| 原始仓库 | https://github.com/FudanSELab/ClassEval |
| 许可证 | **MIT**（仓库与数据集均一手核实，2026-09-28） |
| 原始文件 | `data/raw/classeval/data/test-00000-of-00001-5c45fa6e45572491.parquet` |
| 原始 SHA-256 | `ac2f490a8fa0ca63d8b6d166821ca430a382dc04611209e2067a2714cc89df2a` |
| 我们的改动 | 字段统一、按方法切分公开/私有测试、按方法数分层、剔除参考实现无法稳定通过的题 |

**署明**：使用本项目产物时须同时引用原数据集与原作者，**不得声称本目录是新数据集**。

## 内容与规模

| 项 | 数值 |
| --- | --- |
| 原始题数 | 100 |
| 可用题数（参考实现连续 3 次稳定通过） | **91** |
| 排除题数 | 9（原因见 `excluded_tasks.json`） |
| 分层（可用题） | 目标层 32 / 边界层 25 / 负对照层 11 / 方法数 4 者 23 |
| 探索集 | 24（每层 8，seed 20260929） |
| 方法总数（可用题内） | 见 `tasks_public.jsonl` 的 `metadata.n_methods` |

## 文件

| 文件 | 内容 | 可见性 |
| --- | --- | --- |
| `tasks_public.jsonl` | 每题：来源、两种输入（`decompose_free` / `decompose_given`）、参考实现、**公开测试**、分解信息、元数据 | 模型可读 |
| `private/private_tests.jsonl` | 每题的**私有测试** | **不得进入提示词、候选生成或选择流程** |
| `provenance.json` | 来源、原始哈希、各输出文件哈希 | 内部 |
| `excluded_tasks.json` | 被排除题及逐题理由 | 内部 |

## 已知限制

1. 数据是类级单文件任务，**无仓库上下文**；
2. 分层用"方法数量"代理，未做人工/双 Agent 判据标注；
3. 污染风险未知（模型训练边界未披露）；
4. 9 题因环境语义（宿主名/日期/浮点/OS/NumPy 版本/非确定性）被排除，属保守下界。
