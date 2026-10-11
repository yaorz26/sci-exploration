# 项目研究状态

最后更新：2026-10-08T10:09:34Z
状态：active（D1候选成果包、原生计量与冻结评分烟测完成；人工0，正式冻结/边界评测/发布未完成；当前P11隔离运行与交付依赖复核中）

## 当前目标与权限

- 用户确认题目“面向项目功能级代码生成的任务分解评测数据集构建与适用边界研究”、主问题A：等预算下阶段依赖、共享状态、独立可测程度与拆分相对整体收益的关系；数据集也为拟成果。常规构建、审计和预算内诊断自主推进，重大方向、付费、训练/RL和发布另行决定。[evidence: ../docs/week3/data-route/20261008/05_selfbuild_protocol.md; ../docs/week3/data-route/20261008/18_question_A_protocol_v0.2.md]

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

## 下一步与红线

- P11正在隔离运行候选ZIP，检查管理端是否借用原工作区上游依赖；若失败仅修复新交付版本，不改需求/案例/切分/旧结果，模型0。[evidence: ../docs/week3/data-route/20261008/27_portability_and_contract_audit.md]

- 数据卡、来源许可、哈希与v2候选包已可归档；后续正式冻结仍需真实双审、需求缺陷处理及污染/新颖性复核。停止模型扩量，不把候选完整性或工程烟测当问题A答案；不进行正式储备生成。[evidence: ../docs/week3/data-route/20261008/26_candidate_delivery_report.md; ../docs/week3/data-route/20261008/18_question_A_protocol_v0.2.md]
- private不进提示/选择/储备调参，已见开发不冒称未见确认；冻结输出不覆盖；保留负结果/缺失/协议修正；不训练、不RL、不发布、不采购。[evidence: ../docs/week3/data-route/20261008/05_selfbuild_protocol.md]

## 既有分支长期结论

- ClassEval G2收束：24题、每臂2候选，M0/M1/M2为7/24、8/24、7/24；双零M0/M2为16/24=66.7%，三臂全零15/24=62.5%，第二候选未救回；API固定不能测自由拆法，旧五项κ0.436不足支撑可靠分组。D1不改旧负结果。[evidence: experiments/classeval_wp6_v2/wp6_v2_manifest.json; ../docs/week3/data-route/20260929/12_wp6_v2_report.md]
- APPS本地top-down三阶段失败；helper-first已训练，A/B为5/30、7/30，合并12/60对首候选7/60、随机7.2/60、池上限14/60；净增5，bootstrap区间[0.0266666667,0.1433333333]四项冻结门槛过，6胜1负p=0.125不称强显著。限custom split、不是官方成绩/完整复现；ClassEval未训练，RL从未启动且独立No-Go。[evidence: data/processed/funprm_label_calibration_20260924/confirmation_ab_final_gate_20260926.json; experiments/funprm_label_calibration_20260924/confirmation_ab_final_gate_audit_20260926.json; reports/funprm_helperfirst_scale_confirmation_ab_20260926.md]
