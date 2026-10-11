# P67：证据来源与必要范围 schema（完成）

## 具体未知与竞争解释

P66 的候选审计留下一个协议问题：新增证据能否用 contract_origin、necessity_scope、evidence_status 和 provenance 指针机读保存，同时不冒充 dependency、state_scope、testability 正式标签。竞争解释是：三字段足够形成可复核旁车协议；字段过粗会把接口条件误写成任务义务；或者兼容风险要求完全不碰旧 manifest。

## 最低成本验证

读取 P58 六条已保存主张、P58 的测量协议增量、P66 两候选矩阵和 initial20 manifest 哈希。为证据层定义固定枚举：

- contract_origin：任务最终输出义务、指定接口条件、额外局部预期、尚未定规范的观测、公开来源契约、适配要求、未指定；
- necessity_scope：任务最终输出、条件于接口、由整体合法反例证明非必要、候选版本特定、任务必要性未定、unknown；
- evidence_status：supported_finite、partial、unknown、not_specified、contradicted；
- provenance：record_id、source_path、evidence_kind、source_sha256。

然后把 P58 六条主张和 P66 两条正式标签审计记录映射到 schema，检查枚举、必填指针、旧正式字段不写入，以及 initial20 manifest 前后哈希一致。没有模型、来源、任务程序、private 或人工调用。

## 原始结果

- P58 六条记录和 P66 两条候选元数据记录全部通过 schema（8/8）。
- 使用了六类 contract_origin、六类 necessity_scope；证据状态只出现 supported_finite 和 unknown，未把未知补成通过。
- initial20 manifest 前后哈希相同；formal labels、评分、切分均未写入或修改。
- 机器调用计数全为 0；新增产物为 experiments/d1_evidence_provenance_schema_v1_20261009/evidence_provenance_schema_draft.json 和 summary.json。

## 结论与适用边界

最小证据层 schema 可以作为旁车/增量协议保存 P58/P66 类型的证据，并保持正式结构标签分离。它解决的是来源、必要范围和证据状态的可追溯性，不解决人工真值、总体比例或主问题 A 的结构效应；只验证了 8 条定向记录，不能据此宣称全数据集已完成迁移。

下一项转向数据集交付层：检查这个证据层是否能在候选任务包中以不改变旧 manifest 的方式随包携带，并验证缺失/unknown 的序列化规则；若出现兼容冲突，保留 schema 失败并回到独立旁车文件。
