# P69：研究池候选的静态发布前门（完成）

## 具体未知与竞争解释

P68 的旁车包虽然标记为不可发布，但需要验证交付流程是否真的会阻止 unknown、formal_labels=null 和未冻结候选进入正式确认集。可能的结果是联合门槛足够、旁车未被强制读取而会漏放，或门槛过严而没有可解释的拒绝原因。

## 最低成本验证

对 P68 的 delivery_manifest 和 schema sidecar 运行纯静态 gate。允许条件是：candidate_status=formally_frozen、publishable=true、formal labels 已确认、human_reviews>0，且证据记录不含 unknown/not_specified。当前研究池包原样检查；另在内存中构造一个 synthetic_schema_fixture 只验证允许路径，不写回候选文件。

## 原始结果

当前包被拒绝，原因码完整返回：

- candidate_status_not_formally_frozen
- publishable_false
- formal_labels_not_confirmed
- human_reviews_zero
- evidence_status_unknown

合成全字段 fixture 被允许，说明 gate 有可测试的通过路径；该 fixture 明确不属于研究数据，也没有写入人工审查。formal_labels_written=false、initial20_changed=false，模型/任务/来源/private/人工调用均为 0。产物在 experiments/d1_prepublication_gate_v1_20261009/。

## 结论与适用边界

静态前门足以阻止当前研究池旁车包进入正式确认集，并能把拒绝理由具体化。它只验证本地 manifest/sidecar 规则，不证明所有外部消费者版本都执行该 gate；合成 fixture 不能当正式冻结或人工结果。

下一项继续查数据集成果边界：对 P68/P69 的证据层、候选状态和 gate 结果做一次可复核交付清单审计，确认报告、sidecar、manifest、负结果和限制是否能在一个不发布的研究成果包中互相定位。
