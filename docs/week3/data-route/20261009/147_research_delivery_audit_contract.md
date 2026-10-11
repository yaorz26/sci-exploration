# P70：研究成果包的可复核定位是否完整

## 具体未知

P68/P69 已有旁车包和发布前门，但成果仍分散在报告、sidecar、delivery manifest、gate 结果和失败目录中。未知是：能否用一份不发布的研究成果清单把每个候选、证据、限制、负结果和 gate 互相定位，还是仍会出现“报告说通过但找不到原始证据/失败被漏掉”的可复核缺口。

## 竞争解释

1. 相对路径、sha256、状态和失败指针组成的清单足以复核研究池成果。
2. 报告和机器输出分散、相同候选多版本并存，单清单会遗漏版本或把 v1/v2 混淆。
3. 为了可复核而打包可能意外包含 private/hidden 或把不可发布材料误标为成果。

## 最低成本验证

只读 P65—P69 报告、最新 experiment summary、sidecar delivery manifest 和 P69 gate 结果，生成一个 research_pool_delivery_index，逐项检查报告/原始 JSON/失败目录存在、hash 指针一致、candidate_status/formal labels/gate 状态一致、private/hidden 路径为零。清单只做研究池索引，不生成发布包，不改旧数据。

## 预算与红线

预计 15 分钟；模型/API/下载/任务求值/private/人工均为 0。任何缺失或冲突保留为负结果，不能用清单替代正式人工冻结或发布审批。
