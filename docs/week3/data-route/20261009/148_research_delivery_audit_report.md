# P70：研究池成果的可复核交付索引（完成）

## 具体未知与竞争解释

P65—P69 的研究结果分散在报告、原始 JSON、旁车 manifest、gate 结果和一次失败目录中。本阶段检查一份不发布的索引能否把这些对象互相定位并保留版本与负结果。可能的结果是索引完整、版本仍混淆，或打包会误带 private/hidden 并越过发布边界。

## 最低成本验证

只读 10 份 P65—P69 报告、8 个实验产物、P68 delivery manifest、P69 gate summary 和 P67 schema summary，生成 research_pool_delivery_index。逐项登记相对路径和 SHA-256；检查缺失、旁车状态、gate 结果、formal labels、失败目录和 private/hidden 路径。索引不复制 private、不修改旧文件、不生成发布包。

## 原始结果

- 10/10 报告和 8/8 产物均可定位，missing_count=0。
- P66 首次路径错误留下的空目录仍被列为 preserved_failure_directory，未删除失败。
- sidecar 包没有 private/hidden 路径；P68 的研究池状态、P69 的拒绝结果、P67 的 formal_labels_filled=false 互相一致。
- 索引明确 publishable=false；模型、任务、来源、private、人工调用均为 0。
- 产物在 experiments/d1_research_delivery_index_v1_20261009/。

## 结论与适用边界

P65—P69 的报告、原始产物、失败目录和状态可以通过一份不发布索引复核，版本和负结果没有丢失。索引只证明本轮研究池材料的本地可定位性，不代表正式数据集发布、人工冻结或外部复现。

下一项转向数据集成果本身的最小交付声明：检查索引能否自动生成一页“成果/证据/限制/未完成”清单，且不把候选研究池材料写成已完成的正式数据集。
