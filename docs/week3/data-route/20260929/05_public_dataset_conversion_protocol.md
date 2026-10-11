# WP4A 公开数据转换协议与审计（ClassEval 派生物）

日期：2026-09-29 ｜ 状态：**已完成**
数据来源：`FudanSELab/ClassEval`（MIT，HF）→ 原始文件 `data/raw/classeval/data/test-00000-of-00001-5c45fa6e45572491.parquet`
SHA-256（原始）`ac2f490a8fa0ca63d8b6d166821ca430a382dc04611209e2067a2714cc89df2a`

## 一、做了什么（可复跑）

| 步骤 | 规则 | 产物 |
| --- | --- | --- |
| 1. 可用性过滤 | 只保留参考实现在主环境**连续 3 次稳定通过**的题（91/100）；失败 9 题逐题登记原因，**不删除** | `data/processed/classeval_v1/excluded_tasks.json` |
| 2. 字段统一 | 转成契约 §5.3 的结构：`task_id` / `source`（含来源与哈希）/ `inputs` / `reference_impl` / `public_tests` / `private_test_ref` / `decomposition`（方法名、说明、依赖）/ `metadata` | `data/processed/classeval_v1/tasks_public.jsonl` |
| 3. 公开/私有切分 | 按方法顺序取前 ⌈n/2⌉ 个方法的测试类为公开，其余与无法映射者为私有；两侧都必须含 `def test_` | 公开在 `tasks_public.jsonl`；**私有单独存放** `private/private_tests.jsonl` |
| 4. 分层 | 方法数 ≥5 目标层 / ==3 边界层 / ==2 负对照层 / ==4 储备 | 记录在每题 `metadata.layer` |
| 5. 溯源 | 原始 SHA-256 + 数据集/仓库 URL + 许可证 + 任务序号 | `provenance.json`（含各输出文件哈希） |
| 6. 输入变体 | 为实现"如何拆分"的三类对照，每题同时生成：`inputs.decompose_free`（只给类描述＋导入，模型自己决定拆分）与 `inputs.decompose_given`（给完整骨架 = 分解已给） | 两条输入都在 `tasks_public.jsonl` |
| 7. 审计 | 24 题探索集逐题验证"参考实现 + 仅公开测试"与"参考实现 + 全部测试"都通过 | `experiments/wp4a_classeval_regression/split_check/split_check.json`（**24/24 通过**） |
| 8. 单元测试 | 切分函数 6 个用例（含两处已修缺陷的回归用例） | `codeprm-reproduction/tests/test_classeval_split.py`（**6/6 通过**） |

脚本：`scripts/wp4a_classeval/build_dataset_and_freeze.py`、`verify_split.py`；切分模块：`src/classeval_split.py`。

## 二、修复记录（两处缺陷，均已回归测试覆盖）

1. **拼接缺换行**：初版把头部与第一个测试类拼成 `import unittestclass X(...)`，导致 `ClassEval_49` 语法错误 → 已修，并加回归用例。
2. **公开部分为空**：`ClassEval_69` 的公开部分只含 `setUp`、不含 `def test_`，运行时"0 个用例"被误判为通过 → 现在要求两侧都必须含 `def test_`，否则标 `public_available=False`，并从探索集替换（替换记录写在冻结清单）。

## 三、审计结论

- 通过：可用题 91/100、探索集切分 24/24 通过、单测 6/6 通过。
- **未做（如实登记，不视为已完成）**：
  1. **五项可拆分判据的双 Agent 标注**（执行文档 §8.2 第 7 条）——目前分层只用"方法数量"这一机械代理，**不是**人工判定的可拆分性；
  2. 去重：ClassEval 为手工构造题，未做跨题近似重复检测（题目互不重叠，但未形式化验证）；
  3. 污染降低手段：无法实施（模型训练边界未披露）。
