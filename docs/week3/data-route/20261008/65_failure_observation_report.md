# P29结果：策略计分为零，不代表已经逐例测到零正确行为

P9一题两臂的主结果仍为M0/M2各0/1，实际花费640/1850、同6500上限保持。M0保存了完整候选并执行2公开+12隐藏共14次行为评分；M2在helper2阶段失败，没有完整候选，实际行为评分0次。M2 public/private各passed=0和14个case槽位属于生成失败后的主策略记账，不能写成“代码逐例行为准确率0/14”。

| 观察/计分层次 | M0 | M2 |
| --- | --- | --- |
| 预定任务主分母 | 1 | 1 |
| 整题全部通过 | 0/1 | 0/1 |
| 到达行为评分的候选 | 1/1 | 0/1 |
| 实际行为案例求值 | 14 | 0 |
| 生成失败计分占位案例槽位 | 0 | 14 |
| 实际隐藏行为符合 | 5/12 | 未定义，没有候选可测 |

这不豁免M2：完整策略未交付符合需求的候选，主Y仍为0，不能删除后仅报组装成功子集。条件行为率必须同时报告覆盖，它回答另一个问题。结构分组若只选已有完整方案，会改变样本；计划文本存在也不能证明实际共享状态图或局部正确性，程序缺失时记unknown，不记none。

本阶段只读summary、selection_freeze、protocol、请求ledger和实际评分分支。冻结中M0有candidate_path/sha，M2为null且generation_error；M0评分results长度与passed一致，M2有generation_failure而无实际results。M2请求为plan/helper1/helper2，entry未到达。主结果和计费无改写，新评分/模型/API0，人工0。

不能由不同失败阶段断言结构、接口或预算造成效果，也不能估计修补helper/继续生成的反事实成绩。一对工程烟测不是正式关联确认。对问题A的实际作用是固定报告层次：预定策略结果、生成阶段覆盖、实际行为、实际方案属性与真实成本分别给分母和缺失。

下一项P30把P18—P29边界写入问题A候选协议增补，比较旧候选说法与保存反例，明确共同外部入口/方法内helper约束、任务与生成后方案、拒绝/投影、主分母与条件观察。仅登记未来候选，不启用正式模型或改旧结果；完成后转尚未解决的非缓存纯函数组合问题。

证据：`decomposition-bench/experiments/d1_failure_observation_v1_20261008/{arm_observation_records.json,estimand_and_missingness_review.json,input_sources.json,summary.json}`。实现`scripts/d1/analyze_failure_observation.py`，命令`python -B -X utf8 scripts/d1/analyze_failure_observation.py`。
