# 项目研究状态

最后更新：2026-10-08T09:06:50Z
状态：active（D1复核前置审计完成；等待人工双审，正式冻结/边界研究未完成）

## 当前契约与完成范围

- 用户确认题目“面向项目功能级代码生成的任务分解评测数据集构建与适用边界研究”，以问题A为主：等预算下，阶段依赖、共享状态、独立可测程度与拆分相对整体收益的关系；数据集也作为拟成果。常规构建/检查和预算内本地试跑已授权，重大方向才由用户决定。[evidence: ../docs/week3/data-route/20261008/05_selfbuild_protocol.md]
- D1-P1通过：4来源固定提交、BSD-3-Clause/MIT、下载686167字节。首批8题v5候选原型已构建：151案例（16公开/135隐藏）；参考重复3次、不同内部结构实现通过；16个具体语义缺陷被识别；85上游测试及18子测试通过。这是首批历史原型；第二批已达20题候选量，不把自动通过当最终质量合格。[evidence: data/processed/d1_project_prototype8_v5_20261008/manifest.json; experiments/d1_project_prototype8_mutants_v4_20261008/summary.json; experiments/d1_upstream_tests_20261008/summary.json]
- 有限GLM自动审查发现B02返回值歧义并修正；7B把缓存也标无状态，复核不可靠，不采用其标签。没有独立人工真值，也没有可靠量表一致性结论。原型只限定solve入口，评分不访问内部helper。[evidence: ../docs/week3/data-route/20261008/07_prototype_quality_and_review.md; experiments/d1_project_prototype8_v4_20261008/external_contract_audit.json]
- 版本失败均保留：v1空输入/配置输入域冲突；v2漏测contains刷新顺序；v3题面poplast歧义；v5改公开示例为直接output；后续评分器修正候选打印污染JSON通道。修复后16项参考/另一实现复查通过；用例与成员不因模型结果改变。[evidence: ../docs/week3/data-route/20261008/07_prototype_quality_and_review.md; experiments/d1_project_prototype8_v5_20261008/v4_case_equivalence.json; experiments/d1_project_development_pilot_v2_20261008/posthoc_evaluation_audit_stdout_fix.json]

## D1相关工作与成本探针

- 直接核对FEA-Bench与FeatureBench摘要/README/许可：前者83仓库增量功能、单元测试、仓库级补丁；后者200任务、24仓库、3825环境、依赖图驱动的agent功能开发。D1只主张固定来源上的外部solve功能契约、结构条件与拆分对照，检索不完整，不称首个。[evidence: ../docs/week3/data-route/20261008/13_related_work_and_costed_pilot_report.md; experiments/d1_literature_recon_20261008/source_matrix.json]
- 成本探针B04/C03、Qwen2.5-Coder:7b Q4_K_M、seed20261008、temperature0.2、ctx8192、每题每臂6500生成token预算，共24 API调用（预检10/生成14）；M0实际2080 token，M2 11426（约5.5倍），整题0/2对0/2。仅成本/失败形态诊断；本阶段新增Qwen API调用29，累计约59/100。[evidence: ../docs/week3/data-route/20261008/13_related_work_and_costed_pilot_report.md; experiments/d1_costed_pilot_b04_c03_v1_20261008/summary.json; experiments/d1_costed_pilot_b04_c03_v1_20261008/budget_audit.json]
- `num_predict=0`未停止生成，排除为正式计量；单token预检有效但增加调用。下一步先保留成本统计与人工复核，不直接扩大正式确认。

## D1成本协议三题扩展

- v2预先选择B03简单转换、B05多环节编辑、C04实例共享状态；qwen2.5-coder:7b、seed20261008、temperature0.2、ctx8192、每题每臂6500实际生成token。32次API调用（预检16/生成16），墙钟73.67秒；M0实际生成2823 token，M2 12753（约4.52倍）。M0公开2/6、隐藏14/32，M2可评分部分公开1/2、隐藏10/12，另2题生成阶段冻结函数接口失败；两臂整题均0/3。[evidence: experiments/d1_costed_pilot_b03_b05_c04_v1_20261008/summary.json; experiments/d1_costed_pilot_b03_b05_c04_v1_20261008/stratified_summary.json]
- 失败分类只记录评分器可观察类别：M0有IndexError与行为不匹配，M2有2次生成/组装失败；不能把这些类别直接当作算法根因。[evidence: experiments/d1_costed_pilot_b03_b05_c04_v1_20261008/failure_taxonomy.json]
- 阶段复盘：成本流程可执行，但五题合并整题通过仍为M0/M2各0/5，不能回答主问题A；停止同配置扩量，优先人工结构真值、来源/新颖性核对和正式总成本协议。[evidence: ../docs/week3/data-route/20261008/13_related_work_and_costed_pilot_report.md]
## D1复核前置审计

- 零生成审计通过盲审包隔离和两轮成本账本重算：20个盲号唯一、空表未填、requirements未含来源/任务标识；B04/C03的24次和B03/B05/C04的32次账本均能由prompt_eval_count+eval_count重算。[evidence: experiments/d1_freeze_readiness_audit_v1_20261008.json; ../docs/week3/data-route/20261008/16_freeze_readiness_report.md]
- 关键限制：development/reserve与仓库来源完全重合（boltons/cachetools开发，more-itertools/confuse储备），20个功能家族各1题；当前切分不能支持结构因素因果比较。结构标签仍是单人初标，人工判定0。[evidence: experiments/d1_freeze_readiness_audit_v1_20261008.json; ../docs/week3/data-route/20261008/15_formal_evaluation_protocol_draft.md]
- P6阶段状态revise：机器前置审计和反向审计完成，但既有探针未把预检计入严格总预算；先完成人工双审、来源×结构×切分覆盖重做和正式总预算烟测；在线检索入口本轮两次HTTP500，未新增一手材料；不新增模型生成、训练或RL。[evidence: ../docs/week3/data-route/20261008/14_freeze_readiness_phase_contract.md; ../docs/week3/data-route/20261008/16_freeze_readiness_report.md]
## 当前二十题候选与复核缺口

- 当前initial20 v5：4来源20题，307案例（40公开267隐藏），开发11/储备9；自动门槛20/20，参考重复3次及另一结构实现全过，40/40有限语义缺陷识别。原8题需求/测试32文件逐字保留，不按模型成绩筛题。287文件及来源哈希完整。[evidence: data/processed/d1_project_initial20_v5_20261008/manifest.json; experiments/d1_project_initial20_v5_20261008/integrity_audit.json; experiments/d1_project_initial20_v5_20261008/prototype8_equivalence.json; experiments/d1_project_initial20_mutants_v5_20261008/summary.json]
- 第二批失败版本均保留：v1错误模块导入；v2分号编码细节遗漏与布尔评分过宽；v3字典子类未JSON规范化误报；v4自动全过；v5有限复核后澄清并补2例。评分现布尔与数值分开、数值1与1.0相等、输入内容/类型/键顺序保持；8个评分边界反例通过。2400补充差分无分歧，不计307正式用例。[evidence: ../docs/week3/data-route/20261008/11_initial20_quality_and_stage_review.md; experiments/d1_scoring_contract_v2_20261008/summary.json; experiments/d1_expansion_differential_v1_20261008/summary.json]
- 结构尺度v0.2依据外部行为：预标无跨操作12/有8（全局6/分区2），独立可测8/7/5；仍单人初标。GLM12题初审180秒超时、缩至4题完成，未给初标/隐藏。20题盲审包v2已备，人工判定0。数据只做项目来源的独立功能，不评完整仓库集成，只有4轻量来源及关联家族。[evidence: ../docs/week3/data-route/20261008/10_expansion_protocol_and_structure_schema.md; experiments/d1_project_initial20_review_20261008/review_dispositions.json; experiments/d1_blind_annotation20_v2_20261008/README.md]

## 开发诊断结果与解释边界

- 4开发题，模型qwen2.5-coder:7b Q4_K_M、基础seed20261008、temperature0.2、ctx8192；每臂单候选、输出可分配上限4096，先全部候选冻结再评分。v1调用8，M0/M2均0/4且M2全是计划解析失败；v2调用17，均0/4且M2生成失败2/4、另2题组装后行为失败；修复评分器后仍0/4。仅工程探针，不是正式确认或适用边界结论。[evidence: experiments/d1_project_development_pilot_v1_20261008/summary.json; experiments/d1_project_development_pilot_v2_20261008/summary.json; experiments/d1_project_development_pilot_v2_20261008/posthoc_evaluation_audit_stdout_fix.json]
- v2实际成本：M0输入2540+输出1586=4126token，4调用、36.64秒；M2输入11803+输出1874=13677token，13调用、43.16秒。相同输出上限不等于等总成本；helper数量2--3是方法配置，不是数据要求。[evidence: ../docs/week3/data-route/20261008/08_development_probe_report.md]
- B01两次公开提示诊断：修复打印污染后中文纯文本0/2、英文纯文本2/2，仅各1候选、两个公开例子；未评其隐藏，不证明语言效应。原错误结果保留。合计本地调用30/100（审查3+v1 8+v2 17+诊断2）；均已结束。[evidence: experiments/d1_evaluator_stdout_fix_20261008/summary.json; ../docs/week3/data-route/20261008/08_development_probe_report.md]

## 下一步与红线

- 阶段审查：已达到20题候选量和自动门槛，正式冻结仍revise；相关工作、预检计量和三题分层成本探针已完成。停止同配置生成，下一步转向20题独立人工复核、来源/新颖性核对和正式总成本协议，再决定是否进入边界评测。候选目录有部分合并或收窄，不能把目录项数当完成题数。[evidence: ../docs/week3/data-route/20261008/11_initial20_quality_and_stage_review.md; ../docs/week3/data-route/20261008/13_related_work_and_costed_pilot_report.md]
- 开发boltons/cachetools、储备more-itertools/confuse按仓库隔离；储备只验参考质量，未生成/评分被测模型候选。缓存同家族、来源/题型混杂、部分工具函数偏小、污染未知、新颖性复核未完成。结构定义/人工真值/总成本协议仍待补，不宣称数据集完整冻结或通用边界。[evidence: ../docs/week3/data-route/20261008/06_question_A_measurement_design.md; ../docs/week3/data-route/20261008/09_dataset_card_and_expansion_candidates.md]
- private不进提示/选择/储备调参；不覆盖冻结输出，不将已见开发题当未见确认题；先评测，不训练、不RL、不发布；新增付费资源与重大方向需另行决定。[evidence: ../docs/week3/data-route/20261008/05_selfbuild_protocol.md]

## 既有分支长期结论

- ClassEval G2收束：WP6 v2为24题×每臂2候选，M0/M1/M2首候选及池上限7/24、8/24、7/24；双零16/24=66.7%只指M0/M2，三臂全零15/24=62.5%；第二候选没救新题。API固定使其不能测自由拆法，旧五项判据κ=0.436不足以可靠分组。D1不改旧负结果。[evidence: experiments/classeval_wp6_v2/wp6_v2_manifest.json; ../docs/week3/data-route/20260929/12_wp6_v2_report.md; ../docs/week3/data-route/20260929/10_g2_decision.md]
- APPS本地top-down三阶段失败；helper-first已训练且A/B为5/30、7/30，合并12/60对首候选7/60、随机7.2/60、池上限14/60；净增5，bootstrap区间[0.0266666667,0.1433333333]，四项冻结门槛通过；6胜1负双侧p=0.125，不称强统计显著。ClassEval未训练，RL未启动且独立No-Go；旧输出溢出、字段误读和关机失败保留。结论限custom split，非官方成绩或完整论文复现。[evidence: data/processed/funprm_label_calibration_20260924/confirmation_ab_final_gate_20260926.json; experiments/funprm_label_calibration_20260924/confirmation_ab_final_gate_audit_20260926.json; reports/funprm_helperfirst_scale_confirmation_ab_20260926.md]
