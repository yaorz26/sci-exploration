# P68：证据旁车交付兼容探针（完成）

## 具体未知与竞争解释

P67 schema 通过后，仍需知道它能否随研究池候选包交付而不改旧任务文件。竞争解释是：独立 sidecar 加 manifest 指针可以兼容旧消费者；旧消费者可能拒绝新增字段或把 unknown/null 当错误；或者即使技术上兼容，也会把研究池候选误包装成正式数据集。

## 最低成本验证

建立全新目录，只复制 E_B09 与 E_M07 的公开 task、requirements、公开诊断、已有验证结果和 P67 schema sidecar。新增 delivery_manifest 记录相对路径、hash、候选状态、formal_labels_unchanged、unknown/null round-trip 和 private 路径检查。对复制结果做 JSON round-trip、旧 task.json 内容与 SHA-256 对照；不执行候选程序、不读 hidden/private、不改 initial20。

## 原始结果

- 两个候选共 9 个公开文件被复制，旧 task.json 内容和哈希均保持不变。
- formal_labels_unchanged=true；原 null 标签和新增 unknown 值 round-trip 后未改变。
- package 路径未包含 private、hidden 或 private_tests；initial20_changed=false。
- manifest 明确标注 candidate_status=research_pool_not_formally_frozen、publishable=false，阻断把旁车包当正式发布包。
- 模型、任务、来源、private、人工调用均为 0。产物在 experiments/d1_evidence_sidecar_delivery_v1_20261009/。

## 结论与适用边界

证据 sidecar 可以和两个公开研究池候选共存，技术上不需要改旧 task.json；交付边界必须由独立 manifest 明确“未正式冻结、不可发布”。这证明的是包级兼容性，不是旧消费者实际版本的全面兼容，也不改变正式数据集、切分、评分或主问题 A 结果。

下一项转向一项更接近成果交付的检查：用 sidecar 中的 evidence_status 和 candidate_status 做“可发布前门”静态审计，确认任何 unknown/formal_labels=null 的候选都会被阻止进入正式确认集。
