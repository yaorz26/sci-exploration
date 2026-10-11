# 项目研究状态

最后更新：2026-10-08T13:06:56Z
状态：active（P30完成，P31F03纯层合并归并研究已启动；人工0，正式模型评测未启动）

## 当前目标与权限

- 用户确认题目“面向项目功能级代码生成的任务分解评测数据集构建与适用边界研究”、主问题A：等预算下阶段依赖、共享状态、独立可测程度与拆分相对整体收益的关系；数据集也为拟成果。常规构建、审计和预算内诊断自主推进，重大方向、付费、训练/RL和发布另行决定。[evidence: ../docs/week3/data-route/20261008/05_selfbuild_protocol.md; ../docs/week3/data-route/20261008/18_question_A_protocol_v0.2.md]
- P12已区分global六题不同约束：552/552关系、534有限枚举+18锚点、2208求值，实体粒度/聚合观察影响解释；不是全域或模型效应。P13随后完成组合义务检验。[evidence: ../docs/week3/data-route/20261008/30_behavior_coupling_report.md; ../docs/week3/data-route/20261008/31_local_contract_and_composition_contract.md]
- P13两题4正确结构全过、4组件不变的组合缺陷均被识别、24局部锚点72/72求值过；任务侧行为机会与计划侧连接/状态义务应分开。P14随后完成零调用输入情景计量。[evidence: ../docs/week3/data-route/20261008/32_local_contract_and_composition_report.md; ../docs/week3/data-route/20261008/33_budget_crowding_contract.md]

- P14输入情景200/760提示，短代码两helper/三helper原排版输入中位2606/3517.5；同字段排版配对节省中位544。无模型，余额为构造上界；P15检查来源/家族支撑。[evidence: ../docs/week3/data-route/20261008/34_budget_crowding_report.md; ../docs/week3/data-route/20261008/35_structure_support_contract.md]

- P15附加20题候选证据，8已测/12未测、2计划边界、80成本情景；容量4题/全局顺序2题各仅1来源1相关组件，8题矩阵7列秩5。P16检验另一来源的真实功能边界。[evidence: ../docs/week3/data-route/20261008/36_structure_support_report.md; ../docs/week3/data-route/20261008/37_cross_source_cache_contract.md]

- P16扩展池E_B07第二来源容量证据：10/10手算+3280/3280序列、6580求值、4人工缺陷识别；读观察会影响统计/顺序。仍相关缓存家族，原20题不变；P17转公开保序功能。[evidence: ../docs/week3/data-route/20261008/38_cross_source_cache_report.md; ../docs/week3/data-route/20261008/39_cross_source_order_contract.md]

- P17扩展池E_M06：6手算/3110输入/71关系全过、6516求值，4人工缺陷检出。全局保序可与规范实体有限隔离共存；输入流历史不同于操作历史；P18已提取复核反例。[evidence: ../docs/week3/data-route/20261008/40_cross_source_order_report.md; experiments/d1_granularity_review_v1_20261008/evidence_extraction.json]

- P18区分粒度选择/契约不兼容/同问题分歧，v1证据编号混入问题域已在v2修订、原输出保留；8路径仅程序口径检查，人工0/未算κ。P19检验已有合法文本可容纳性。[evidence: ../docs/week3/data-route/20261008/42_granularity_review_report.md; ../docs/week3/data-route/20261008/43_valid_text_budget_contract.md]

- P19两份给定正确四阶段文本合计3350/3758，低于6500；旧4响应API输出各比文本多1，不改真实计费。P20检验同任务的不同状态所有权/共享边界。[evidence: ../docs/week3/data-route/20261008/44_valid_text_budget_report.md; ../docs/week3/data-route/20261008/45_plan_state_distribution_contract.md]

- P20同C03/两个helper的三结构原案例33/33、2343序列/7029求值均过，状态可留入口/封装helper/跨helper传递；非模型收益或通用状态分析。P21已登记退化输出与不可测分母。[evidence: ../docs/week3/data-route/20261008/46_plan_state_distribution_report.md; ../docs/week3/data-route/20261008/47_relation_vacuity_contract.md]

- P21零值错误程序相等103/103、绝对0/210、阳性0/2，始终抛错105不可测；执行/正确/关系分开，不倒推P12参考关系错误。P22已登记跨来源支撑审查。[evidence: ../docs/week3/data-route/20261008/48_relation_vacuity_report.md; ../docs/week3/data-route/20261008/49_expansion_support_contract.md]

- P22加入两扩展后证据出现矩阵秩5→7，单加各6；容量仍贴合缓存关联群，严格操作历史仍秩6。原数据不改，P23检验12未测公开任务。[evidence: ../docs/week3/data-route/20261008/50_expansion_support_report.md; ../docs/week3/data-route/20261008/51_unmeasured_task_screen_contract.md]

- P23原未测C05/M05新关系26/26、29输入/58求值：缓存群含无历史逐对判断，M05无状态却有跨列有效域依赖。未测其余10仍未知，P24已冻结手算候选。[evidence: ../docs/week3/data-route/20261008/53_unmeasured_task_screen_report.md; ../docs/week3/data-route/20261008/54_alignment_composition_contract.md]

- P24两个相同纯组件的合法次序7锚点/640输入全过，局部18/18；组合误取索引前L的缺陷58/640，义务为有效行集合非唯一次序。P25登记预期拒绝的投影适用性。[evidence: ../docs/week3/data-route/20261008/55_alignment_composition_report.md; ../docs/week3/data-route/20261008/56_expected_rejection_contract.md]

- P25 F04五输入10/10符合，其中两预期ValueError/四求值；name关系2可观察/3不可观察，拒绝不算任意失败、相同拒绝不提供name值。P26已登记保存反例判别集。[evidence: ../docs/week3/data-route/20261008/57_expected_rejection_report.md; ../docs/week3/data-route/20261008/58_measurement_record_contract.md]

- P26附件11有限证据/9未测、两候选另表655旧关系/三计划任务；M05/F04四编码相同，v1同实体问题不适用混投影缺值保留/v2修订。P27新入口表示已登记。[evidence: ../docs/week3/data-route/20261008/59_measurement_record_report.md; ../docs/week3/data-route/20261008/60_method_gate_contract.md]

- P27真实门槛M0接受6/6、M2入口4/6，参数dict注解拒绝两份而返回注解允许；四新代码公开8/8，非模型发生率。P28离线候选修订已登记。[evidence: ../docs/week3/data-route/20261008/61_method_gate_report.md; ../docs/week3/data-route/20261008/62_entry_annotation_gate_contract.md]

- P28候选入口6正确表示接受/7调用形状控制拒绝；P9helper2仍严格拒绝，旧0/1、1850保持，正式pipeline不改。P29已登记失败观察分母。[evidence: ../docs/week3/data-route/20261008/63_entry_annotation_gate_report.md; ../docs/week3/data-route/20261008/64_failure_observation_contract.md]

- P29真实P9主两臂0/1保留，但行为实际14对0，M2占位14不可作已测0%；完整方案缺失属性未知，640/1850不改。P30候选增补已登记。[evidence: ../docs/week3/data-route/20261008/65_failure_observation_report.md; ../docs/week3/data-route/20261008/66_question_A_protocol_update_contract.md]

- P30独立v0.3候选由六保存反例增补层次/共同外部入口，旧协议保留、正式数值/人工未冻结。P31已登记纯二元合并可能丢全候选类型证据。[evidence: ../docs/week3/data-route/20261008/67_question_A_protocol_v0.3_candidate.md; ../docs/week3/data-route/20261008/68_layered_merge_reduction_contract.md]

## 数据与人工复核

- initial20 v5为4来源20题、307用例（40公开/267隐藏）、11开发/9储备；20/20自动门槛、参考3次及另一结构实现通过、40/40有限语义缺陷被识别，原8题32文件逐字保留。固定commit及BSD/MIT许可，不是完整项目集成或正式冻结。[evidence: data/processed/d1_project_initial20_v5_20261008/manifest.json; experiments/d1_project_initial20_mutants_v5_20261008/summary.json; experiments/d1_project_initial20_v5_20261008/prototype8_equivalence.json]
- 结构v0.2仍作者初标：无跨操作12/有8，全局6/分区2；独立可测yes8/partial7/no5，真实人工0。有限GLM仅4新题复核；Qwen7B标签失真不采用，不称可靠真值。[evidence: data/processed/d1_project_initial20_v5_20261008/manifest.json; experiments/d1_project_initial20_review_20261008/review_dispositions.json]
- v3仅交付reviewer_only.zip，管理映射独立；21/21回收/κ/交付检查通过。合成测试不算人工，真实双审0，未发送材料；程序不能证明声明真实或需求无法猜来源。[evidence: experiments/d1_blind_annotation20_v3_20261008/README.md; experiments/d1_review_pipeline_selfcheck_20261008.json]
- 保持boltons/cachetools开发、more-itertools/confuse储备隔离。20细分家族形成15显式关联组件，不是独立样本数。来源×结构相关限制解释和外推，但不自动使同题配对无效；问题A为关联，不新增因果目标或重排储备。[evidence: experiments/d1_family_link_audit_v1_20261008.json; ../docs/week3/data-route/20261008/18_question_A_protocol_v0.2.md]

## 成本、负结果与修正

- 历史五题成本探针：qwen2.5-coder:7b Q4_K_M、seed20261008、temperature0.2、ctx8192、每题每臂6500生成token上限。M0/M2整题均0/5；生成token为4903/24179（4.93倍）；含预检全部token为8004/45301（5.66倍）。56调用=28预检/28生成，初轮24调用更正12/12，旧10/14有误。预检单列非严格总预算效果确认。[evidence: experiments/d1_cost_allin_audit_v1_20261008.json; ../docs/week3/data-route/20261008/17_review_delivery_and_protocol_revision.md]
- M2两题生成/组装失败；旧执行器未保存完整逐调用prompt/response，失败helper/entry原文缺失，不能由异常进一步推断根因。8成功候选哈希核对通过。旧4题诊断v1/v2均0/4，输入输出不等成本；小样本公开中英文差异不证语言效应。截至P7约91/100；P8/P9新增7调用3173token，当前约98/100。[evidence: experiments/d1_cost_allin_audit_v1_20261008.json; ../docs/week3/data-route/20261008/08_development_probe_report.md]
- 历史题意、导入、布尔评分、分号、字典子类、打印污染等失败保留；评分1与1.0相等但布尔区分，输入类型和键顺序保持；2400补充差分不计307正式用例。旧版细节见快照/主题记忆。[evidence: ../docs/week3/data-route/20261008/11_initial20_quality_and_stage_review.md; snapshots/PROJECT_STATE_before_P7_20261008.md]

## 相关工作与工具准备

- 两篇官方HTML成功获取并定向阅读方法，不称通读/穷尽。FEA-Bench提供新增组件接口；FeatureBench有从零实现及接口消融。D1贡献收窄为内部自由拆法、行为结构证据和总预算关联比较，不以项目来源/独立实现主张首创；污染未知。[evidence: experiments/d1_literature_fulltext_v1_20261008/method_evidence.json; ../docs/week3/data-route/20261008/17_review_delivery_and_protocol_revision.md]
- P7历史模拟12/12通过；P8原生词表与API两次81输入吻合，P9四请求计数全吻合，不再生成预检。全链路合成v2 13/13，真实请求/冻结/失败42/42复核。原生词表只加载vocab，与本机llama.cpp build631109b34相配；逻辑token包括缓存输入，不等价GPU算量。[evidence: experiments/d1_allin_pipeline_simulation_v2_20261008/summary.json; experiments/d1_tokenizer_integration_v1_20261008/final_integrity_and_failure_audit.json; ../docs/week3/data-route/20261008/22_tokenizer_integration_report.md]

## 最新工程结果与候选成果

- P8 B03 M0短输出128截断失败保留；P9 B03两臂同6500总token上限、seed20261008/temp0.2/ctx8192、Qwen7B Q4_K_M，无预检，实际4调用2490token。M0 640公开0/2、隐藏5/12、整题0/1；M2 1850在第二helper重定义第一helper被拒绝、整题0/1，无行为评分。真实可解析候选的冻结评分路径已执行，不说明题答对或拆分边界；P8/P9总7调用3173token。[evidence: experiments/d1_allin_native_pair_b03_v1_20261008/summary.json; ../docs/week3/data-route/20261008/24_native_pair_smoke_report.md]
- 本地候选成果包v2：20题、307用例、287原始文件、ZIP290成员，逐文件与许可哈希核对、8/8检查通过。人工0、未冻结未发布；含private仅管理端，盲审只交reviewer_only.zip。v1缓存409文件失败保留。[evidence: experiments/d1_candidate_delivery_v2_20261008/delivery_verification_final.json; ../docs/week3/data-route/20261008/26_candidate_delivery_report.md]

- P11查实v2参考实现依赖工作区缺库；v4补4固定commit上游库及PyYAML6.0.3纯Python/许可，285/287原文件不变，2路径补丁原字节另存，题面/测试/切分不改。Windows11/Python3.13.7的-I -S隔离40/40运行、614/614案例执行、14/14复核通过；614非新案例，机器同作者复核。[evidence: experiments/d1_portability_v4_isolation_20261008/summary.json; experiments/d1_candidate_delivery_v4_portable_20261008/portable_delivery_verification_v2.json; ../docs/week3/data-route/20261008/28_portability_and_contract_report.md]
- 307原记录=40公开+267隐藏保留；B02 public_2/hidden_1同输入期望，实际不同输入306、隐藏未公开266，不影响整题全部通过但不作新隐藏证据。6题39条关键行为对照非全覆盖，结构仍作者初标、人工0；本轮模型0，累计约98/100。[evidence: experiments/d1_contract_traceability6_v1_20261008/traceability_private.json; experiments/d1_candidate_delivery_v4_portable_20261008/DELIVERY_NOTES.md]

## 下一步与红线


- 当前交付采用可迁移v4，v2保留为存储完整性历史；当前P31检验F03纯合并逐对归并与全候选门槛，按目标计划接续；全量契约/输入域仍为研究队列，正式冻结时处理重复项，仍需真实双审和协议/标签冻结。停止模型扩量，不把运行通过或有限契约对照当问题A答案；不进行正式储备生成。[evidence: ../docs/week3/data-route/20261008/28_portability_and_contract_report.md; ../docs/week3/data-route/20261008/18_question_A_protocol_v0.2.md]
- private不进提示/选择/储备调参，已见开发不冒称未见确认；冻结输出不覆盖；保留负结果/缺失/协议修正；不训练、不RL、不发布、不采购。[evidence: ../docs/week3/data-route/20261008/05_selfbuild_protocol.md]

## 既有分支长期结论

- ClassEval G2收束：24题、每臂2候选，M0/M1/M2为7/24、8/24、7/24；双零M0/M2为16/24=66.7%，三臂全零15/24=62.5%，第二候选未救回；API固定不能测自由拆法，旧五项κ0.436不足支撑可靠分组。D1不改旧负结果。[evidence: experiments/classeval_wp6_v2/wp6_v2_manifest.json; ../docs/week3/data-route/20260929/12_wp6_v2_report.md]
- APPS本地top-down三阶段失败；helper-first已训练，A/B为5/30、7/30，合并12/60对首候选7/60、随机7.2/60、池上限14/60；净增5，bootstrap区间[0.0266666667,0.1433333333]四项冻结门槛过，6胜1负p=0.125不称强显著。限custom split、不是官方成绩/完整复现；ClassEval未训练，RL从未启动且独立No-Go。[evidence: data/processed/funprm_label_calibration_20260924/confirmation_ab_final_gate_20260926.json; experiments/funprm_label_calibration_20260924/confirmation_ab_final_gate_audit_20260926.json; reports/funprm_helperfirst_scale_confirmation_ab_20260926.md]
