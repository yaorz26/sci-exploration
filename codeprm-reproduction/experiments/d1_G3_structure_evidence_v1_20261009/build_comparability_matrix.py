from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPRO = ROOT.parents[1]


def read(rel):
    return json.loads((REPRO / rel).read_text(encoding='utf-8'))


structure = read('experiments/d1_G3_structure_evidence_v1_20261009/structure_records_v2.json')
allowed = {
    'REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS': {
        'input_domain': ('observed', '相对/绝对路径、配置来源/模板公开入口', ['experiments/d1_repository_feature_candidate_v1_20261009/actual_project_v1/structure_evidence_v1.json']),
        'operation_history': ('observed', '来源构建后再读取Filename，来源元数据影响后续路径', ['experiments/d1_repository_feature_candidate_v1_20261009/actual_project_v1/structure_evidence_v1.json']),
        'later_public_result': ('observed', '解析出的最终路径', ['experiments/d1_runnable_repository_task_v2_20261009/complete_actual.json']),
        'preserved_behavior_control': ('observed', '默认/绝对路径/父版本失败控制', ['experiments/d1_runnable_repository_task_v2_20261009/summary.json']),
        'cross_component_chain': ('observed', 'ConfigSource→core→Filename的有限数据链', ['experiments/d1_repository_feature_candidate_v1_20261009/actual_project_v1/structure_evidence_v1.json']),
        'public_interface_condition': ('observed', '固定ConfigSource/YamlSource/Filename/set_file入口', ['experiments/d1_runnable_repository_task_v2_20261009/candidate/requirement.md']),
        'legal_organization_freedom': ('observed_candidate', '同八输入单模块组织8/8；仅有限外部相容', ['experiments/d1_repository_alternative_organization_v1_20261009/actual.json']),
        'internal_state_ownership': ('unknown', '来源对象元数据如何存储不构成任务真值；未证全局/跨请求状态', ['experiments/d1_repository_feature_candidate_v1_20261009/actual_project_v1/structure_evidence_v1.json']),
        'observation_side_effect': ('observed', '公开读取本身未登记会改变配置源的副作用', ['experiments/d1_runnable_repository_task_v2_20261009/candidate/evaluate.py']),
        'source_family_confounding': ('observed', '与PR142同confuse来源/机制家族', ['experiments/d1_G3_structure_evidence_v1_20261009/structure_records_v2.json']),
        'A_use': ('limited', '可作为数据连接候选；不能单独估计结构因素或因果', ['experiments/d1_G4_pair_design_v1_20261009/paired_design_v2.json']),
    },
    'REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED': {
        'input_domain': ('observed', '前缀环境变量和普通YAML标量/嵌套键', ['experiments/d1_G2_confuse_pr142_env_source_v1_20261009/candidate/public_cases.json']),
        'operation_history': ('observed', 'set_file后set_env再get，来源顺序改变冲突字段', ['experiments/d1_G2_confuse_pr142_env_source_v1_20261009/behavior_feature.json']),
        'later_public_result': ('observed', 'Configuration视图的host/timeout/port读取', ['experiments/d1_G2_confuse_pr142_env_source_v1_20261009/behavior_feature.json']),
        'preserved_behavior_control': ('observed', '无匹配变量保留文件值，前缀外变量排除', ['experiments/d1_G2_confuse_pr142_env_source_v1_20261009/behavior_feature.json']),
        'cross_component_chain': ('observed', '环境/YAML来源→Configuration→配置视图', ['experiments/d1_G2_confuse_pr142_env_source_v1_20261009/stage_result.json']),
        'public_interface_condition': ('inferred_constraint', 'set_env最高优先是候选构建约束；PR正文强调显式opt-in/分层', ['experiments/d1_repository_feature_candidate_v1_20261009/confuse_pr142_metadata.json', 'experiments/d1_G2_confuse_pr142_env_source_v1_20261009/candidate/requirement.md']),
        'legal_organization_freedom': ('observed_candidate', '官方/独立env_overlay各3/3；共享Loader/同助手', ['experiments/d1_G2_confuse_pr142_env_source_v1_20261009/behavior_alternative.json']),
        'internal_state_ownership': ('unknown', '来源顺序影响get但不指定helper/容器所有权', ['experiments/d1_G2_confuse_pr142_env_source_v1_20261009/stage_result.json']),
        'observation_side_effect': ('observed_condition', 'worker显式清理命名空间；一般Configuration读取副作用未作全域断言', ['experiments/d1_G2_confuse_pr142_env_source_v1_20261009/candidate/evaluate_env_source.py']),
        'source_family_confounding': ('observed', '与PR126同confuse来源/配置机制家族', ['experiments/d1_G3_structure_evidence_v1_20261009/structure_records_v2.json']),
        'A_use': ('limited', '可作为连接义务候选；同confuse任务不能提供独立来源比较', ['experiments/d1_G4_pair_design_v1_20261009/paired_design_v2.json']),
    },
    'REPO_MORE_PR440_GROUP_LIFETIME_LIMITED': {
        'input_domain': ('observed', '相邻key的有限iterable和key/value/reduce回调', ['experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/candidate/public_cases.json']),
        'operation_history': ('observed', '外层推进后已归约组结果是否保留；无reduce保留父懒行为', ['experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/behavior_feature.json']),
        'later_public_result': ('observed', '外层(k,result)结果和旧懒group读取', ['experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/behavior_feature.json']),
        'preserved_behavior_control': ('observed', '父/feature/替代均通过无reduce父行为，延迟控制保留它', ['experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/stage_result.json']),
        'cross_component_chain': ('observed', 'groupby推进→回调消费/归约→外层读取', ['experiments/d1_G2_more_pr440_group_lifetime_v1_20260909/stage_result.json']),
        'public_interface_condition': ('observed', 'groupby_transform的实际reducefunc；PR标题正文groupfunc差异已记录', ['experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/candidate/requirement.md']),
        'legal_organization_freedom': ('observed_candidate', '官方/独立模块各3/3；延迟归约1/3', ['experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/stage_result.json']),
        'internal_state_ownership': ('unknown', '回调内保存结果是合法实现选择，未规定列表/缓存/iterator所有权', ['experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/candidate/requirement.md']),
        'observation_side_effect': ('observed', '推进外层会使未消费旧group失效；回调内结果在本域可观察', ['experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/behavior_late_reduction.json']),
        'source_family_confounding': ('observed', 'more-itertools单来源；与confuse/cache机制不共变支持', ['experiments/d1_G3_structure_evidence_v1_20261009/structure_records_v2.json']),
        'A_use': ('limited', '补K2历史义务；不构成三轴独立样本或结构因果', ['experiments/d1_G4_pair_design_v1_20261009/paired_design_v2.json']),
    },
    'REPO_CACHETOOLS_EXPIRED_REPORT': {
        'input_domain': ('observed', '可控timer、缓存键值与expire/公开状态调用', ['experiments/d1_repository_expiry_public_oracle_v1_202609/candidate/requirement.md']),
        'operation_history': ('observed', '插入/时间推进/expire改变报告与后续可见状态', ['experiments/d1_repository_expiry_public_oracle_v1_202609/summary.json']),
        'later_public_result': ('observed', '报告、len/currsize/迭代等公开结果', ['experiments/d1_repository_expiry_public_oracle_v1_202609/summary.json']),
        'preserved_behavior_control': ('observed', '完整/委托5/5、报告/延迟1/5', ['experiments/d1_repository_expiry_public_oracle_v1_202609/summary.json']),
        'cross_component_chain': ('observed', 'TTLCache状态→expire报告/公开容量', ['experiments/d1_public_cleanup_observability_feasibility_v1_20261009/public_observation_paths_first_action.json']),
        'public_interface_condition': ('observed', 'expire/len/currsize/迭代为公开观察', ['experiments/d1_public_cleanup_observability_feasibility_v1_20261009/public_observation_paths_first_action.json']),
        'legal_organization_freedom': ('observed_candidate', '完整/委托组织在五输入有限相容', ['experiments/d1_repository_expiry_public_oracle_v1_20261009/summary.json']),
        'internal_state_ownership': ('unknown', '基类私有容器不适合作所有合法组织判据', ['experiments/d1_repository_expiry_public_oracle_v1_20261009/summary.json']),
        'observation_side_effect': ('observed', 'len/currsize/部分读取调用expire，可能补清理', ['experiments/d1_public_cleanup_observability_feasibility_v1_20261009/public_observation_paths_first_action.json']),
        'source_family_confounding': ('observed', '单独cachetools来源/缓存机制；强时点条款未验收', ['experiments/d1_G3_structure_evidence_v1_20261009/structure_records_v2.json']),
        'A_use': ('not_ready', '可作为边界反例，但强时点未解，不能进入可用配对分母', ['experiments/d1_G1_task_admission_v1_20261009/task_admission_and_gaps.json']),
    },
}
# 修正上一段引用路径的历史日期拼写，保留原计划文本不改。
for row in allowed['REPO_MORE_PR440_GROUP_LIFETIME_LIMITED'].values():
    if isinstance(row, tuple):
        row[2][:] = [p.replace('20260909', '20261009') for p in row[2]]
rows = []
for candidate in structure['records']:
    matrix = allowed[candidate['id']]
    rows.append({'id': candidate['id'], 'source': candidate['source'],
                 'evidence_status': {field: {'status': value[0], 'description': value[1], 'evidence': value[2]}
                                     for field, value in matrix.items()},
                 'formal_label': None, 'split': None, 'human_reviews': 0,
                 'model_effect': None})
common = ['input_domain', 'operation_history', 'later_public_result', 'preserved_behavior_control',
          'cross_component_chain', 'public_interface_condition', 'legal_organization_freedom',
          'internal_state_ownership', 'observation_side_effect', 'source_family_confounding', 'A_use']
cross = {field: {row['id']: row['evidence_status'][field]['status'] for row in rows} for field in common}
conclusion = {
    'shared_observable_dimensions': ['operation_history', 'later_public_result', 'preserved_behavior_control', 'public_interface_condition'],
    'shared_dimensions_are_limited': '这些维度可用于候选筛选/评价协议，但机制不同，不能直接作为同一正式结构轴或因果变量',
    'task_specific_dimensions': {'PR126/PR142': '配置来源/优先级/路径解析链', 'PR440': '组生命周期/回调归约', 'cache': '过期清理报告与观察副作用'},
    'must_remain_unknown': ['internal_state_ownership全候选', 'cache返回前物理完成', '跨来源相同机制的独立性', '不同合法组织的全域等价', '结构—收益关联'],
    'g4_decision': '未来若做同题方法比较，使用任务级行为Y和逐任务证据；结构字段仅作候选筛选/分层描述，不估计三轴独立关联。cache不进入可用分母，PR126/142不能当独立confuse来源。',
    'why_not_packaging': '矩阵改变纳入与解释上限，否决把抽象数据流当统一结构标签；不增加任务/行为/文件数量',
}
result = {'time': datetime.now(timezone.utc).isoformat(), 'plan': '213_cross_candidate_observation_matrix_plan.md',
          'source_structure_file': 'structure_records_v2.json', 'records': rows, 'cross_field_status': cross,
          'conclusion': conclusion, 'new_behavior_calls': 0, 'new_model_calls': 0, 'human_reviews': 0,
          'formal_labels': None, 'split': None, 'procedural_note': '引用包含历史已有结构证据；非事前标签冻结'}
with (ROOT / 'comparability_matrix.json').open('x', encoding='utf-8') as output:
    json.dump(result, output, ensure_ascii=False, indent=2)
with (ROOT / 'comparability_input_hashes.json').open('x', encoding='utf-8') as output:
    json.dump({'structure_records_v2': hashlib.sha256((ROOT / 'structure_records_v2.json').read_bytes()).hexdigest()}, output, indent=2)
print(json.dumps({'records': len(rows), 'shared_dimensions': len(conclusion['shared_observable_dimensions']),
                  'unknown_dimensions': len(conclusion['must_remain_unknown']), 'new_behavior_calls': 0,
                  'formal_labels': None}, ensure_ascii=False))
