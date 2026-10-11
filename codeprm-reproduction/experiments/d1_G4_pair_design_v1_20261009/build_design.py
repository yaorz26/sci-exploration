from datetime import datetime, timezone
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPRO = ROOT.parents[1]
evidence = json.loads((REPRO / 'experiments/d1_G3_structure_evidence_v1_20261009/structure_records.json').read_text(encoding='utf-8'))
rows = []
for n in (1, 2, 3, 6):
    for s in (1, 3):
        rows.append({'tasks': n, 'seeds_example_not_frozen': s,
                     'generation_requests_minimum': n*s*5, 'generation_requests_if_three_components': n*s*6,
                     'both_arms_token_cap_if_B6500': 2*6500*n*s,
                     'includes_calibration_and_smoke': False})
design = {
    'time': datetime.now(timezone.utc).isoformat(), 'status': '未冻结设计，当前生成不开放',
    'candidate_scope': [{'task_id': row['id'], 'current_status': row['status'],
                         'eligible_after_human_protocol_freeze': row['source'] == 'confuse'}
                        for row in evidence['records']],
    'unit': '题目×seed下的两个策略配对；任务聚合，seed不当独立任务',
    'common': {'requirement_and_parent_context': '同题同冻结需求/父源码片段及行坐标/公开案例',
               'patch_interface': 'scripts/d1/repository_patch_entry.py::prepare_patch',
               'final_candidate': '指定包内现有/新增.py的原子统一补丁，完整应用后评分',
               'api': '仅固定公开API，M0/M2内部helper/文件组织自由',
               'evaluator': '同一冻结完整候选行为验收，不看组件局部分数挑答案',
               'reference_visibility': 'feature/正确补丁/控制/管理/隐藏评价不进提示'},
    'M0': {'generation_requests': 1, 'process': '一次输出完整多文件补丁；允许内部helper'},
    'M2': {'generation_requests': '4—5', 'process': ['计划1次，自定2—3组件/接口，不预给正确分解',
                                                    '逐组件2—3次，保存原始回答/契约',
                                                    '组装1次输出完整项目补丁，承担整合义务'],
           'unresolved_runtime_adapter': '原helper门槛在项目补丁协议中尚未正式冻结；不能以补丁入口证明M2合规'},
    'budget': {'task_method_cap_example_not_frozen': 6500, 'context_example_not_recalibrated': 8192,
               'count': '计划/组件/组装/预检/重试/重复上下文的全部输入+输出',
               'request_precheck': '核验token身份；输入+最小输出在剩余总预算及ctx内才发',
               'max_output': '逐请求上限须能在共享总账剩余值中容纳',
               'interpretation': '同上限不是实际token/费用相同，实际用量逐请求保存'},
    'outcomes': {'primary_Y': '完整候选全部冻结行为通过为1；生成/组装/预算耗尽/补丁失败为0',
                 'paired_delta': 'Y(M2)-Y(M0)，策略关联而非结构因果',
                 'conditional_behavior': '无完整候选时null；不能用占位分数解释算法正确率',
                 'analysis_limit': '当前两可用候选同来源同家族，结构效应不可独立估计，不拟合三轴回归'},
    'entry_requirements': ['真实双盲人类审查与正式任务/标签/协议冻结', '候选需求条款与交付一致',
                           'token计量身份与DLL重校准、实际上下文冻结', '项目M2适配/开发烟测及完整总预算授权',
                           '隔离评价/来源家族/暴露及所有方法失败分母'],
    'current_no_run_reasons': ['旧调用保守约98/100，剩约2不足一题5—6请求',
                               'DLL身份与原校准不同，不可计量', '真实人类双审0/正式结构标签null',
                               'cache强时点/交付尚未解决，PR142真实生成上下文尚未核验'],
    'table': rows, 'new_model_calls': 0, 'new_behavior_calls': 0,
    'next': 'G5一次研究候选成果交付；主问题A关联未测',
}
with (ROOT / 'paired_design.json').open('x', encoding='utf-8') as output:
    json.dump(design, output, ensure_ascii=False, indent=2)
lines = ['# 实际候选配对的资源与未执行依据', '',
         '这是未冻结设计，未调用模型。当前有限两项confuse候选；cache保留待解决，不纳入可用分母。', '',
         '| 题数 | seed示例 | 原M0+M2生成请求 | 两臂token总上限示例 |',
         '| --- | --- | --- | --- |']
for row in rows:
    lines.append(f"| {row['tasks']} | {row['seeds_example_not_frozen']} | {row['generation_requests_minimum']}—{row['generation_requests_if_three_components']} | {row['both_arms_token_cap_if_B6500']} |")
lines += ['', '以上不含校准/开发烟测，token是每臂B=6500的总上限而非实际用量。即便一题一seed也需5—6请求；旧剩约2，不能完整比较。', '',
          '预算不足、DLL身份不符、人类0、正式任务/标签/协议未冻结各自都能阻止运行。不能让旧给定patch、手写组织、旧仅生成预算结果充当A的证据。', '',
          '共同入口只处理最终完整补丁。项目M2计划/组件/组装适配尚未正式冻结；给定补丁入口通过不是策略运行通过。future模型仅父上下文/需求/公开例，评价材料隔离。', '',
          '当前按宏观计划交付研究候选和有证据的观察边界，不请求额外资源，不执行生成。']
with (ROOT / 'resource_boundary.md').open('x', encoding='utf-8') as output:
    output.write('\n'.join(lines) + '\n')
print(json.dumps({'eligible_finite_candidates': 2, 'pending': 1, 'minimum_calls_one_pair': 5,
                  'calls_two_tasks_one_seed': [10,12], 'current_generated': 0}, ensure_ascii=False))
