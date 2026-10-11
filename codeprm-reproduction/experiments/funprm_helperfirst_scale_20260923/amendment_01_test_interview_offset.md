# 扩量协议修订 01：test/interview 新颖性偏移

状态：在扩量阶段任何模型调用之前冻结。日期：2026-09-23（Asia/Shanghai）。

- 原计划抓取 `test/interview` 的前 40 道候选。全项目题号扫描发现 `apps-test-0..39` 已被既有 `apps_test_interview40` 数据和实验记录占用，切分器因此拒绝冻结确认集。
- 修订为 `test/interview --skip-matching=40 --limit=40`，即从固定 revision 中抓取下一批 40 道候选。
- `test/introductory` 来源、训练/验证来源、每个确认集的 15+15 分层、总题数、清理规则、模型预算和全部成功门槛不变。
- 原始的 0--39 候选及清理文件保留作审计，但显式排除，不进入任何冻结切分或后续实验。
