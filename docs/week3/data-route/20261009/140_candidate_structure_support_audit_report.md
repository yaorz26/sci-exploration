# P66：新增候选的结构比较支撑审计（完成）

## 具体未知与竞争解释

本阶段问的是：E_B09 与 E_M07 能否为主问题 A 的阶段依赖、共享状态、独立可测三轴提供有证据的结构比较，还是只能补充输出契约和评分器边界。可能的解释分别是“公开可重放输入和不同输出用途已经足够作为低状态/可测锚点”、“需求未写出阶段和持久状态不能当作没有，正式三轴仍未知”，以及“字段用途不同只是一次调用内的输出投影，不等于阶段可独立验证”。

## 最低成本验证

审计只读取两个候选的 task.json、requirements.md、P61/P63 已保存验证结果及哈希；没有重跑程序、模型、来源或 private 数据。每个维度只使用 explicit、partial、not_specified、unknown，不把缺失文字自动改成 yes/no。原始矩阵见 experiments/d1_candidate_structure_support_audit_v2_20261009/candidate_structure_support_matrix.json。

## 原始证据与结果

- 两候选的跨阶段依赖均为 not_specified：需求只有单次 solve(payload) 契约，没有阶段接口或跨阶段引用。
- 两候选的同一次调用输入保护均为 explicit，但跨调用共享状态均为 unknown；可重放 JSON 输入不等于持久状态不存在。
- 两候选都明确列出两个不同用途的输出，但字段级独立可测性均为 partial：P61 的 count/mode 投影和 P63 的 minimum/maximum 见证了输出契约边界，没有形成阶段边界。
- 两候选的正式结构标签均为 unknown：原始 labels/structural_labels 为 null，formal_split 为 null，人工复核为 0。
- 两候选共享三类可比的测量证据：公开输入/输出契约、有限正常与异常域、输入不变或可重放检查；同时仍分别属于 boltons 与 more-itertools 关联家族，不能当作独立来源样本。
- 因此，measurement_contract_comparison_supported=true，formal_main_A_contrast_supported=false。这次审计没有补填低依赖、高可测或无状态标签。

首次 v1 审计因把 E_M07 的 three_execution_results.json 路径误指到候选目录而失败；空目录保留在 experiments/d1_candidate_structure_support_audit_v1_20261009/，修正路径后的 v2 完成，未覆盖旧数据。

## 对主问题 A 的影响与下一步

新增候选确实扩大了“公开功能契约—适配边界—输出投影”的证据池，但没有解除结构标签缺口。下一项转为协议层问题：能否把 contract_origin、necessity_scope、evidence_status 三个证据字段加入候选数据集，而不把它们冒充正式结构因素；先做字段模式和既有 P58 审计的兼容性检查，不新增模型调用或人工标签。
