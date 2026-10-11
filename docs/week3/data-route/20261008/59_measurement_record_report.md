# P26结果：保留旧编码，并补充能回答不同问题的证据记录

原20题中新附件记录11题已有有限行为关系、9题尚无该类测量；另表保留两个未分配切分的扩展候选。655条观察记录全部来自保存输出：P12的552、P23的26、P25的5、E_M06的71及E_B07一个已保存同容量反例，没有新任务求值。三题特定手工方案证据、三类成本证据单列，不将生成后方案或人工给定文本倒灌为任务真值。

## 编码相同能否代替问题相同

回查manifest中的跨操作状态、状态范围、独立可测与行为依赖四项，M05/F04完全相同：none、none、yes、[ordered_transform,branch_rules]。保存证据却回答不同问题：M05新增短列改变共同有效域；F04其他字段非法导致整题拒绝，name无值可观察。不能仅凭编码相同推出相同实体尺度、局部投影或有效输入条件。

旧标签本身有文字证据，它们也没有声称所有输入上每个局部输出都可观察。本阶段不把此反例称为yes标签错误，不证明最低应有多少维度或“一项二元补充绝不可能”。它排除的是把几项编码当作完整的操作性测量记录；几个编码可以保留作历史导航，具体判断仍需问题单位和证据。

原20题存在5个此类相同编码的多题组，但这不是5个错误或新独立统计单位。9类保存反例判别记录覆盖：C04两粒度、casefold同实体、任务/方案状态、B05数据版本、M05有效域/合法次序、错误程序关系、F04拒绝投影、未测/null及来源出现0。该映射由同助手审查，非独立人工可靠性、κ或模型答案。

## 第二遍发现并保留的错误

v1把E_M06原拼写A/a关系的“跨实体问题不适用”写成projection_applicable=false。但原始输出清楚给出两个可观察的目标规范类代表，问题是它们属于同一实体，不是没有投影。v1输出保留，v2将投影可观察记true、foreign_entity_claim_applicable另记false，同时显式保存capacity、typed、mode等问题条件，证据编号仍放在单位之外。

这不是单纯命名修饰：如果混写，后续可能错误删掉真实可观察的同实体历史反例。F04两合法拒绝则相反，语义结果相等且正确，但name局部投影确实不可观察。两个例子共同要求适用问题、结果是否正确、投影是否存在分别保存。

## 可复核产物与范围

当前采用`d1_measurement_record_v2_20261008/`：task_records保留原作者v0.2、切分/来源；observations保存问题单位/条件及有限结果，evidence_ref指原文件/编号；plan_records保存具体方案义务；cost_layers区分占位情景、合法人工文本与真实API花费；扩展另表。9个无此类行为证据任务仍null，其中B05有计划证据，不因此伪补成完整任务测量。

模型/API/任务求值/下载0，人工0；655不是新增测试，原20题307/11开发9储备、初标/旧κ/盲审ZIP不改。文件散列只服务新附件来源追踪，不重跑校准或参考评分。尚无独立语义可靠性或主问题A收益结论。

阶段完成，不继续堆测量字段。接续P27审查方法自身的接受条件：当前M0只检查solve存在，M2入口检查参数AST完全一致。新增无行为变化的参数类型注解是否会导致一臂接受、另一臂在评分前拒绝？以正确给定代码的新形式、实际门槛和公开例子作低成本反例，不调用模型、不据此预判效应或改旧结果。

证据：`codeprm-reproduction/experiments/d1_measurement_record_v1_20261008/`（保留错误初版）、`d1_measurement_record_v2_20261008/{task_records.json,expansion_records.json,observations.json,plan_records.json,cost_layers.json,discriminating_review.json,record_schema_and_provenance.json,summary.json}`。脚本`scripts/d1/build_measurement_records.py`；实际v2命令`python -B -X utf8 scripts/d1/build_measurement_records.py`，输出不得覆盖。
