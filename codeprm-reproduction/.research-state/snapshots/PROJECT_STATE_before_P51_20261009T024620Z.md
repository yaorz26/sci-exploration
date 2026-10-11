# 项目研究状态

最后更新：2026-10-09T02:36:07.705439+00:00
状态：active（P43—P48有限验证完成，P49进行中；主A效果/人工/正式冻结未完成）

## 当前任务与权限

- 用户确认题目“面向项目功能级代码生成的任务分解评测数据集构建与适用边界研究”，主问题A是同题—方法总token上限下阶段依赖、共享状态、独立可测与拆分相对整体收益的关联，非因果识别。数据集也为拟成果；用户中断后明确继续，按目标/计划持续接续，只有重要方向/资源另询。[evidence: .research-state/RESEARCH_TARGET.md; ../memory/decisions-and-next-steps.md]
- P39两个官方v1缓存六窗口：Token IO/动态任务图已有、步数上限非多阶段总token cap；所查段未见联合框架不等穷尽否定，贡献收窄。后续P40前置支撑、P41来源、P42新功能已完成，当前P43数值契约接续。[evidence: ../docs/week3/data-route/20261008/85_measurement_contribution_literature_report.md; ../docs/week3/data-route/20261008/86_pre_generation_contrast_support_contract.md; experiments/d1_measurement_contribution_literature_v1_20261008/targeted_evidence_and_contribution_review.json]

## 数据与实际效果

- initial20 v5：4来源20题307记录（40公开/267隐藏），11开发9储备；B02一隐藏与公开同输入，实际不同输入306/未公开隐藏266。20细家族15显式关联组件非独立样本。结构作者初标12无历史/8有、global6/partitioned2、yes8/partial7/no5；真实人工0，正式标签/协议冻结未完成。[evidence: data/processed/d1_project_initial20_v5_20261008/manifest.json; experiments/d1_family_link_audit_v1_20261008.json; ../docs/week3/data-route/20261008/28_portability_and_contract_report.md]
- 当前成果为可迁移v4管理包，补4固定来源库/PyYAML6.0.3及两路径，285/287原文件不变；Win11/Python3.13.7的-I -S实测40/40运行、614/614案例执行、14/14同助手复核，非新案例/跨平台/独立语义真值。轻量库功能适配不是完整项目集成，污染未知；盲审仅reviewer_only.zip，人工0/未发布。[evidence: experiments/d1_candidate_delivery_v4_portable_20261008/portable_delivery_verification_v2.json; experiments/d1_portability_v4_isolation_20261008/summary.json; ../docs/week3/data-route/20261008/28_portability_and_contract_report.md]
- 真实P9 B03：M0/M2同6500总上限，实际640/1850、整题均0/1；M0公开0/2隐藏5/12，M2helper2撞名没有完整候选。M0实际行为14、M2实际0/占位14，条件行为未定义。P8/P9共7调用3173token，累积约98/100；当前不再生成，不用旧失败解释算法根因。[evidence: experiments/d1_allin_native_pair_b03_v1_20261008/summary.json; experiments/d1_failure_observation_v1_20261008/summary.json]
- 旧五题两臂0/5仅6500生成阶段上限；生成4903/24179（4.93倍）、含预检8004/45301（5.66倍）、56调用28预检/28生成，旧10/14拆账纠正为12/12。失败helper/entry原文缺失，保留负结果不混总预算正式效果。[evidence: experiments/d1_cost_allin_audit_v1_20261008.json; ../docs/week3/data-route/20261008/17_review_delivery_and_protocol_revision.md]

## 已验证测量边界

- P12—P25：行为耦合与全局排序/容量/历史分开；粒度/聚合观察可产生假阳性，任务机会不替代计划连接。任务状态不决定计划状态图；正确给定文本3350/3758可容纳不是模型能生成；关系相等不代替绝对正确，合法拒绝未必提供局部投影。来源/家族别名、有限域与人工0限制保留，两扩展候选不计入原20题。[evidence: ../memory/data-route-log.md; ../docs/week3/data-route/20261008/30_behavior_coupling_report.md; ../docs/week3/data-route/20261008/50_expansion_support_report.md; ../docs/week3/data-route/20261008/57_expected_rejection_report.md]
- P26—P30：附件11有限/9未测、655旧观察，M05/F04粗编码相同但域/投影不同；v1混不适用与投影缺值在v2修正。实际M0入口6/6、M2 4/6拒参数注解，独立候选6接受/7形状拒绝，旧P9不变；v0.3六反例协议候选未集成正式pipeline，helper严格规则仍在。[evidence: ../docs/week3/data-route/20261008/59_measurement_record_report.md; ../docs/week3/data-route/20261008/63_entry_annotation_gate_report.md; ../docs/week3/data-route/20261008/67_question_A_protocol_v0.3_candidate.md]
- P31—P33：F03无操作状态仍有路径全候选门槛，216格左错28/右14/双错14/不结合14、546实际求值。可结合摘要216结合/432终值符合、两删减接口与两路径碰撞解释信息保留，非最小/效率。P31定位实现意外见F03十二隐藏输入描述及相邻题，期望/隐藏评分0；后续非未见确认，首反例事前冻结。[evidence: ../docs/week3/data-route/20261008/69_layered_merge_reduction_report.md; ../docs/week3/data-route/20261008/71_layered_merge_summary_report.md; ../docs/week3/data-route/20261008/73_path_local_summary_report.md]
- P34/P35：限定排序接口丢行身份，六手算错误3/6、索引与原输入恢复6/6、局部18/18。同helper可重算救回；实际M2三入口门槛全接受含零helper调用控制，但提示要求与执行门槛不同，不称协议合规。P19八entry文本非API/P9实际entry0；v1元数据错误保留v2过。[evidence: ../docs/week3/data-route/20261008/75_interface_information_recovery_report.md; ../docs/week3/data-route/20261008/77_actual_M2_recovery_boundary_report.md]
- P36/P37：新丢弃返回程序6/6、12干预机制过，同helper一次可驱动/断言/丢弃；异常传播也不证终值贡献。六真实保存M2单位完整3/缺失3，旧三个完整候选六公开trace都进入helper正常，当前总预算M2完整0。旧协议不填主效果，调用非返回贡献。[evidence: ../docs/week3/data-route/20261008/79_helper_runtime_influence_report.md; ../docs/week3/data-route/20261008/81_saved_M2_observability_report.md]
- P38：B06十输入/20求值/五关系符合，合法error:missing/缺失及找到null/default=null缺失各同输出；两个不同default的三干预对区分具体分支。数据标记不是函数异常；不凭返回相等判相同分支，不改初标。[evidence: ../docs/week3/data-route/20261008/83_missing_marker_collision_report.md; experiments/d1_missing_marker_collision_v1_20261008/summary.json]

- P40原20严格同来源/同其余两轴匹配：190全对/41同来源、依赖1/状态2/可测0；开发同、储备三轴0，状态全在缓存群。8依赖集合各仅一种可测初标，机制待P41；不否定描述联合关联。[evidence: ../docs/week3/data-route/20261008/87_pre_generation_contrast_support_report.md; experiments/d1_pre_generation_contrast_support_v1_20261008/summary.json]

- P41当前构建器复制逐题五元组，三文件静态声明路径20/20五字段一致，排除构建时从依赖/legacy推算可测字段；独立存储不等独立判断/人类，样本对应保留。[evidence: ../docs/week3/data-route/20261008/89_testability_label_provenance_report.md; experiments/d1_testability_label_provenance_v1_20261008/source_copy_comparison.json]

- P42 E_B08研究候选mean/variance不同用途，两种合法计算次序；21诊断单位含6旧/15新均在预声明1e-12内。旧公式预期非事前手算、实现调用非任务义务已明确更正；[1,1,5]方差差4.44e-16，标签null/未并入原20。[evidence: ../docs/week3/data-route/20261008/91_noncache_stats_testability_report.md; experiments/d1_noncache_stats_alternative_order_v1_20261008/summary.json; experiments/d1_noncache_stats_alternative_order_v1_20261008/correction_programs_and_anchors_frozen.json]

- P43已冻结一保存差异/原json_equal，八比较对一次执行，精确规则拒4.44e-16差异；int/float相同、bool分开，非有限仅孤立控制非整个评分器结论。候选精度尚未冻结。[evidence: ../docs/week3/data-route/20261008/93_numeric_contract_comparison_progress.md; experiments/d1_numeric_contract_comparison_v1_20261008/original_comparator_observation.json]

## 下一步与红线

- 当前P47先冻结P44逐值预期，六新来源包装与保存18输出实际评分，辨空域default适配/bool输出。停止浮点阈值支路；画像仍可描述但无同一删除稳定画像；阶段账本延迟已补记，不称严格全流程预注册。[evidence: .research-state/RESEARCH_PLAN.md; ../docs/week3/data-route/20261009/101_discrete_adapter_fidelity_contract.md; ../docs/week3/data-route/20261009/100_joint_profile_sensitivity_report.md]
- 保持boltons/cachetools开发、more-itertools/confuse储备；private不进提示/选择/调参，不进行正式储备生成；原始输出/失败/分母不覆盖。付费、训练/RL、发布未授权。[evidence: ../docs/week3/data-route/20261008/05_selfbuild_protocol.md; .research-state/RESEARCH_TARGET.md]
- ClassEval G2收束24题、2候选，7/8/7成功、双零16/24/三臂全零15/24；旧κ0.436不足。APPS helper-first两确认12/60对首7/60、随机7.2/60、上限14/60、净5/区间[0.0266666667,0.1433333333]，6胜1负p=.125非强显著；top-down失败，ClassEval未训练，RL未启动，旧结论不改。[evidence: experiments/classeval_wp6_v2/wp6_v2_manifest.json; reports/funprm_helperfirst_scale_confirmation_ab_20260926.md; ../memory/research-findings.md]

## P48接续检查点

E_B09另池公开候选十二新边界三程序各12/12，36新执行；共享guard非独立oracle，count/default分离显式适配，来源许可完整，结构标签null。当前P49查开发相同画像下构造预算差，原20/307/切分/效果不改。[evidence: ../docs/week3/data-route/20261009/104_discrete_candidate_boundary_report.md; .research-state/RESEARCH_PLAN.md]

P49开发三重复画像5对的构造输入差全由固定模板仿射M2=4*M0+488解释，最大588/6500；当前P50验证整数声明/数值比较/构造项目消费者分歧，非真实项目集成。[evidence: ../docs/week3/data-route/20261009/106_joint_profile_budget_report.md; ../docs/week3/data-route/20261009/107_output_type_composition_contract.md]
