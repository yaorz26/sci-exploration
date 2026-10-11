# 独立结构审查说明 v0.3

只读取本包的需求、公开例子和本说明，独立完成全部20题。不要查询源码、
作者标签、隐藏用例、模型成绩或另一位审查员的答案。提交前不协商。
已经参加构建或见过以上材料者应在表头披露，不能计作独立人类双审。

四个维度分开判断，不标“应该拆”。题面不足时允许unknown，并解释原因。

| 字段 | 判断规则 |
| --- | --- |
| cross_operation_state | none：历史操作不改变之后结果；operation_sequence：前一操作改变后续结果；unknown：题面不足。单次循环的游标不自动是外部语义状态。 |
| state_scope | none：无跨操作状态；global：不同键或实例相互影响；partitioned：仅同键或同实例相互影响；unknown：不足。 |
| behavior_dependencies | 可多选direct（一个主要行为）、ordered_transform（后一步消费前一步结果）、branch_rules（条件分支）、operation_sequence（历史依赖）；不足时空列表并解释。 |
| separate_behavior_testability | yes：至少两个用途不同的语义行为，分别写明输入、输出与可单独验证理由；partial：可区分行为，但历史/整体一致性也需验证；no：只能给整体行为；unknown：题面不足。 |

同一功能的命中/缺失、参数开关、输入类型差异不能凑成两个独立用途。
仅把最终输出按字段拆开也不自动满足yes。描述需求的行为关系，不要求模型用相同helper。
state_evidence写题面证据；有状态时另写前后操作怎样改变结果。yes的
separate_behavior_contracts至少填写两个对象，各含behavior、input、output、independent_reason。
对no或unknown也写testability_evidence。发现歧义写requirement_defects。

meta中填写审查员匿名ID、completed_at和attestations。只有真实人类、未参与构建、
未看禁用材料、独立填写且没有猜造答案，才能把相应声明填true。
可记录recognized_source=true表示自己从需求认出了来源，无须检索核实。
表由审查员如实填写；程序验证声明的格式，无法证明声明真伪。

表头声明缺失、同一审查员双表、未写证据或漏题会被拒绝。
unknown保留为类别；另报告双方均确定时的覆盖率，不能通过丢弃unknown抬一致性。
κ表示扣除随机同意后的吻合程度；零方差时可能不可定义，不能写成完美κ。
填好后的两份原始表由管理端留存，分歧协商另存，不能覆盖原表。
