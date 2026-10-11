# P68：证据旁车文件能否兼容候选任务包

## 具体未知

P67 的证据层 schema 在独立文件中通过了 8 条记录，但尚未验证它能否随候选任务包交付。未知是：只增 sidecar 和 manifest 指针是否能保持旧 task.json、旧评分入口和 unknown/null 语义稳定，还是现有包校验会把证据字段误当正式标签或因缺失值失败。

## 竞争解释

1. 旁车文件加 manifest 指针足够，旧任务文件和旧消费者可以原样读取，新消费者按 schema 读取证据。
2. 旧消费者要求固定字段集合或把 null/unknown 当非法，必须单独维护证据包。
3. 任务包复制和来源关系会把 P66 的非正式候选误包装成正式数据集，交付边界本身需要显式阻断。

## 最低成本验证

建立一个全新、只含公开候选文件的临时交付目录，复制 E_B09/E_M07 的 task/requirements/公开诊断和 P67 schema sidecar；新增 delivery manifest 只保存相对路径、hash、candidate_status、formal_labels_unchanged 和 unknown/null 计数。运行本地检查：旧 task.json 哈希不变、sidecar round-trip 后枚举不变、未知字段不被改写、目录不含 private 路径；不重跑程序、不读 hidden、不改 initial20。

## 预算与红线

预计 15 分钟；模型/API/下载/任务求值/private/人工均为 0。该包是可恢复的研究池交付探针，不是正式发布包，不改变 initial20、储备、切分、评分或人工审查状态。
