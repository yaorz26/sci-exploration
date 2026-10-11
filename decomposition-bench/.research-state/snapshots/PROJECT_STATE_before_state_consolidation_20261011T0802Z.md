# 项目研究状态
最后更新：2026-10-11T07:42:00Z
状态：active（用户明确恢复；G5最终纠正版已交付，主A等待新资源计划）
历史阶段状态保存在snapshots/PROJECT_STATE_before_P74_20261009T0628.md；以下阶段记录须以最新追加为准。

## 当前任务与权限

- 用户确认题目“面向项目功能级代码生成的任务分解评测数据集构建与适用边界研究”，主问题A是同题—方法总token上限下阶段依赖、共享状态、独立可测与拆分相对整体收益的关联，非因果识别。数据集也为拟成果；用户中断后明确继续，按目标/计划持续接续，只有重要方向/资源另询。[evidence: .research-state/RESEARCH_TARGET.md; ../memory/decisions-and-next-steps.md]
- P39两个官方v1缓存六窗口：Token IO/动态任务图已有、步数上限非多阶段总token cap；所查段未见联合框架不等穷尽否定，贡献收窄。后续P40前置支撑、P41来源、P42新功能已完成，该文献审查已完成，P56公开规范核对完成，P57局部顺序反例完成，P58证据范围审查完成，P59候选执行完成，P60两参考验证完成，P61输出投影、P62语义重写、P63第二来源候选与P64并列反例均完成；当前P65合法代表判定首动作已冻结。[evidence: ../docs/week3/data-route/20261008/85_measurement_contribution_literature_report.md; ../docs/week3/data-route/20261008/86_pre_generation_contrast_support_contract.md; experiments/d1_measurement_contribution_literature_v1_20261008/targeted_evidence_and_contribution_review.json]

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

- P43已冻结一保存差异/原json_equal，八比较对一次执行，精确规则拒4.44e-16差异；int/float相同、bool分开，非有限仅孤立控制非整个评分器结论。后十控制偏离旧上限/普通==已另文件更正，精度无唯一依据、E_B08留池。[evidence: ../docs/week3/data-route/20261008/93_numeric_contract_comparison_progress.md; experiments/d1_numeric_contract_comparison_v1_20261008/original_comparator_observation.json]

## 下一步与红线

- 当前P65十四输出对/两规则28比较，八保存合法代表/六错误输出预测/hash已冻结，比较尚0、任务0；当前无key候选不改。P64八fn方案求值公共语义8/8、两个合法并列差异，精确source4/4而builtin2/4；原solve_calls命名实际入口0已另释。[evidence: .research-state/RESEARCH_PLAN.md; ../docs/week3/data-route/20261009/136_keyed_tie_report.md; ../docs/week3/data-route/20261009/137_admissible_extrema_comparator_contract.md; experiments/d1_admissible_extrema_comparator_v1_20261009/fourteen_pairs_and_admissibility_predictions_frozen.json]
- 保持boltons/cachetools开发、more-itertools/confuse储备；private不进提示/选择/调参，不进行正式储备生成；原始输出/失败/分母不覆盖。付费、训练/RL、发布未授权。[evidence: ../docs/week3/data-route/20261008/05_selfbuild_protocol.md; .research-state/RESEARCH_TARGET.md]
- ClassEval G2收束24题、2候选，7/8/7成功、双零16/24/三臂全零15/24；旧κ0.436不足。APPS helper-first两确认12/60对首7/60、随机7.2/60、上限14/60、净5/区间[0.0266666667,0.1433333333]，6胜1负p=.125非强显著；top-down失败，ClassEval未训练，RL未启动，旧结论不改。[evidence: experiments/classeval_wp6_v2/wp6_v2_manifest.json; reports/funprm_helperfirst_scale_confirmation_ab_20260926.md; ../memory/research-findings.md]

## P48接续检查点

E_B09另池公开候选十二新边界三程序各12/12，36新执行；共享guard非独立oracle，count/default分离显式适配，来源许可完整，结构标签null。随后P49已查开发相同画像下构造预算差，原20/307/切分/效果不改。[evidence: ../docs/week3/data-route/20261009/104_discrete_candidate_boundary_report.md; .research-state/RESEARCH_PLAN.md]

P49开发三重复画像5对的构造输入差全由固定模板仿射M2=4*M0+488解释，最大588/6500；P50已证整数声明/数值比较/构造项目消费者分歧，非真实项目集成。[evidence: ../docs/week3/data-route/20261009/106_joint_profile_budget_report.md; ../docs/week3/data-route/20261009/107_output_type_composition_contract.md]

## P43—P50新结论与P51接续

- P44/P47新来源六包装通过、保存18分数6/6、6/6、5/6，13对象14属性28比较；单对象空count=-1说明明确适配，原22计数以sidecar纠正。[evidence: ../docs/week3/data-route/20261009/102_discrete_adapter_fidelity_report.md; experiments/d1_discrete_adapter_fidelity_v1_20261009/count_clarification.json]
- P45/P46全20/开发/储备画像10/7/5、重复5/3/3；13删除每次重复却无同一稳定画像，粗关联有限。[evidence: ../docs/week3/data-route/20261009/98_joint_profile_support_report.md; ../docs/week3/data-route/20261009/100_joint_profile_sensitivity_report.md]
- P48 E_B09三结构12/12共36新执行，另池公开候选/许可完整，类型/全域/人工未冻；共享guard与同来源不充独立证据。[evidence: ../docs/week3/data-route/20261009/104_discrete_candidate_boundary_report.md]
- P49最大构造输入差588，11行仿射4*M0+488完全解释；P50四实际评分中float count通过、构造range TypeError，原规则不保特定消费/整数声明。非真实项目集成，不能推广原20；E_B09类型门槛已P51有限比较验证，v2未全链验证。[evidence: ../docs/week3/data-route/20261009/106_joint_profile_budget_report.md; ../docs/week3/data-route/20261009/108_output_type_composition_report.md]

P51已完成六对18判断（12函数/6类型），严格模式保合法float default；P52非缓存公开文本流来源与六终值已冻结、solve0，接续按111号预算执行。[evidence: ../docs/week3/data-route/20261009/110_typed_candidate_gate_report.md; ../docs/week3/data-route/20261009/111_noncache_stream_contract.md; experiments/d1_noncache_stream_v1_20261009/source_and_final_anchors_frozen.json]

P52六新组18solve：持续/前缀重算各6/6、六轨迹14快照一致，逐片2/6；同源API不是独立真值，当前P53新close前缀结构检验终值掩盖时机差异。[evidence: ../docs/week3/data-route/20261009/112_noncache_stream_report.md; ../docs/week3/data-route/20261009/113_stream_finalization_contract.md]

P53新close结构终值6/6、轨迹3/6，四EOF预测3/4；失败不覆盖，停止HTML细节/E_B10留池。当前P54原B03新单次匹配/两类阶段连接，明确非旧模型根因。[evidence: ../docs/week3/data-route/20261009/114_stream_finalization_report.md; ../docs/week3/data-route/20261009/115_ansi_single_pass_contract.md]

P54来源/独立扫描各6/6，两类别串行各5/6不同失败，三非幂等；当前P55原串区间接口修复，非模型效果/旧失败归因。[evidence: ../docs/week3/data-route/20261009/116_ansi_single_pass_report.md; ../docs/week3/data-route/20261009/117_ansi_original_spans_contract.md]

P55两原span入口各6/6、24局部span过，来源新查询0；当前P56两公开例/六保存结果先冻，仅八行零执行规范核对，原题保留/未来增量另存。[evidence: ../docs/week3/data-route/20261009/118_ansi_original_spans_report.md; ../docs/week3/data-route/20261009/119_ansi_contract_clarification_contract.md]


P56八行公开/保存对照完成，未来增量未冻；P57三结构事前契约已登记，首动作六合法两非法逐值预期冻结，禁止旧例重跑/源库或curator导入。[evidence: ../docs/week3/data-route/20261009/120_ansi_contract_clarification_report.md; ../docs/week3/data-route/20261009/121_range_local_observability_contract.md]


P57强局部次序可拒合法整体，固定sorted接口的多重集合义务具有必要充分理由，但不是任意helper角色必要性。P58先冻六定向证据主张，零新执行，不以可运行局部测试直接推任务固有可测。[evidence: ../docs/week3/data-route/20261009/122_range_local_observability_report.md; ../docs/week3/data-route/20261009/123_local_contract_scope_audit_contract.md]


P58六证据范围审查完成，字段候选contract_origin/necessity_scope避免强局部表示替代任务义务；当前P59执行器另版，八新输入五结构/40solve先冻，原20/旧评分/旧36不改。[evidence: ../docs/week3/data-route/20261009/124_local_contract_scope_audit_report.md; ../docs/week3/data-route/20261009/125_typed_candidate_execution_contract.md]


P59候选v2完整执行已支持正常值/合法异常/输入严格不变合用，40新solve；当前P60先冻结两未测参考和八保存诊断，只16新solve，不把源码包装语句算作实际源API记录。另版结果/manifest，原20/旧36/初标/评分保持。[evidence: ../docs/week3/data-route/20261009/126_typed_candidate_execution_report.md; ../docs/week3/data-route/20261009/127_typed_reference_agreement_contract.md]


P60新两参考各8/8且严格同保存whole，当前P61四合法四格/两容器default异常先冻，模型/API0、标签null。执行/字段投影/24输出控制待接续，不冒称后台计算或主A效果。[evidence: ../docs/week3/data-route/20261009/128_typed_reference_agreement_report.md; ../docs/week3/data-route/20261009/129_discrete_output_projection_contract.md; experiments/d1_discrete_output_projection_v1_20261009/six_new_inputs_and_projection_predictions_frozen.json]


P61正常用途分离/共同有效域已有限验证，当前P62改变算法次序而保留语义：原树按实际乘积先选，再映射删除后路径；检验除法阈值在浮点边界，不扩旧P13/众数同类格。[evidence: ../docs/week3/data-route/20261009/130_discrete_output_projection_report.md; ../docs/week3/data-route/20261009/131_threshold_pullback_contract.md]


P62反例表明语义义务不等唯一物化次序，有限乘积/路径方案可先选原叶子；浮点逆阈值不普遍等价。当前P63补第二来源的非缓存公开契约，原储备/模型/人工/正式冻结红线不变。[evidence: ../docs/week3/data-route/20261009/132_threshold_pullback_report.md; ../docs/week3/data-route/20261009/133_second_source_extrema_contract.md]


P63 E_M07源公开上下界可用一遍/两遍计算，候选无key整数域明确限定。P64针对来源并列max宽规范，未来abs域不同代表是否被精确参考误拒，原任务/候选不扩域。[evidence: ../docs/week3/data-route/20261009/134_second_source_extrema_report.md; ../docs/week3/data-route/20261009/135_keyed_tie_contract.md]


P64公开语义允许代表差异，不能由固定来源决定唯一预期；求值单位fn8/solve入口0另存澄清。P65先冻14输出及接纳预测，拟28比较零来源/任务，用成员/int/极值规则检验未来variant，不改当前E_M07。[evidence: ../docs/week3/data-route/20261009/136_keyed_tie_report.md; ../docs/week3/data-route/20261009/137_admissible_extrema_comparator_contract.md; experiments/d1_admissible_extrema_comparator_v1_20261009/fourteen_pairs_and_admissibility_predictions_frozen.json]

## P65—P67 最新接续（2026-10-09T04:59:48Z）

P65 14对比较完成，strict 8/14且八合法全收、六控制全拒；P66 审计矩阵保留缺失证据，不填正式结构标签。当前 P67 只读既有主张和 manifest，验证证据字段的可机读性与向后兼容。[evidence: ../docs/week3/data-route/20261009/138_admissible_extrema_comparator_report.md; ../docs/week3/data-route/20261009/140_candidate_structure_support_audit_report.md; ../docs/week3/data-route/20261009/141_evidence_provenance_schema_contract.md]

## P67—P68 最新接续（2026-10-09T05:13:21Z）

P67 的 8 条证据记录全部通过 schema，旧 initial20 manifest 未变。当前 P68 仅建立公开研究池旁车包并检查旧 task 文件、unknown/null 和 private 隔离。[evidence: ../docs/week3/data-route/20261009/142_evidence_provenance_schema_report.md; ../docs/week3/data-route/20261009/143_evidence_sidecar_delivery_contract.md]

## P68—P69 最新接续（2026-10-09T05:19:27Z）

P68 的公开研究池旁车包通过复制、hash、round-trip 与 private 隔离检查。当前 P69 只做静态发布 gate，拒绝未冻结/unknown/null，允许路径仅合成 fixture。[evidence: ../docs/week3/data-route/20261009/144_evidence_sidecar_delivery_report.md; ../docs/week3/data-route/20261009/145_prepublication_gate_contract.md]

## P69—P70 最新接续（2026-10-09T05:23:33Z）

P69 研究池旁车包被 gate 拒绝并返回具体原因；当前 P70 只读审计 P65—P69 产物的互相定位、hash、失败保留和 private 隔离，不生成发布包。[evidence: ../docs/week3/data-route/20261009/146_prepublication_gate_report.md; ../docs/week3/data-route/20261009/147_research_delivery_audit_contract.md]

## P70—P71 最新接续（2026-10-09T05:34:36Z）

P70 索引已核对报告/产物/失败/状态/hash；当前 P71 只生成 research_pool_only 成果声明并强制列出限制与禁止表述，不发布或冻结数据。[evidence: ../docs/week3/data-route/20261009/148_research_delivery_audit_report.md; ../docs/week3/data-route/20261009/149_research_outcome_statement_contract.md]

## P72—P73 最新接续（2026-10-09T06:05:07Z）

P72 四条行为证据行没有形成正式一轴对照。当前 P73 只设计依赖/状态/可测控制配对和负对照，固定来源/切分/题面规模，不执行模型、不读private、不改旧标签。[evidence: ../docs/week3/data-route/20261009/151_behavior_backed_structure_rows_report.md; ../docs/week3/data-route/20261009/152_controlled_pair_design_contract.md]

## 当前覆盖说明（P74→P75）
用户要求防止过度评测、重心偏离，停止P71。P72机械一轴0不否定主A关联研究；C03原例每实现11/合计33；P73只有文本设计。P74两任务实际执行36/36，详155号及新summary。P75执行新混合版本，不重跑旧任务，不扩模型预算。

## 最新状态P75→P76（覆盖旧当前项）
新增四同家族候选/六独特公开输入/24任务记录/60solve，全部符合冻结锚点；不是60独立样本、自然项目需求及正式标签未确认。P76需求与公开源码/许可阅读已启动，按158号冻结新六输入；停止树扩量。旧P66/P70复制检查点不可当实际校验证据，纠正见experiments/d1_checkpoint_claim_clarification_20261009.md。

## 最新状态P76→P78
P76实际18solve/18通过，9组内关系符合；P77公开历史筛选选择confuse PR126，跨ConfigSource/Filename，保存parent/merge及非测试源码。P76一次上游公开测试匹配暴露已登记，不声称零暴露。P78六POSIX锚点、三参考18solve待执行；模型/人工/正式标签未涉及。


## P80—P81 最新阶段

P80恢复confuse PR126真实项目前后版本。commit API确认直接父 `8b69242b8facdd7d1f87113693ea72017d61a0ff`；父版本对三个新增入口均TypeError，合并版本源目录解析通过，真实诊断见 `experiments/d1_repository_feature_candidate_v1_20261009/actual_project_v1/real_feature_diagnostics.json`，报告166。P78手写POSIX适配器忠实性未知，不能计作项目证据。P81只复核 `task_spec.json` 的四个行为例与不泄漏约束，正式标签/split/model/human仍null/0，候选research_pool_only不可发布。


## P82 结构边界

PR126真实源码证据支持 source metadata→Filename.value 的跨文件数据链和对象级状态，行为例可执行；无全局状态证据，正式三轴与人工标签保持 null/0。P80—P82只形成一个研究池候选，不回答主A，不改initial20。后续必须解决多任务可比结构、人工冻结和总token模型比较，禁止用更多包装/门/候选数替代。

## P83—P91最新事实

P83真实confuse任务完整8/8，source-only5/8、core遗漏7/8；单模块替代8/8。全包13935/三模块11246输入超6500/8192；API上下文1982+已知正确patch1400=3382可容纳并严格复原三模块，非生成。固定多轮重发上下文累计8025/10004超6500，非所有拆分方法。P88真实TTLexpire任务完整5/5；仅清理返回0/5状态5/5，仅报告返回5/5状态1/5。P89发现生成器消费后观测掩盖清理时点；P90新条款接纳即时生成器、拒延迟清理，原任务和评分不改。所有本轮模型/API/人工0，正式标签/split null，原20题307记录/冻结限制不改。P91在experiments/d1_repository_generation_adapter_feasibility_v1_20261009/existing_interfaces_first_action.json有真实接口调查；下一步先制定适配计划并三审。

## P91—P95最新事实

P91六给定条件三个工作区21旧公开行为实际执行，三失败行为null；模拟transport5/模型0。P92 DLL expected8eeb51/actualac18a0身份不符，在模型请求前停止，未耗额度，旧约98/100保持、无新真实生成。P93一个原mixed输入证基类存储误拒公开相容委托，消费后底层可漏收延迟；P94另存P90需求的公开API评价，完整/委托5/5，仅报告/延迟1/5。20场景为五旧输入四组织，无新独立输入/正式任务/人工/模型。P95已定向提取公开读取清理路径，下一步先详尽计划与三审；不能把公开观察当物理全域证明。[evidence: ../docs/week3/data-route/20261009/184_repository_patch_entry_result_and_next_questions.md; ../docs/week3/data-route/20261009/186_real_probe_pre_request_failure_and_next_questions.md; ../docs/week3/data-route/20261009/188_state_ownership_counterexample_and_next_questions.md; ../docs/week3/data-route/20261009/190_public_cache_oracle_result_and_next_questions.md; experiments/d1_public_cleanup_observability_feasibility_v1_20261009/public_observation_paths_first_action.json]


## 当前宏观路线（覆盖历史当前项）

用户要求先审定宏观计划再执行；191号三轮顺序自审修订后，当前RESEARCH_PLAN为唯一执行路线。G1任务标准（45分钟只读/零新行为）→G2按具体缺口构建真实功能（至多调查8/新增4）→G3结构证据→G4条件式同预算比较→G5候选成果。下一G1尚未启动；P95停止自动接续，源调查证据与历史计划完整保留。本轮无新增行为/模型，题目/A/原20/11—9/标签与人工/约98预算不改。当前只开放零模型研究候选与边界分支；六题1seed按原M2需30—36调用，旧剩余额度不足、DLL不符/双审0，正式A实证仍未开启。[evidence: .research-state/RESEARCH_PLAN.md; ../docs/week3/data-route/20261009/191_d1_macro_plan_reviews.md; experiments/d1_macro_replan_20261009/review_completion.json]

## 宏观G1/G2当前恢复点（覆盖旧当前项）

G1只读两现有候选，无新增行为；cache物理时点/脚本文字缺口保留。G2 more游标与公开M03重复，父恢复失败；全根检索意外private/公开测试片段暴露登记，未用于构建/评分。PR142官方父/合并非测试源码153274字节/24文件；有限公开3场景×4组织12worker，父0/3入口缺失，合并/替代各3/3，优先级遗漏2/3。正式标签/split null，真实人工/模型0，主A关联未测。下一问题G2 boltons逆序JSONL，先198号三审后读来源，不恢复P95。[evidence: experiments/d1_G1_task_admission_v1_20261009/task_admission_and_gaps.json; experiments/d1_G2_more_itertools_cursor_v1_20261009/accidental_exposure.json; experiments/d1_G2_confuse_pr142_env_source_v1_20261009/stage_result.json; ../docs/week3/data-route/20261009/197_G2_env_source_result_and_next_question_audit.md]

## 第一轮G1—G5成果/宏观v2当前恢复点

第一轮G1—G5零模型路线已完成；两项有限confuse任务交付v2，一cache待解。208号宏观v2/局部三审完成，当前只接续PR440组生命周期一次G2扩展，先公开排重/官方父恢复；原预算继承，失败No-Go不自动搜新题。
G2新PR142三场景12worker，合并/独立组织3/3、优先级遗漏2/3；G3结构证据分层，三管理候选两来源、有限可用两项同confuse，cache強时点与脚本缺口保留，K2/K3未填。PR466官方未合并No-Go，元数据公开ioutils测试暴露保留。G4原策略一题5—6请求/两题10—12，旧约98/100/DLL/人类/冻结缺口阻止运行。G5 v1复制因research_controls缺LICENSE失败；对应官方父许可证恢复到独占v2、CLI/hash接线通过，旧语义不重跑。formal_labels/split null，真实人工0/新增模型0。[evidence: experiments/d1_G3_structure_evidence_v1_20261009/structure_records.json; experiments/d1_G4_pair_design_v1_20261009/paired_design_v2.json; experiments/d1_G5_candidate_delivery_v1_20261009/delivery_wiring_check.json; ../docs/week3/data-route/20261009/207_macro_cycle_result_and_next_question_audit.md; ../docs/week3/data-route/20261009/208_macro_extension_pr440_plan.md]

## PR440与流程纠正（覆盖旧当前项）

PR440 merged=true，父/合并非测试8文件236482字节，三个公开场景×四组织12worker：官方/独立3/3，父/延迟1/3；reducefunc在外层推进后保留归约值，无reducefunc保留父懒组。它补非缓存组生命周期义务，labels/split null、人工/模型0。G3 structure_records_v2为四管理候选/三来源、有限三项/cache待解，但未在本局部循环前完成三轮深挖与计划审查，标记事后证据，不冒称严格事前。G5 v3三任务合并包装因路径/manifest/evaluation冲突及hash时序缺陷超过两次修复，WITHDRAWN；稳定v2两confuse交付与PR440独立实验目录保留。下一工作只针对科学未知，先三轮问题挖掘和审查，不修v3。[evidence: experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/stage_result.json; experiments/d1_G3_structure_evidence_v1_20261009/structure_records_v2.json; data/processed/d1_actual_project_candidate_v3_20261009/WITHDRAWN.md; ../docs/week3/data-route/20261009/211_PR440_checkpoint_and_procedure_corrections.md]

## 当前科学结果与接续依赖

PR142/PR440各3场景12worker合24worker/6独特公开场景；新增两有限功能任务，不是模型成绩。四管理候选/三来源，有限可用三任务/两来源，cache待解。稳定v2交付两confuse加独立PR440 candidate；合并v3WITHDRAWN和G3事后时序纠正保留。跨候选共同观察维度只能用于筛选/协议，内部状态所有权/强物理时点/机制独立/全域等价/收益关联unknown；PR126副作用由未核验改unknown。214号三轮接续审查否决重复包装/静态门/两次模型探针；持续授权仍active，无实际后台模型/行为，下一工作须有新证据与先审计划。[evidence: experiments/d1_G3_structure_evidence_v1_20261009/comparability_matrix_v3_scope_clarification.json; ../docs/week3/data-route/20261009/214_comparability_result_and_next_question_audit.md; .research-state/RESEARCH_PLAN.md]

## 用户中断恢复点（覆盖旧当前项）

用户明确中断，D1研究及自动接续暂停。只读契约核对已完成：PR126直接YamlSource参数、PR142未显式调用前的自动加入、PR440默认回调有未独立观察条款；静态缺口不等于已证假通过。218号PR126最小反例计划仅完成第一轮可行性审查，第二/三轮未执行；未构造控制、未冻结/运行新行为，新增模型/行为/人工/下载均0。必须等用户明确恢复后，先完成剩余审查再决定执行；旧结果、候选与失败全部保留。
[evidence: experiments/d1_G3_contract_integrity_v1_20261009/contract_observation_audit.json; ../docs/week3/data-route/20261009/218_pr126_direct_entry_counterexample_plan.md]


## 2026-10-11恢复后的G3契约完整性小循环

用户已明确恢复D1。218号计划三轮审查完成并执行PR126直接YamlSource最小反例：控制旧8/8且新0/1，完整/独立组织各1/1；该结果证明旧评价可误收明示API不完整实现。源码映射把新增锚点定为接口验收条件，结构字段仍unknown。222号三轮接续审核否决PR142/PR440同类重复补测；当前下一高信息工作依赖新人工审查或完整模型身份/预算，没有后台实验。
[evidence: ../docs/week3/data-route/20261011/223_contract_integrity_cycle_result.md; ../docs/week3/data-route/20261011/222_after_api_mapping_next_question_audit.md]
## 2026-10-11 G4 本地 Ollama 阶段

按既定 `paired_design_v2.json`，用户授权本地有成本运行；PR126/PR142各一seed，M0/M2每臂6500服务端token。v1/v2各6次请求，共12次；v1四臂超预算，v2 M0预算内但严格hunk错位，M2分别计划解析失败与组件超预算。对M0格式剥离后仍hunk错位，四臂无完整候选，行为分子未定义，不能计算主A效果。[evidence: ../docs/week3/data-route/20261011/228_g4_local_ollama_result.md; ../codeprm-reproduction/experiments/d1_G4_local_ollama_real_project_pair_v1_20261011/; ../codeprm-reproduction/experiments/d1_G4_local_ollama_real_project_pair_v2_20261011/]

阶段审查：G4资源边界目标完成，失败分母和服务端计量齐全；状态为complete with boundary。方向审查：否决同模型同上下文第三次重试、格式包装和后处理评分，转原计划G5；若改变总token、模型或补丁接口，须另立计划并三审。[evidence: ../docs/week3/data-route/20261011/229_g4_next_question_audit.md]

## 2026-10-11 G5 阶段性交付

真实项目候选、PR126评价器契约盲点和G4本地生成资源边界已合成一份研究结果；研究池可复查，但正式labels/split/人工0，主A收益未测。当前暂以适用边界交付，若恢复主A必须先冻结新的总token、模型身份或补丁接口并重新三审。[evidence: ../docs/week3/data-route/20261011/230_g5_d1_boundary_synthesis.md]

## 2026-10-11 G4 计量纠正

撤回旧“v1/v2在6500预算下不可执行”和“12次请求”表述：实际10次请求，旧运行器未做事前预算预检。第三版加入Qwen tokenizer ChatML预检，服务端计数逐次一致；4次请求发送、1次组件预检拒绝，四臂仍无完整候选。[evidence: ../docs/week3/data-route/20261011/231_g4_preflight_correction.md; ../codeprm-reproduction/experiments/d1_G4_local_ollama_real_project_pair_v3_20261011/]

## 2026-10-11 G4 完整 API 上下文批次

修复固定行段遗漏后，按完整 AST API 上下文执行三题 M0/M2；共11次请求、已知23380 token、服务端与本地ChatML计数一致。M0三题均补丁入口失败，M2三题均在组装前预算拒绝；无候选、无行为分子，主A未测。[evidence: ../docs/week3/data-route/20261011/232_g4_symbol_context_result.md; ../codeprm-reproduction/experiments/d1_G4_symbol_context_pair_v1_20261011/]

G5最终纠正版取代230号旧合成的过强资源表述；仅保留严格v3与完整API批次能支持的窄结论，旧输出和纠正链完整保留。[evidence: ../docs/week3/data-route/20261011/233_g5_d1_final_corrected_synthesis.md]

## 2026-10-11 中断保存
- 时间：2026-10-11T07:46:32.0506586Z
- 用户明确中断当前D1接续。
- 当前问题：区分完整API上下文批次的M0补丁失败究竟是运输格式还是代码/语义错误。
- 已完成：读取原始批次摘要与三份M0 normalized.patch；已开始三轮问题审查，但尚未执行审查脚本或任何新模型/行为调用。
- 恢复动作：恢复后先完成该问题的三轮实质审查；只有审查通过才运行一次只读归因分析。宏观计划与原始数据保持不变。

