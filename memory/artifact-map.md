# 重要文件地图

## 人类阅读入口

- `docs/week3/10.8_D1研究问题参考表述与数据集定位.md`：D1 用户方向决定、五种研究问题表述、推荐主线、结构自由的评测需求与数据集成果边界；题目与问题A已确认；正式评测参数未冻结。
- `README.md`：工作区总入口。
- `docs/README.md`：docs 目录规则与阅读入口。**2026-09-28 起的归档规则**：`docs/basic-require/` 只允许人类用户修改和增添（AI 不得写入），当前仅存 `基本情况.md`、`文献.md`、`9.27.md`；AI 产出的 md 按创建日期归入 `docs/week1/`（≤2026-09-13）、`docs/week2/`（2026-09-14 至 09-27）、`docs/week3/`（≥2026-09-28）；docs 根目录只保留 `README.md`。
- `docs/week2/研究总览_当前结论与后续方向.md`：当前收获、问题和后续路线（2026-09-28 由 docs 根目录移入 week2）。
- `docs/week2/9.26_9.14以来进展思路与待定问题.md`：面向导师的汇报材料第一份（9.14 以来进展、思路三次改写、待导师决定的六个问题）。
- `docs/basic-require/9.27.md`：9.27 讨论摘要（关键词式：做了什么 / 进展 / 遇到的问题 / 原因 / 解决思路 / 后续规划）。
- `docs/week2/9.27思路演进与方向决策.md`：面向导师的汇报材料第二份（思路演进五步、研究问题重述"拆分在什么任务条件下成立"、三方向决策表 A/B/C、追问预案）。
- `docs/week3/9.28数据集路线_分步执行与Agent移交文档.md`：导师反馈后的数据路线**当前执行版 v5**（2026-09-28 修正 4 处内部不一致）；含 WP0--WP6、G1/G2 门槛、公开数据与自建数据分支、三层负对照来源、扩大确认资源闭环、验收标准和 Agent 派单/移交模板。
- `docs/week3/计划审核/`（2026-09-28 建立，目录）：存放 9.28 数据集路线"计划审核"过程的全部文件；正式结果不在其中。**位置更正**：最初被误建在工作区根目录 `计划审核中/`，经用户指正后整体移入 `docs/week3/计划审核/`（源目录已删除）。目录下 `00_目录说明.md` 说明用途、文件清单与阅读顺序。
- `docs/week3/计划审核/9.28数据集路线执行文档_审阅意见.md`：对该执行文档的独立审阅（可行性 / 价值与意义 / 能否产出可靠结果），含 10 条最小改动清单、5 项待用户或导师拍板事项，以及本机实测事实附录（Docker 守护进程未运行、WSL Ubuntu-22.04、C 盘剩 38.8 GiB / D 盘剩 120.3 GiB）。
- `docs/week3/计划审核/9.28数据集路线审阅意见_批判性采纳记录.md`：当前采纳记录 v2；逐条记录首轮审阅与复核意见的采纳、改写、边界和 v3 落点，并更正 `4/20` 的来源。
- `docs/week3/计划审核/9.28数据集路线v2与采纳记录_复核意见.md`：对 v2 与采纳记录的复核。含逐项核验（21 项中 19 项落点一致）、文件系统独立审计（13:12 后仅 `docs/` 与 `memory/` 共 8 个文件变动，`decomposition-bench/` 内 0 个）、v1--v2 比对结论；4 项中等问题（§2.1 漏记选择侧正结果、改版无版本留痕导致 v1 不可恢复、负对照层来源未指定、扩大确认的资源来源未着落）与 5 项轻微问题，以及 2 项补充待决事项。
- `docs/week3/计划审核/9.28数据集路线v3_复核修订记录.md`：对复核意见的逐项独立判断与最终修订记录；说明内部负对照优先、APPS 只能外部描述、G2 无资源即正式收束。
- `docs/week3/计划审核/9.28数据集路线_分步执行与Agent移交文档_v2_20260928.md`：修订前执行版 v2 存档。
- `docs/week3/计划审核/9.28数据集路线_分步执行与Agent移交文档_v4_20260928.md`：修订前执行版 v4 存档（v5 修订前留痕）。
- `docs/week3/计划审核/9.28数据集路线执行版v4_复审意见.md`：v4 的三维复审（可行性 / 价值与意义 / 期望产出）+ 4 处内部不一致 + `wsl_root_free_gib=939` 的解释。

## 数据路线产物（WP0--WP1，2026-09-28 起）

- 产物根目录：`docs/week3/data-route/20260928/`（后续批次按新日期建同级目录）
- WP0 研究问题与数据字段契约：`00_research_question_and_data_contract.md`
- WP0 一页决策请求单：`00_decision_request.md`
- 加训练/RL 的选项分析：`00b_adding_training_or_rl_option_analysis.md`（DecompRL 原文的 80×H100 配置与 Table 1 token 预算曲线，对照本机单卡）
- FAST-0 报告（BigCodeBench）：`00a_fast0_bigcodebench_smoke_report.md`
- WP1 第一轮（**未完成**）：`01_public_dataset_search_log.md`、`01_public_dataset_landscape.md`、`01_public_dataset_candidates.csv`、`01_prior_answer_and_research_gap.md`
- WP2 静态审计（第一轮完成）：`02_static_audit_classeval.md`、`02_static_audit_evocodebench.md`、`02_static_audit_deveval.md`、`02_static_audit_commit0.md`、`02_static_audit_summary_and_shortlist_update.md`
- WP2 补充核查：`03_wp2_supplement_licenses_cutoff_wsl_lca.md`（上游许可、Qwen 训练边界、WSL 实测、LCA 评测方式）
- WP1 收口：`04_wp1_venue_search_and_gap_update.md`（会议导向检索、MoT 论文身份更正、增量重估、LCA 六任务指标、EvoCodeBench 映射核查）
- WP3--WP5 与 G1（2026-09-29，`docs/week3/data-route/20260929/`）：`03_smoke_protocol.md`、`03_smoke_report_classeval.md`、`04_dataset_route_decision.md`（G1）、`05_public_dataset_conversion_protocol.md`、`06_dataset_freeze_protocol.md`
- P0 与 WP6 预注册（2026-09-29）：`06a_headroom_probe_report.md`（P0 探针）、`07_annotation_reliability.md`（五项判据双标注一致率）、`08_wp6_preregistration.md`（WP6 预注册）
- WP6 与 G2（2026-09-29）：`09_wp6_report.md`（含组装工具缺陷披露与更正后结果）、`10_g2_decision.md`（正式收束 + v2 复核附录）
- v2 公平化重跑（2026-09-29）：`12_wp6_v2_report.md`；机器产物 `experiments/classeval_wp6_v2/wp6_v2_manifest.json`；脚本 `scripts/wp6_classeval/run_wp6_v2.py`
- 去向选项分析（2026-09-29）：`11_how_to_proceed_options.md`
- WP6 机器产物与脚本：`experiments/classeval_wp6/{wp6_manifest.json,wp6_m2_corrected.json,assembled/,candidates/,evaluations/}`、`scripts/wp6_classeval/{run_wp6.py,rerun_m2_assembly.py}`、`src/classeval_assemble.py`、`tests/test_classeval_assemble.py`
- WP6/P0 机器产物与脚本：`experiments/classeval_headroom_probe/`、`experiments/classeval_wp6/`、`experiments/wp3_classeval/annotation/`、`scripts/p0_headroom/run_probe.py`、`scripts/wp6_classeval/run_wp6.py`、`scripts/wp3_classeval/annotation_agreement.py`
- 冻结数据：`decomposition-bench/data/processed/classeval_v1/`（`tasks_public.jsonl`、`private/private_tests.jsonl`、`provenance.json`、`excluded_tasks.json`、`dataset_card.md`、`README.md`）与 `decomposition-bench/data/splits/classeval_v1/frozen_manifest.json`
- 相关机器产物与脚本：`experiments/wp3_classeval/`、`experiments/wp4a_classeval_regression/`、`scripts/wp3_classeval/`、`scripts/wp4a_classeval/`、`src/classeval_split.py`、`tests/test_classeval_split.py`
- WP2 机器产物：`decomposition-bench/experiments/wp2_classeval/classeval_smoke_manifest.json`；原始数据 `decomposition-bench/data/raw/classeval/data/...parquet`、`data/raw/evocodebench/{data_extracted/data.jsonl,upstream_repo_licenses.json}`
- FAST-0 脚本：`decomposition-bench/scripts/fast0_bigcodebench/`（`inspect_dataset.py`、`run_reference_tests.py`、`probe_hf_metadata.py`、`verify_licenses_via_proxy.py`、`verify_paper_and_dataset_ids.py`、`probe_hf_licenses_extra.py`）
- FAST-0 机器产物：`decomposition-bench/experiments/fast0_bigcodebench/`（`fast0_smoke_manifest.json` v1、`fast0_smoke_manifest_v2_pytz.json` v2、`work/<task>/ref_solution_with_tests.py`）
- FAST-0 原始数据：`decomposition-bench/data/raw/bigcodebench/v0.1.4/bigcodebench_v0.1.4_full.parquet`（2.25 MiB）
- FAST-0 隔离环境（D 盘）：`decomposition-bench/.venvs/bigcodebench_fast0/`；缓存 `D:\yaorz\research\.cache\{pip,uv,hf}`
- `docs/week3/计划审核/9.28数据集路线审阅意见_批判性采纳记录_v1_20260928.md`：修订前采纳记录存档。
- `docs/week2/阶段一拆解机制负结果深度归因与论文拆分对照_20260926.md`：七层因果链 + 逐篇"拆分"对照 + "重组 × 学习"四象限定位。
- `docs/week2/9.14科研计划部署.md`、`docs/week2/9.14科研计划部署_大学生易懂执行版.md`：9.14 计划部署（技术版 / 大学生易懂版）。
- `docs/week2/9.18当前研究结果与后续工作.md`：9.18 阶段结果总结（含"适合拆分的五项条件"§8）。
- `docs/week2/论文中的拆分为何有效_与本地No-Go的差异.md`：论文正结果与本地负结果的逐项对照。
- `当前情况总结.md`：旧版详细恢复摘要，仍保留。
- `articles/README.md`：论文入口。
- `docs/week3/公开数据集与论文链接清单.md`：WP1 检索到的公开数据集与相关论文的链接 + 一手核实的许可证（GitHub API / HF API / arXiv 页），含三处命名坑提醒与未核实清单。

## 项目记忆

- `PROJECT_MEMORY.md`：每轮必读、当前状态。**2026-09-29 起启用自动压缩**（上限约 150 行；已完成细节移入主题记忆，只留状态与指针）。
- `docs/week3/10.2研究总览_自9.14以来全过程与当前状态.md`：**面向用户的全过程总览**（自 9.14 起，含三阶段数字、时间线、未闭合项与限制）；用户要求"总结"时先看它。
- `docs/week3/10.2导师决策请求单_数据路线收束后的方向选择.md`：**面向导师的第二次决策请求单**（9.27 汇报的后续）；3 件待导师定事项（研究问题表述宽窄 / 方向 D0-D3 / 结论标签）+ 可选补测 + 限制条件；草稿性质，交前需用户审改。
- `tmp/scan_models_in_papers.py`：统计本地论文全文里的模型提及与理由句（一次性分析脚本，可复跑）。**注意：该脚本服务的"论文模型选型"问答已按用户要求只留在对话里，未落盘为文档**。
- `memory/dialogue/2026-10.md`：2026 年 10 月逐轮记录（D076 起）；9 月记录在 `2026-09.md`（D001--D075）。**该目录自 2026-10-02 起停止更新，只读归档**；新记录写入主题记忆。
- `memory/data-route-log.md`：数据路线（2026-09-28 起）全过程细节的承接文件——研究问题、执行文档 v1→v5、WP0/FAST-0/WP1/WP2 结论与数字、环境实测、训练/RL 选项分析、下一步。
- `memory/`：辅助记忆。
- `.codebuddy/skills/project-memory-maintainer/SKILL.md`：记忆技能唯一正文。
- `.agents/skills/project-memory-maintainer/SKILL.md`：Codex 发现适配器。
- `.codebuddy/rules/01-项目记忆维护协议.md`：always-on 规则。

## 研究状态与证据

- `decomposition-bench/.research-state/PROJECT_STATE.md`：研究状态导航。
- `decomposition-bench/.research-state/ledger.jsonl`：追加式研究账本。
- `decomposition-bench/experiments/README.md`：实验协议索引。
- `decomposition-bench/reports/README.md`：正式报告索引。
- `decomposition-bench/data/README.md`：数据层次和规则。
- `decomposition-bench/scripts/README.md`：脚本入口。

## 当前 FunPRM 结果

- 报告：`decomposition-bench/reports/funprm_exact_prefix_generative_result_20260922.md`
- 协议：`decomposition-bench/experiments/funprm_exact_prefix_20260922/preregistration.md`
- 预算与结果：`decomposition-bench/experiments/funprm_exact_prefix_20260922/budget_manifest.json`
- 标签审计：`decomposition-bench/data/processed/funprm_exact_prefix_train50_k4_seed42000_20260922_unit_reward_audit.json`
- 开发审计：`decomposition-bench/data/processed/funprm_holdout30_generative_exact_prefix_k4_v1_audit.json`
- 确认审计：`decomposition-bench/data/processed/funprm_confirm_after80_generative_exact_prefix_k4_v1_audit.json`
- adapter：`decomposition-bench/outputs/models/funprm_qwen25coder_7b_generative_exact_prefix_k4_v1/`

## Top-down 阶段 1

- 协议：`decomposition-bench/experiments/funprm_topdown_20260922/preregistration.md`
- 基线快照：`decomposition-bench/experiments/funprm_topdown_20260922/baseline_snapshot.json`
- 失败审查：`decomposition-bench/reports/funprm_topdown_phase1_smoke_20260922.md`
- 机器审计：`decomposition-bench/data/processed/funprm_topdown_smoke10_qwen25coder_7b_n2_seed52_audit.json`
- v1/v2 原始输出：`decomposition-bench/data/processed/funprm_topdown_smoke10_qwen25coder_7b_n2_seed52_v*_*.json*`

## Top-down 阶段 1b

- 协议：`decomposition-bench/experiments/funprm_topdown_structured_20260922/preregistration.md`
- 正式失败报告：`decomposition-bench/reports/funprm_topdown_structured_phase1b_20260922.md`
- 结构化生成模块：`decomposition-bench/src/structured_topdown.py`
- 运行器：`decomposition-bench/scripts/run_structured_topdown_experiment.py`
- 事后机械装配分析：`decomposition-bench/scripts/analyze_structured_topdown_smoke.py`
- 正式输出：`decomposition-bench/data/processed/funprm_topdown_structured_smoke10_qwen25coder_7b_n2_seed52_v1_{generations,evaluations,summary}.json*`
- 事后审计：`decomposition-bench/data/processed/funprm_topdown_structured_smoke10_qwen25coder_7b_n2_seed52_v1_audit.json`

## Top-down 阶段 1c 与 helper-first 扩量

- 阶段 1c 报告：`decomposition-bench/reports/funprm_topdown_phase1c_ab_20260923.md`
- 阶段 1c 协议：`decomposition-bench/experiments/topdown_ab_phase1c_20260923/`
- 扩量预注册：`decomposition-bench/experiments/funprm_helperfirst_scale_20260923/preregistration.md`
- 冻结切分：`decomposition-bench/data/splits/funprm_helperfirst_scale_20260923/frozen_splits_manifest.json`
- 扩量门控报告：`decomposition-bench/reports/funprm_helperfirst_scale_gate_20260924.md`
- 1308次最终节点：`decomposition-bench/data/processed/funprm_helperfirst_scale_20260923/train100_prefix_rollouts_k16_seed20261124_v1_unit_reward_nodes.jsonl`
- 原协议最终门控：`decomposition-bench/data/processed/funprm_helperfirst_scale_20260923/train100_prefix_rollouts_k16_seed20261124_v1_final_gate_audit.json`

## 标签独立校准与暂停恢复点

- 校准预注册：`decomposition-bench/experiments/funprm_label_calibration_20260924/preregistration.md`
- 哈希64节点清单：`decomposition-bench/data/splits/funprm_label_calibration_20260924/hash64_manifest.json`
- 校准节点副本：`decomposition-bench/data/processed/funprm_label_calibration_20260924/hash64_k8_nodes.jsonl`
- 校准机器审计：`decomposition-bench/data/processed/funprm_label_calibration_20260924/hash64_k8_calibration_audit.json`
- 冻结训练协议：`decomposition-bench/experiments/funprm_label_calibration_20260924/training_protocol.md`
- 训练数据清单：`decomposition-bench/experiments/funprm_label_calibration_20260924/training_data_manifest.json`
- 最小训练集：`decomposition-bench/data/processed/funprm_label_calibration_20260924/train100_prm_nodes_v1.jsonl`
- token 审计器：`decomposition-bench/scripts/audit_funprm_training_tokens.py`
- token 审计结果：`decomposition-bench/data/processed/funprm_label_calibration_20260924/train100_prm_token_audit.json`

## 扩量评分器验证与最终确认

- 扩量adapter：`decomposition-bench/outputs/models/funprm_qwen25coder_7b_generative_helperfirst_scale_v1/`
- 20题验证门控v2：`decomposition-bench/data/processed/funprm_label_calibration_20260924/validation20_gate_audit_v2.json`
- 被保留的错误门控审计：`decomposition-bench/data/processed/funprm_label_calibration_20260924/validation20_gate_audit.json`
- 确认运行冻结清单：`decomposition-bench/experiments/funprm_label_calibration_20260924/confirmation_run_manifest.json`
- 确认A v1中止记录：`decomposition-bench/experiments/funprm_label_calibration_20260924/confirmation_a30_v1_abort_record.json`
- A v1不完整输出前缀：`decomposition-bench/data/processed/funprm_label_calibration_20260924/confirmation_a30_functionized_qwen25coder_7b_n10_seed20261224_v1`
- 评测器输出上限修复：`decomposition-bench/src/executor.py`
- 无限输出回归测试：`decomposition-bench/tests/test_executor.py`
- A/B选择冻结：`decomposition-bench/experiments/funprm_label_calibration_20260924/confirmation_ab_selection_freeze_20260925.json`
- A/B选择私测审计：`decomposition-bench/experiments/funprm_label_calibration_20260924/confirmation_a30_private_selection_audit_20260925.json`、`confirmation_b30_private_selection_audit_20260925.json`
- 关机前A上限扫描中止记录：`decomposition-bench/experiments/funprm_label_calibration_20260924/confirmation_a30_pool_oracle_shutdown_abort_20260926.json`
- A/B候选池上限：`decomposition-bench/data/processed/funprm_label_calibration_20260924/confirmation_a30_pool_oracle_20260926.json`、`confirmation_b30_pool_oracle_20260926.json`
- A/B候选池上限审计：`decomposition-bench/experiments/funprm_label_calibration_20260924/confirmation_a30_pool_oracle_audit_20260926.json`、`confirmation_b30_pool_oracle_audit_20260926.json`
- 双确认最终机器门槛：`decomposition-bench/data/processed/funprm_label_calibration_20260924/confirmation_ab_final_gate_20260926.json`
- 双确认最终独立复核：`decomposition-bench/experiments/funprm_label_calibration_20260924/confirmation_ab_final_gate_audit_20260926.json`
- 双确认正式报告：`decomposition-bench/reports/funprm_helperfirst_scale_confirmation_ab_20260926.md`

## 论文原文文本

- `archive/pdftext/`：论文 PDF 的纯文本抽取。原有 CodePRM、FunPRM、AdapTrack、EfficientGrammer-Constrained、Lookahead-then-Verify、SeeCodePRM；
- `archive/pdftext/08_DecompRL.txt`、`archive/pdftext/09_MoT.txt`：2026-09-26 新增，被 `docs/week2/阶段一拆解机制负结果深度归因与论文拆分对照_20260926.md` 引用为原文核对依据（DecompRL Table 1/Table 4/§6/Appendix J；MoT Algorithm 1）；
- 抽取脚本：`tmp/extract_extra_pdfs.py`（依赖隔离 venv 的 pypdf）。

## 代码与计划

- 仓库入口：`decomposition-bench/README.md`
- 当前计划归档：`decomposition-bench/docs/plans/`
- 主代码：`decomposition-bench/src/`
- 运行与分析：`decomposition-bench/scripts/`
- 测试：`decomposition-bench/tests/`

## 不应随意移动

- `decomposition-bench/data/processed/`：大量报告和 JSON 内嵌路径依赖。
- `decomposition-bench/outputs/` 和 `models/`：本地运行产物和模型。
- `tmp/`：虽然命名为临时目录，但脚本被旧研究文档引用。
- 冻结实验目录和旧报告：历史证据链的一部分。

## D1原型与开发探针（2026-10-08）

- 当前可运行原型：decomposition-bench/data/processed/d1_project_prototype8_v5_20261008/（8题、151案例，public/private分离）；原始来源data/raw/d1_project_v1_20261008/，旧v1--v4保留。
- 人类阅读入口：docs/week3/data-route/20261008/05_selfbuild_protocol.md、06_question_A_measurement_design.md、07_prototype_quality_and_review.md、08_development_probe_report.md、09_dataset_card_and_expansion_candidates.md。
- 构建/评测/试跑：decomposition-bench/scripts/d1/（acquire_sources.py、task_specs.py、build_dataset.py、evaluate_candidate.py、bounded_execution.py、audit_semantic_mutants.py、run_local_pilot.py）。
- 两轮开发：decomposition-bench/experiments/d1_project_development_pilot_v{1,2}_20261008/及同名.protocol.json；含public-only提示、模型回复、冻结候选、代码快照、summary；v2另有posthoc_evaluation_audit_stdout_fix.json。
- 自动/来源证据：experiments/d1_project_prototype8_mutants_v{2,3,4}_20261008/、d1_upstream_tests_20261008/、d1_project_prototype8_source_evidence_20261008/；GLM审查d1_project_prototype8_review_20261008/review_stdout_v3.txt；本地不采纳标注原始输出另存。
- 公开提示诊断：experiments/d1_public_prompt_diagnostic_20261008/；打印通道修复：d1_evaluator_stdout_fix_20261008/；旧错误成绩保留，不覆盖。


## D1二十题初版候选（2026-10-08，当前有效）

- docs/week3/data-route/20261008/10_expansion_protocol_and_structure_schema.md：第二批12功能构建契约、外部行为结构尺度v0.2、语义粒度边界。
- docs/week3/data-route/20261008/11_initial20_quality_and_stage_review.md：20题307案例、质量及版本失败、有限复核/人工缺口、阶段判断和下一步。
- decomposition-bench/data/processed/d1_project_initial20_v5_20261008/：当前20题候选；public只含外部需求/公开例，private含307用例、参考/另实现、固定来源许可、结构初标和脚本快照。
- decomposition-bench/experiments/d1_project_initial20_v5_20261008/：质量汇总、287文件哈希、完整性、原8题32文件逐字对照、家族敏感性分组；initial20 v1--v4均为历史版本，不删除。
- decomposition-bench/experiments/d1_project_initial20_mutants_v5_20261008/：40个有限语义缺陷及识别证据。
- decomposition-bench/experiments/d1_expansion_differential_v1_20261008/：4功能各600次差分诊断，seed20261008，2400无分歧，不计正式用例。
- decomposition-bench/experiments/d1_scoring_contract_v2_20261008/：8项评分边界候选、输入、结果；布尔/数值/输入不变/打印通道。
- decomposition-bench/experiments/d1_project_initial20_review_20261008/：12题GLM审查超时、4题有限答复和采纳理由，非人工真值。
- decomposition-bench/experiments/d1_blind_annotation20_v2_20261008/：20题盲审包与空白判定表；curator_key_private.json不得给审查员。v1较旧题面留档。
- decomposition-bench/scripts/d1/task_specs_expansion.py、check_expansion_differential.py、verify_scoring_contract.py、prepare_blind_annotation.py：新增功能、差分/评分诊断和盲审导出。


## D1相关工作与成本探针（2026-10-08）

- docs/week3/data-route/20261008/12_literature_and_cost_phase_contract.md：相关工作、计量和小探针入口契约。
- docs/week3/data-route/20261008/13_related_work_and_costed_pilot_report.md：FEA-Bench/FeatureBench边界、Ollama计量失败、成本小探针和阶段判断。
- decomposition-bench/experiments/d1_literature_recon_20261008/：论文摘要XML、作者README/许可哈希、来源矩阵和GitHub发现记录。
- decomposition-bench/configs/d1_costed_pilot_b04_c03_v1_20261008.json、scripts/d1/run_costed_local_pilot.py：输入token预检、动态6500生成token预算协议。
- decomposition-bench/experiments/d1_costed_pilot_b04_c03_v1_20261008/：24调用原始prompt/response、token账本、候选、评分、预算审计和汇总。
- 同目录`failure_taxonomy.json`：按评分器可观察类别汇总失败，不解释为算法根因。

## D1成本探针v2产物（2026-10-08）

- 协议：decomposition-bench/configs/d1_costed_pilot_b03_b05_c04_v1_20261008.json
- 原始实验：decomposition-bench/experiments/d1_costed_pilot_b03_b05_c04_v1_20261008/（summary.json、call_ledger.json、selection_freeze.json、candidates/）
- 统计脚本：decomposition-bench/scripts/d1/summarize_costed_pilot.py、summarize_pilot_failures.py
- 汇总：同实验目录下stratified_summary.json、failure_taxonomy.json
- 报告：docs/week3/data-route/20261008/13_related_work_and_costed_pilot_report.md；状态审计：decomposition-bench/experiments/d1_costed_phase_state_audit_v2_20261008.json
## D1复核前置产物（2026-10-08）

- 阶段契约：docs/week3/data-route/20261008/14_freeze_readiness_phase_contract.md
- 正式协议草案：docs/week3/data-route/20261008/15_formal_evaluation_protocol_draft.md
- 前置审计报告：docs/week3/data-route/20261008/16_freeze_readiness_report.md
- 审计脚本：decomposition-bench/scripts/d1/audit_freeze_readiness.py
- 审计输出：decomposition-bench/experiments/d1_freeze_readiness_audit_v1_20261008.json；阶段状态审计decomposition-bench/experiments/d1_p6_state_audit_v2_20261008.json
- 反向审计：decomposition-bench/experiments/d1_p6_adversarial_review_v1_20261008.json


## D1交付修订及严格预算模拟产物（2026-10-08）

- 旧成本探针条目的“24调用完整prompt/response”有误：保留描述历史但以此更正为准，仅prompt哈希、计数、计划原文及成功候选；失败helper/entry原文缺失。17号报告与d1_cost_allin_audit_v1_20261008.json明确记录限制。
- docs/week3/data-route/20261008/17_review_delivery_and_protocol_revision.md：交付、五题全部成本、24调用12/12更正、来源/家族判断和一手方法定位。
- 同目录18_question_A_protocol_v0.2.md：当前正式候选协议，取代15号草案的重排、因果、题独立区间和失败归因建议；19_total_budget_instrument_contract.md、20_total_budget_instrument_report.md：P7工具契约与12模拟反例报告。
- decomposition-bench/experiments/d1_blind_annotation20_v3_20261008/：reviewer_only.zip可交付，reviewer/含4文件，curator_private/仅管理端保留，不能整体交给审查员；实际回收0。
- decomposition-bench/scripts/d1/review_human_annotations.py、check_review_pipeline.py：双审准备/校验/κ及21反例；机器证据experiments/d1_review_pipeline_selfcheck_20261008.json。
- decomposition-bench/scripts/d1/audit_allin_cost.py、audit_family_links.py；对应experiments/d1_cost_allin_audit_v1_20261008.json、d1_family_link_audit_v1_20261008.json，非独立复核experiments/d1_p6_adversarial_review_v2_20261008.json。
- decomposition-bench/experiments/d1_literature_fulltext_v1_20261008/：官方两篇HTML/抽取文本/下载哈希；method_evidence.json记录实际定向阅读章节，不称通读。
- decomposition-bench/scripts/d1/budgeted_generation.py、check_budgeted_generation.py；experiments/d1_total_budget_simulation_v1_20261008/保存12检查汇总及合成请求/响应/账本，不是真实API输出。
- decomposition-bench/.research-state/snapshots/PROJECT_STATE_before_P7_20261008.md：修订前历史状态，部分判断被17/18号及追加账本更正；当前读PROJECT_STATE.md。


## P8-P10产物（2026-10-08）

- `docs/week3/data-route/20261008/21_tokenizer_integration_contract.md`、`22_tokenizer_integration_report.md`、`23_native_pair_smoke_contract.md`、`24_native_pair_smoke_report.md`、`25_candidate_delivery_contract.md`、`26_candidate_delivery_report.md`。
- `decomposition-bench/scripts/d1/native_tokenizer.py`、`budgeted_generation.py`、`run_allin_pipeline.py`、`check_allin_pipeline.py`、`calibrate_native_tokenizer.py`、`audit_native_pipeline.py`。
- `decomposition-bench/experiments/d1_tokenizer_integration_v1_20261008/`：native_probe、校准请求/响应、来源证据、真实P8/P9完整失败审计及事后代码快照。
- `decomposition-bench/experiments/d1_allin_pipeline_simulation_v2_20261008/`：合成13/13全链路；`d1_allin_native_pair_b03_v1_20261008/`：P9四请求、冻结、评分、失败原文。
- `decomposition-bench/experiments/d1_candidate_delivery_v1_20261008/`：缓存409文件的失败打包保留；`d1_candidate_delivery_v2_20261008/`：287研究文件、ZIP290、8/8交付验证、包外最终哈希。


## 2026-10-08：D1-P11可迁移交付与契约证据

- 契约/报告：`docs/week3/data-route/20261008/27_portability_and_contract_audit.md`、`28_portability_and_contract_report.md`。
- 当前推荐管理端ZIP：`decomposition-bench/experiments/d1_candidate_delivery_v4_portable_20261008/d1_project_initial20_v5_portable_candidate.zip`；同目录PORTABILITY_PATCHES、RUNTIME_DEPENDENCIES、包外DELIVERY_CHECKSUMS_EXTERNAL/DELIVERY_NOTES、portable_delivery_verification_v2.json为补丁/许可/14项复核入口；含private不交盲审人类。
- 运行证据：`experiments/d1_portability_v2_isolation_20261008/corrected_summary.json`（参考缺库0/20、另一结构20/20）、`experiments/d1_portability_v4_isolation_20261008/summary.json`（40/40，614/614）；位于decomposition-bench下。失败v3中间包及BUILD_FAILURE保留。
- 六题39条管理端契约索引：`decomposition-bench/experiments/d1_contract_traceability6_v1_20261008/traceability_private.{json,md}`，非全覆盖/人工真值，不进入审查员包。
- 实现：`decomposition-bench/scripts/d1/{audit_package_portability.py,package_portable_candidate.py,verify_portable_delivery.py,audit_contract_traceability.py}`。

## 2026-10-08：P12—P18研究证据与独立扩展池

- 当前研究目标/计划：`decomposition-bench/.research-state/RESEARCH_TARGET.md`、`RESEARCH_PLAN.md`；状态与追加账本仍为同目录PROJECT_STATE/ledger。
- 契约和结果：`docs/week3/data-route/20261008/29_behavior_coupling_contract.md`、30_behavior_coupling_report、31_local_contract_and_composition_contract、32_local_contract_and_composition_report、33_budget_crowding_contract、34_budget_crowding_report、35_structure_support_contract、36_structure_support_report、37_cross_source_cache_contract、38_cross_source_cache_report、39_cross_source_order_contract、40_cross_source_order_report、41_granularity_review_contract（均.md）。
- 原始证据位于`decomposition-bench/experiments/`：`d1_semantic_contrasts_v1_20261008/`成对输入/实体投影；`d1_local_composition_v1_20261008/`4正确结构/4人工缺陷/冻结；`d1_prompt_crowding_v1_20261008/`200构造情景/提示原文/计量复核；`d1_structure_evidence_sidecar_v1_20261008/`20题管理端附件/来源支撑/精确矩阵。
- 扩展候选：`d1_expansion_cache_candidate_v1_20261008/`为E_B07策略/统计，`d1_expansion_order_candidate_v1_20261008/`为E_M06规范键/首次保序，均expansion_pool_unassigned；契约、手算先冻结、原始有限求值保存，不计入原20题/307用例，不交盲审或模型。
- 当前P18：`d1_granularity_review_v1_20261008/evidence_extraction.json`，3条保存反例已提取、逐粒度协议待完成。脚本分别为`decomposition-bench/scripts/d1/run_semantic_contrasts.py`、probe_local_composition、measure_prompt_crowding、build_evidence_support、probe_cross_source_cache、probe_cross_source_order（均.py）。
- 方法一手来源：`decomposition-bench/experiments/d1_measurement_sources_v1_20261008/hyperproperties.pdf`及first3pages文本、获取失败与成功记录；定向读前3页、不称通读/关系测试首创。


## 2026-10-08：P18—P24新证据入口

- 契约/报告目录`docs/week3/data-route/20261008/`：42_granularity_review_report、43_valid_text_budget_contract、44_valid_text_budget_report、45_plan_state_distribution_contract、46_plan_state_distribution_report、47_relation_vacuity_contract、48_relation_vacuity_report、49_expansion_support_contract、50_expansion_support_report、51_unmeasured_task_screen_contract、52_unmeasured_probe_freeze、53_unmeasured_task_screen_report、54_alignment_composition_contract（均.md）。
- 原始输出在`decomposition-bench/experiments/`：d1_granularity_review_v2_20261008、d1_valid_text_budget_v1_20261008、d1_plan_state_distribution_v1_20261008、d1_relation_vacuity_v1_20261008、d1_expansion_support_v1_20261008、d1_unmeasured_task_screen_v1_20261008、d1_unmeasured_task_probes_v1_20261008；旧粒度v1/原输入与导入失败记录保留。
- 实现`decomposition-bench/scripts/d1/`：analyze_granularity_review、measure_valid_text_budget、probe_plan_state_distribution、probe_relation_vacuity、analyze_expansion_support、probe_unmeasured_tasks（均.py）；按实际脚本路径运行需支持本地模块，不直接加-I。
- 当前接续：`decomposition-bench/experiments/d1_alignment_composition_v1_20261008/first_hand_anchor_frozen.json`，尚只有手算冻结，没有程序执行结果。状态/计划见`.research-state/PROJECT_STATE.md`、RESEARCH_TARGET、RESEARCH_PLAN和追加账本。

- P24完成新增`docs/week3/data-route/20261008/55_alignment_composition_report.md`；`decomposition-bench/scripts/d1/probe_alignment_composition.py`、同实验目录code_freeze/hand_anchors_frozen/local_results/anchor_results/finite_inputs/summary。P25当前`56_expected_rejection_contract.md`、`experiments/d1_expected_rejection_v1_20261008/public_requirement_extracted.json`（尚无新关系结果），状态/计划更新至P25。

- P25完成新增57_expected_rejection_report.md、scripts/d1/probe_expected_rejection.py及d1_expected_rejection_v1_20261008/冻结/输入/关系/summary；当前P26为58_measurement_record_contract.md、d1_measurement_record_v1_20261008/evidence_sources_extracted.json（八类来源，非完成结果）。路径根分别docs/week3/data-route/20261008与decomposition-bench。


## 2026-10-08：P26—P34新研究入口

- 契约/报告在docs/week3/data-route/20261008/：58—74号，包括59_measurement_record_report、61_method_gate_report、63_entry_annotation_gate_report、65_failure_observation_report、67_question_A_protocol_v0.3_candidate、69_layered_merge_reduction_report、71_layered_merge_summary_report、73_path_local_summary_report、74_interface_information_recovery_contract（均.md）。旧18号v0.2保留；67号未集成正式pipeline。
- 原始实验目录根decomposition-bench/experiments/：d1_measurement_record_v1/v2_20261008（v1保留），d1_method_gate_v1_20261008，d1_entry_annotation_gate_v1_20261008（field_semantics_clarification.json明确旧含混字段），d1_failure_observation_v1_20261008，d1_question_A_protocol_v0_3_candidate_20261008，d1_layered_merge_reduction_v1_20261008，d1_layered_merge_summary_v1_20261008，d1_path_local_summary_v1_20261008。
- 脚本在decomposition-bench/scripts/d1/：build_measurement_records、probe_method_gate、probe_entry_annotation_gate、analyze_failure_observation、probe_layered_merge_reduction、probe_layered_merge_summary、probe_path_local_summary（均.py）。需普通python -B -X utf8支持本地模块。当前P34只有d1_interface_information_recovery_v1_20261008/first_hand_collision_frozen.json，尚未执行计划比较；状态/目标/计划/追加账本在.research-state/。
- 原口径、暴露限制与负结果见memory/data-route-log.md§二十八。


## 2026-10-08：P34—P39产物

- docs/week3/data-route/20261008/75_interface_information_recovery_report、76_actual_M2_recovery_boundary_contract、77_actual_M2_recovery_boundary_report、78_helper_runtime_influence_contract、79_helper_runtime_influence_report、80_saved_M2_observability_contract、81_saved_M2_observability_report、82_missing_marker_collision_contract、83_missing_marker_collision_report、84_measurement_contribution_literature_contract（均.md）。
- 原始实验根decomposition-bench/experiments/：d1_interface_information_recovery_v1_20261008、d1_actual_M2_recovery_boundary_v1/v2_20261008（v1失败保留）、d1_helper_runtime_influence_v1_20261008、d1_saved_M2_observability_v1_20261008（六worker输入/输出）、d1_missing_marker_collision_v1_20261008。
- scripts/d1/：probe_interface_information_recovery、probe_actual_M2_recovery_boundary、probe_helper_runtime_influence、observe_saved_M2、probe_missing_marker_collision（均.py）。当前P39目录d1_measurement_contribution_literature_v1_20261008含问题冻结、web通道失败及缓存定位；尚无完整贡献比较。已有官方全文cache在d1_literature_fulltext_v1_20261008，不冒称通读/最新版本确认。
- 原口径/协议区分/失败/暴露与资源限制见memory/data-route-log.md§二十九，当前状态/目标/计划/账本在decomposition-bench/.research-state/。


## 既有入口原口径

- 数据路线工作包产物：`docs/week3/data-route/20260928/`（`00_*` 契约与决策单、`00a_*` FAST-0、`01_*` WP1、`02_*` WP2 审计与汇总、`03_*` WP2 补充、`04_*` WP1 收口）
- 公开数据集与论文链接清单（许可证一手核实）：`docs/week3/公开数据集与论文链接清单.md`
- 执行文档的审阅/采纳/复核/快照：`docs/week3/计划审核/`（含 `00_目录说明.md`）
- 既有本机环境与依赖可行性记录：`decomposition-bench/reports/research_feasibility_2026-09-05.json`


### 项目导航入口原口径

- docs 目录规则与阅读入口：`docs/README.md`
- **自 9.14 全过程总结（2026-10-02）**：`docs/week3/10.2研究总览_自9.14以来全过程与当前状态.md`
- 数据路线执行文档（**当前执行版 v5**）：`docs/week3/9.28数据集路线_分步执行与Agent移交文档.md`


## 2026-10-08：P39—P43研究入口

- docs/week3/data-route/20261008/85_measurement_contribution_literature_report.md；86_pre_generation_contrast_support_contract.md；87_pre_generation_contrast_support_report.md；88_testability_label_provenance_contract.md；89_testability_label_provenance_report.md；90_noncache_testability_opportunity_contract.md；91_noncache_stats_testability_report.md；92_numeric_contract_comparison_contract.md；93_numeric_contract_comparison_progress.md。
- decomposition-bench/experiments/d1_measurement_contribution_literature_v1_20261008/targeted_evidence_and_contribution_review.json；d1_pre_generation_contrast_support_v1_20261008/；d1_testability_label_provenance_v1_20261008/；d1_noncache_stats_testability_v1_20261008/（含保留的过强解释）；d1_noncache_stats_alternative_order_v1_20261008/（更正/新方案）；d1_numeric_contract_comparison_v1_20261008/（P43当前）。
- decomposition-bench/scripts/d1/audit_measurement_literature.py、analyze_pre_generation_contrast_support.py、audit_testability_label_provenance.py、probe_noncache_stats_testability.py、probe_stats_alternative_order.py；研究状态/账本/快照 .research-state/。


## 主记忆研究证据导航原项（2026-10-08）

研究证据入口

- **D1 问题参考与数据集定位**：`docs/week3/10.8_D1研究问题参考表述与数据集定位.md`（用户已选D1、题目与问题A；具体设计持续有版本修订）。
- 文档导航：docs/README.md；自9.14全过程10.2总览与当前执行v5入口见memory/artifact-map.md“项目导航入口原口径”。

- 旧工作包、公开来源许可清单、计划审核快照与本机可行性入口见memory/artifact-map.md“既有入口原口径”；原文件及事实保持。

- 数据路线全过程细节（压缩后的承接文件）：`memory/data-route-log.md`

- 9.27 导师汇报材料：`docs/week2/9.27思路演进与方向决策.md`；9.26 进展与待定问题：`docs/week2/9.26_9.14以来进展思路与待定问题.md`
- 阶段一负结果归因与论文拆分对照：`docs/week2/阶段一拆解机制负结果深度归因与论文拆分对照_20260926.md`
- 研究总览：`docs/week2/研究总览_当前结论与后续方向.md`；9.18 阶段结果：`docs/week2/9.18当前研究结果与后续工作.md`
- 论文拆分与本地负结果对照：`docs/week2/论文中的拆分为何有效_与本地No-Go的差异.md`
- 最终报告：`decomposition-bench/reports/funprm_helperfirst_scale_confirmation_ab_20260926.md`
- 最终门槛 / 复核 / 分析冻结：`decomposition-bench/data/processed/funprm_label_calibration_20260924/confirmation_ab_final_gate_20260926.json`、`experiments/funprm_label_calibration_20260924/confirmation_ab_final_gate_audit_20260926.json`、`confirmation_ab_analysis_freeze_20260925.json`
- 项目研究状态：`decomposition-bench/.research-state/PROJECT_STATE.md`（含账本 `ledger.jsonl`）
- 记忆索引与文件地图：`memory/README.md`、`memory/artifact-map.md`、`memory/user-requirements.md`（逐轮记录 `memory/dialogue/` 自 2026-10-02 起停用，只读归档）



## 2026-10-09：D1 P43—P51新证据入口

- 根docs/week3/data-route/20261009/95—109号（契约/报告）；94号位于decomposition-bench/docs/week3/data-route/20261008/94_numeric_contract_options_report.md，路径区别保留。
- decomposition-bench/experiments/d1_numeric_contract_options_v1_20261009/、d1_discrete_stats_candidate_v1_20261009/及d1_discrete_adapter_fidelity_v1_20261009/：原输出/范围/计数纠正另文件，P44旧18不重跑。
- d1_joint_profile_support_v1_20261009/、d1_joint_profile_sensitivity_v1_20261009/、d1_joint_profile_budget_v1_20261009/（均在decomposition-bench/experiments/）：画像重复/删除敏感性、11开发旧预算连接及仿射解释。
- decomposition-bench/experiments/d1_discrete_candidate_boundary_v1_20261009/candidate/task.json与requirements.md为E_B09公开另池成果候选；同目录原来源/许可/三参考/公开诊断；父目录冻结预期/三个有界原结果/summary。
- decomposition-bench/experiments/d1_output_type_composition_v1_20261009/：四有界评分与同执行消费轨迹；d1_typed_candidate_gate_v1_20261009/six_pairs_frozen.json为当前P51首动作，尚无比较结果。
- 新研究程序位于decomposition-bench/scripts/d1/：build_discrete_boundary_candidate.py、analyze_joint_profile_budget.py、probe_output_type_composition.py；前阶段probe_numeric_contract_options.py、probe_discrete_stats_candidate.py、analyze_joint_profile_support.py、analyze_joint_profile_sensitivity.py、probe_discrete_adapter_fidelity.py。总入口仍.research-state/target、plan、ledger。


- P51完成：docs/week3/data-route/20261009/110_typed_candidate_gate_report.md；decomposition-bench/experiments/d1_typed_candidate_gate_v1_20261009/summary.json、candidate_v2_delta/（规则增量未全链集成）、candidate_delta_manifest.json；程序scripts/d1/validate_typed_candidate_gate.py。
- 当前P52：docs/week3/data-route/20261009/111_noncache_stream_contract.md；decomposition-bench/experiments/d1_noncache_stream_v1_20261009/source_and_final_anchors_frozen.json，六终值解析预期/公开源码节点/hash已冻，尚无新solve结果。


## 2026-10-09：P52—P56新研究证据

- 根docs/week3/data-route/20261009/112_noncache_stream_report.md、113_stream_finalization_contract.md、114_stream_finalization_report.md、115_ansi_single_pass_contract.md、116_ansi_single_pass_report.md、117_ansi_original_spans_contract.md、118_ansi_original_spans_report.md、119_ansi_contract_clarification_contract.md。
- decomposition-bench/experiments/d1_noncache_stream_v1_20261009/：三结构原worker/轨迹/计数/summary，18新solve；d1_stream_finalization_v1_20261009/：新EOF结构/六轨迹、四预测3/4失败原样留档；d1_ansi_single_pass_v1_20261009/：六新公开规则/单次预期/独立扫描与两阶段及二次来源；d1_ansi_original_spans_v1_20261009/：两新程序/事前局部span/真实helper轨迹/summary。
- 当前decomposition-bench/experiments/d1_ansi_contract_clarification_v1_20261009/evidence_and_two_example_predictions_frozen.json，两公开例解析预测/保存结果哈希已冻，八行对照尚未执行；原数据不覆盖。
- 程序decomposition-bench/scripts/d1/{probe_noncache_stream.py,probe_stream_finalization.py,probe_ansi_single_pass.py,probe_ansi_original_spans.py}；当前119号及.research-state/RESEARCH_PLAN接续。


## 2026-10-09：P56—P61新证据与当前接续

- 根docs/week3/data-route/20261009/120_ansi_contract_clarification_report.md、121_range_local_observability_contract.md、122_range_local_observability_report.md、123_local_contract_scope_audit_contract.md、124_local_contract_scope_audit_report.md、125_typed_candidate_execution_contract.md、126_typed_candidate_execution_report.md、127_typed_reference_agreement_contract.md、128_typed_reference_agreement_report.md、129_discrete_output_projection_contract.md。
- decomposition-bench/experiments/d1_ansi_contract_clarification_v1_20261009/已有八行对照/原题副本/未来单次候选/summary；d1_range_local_observability_v1_20261009/事前八锚点/三程序/24solve/18局部；d1_local_contract_scope_audit_v1_20261009/六主张冻结/证据见证/协议增量；d1_typed_candidate_execution_v1_20261009/八新锚点五程序/40solve/candidate_v2完整公开执行候选；d1_typed_reference_agreement_v1_20261009/两参考16solve/三参考新manifest。
- 当前P61：decomposition-bench/experiments/d1_discrete_output_projection_v1_20261009/six_new_inputs_and_projection_predictions_frozen.json，四格/两非法/type/范围/hash已冻，solve0；129号与.research-state/RESEARCH_PLAN接续。最新检查点experiments/d1_state_P61_checkpoint_20261009.json：validtrue/327events/70warnings保留。
- 新程序decomposition-bench/scripts/d1/{analyze_ansi_contract_clarification.py,probe_range_local_observability.py,audit_local_contract_scope.py,probe_typed_candidate_execution.py,probe_typed_reference_agreement.py}；v2执行入口experiments/d1_typed_candidate_execution_v1_20261009/candidate_v2/evaluate_typed_candidate.py，原scripts/d1/evaluate_candidate.py未改。


## 2026-10-09：P61—P65新证据与接续

- 根docs/week3/data-route/20261009/130_discrete_output_projection_report.md、131_threshold_pullback_contract.md、132_threshold_pullback_report.md、133_second_source_extrema_contract.md、134_second_source_extrema_report.md、135_keyed_tie_contract.md、136_keyed_tie_report.md、137_admissible_extrema_comparator_contract.md。
- decomposition-bench/experiments/d1_discrete_output_projection_v1_20261009/18solve原输出/字段投影/12关系/24输出控制；d1_threshold_pullback_v1_20261009/六锚点/三程序18solve/舍入算术与trace；d1_second_source_extrema_v1_20261009/公开源码/hash/许可/18solve与candidate/（E_M07完整task/需求/三参考/sources/六诊断）；d1_keyed_tie_v1_20261009/四新abs-key输入/八fn输出/合法判定/精确误拒/evaluation_unit_clarification.json。
- 当前P65：decomposition-bench/experiments/d1_admissible_extrema_comparator_v1_20261009/fourteen_pairs_and_admissibility_predictions_frozen.json，八保存合法/六构造输出/hash/两规则预测已冻，比较0；137号及.research-state/RESEARCH_PLAN接续。检查点experiments/d1_state_P65_checkpoint_v2_20261009.json：validtrue/339events/70旧warnings保留，v1原文件仍在。
- 新程序decomposition-bench/scripts/d1/{probe_discrete_output_projection.py,probe_threshold_pullback.py,build_extrema_candidate.py,probe_keyed_tie.py}；原20/评分/旧源数据不改。

    
## P65—P70（2026-10-09）证据与交付边界

- 138 docs/week3/data-route/20261009/138_admissible_extrema_comparator_report.md；experiments/d1_admissible_extrema_comparator_v1_20261009/ 含冻结14对、比较结果/summary；脚本 scripts/d1/compare_admissible_extrema.py。
- 139—140 139_candidate_structure_support_contract.md、140_candidate_structure_support_audit_report.md；experiments/d1_candidate_structure_support_audit_v1_20261009/ 保留路径失败空目录，v2含矩阵/summary；脚本 scripts/d1/audit_candidate_structure_support.py。
- 141—142 141_evidence_provenance_schema_contract.md、142_evidence_provenance_schema_report.md；experiments/d1_evidence_provenance_schema_v1_20261009/ 含schema草案/summary；脚本 scripts/d1/validate_evidence_provenance_schema.py。
- 143—144 143_evidence_sidecar_delivery_contract.md、144_evidence_sidecar_delivery_report.md；experiments/d1_evidence_sidecar_delivery_v1_20261009/ 含两个公开候选旁车、delivery_manifest/summary；脚本 scripts/d1/probe_evidence_sidecar_delivery.py。
- 145—146 145_prepublication_gate_contract.md、146_prepublication_gate_report.md；experiments/d1_prepublication_gate_v1_20261009/ 含gate结果/summary；脚本 scripts/d1/check_prepublication_gate.py。
- 147—148 147_research_delivery_audit_contract.md、148_research_delivery_audit_report.md；experiments/d1_research_delivery_index_v1_20261009/ 含研究池索引/summary；脚本 scripts/d1/build_research_delivery_index.py。
- 当前状态：P70完成、P71已启动；最新checkpoint experiments/d1_state_P70_checkpoint_v2_20261009.json，events352/event_ids331，P71契约运行中；模型/API/人工/private调用均0。


## 2026-10-09：最新候选及当前P76（覆盖旧当前导航）

- docs/week3/data-route/20261009/154_input_result_tree_pair_contract.md、155_input_result_tree_pair_report.md；decomposition-bench/experiments/d1_input_result_tree_pair_v1_20261009/含E_B11/E_B12需求、公开例、三参考、source及许可、冻结/raw/summary；scripts/d1/build_input_result_tree_pair.py。
- 156_value_path_version_tasks_contract.md、157_value_path_version_tasks_report.md；experiments/d1_value_path_version_tasks_v1_20261009/含E_B13/E_B14公开需求、例、两参考、冻结/raw/summary；scripts/d1/build_value_path_version_tasks.py。候选标签/切分null，非正式数据冻结。
- 当前158_group_context_candidate_contract.md；experiments/d1_group_context_candidate_v1_20261009/public_source_first_action.json为已读源码段与hash/需求首动作，实际solve0，下一步冻结新锚点。
- 旧P66/P70/P70_v2检查点由P65修改计数形成，不能作完整校验证据；原文件保留，纠正见experiments/d1_checkpoint_claim_clarification_20261009.md。最新实际校验应另见experiments/d1_state_P75_actual_checkpoint_20261009.json；只认实际验证器结果。


- 2026-10-09 P80—P82真实项目候选：`docs/week3/data-route/20261009/165_research_focus_correction_and_repository_task.md`、166/167/168报告；`decomposition-bench/experiments/d1_repository_feature_candidate_v1_20261009/actual_project_v1/`含父/合并源码、commit验证、真实API诊断、task_spec及两版复核、结构证据。候选research_pool_only，正式标签/模型/人工为null/0。


## 2026-10-09：P83—P91实际项目任务

- 总结与审查计划：docs/week3/data-route/20261009/169_d1_multiturn_summary_and_cycle_plan.md（成对蓝图未执行，170号取代）；170—182号按各标题保存计划三审、原始结果和下一问题三轮深挖。
- confuse可运行任务：decomposition-bench/experiments/d1_runnable_repository_task_v2_20261009/candidate/；v1环境失败目录保留。替代组织：d1_repository_alternative_organization_v1_20261009/。预算：d1_repository_context_budget_v1_20261009/、d1_repository_symbol_context_patch_v1_20261009/、d1_repository_method_input_budget_v1_20261009/（均在experiments）。
- cachetools真实任务：decomposition-bench/experiments/d1_cache_expiry_repository_task_v1_20261009/execution_v1/candidate/；源码/官方需求在上级。当前时点修订候选：experiments/d1_repository_expiry_timing_amendment_v1_20261009/candidate/，包含旧五例与新增evaluate_timing.py；原定义不覆盖。时点反例原始：d1_repository_expiry_timing_v1_20261009/。
- 真实脚本在decomposition-bench/scripts/d1/：evaluate_repository_path_feature、build_runnable_repository_task、probe_repository_alternative_organization、measure_repository_context_budget、probe_repository_symbol_context_patch、measure_repository_method_input_budget、evaluate_repository_expiry_feature、build_repository_expiry_task、probe_repository_expiry_timing、evaluate_repository_expiry_timing（均.py）。
- 当前P91首动作：experiments/d1_repository_generation_adapter_feasibility_v1_20261009/existing_interfaces_first_action.json，有限代码接口调查，正式三审尚未完成，不调用模型。


## 2026-10-09：P91—P95项目入口与评价修订（覆盖旧当前导航）

- 计划/结果183—190号：docs/week3/data-route/20261009/，含顺序计划三审、失败、三轮下一问题深挖；P92不是已生成真实候选。
- 预算补丁入口：decomposition-bench/scripts/d1/repository_patch_entry.py、probe_repository_patch_entry.py；experiments/d1_repository_patch_entry_v2_20261009/含六条件freeze/selection/summary/request/raw/behavior，v1表示fixture失败保留。
- 实际发请求前失败：experiments/d1_repository_real_patch_feasibility_v1_20261009/budget_and_identity_first_action.json与d1_repository_real_patch_probe_v1_20261009/pre_request_failure.json；脚本run_repository_patch_probe.py尚未发模型请求，DLL不一致禁止沿旧校准生成，不绕过红线。
- 存储误拒反例：experiments/d1_delegated_state_oracle_v2_20261009/，四工作区/冻结/原始输出，v1环境失败保留；脚本probe_delegated_state_oracle.py。
- 当前cache公开API候选评价入口：experiments/d1_repository_expiry_public_oracle_v1_20261009/candidate/{workspace,requirement.md,evaluate.py,RUN.md}；上级freeze/四actual/四process/summary。脚本evaluate_repository_expiry_public_state.py、build_public_cache_oracle_revision.py。原P88/P90目录均保留。
- 当前P95有限接续：experiments/d1_public_cleanup_observability_feasibility_v1_20261009/public_observation_paths_first_action.json；尚未实施新行为实验，先详尽计划三审。

- 本轮真实状态校验：decomposition-bench/experiments/d1_state_P94_actual_checkpoint_v1_20261009.json，实际验证器返回valid true、418事件、0错误、75历史/来源警告保留；不是清零全部警告或数据集人工冻结。


## 2026-10-09：宏观计划为唯一执行导航（覆盖旧P95当前项）

- 当前宏观执行版：decomposition-bench/.research-state/RESEARCH_PLAN.md；目标与状态同步，G1只读纳入条件为下一项，P95停止自动接续。
- 三轮实质审查与修订：docs/week3/data-route/20261009/191_d1_macro_plan_reviews.md；可行性、意义、可信度依次进行，未开展新研究实验。
- 不可覆盖的旧计划/各版输入/执行版/纠正与审查完成状态：decomposition-bench/experiments/d1_macro_replan_20261009/{legacy_RESEARCH_PLAN.md,macro_plan_v1.md,macro_plan_v2_after_feasibility.md,macro_plan_v3_after_meaning.md,macro_plan_execution_v1_after_three_reviews.md,intervention.json,review_completion.json}。这些是计划恢复资料，不是新增研究数据或模型结果。

- 宏观状态实际校验：decomposition-bench/experiments/d1_state_macro_plan_actual_checkpoint_v2_20261009.json，valid true、421事件/0错误/76保留警告；v1亦保留。新方向事件缺decision字段已追加明确决定、更正关联，不覆盖原记录；不代表数据集/人工冻结。

- G1/G2本次证据：192/193号纳入、194/195号游标No-Go与污染、196/197号PR142计划/结果；experiments/d1_G1_task_admission_v1_20261009/、d1_G2_more_itertools_cursor_v1_20261009/、d1_G2_confuse_pr142_env_source_v1_20261009/（官方父/merge、freeze、12worker原始结果、stage_result、candidate/）；主记忆恢复入口data-route-log§四十一。

- 首轮宏观成果：data/processed/d1_actual_project_candidate_v2_20261009/{README.md,manifest.json,run_evaluation.py,public/,evaluation/,pending/,evidence/}；v1部分目录及复制失败保留。198—208号：来源/暴露/No-Go、G3结构、G4设计、G5一次交付、宏观v2限定PR440；d1_G3_structure_evidence_v1_20261009/、d1_G4_pair_design_v1_20261009/、d1_G5_candidate_delivery_v1_20261009/、d1_G2_more_pr440_group_lifetime_v1_20261009/，详细口径data-route-log§四十二。

- PR440与纠正：experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/{official_pr_metadata.json,source_manifest.json,candidate/,freeze_before_execution.json,behavior_*.json,stage_result.json}；d1_G3_structure_evidence_v1_20261009/structure_records_v2.json；G5失败合并目录data/processed/d1_actual_project_candidate_v3_20261009/WITHDRAWN.md；209—211号与data-route-log§四十三。稳定交付仍v2；PR440独立候选待增量注册。

- 可比范围：212/213/214号，experiments/d1_G3_structure_evidence_v1_20261009/comparability_matrix_v3_scope_clarification.json（初版与v2错误/引用纠正仍保留），matrix_scope_clarification.json；当前接续依赖见data-route-log§四十四及RESEARCH_PLAN末项。

- 契约核对与暂停：215—218号报告；experiments/d1_G3_contract_integrity_v1_20261009/{contract_observation_audit.json,attempt1_failure.json,plan_v*.md,interrupt_20261009T131205Z/}；d1_G3_pr126_entry_gap_v1_20261009仅plan_v0/plan_v1，无新行为结果。详data-route-log§四十五。

- 2026-10-11 G3契约完整性：docs/week3/data-route/20261011/{219_pr126_entry_gap_result.md,220_next_question_api_vs_structure_audit.md,221_api_structure_mapping_plan.md,222_after_api_mapping_next_question_audit.md,223_contract_integrity_cycle_result.md}；实验目录d1_G3_pr126_entry_gap_v1_20261009含冻结、4份原始结果、结构映射、stage/direction审查。
## 2026-10-11 G4 本地模型运行

- 执行记录与结果：`docs/week3/data-route/20261011/227_g4_local_execution_record.md`、`228_g4_local_ollama_result.md`、`229_g4_next_question_audit.md`。
- v1 原始实验：`decomposition-bench/experiments/d1_G4_local_ollama_real_project_pair_v1_20261011/`；v2 压缩上下文与格式隔离：`...pair_v2_20261011/`。
- 运行脚本：两版目录各自的 `run_pair.py`；格式诊断脚本为 v2 `format_repair_diagnostic.py`，原始响应按请求目录保存。
- G5成果合成：`docs/week3/data-route/20261011/230_g5_d1_boundary_synthesis.md`。
- 计量纠正与严格预检：`docs/week3/data-route/20261011/231_g4_preflight_correction.md`、`decomposition-bench/experiments/d1_G4_local_ollama_real_project_pair_v3_20261011/`，本地tokenizer/服务端逐次计数相等，四次请求发送/一次预算预检拒绝。
- 完整父API上下文批次：`docs/week3/data-route/20261011/232_g4_symbol_context_result.md`、`decomposition-bench/experiments/d1_G4_symbol_context_pair_v1_20261011/`；三题M0/M2共11次请求，M0补丁入口失败，M2组装前预算拒绝。
- G5最终纠正版：`docs/week3/data-route/20261011/233_g5_d1_final_corrected_synthesis.md`，取代230号旧资源表述。
