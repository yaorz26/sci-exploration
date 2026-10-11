# P69：unknown/未冻结候选能否被发布前门阻止

## 具体未知

P68 证明 sidecar 可以和研究池候选共存，但还未证明交付流程会阻止 unknown/formal_labels=null 的候选进入正式确认集。未知是：只用 candidate_status、publishable、formal labels、human_reviews 和 evidence_status 的静态前门是否足够，还是会漏放研究池候选或误拒合法的正式候选。

## 竞争解释

1. manifest 状态、正式标签和证据状态联合门槛足以阻断当前研究池包。
2. 旁车虽然存在，现有流程未强制读取它，unknown 或 null 可能被静默当作可用。
3. 门槛过严会把“证据未知但尚未正式冻结”的合法研究池材料误当错误；门槛应返回原因而不是修改数据。

## 最低成本验证

对 P68 现有交付 manifest 做纯静态 gate：正式包必须声明 formally_frozen、publishable=true、formal labels 非 null、human_reviews>0、证据记录无 unknown/not_specified。当前包应拒绝并返回原因码；再在内存中构造一个标记为 synthetic_schema_fixture 的全字段通过对象，验证 gate 的允许路径，不把它当真实数据或人工审查。不得改候选文件、initial20 或切分，不调用模型/任务程序/private。

## 预算与红线

预计 15 分钟；模型/API/下载/任务求值/private/人工均为 0。gate 只验证发布边界，不把合成 fixture 或 schema 通过写成正式冻结。
