# P5b Seed42 M2 错误归因审计

## 目的

本审计只读取已完成的 seed42 摘要和 JSONL，不生成新候选、不访问新的模型输出，也不改变正式选择结果。目标是区分三类问题：候选没有形成、结构组合失败、候选形成后语义仍不正确。

## 候选形成率

| 分层 | M2a 候选题数 | M2a 缺失题数 | M2b 候选题数 | M2b 缺失题数 |
| --- | ---: | ---: | ---: | ---: |
| 简单 | 15/20 | 5 | 13/20 | 7 |
| 中等 | 13/20 | 7 | 12/20 | 8 |
| 困难 stdin | 15/20 | 5 | 13/20 | 7 |

M2 候选缺失不是测试执行失败：这些题在进入私有评测前已经因为分解、实现池或组合结构问题没有可评测候选。

## 结构错误计数

下表是各运行摘要中的错误计数总和。一个请求可能产生多个错误，因此这些数字不能直接当作独立失败题数。

| 分层 | 方法 | 主要错误计数 |
| --- | --- | --- |
| 简单 | M2a | `function_count_out_of_range` 2；`extra_function_definitions` 5；`signature_mismatch` 6；`nested_function_definitions` 7；`empty_implementation_pool` 4；`missing_function` 2 |
| 简单 | M2b | `function_count_out_of_range` 2；`signature_mismatch` 6；`nested_function_definitions` 6；`empty_implementation_pool` 5；`missing_function` 5；`forward_dependency` 3；`entrypoint_not_last` 1；`extra_function_definitions` 4 |
| 中等 | M2a | `nested_function_definitions` 13；`empty_implementation_pool` 3；`extra_function_definitions` 2；`function_count_out_of_range` 4；`signature_mismatch` 6；`entrypoint_not_last` 2 |
| 中等 | M2b | `nested_function_definitions` 27；`empty_implementation_pool` 10；`forward_dependency` 4；`extra_function_definitions` 4；`entrypoint_not_last` 3；`function_count_out_of_range` 2；`signature_mismatch` 4 |
| 困难 stdin | M2a | `empty_docstring` 12；`function_count_out_of_range` 2；`extra_function_definitions` 6；`nested_function_definitions` 27；`empty_implementation_pool` 11；`extra_top_level_statements` 2；解析语法错误 2 |
| 困难 stdin | M2b | `nested_function_definitions` 34；`extra_function_definitions` 7；`empty_implementation_pool` 14；解析语法错误 4；`forward_dependency` 5 |

### 原始记录复核

对六个正式 M2 分解 JSONL 逐条复核后，分解阶段记录数均为 40 条；有效记录如下：

| 分层 | M2a 有效分解 | M2b 有效分解 | 仅空文档错误记录 |
| --- | ---: | ---: | ---: |
| 简单 | 32/40 | 30/40 | 0 |
| 中等 | 28/40 | 31/40 | 0 |
| 困难 stdin | 35/40 | 35/40 | 0 |

实现 JSONL 的逐条复核显示，语法解析通过率为：简单 M2a `210/210`、M2b `202/202`；中等 M2a `188/188`、M2b `210/210`；困难 M2a `251/252`、M2b `258/262`。解析通过不等于实现可组合：解析通过的记录仍可能包含嵌套函数、额外函数或缺失目标函数，随后会被实现池/组合结构校验淘汰。

六个组合 JSONL 均有 20 条题级记录；一旦形成候选，候选选择和最终评测均能完成。困难层 M2a 为 `15/20` 题形成候选，M2b 为 `13/20`，但两者私有池 oracle 仍为 `0/20`。

## 语义正确性检查

候选形成后仍需看私有池 oracle：

- 简单层：M2a `10/20`、M2b `7/20`。
- 中等层：M2a `2/20`、M2b `3/20`。
- 困难 stdin：M2a `0/20`、M2b `0/20`。

困难层的结论尤其明确：即使 M2a 有 15 题、M2b 有 13 题形成了可组合候选，私有池中也没有任何题达到全通过。因此问题不只是公共选择错失正确候选，也包括组合后程序本身缺乏语义正确性。

## 诊断结论

1. **首要瓶颈是结构协议可靠性。** 困难 stdin 层大量出现嵌套函数、额外函数、空实现池、额外顶层语句和解析失败；这些错误在私有评测之前就淘汰了候选。
2. **修复结构协议也未必足够。** 困难层现有可组合候选的池 oracle 仍为 0/20，说明还存在算法语义或阶段接口错误。
3. **重复 seed43 不能回答新的机制问题。** 它只会重新测量同一结构瓶颈，且不能改变当前 RL 决策门；更高信息增益的下一步应是协议修复后的低成本定向审计。

## 建议的后续实验门槛

只有在修改协议后，先用 3--5 个未评分困难 stdin 题完成以下低成本检查，才考虑扩大实验：

- 分解输出的函数契约和文档非空率达到 100%；
- 实现池为空率为 0%；
- 组合器结构错误为 0%；
- 至少一个公共全通过候选能稳定形成；
- 结构修复不引入直接整题回退或额外预算。

在这些条件未满足前，不应重复 60 题全量生成，也不应启动 RL。
