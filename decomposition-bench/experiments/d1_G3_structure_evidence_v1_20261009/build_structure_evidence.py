from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPRO = ROOT.parents[1]


def load(rel):
    return json.loads((REPRO / rel).read_text(encoding='utf-8'))


g1 = load('experiments/d1_G1_task_admission_v1_20261009/task_admission_and_gaps.json')
alternate = load('experiments/d1_repository_alternative_organization_v1_20261009/actual.json')
cache = load('experiments/d1_repository_expiry_public_oracle_v1_20261009/summary.json')
paths = load('experiments/d1_public_cleanup_observability_feasibility_v1_20261009/public_observation_paths_first_action.json')
env_root = 'experiments/d1_G2_confuse_pr142_env_source_v1_20261009/'
env = {label: load(env_root + 'behavior_' + label + '.json') for label in ('parent', 'feature', 'alternative', 'priority_omission')}
assert alternate['passed'] == 8 and alternate['total'] == 8
assert env['priority_omission']['cases'][2]['observed']['host']['value'] == 'file.local'
observing_cleanup = [r['symbol'] for r in paths['public_observation_methods']
                     if 'self.expire(time)' in r['source']]
rows = [
    {
        'id': 'REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS', 'source': 'confuse',
        'mechanism_family': '配置来源解释', 'status': '有限行为候选',
        'external_entities': ['Configuration/ConfigSource', 'Filename模板', '来源文件/应用目录'],
        'legal_domain': '八个保存公开API锚点；全域未知',
        'operation_history': '来源构建/文件加入后由配置视图读取路径；仅来源对象生命周期证据',
        'task_obligation': '来源路径基准/模板覆盖/文件入口决定最终Filename解析结果',
        'interface_condition': '固定公开来源/模板/文件载入入口；内部文件/helper次序不固定',
        'state_scope_evidence': '参考来源对象保存元数据；替代组织外部相容；不要求跨helper共享相同容器',
        'testability_opportunity': '开关/默认/绝对路径/载入入口可分别观察；不证明不同用途能独立验证',
        'control_results': g1['rows'][0]['behavior_evidence'],
        'organization': {'alternative_passed': alternate['passed'], 'total': alternate['total'],
                         'scope': '同八输入的单模块组织，不是全库等价'},
        'unsupported_inference': ['跨文件链不证明唯一阶段顺序', '多个开关不证明多个独立用途', '对象元数据不证明特定分解共享状态'],
        'evidence': [g1['rows'][0]['current_candidate'], 'experiments/d1_repository_alternative_organization_v1_20261009/actual.json'],
    },
    {
        'id': 'REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED', 'source': 'confuse',
        'mechanism_family': '配置来源解释', 'status': '有限PR子范围候选',
        'external_entities': ['环境变量', 'YAML文件来源', 'Configuration/配置视图'],
        'legal_domain': '无父子键冲突的嵌套字符串键/有效YAML标量/有限三个公开场景',
        'operation_history': 'set_file→set_env→get；显式加入次序约束公开优先级',
        'task_obligation': '环境名/值映射进入配置；最高优先覆盖与下层未提供键回退共同决定输出',
        'interface_condition': 'set_env入口/最高优先为构建者约束；PR不强制内部EnvSource/build_dict',
        'state_scope_evidence': '同Configuration内来源顺序影响后续get；不指定哪个helper拥有状态',
        'testability_opportunity': '来源单独有效/冲突整合可分别观察；host与timeout仍同一配置用途',
        'control_results': {label: {'passed': obj['passed'], 'total': obj['total']} for label, obj in env.items()},
        'organization': '官方来源类与父包独立env_overlay模块各3/3；共用既有Loader，同助手构造',
        'discriminating_observation': {'case': 'nested_overlay_and_fallback',
            'correct': env['feature']['cases'][2]['observed'],
            'priority_omission': env['priority_omission']['cases'][2]['observed']},
        'unsupported_inference': ['不覆盖PR列表/reload/完整YAML/冲突键', '来源解析通过不保证项目整合', '来源优先级不规定唯一解析/组合算法'],
        'evidence': [env_root + 'candidate/requirement.md', env_root + 'freeze_before_execution.json', env_root + 'behavior_feature.json', env_root + 'behavior_priority_omission.json'],
    },
    {
        'id': 'REPO_CACHETOOLS_EXPIRED_REPORT', 'source': 'cachetools',
        'mechanism_family': '缓存过期历史', 'status': '强时点条款/交付不一致待解决',
        'external_entities': ['TTLCache', '可控timer', '过期报告/公开容量和键视图'],
        'legal_domain': '五个保存公开场景；物理时点全域未识别',
        'operation_history': '插入/时间推进/expire改变本次报告和后续公开容量/可见键',
        'task_obligation': '报告本次过期(key,value)并完成清理；额外调用返回前物理完成条款保留待解决',
        'interface_condition': '公开expire/迭代/len/currsize观察；不得固定基类私有容器',
        'state_scope_evidence': '合法委托给内部缓存公开相容，外层基类空存储不能否定合法组织',
        'testability_opportunity': '报告和公开状态可分别观察，不等于两种独立应用用途',
        'control_results': cache['rows'],
        'organization': '完整/委托各5/5；报告/延迟各1/5；同五输入，不是四题',
        'observation_condition': {'public_reads_call_expire': observing_cleanup,
                                  'meaning': '测量可能补清理，公开状态符合不能证明先前物理完成'},
        'unresolved': g1['rows'][1]['delivery_defect'],
        'unsupported_inference': ['不得用消费后/补清理后的符合推返回前物理时点', '不能用基类私有存储统一判所有合法组织', '报告/状态两个字段不证明用途独立'],
        'evidence': [g1['rows'][1]['current_candidate'], 'experiments/d1_repository_expiry_public_oracle_v1_20261009/summary.json', 'experiments/d1_public_cleanup_observability_feasibility_v1_20261009/public_observation_paths_first_action.json'],
    },
]
for row in rows:
    row.update(formal_labels=None, split=None, human_reviews=0, model_effect=None)
sources = sorted({row['source'] for row in rows})
record = {'time': datetime.now(timezone.utc).isoformat(), 'plan': '202_G3_structure_evidence_plan.md',
    'records': rows, 'candidate_tasks': len(rows), 'sources': sources,
    'bounded_behavior_candidates': 2, 'unresolved_strong_obligation_candidates': 1,
    'new_behavior_calls': 0, 'new_model_calls': 0, 'human_reviews': 0,
    'new_evidence_conclusion': '行为义务/接口约束/组织证据/观察条件必须分层，当前不足形成统一正式三轴真值',
    'support': {'configuration_connection': ['PR126', 'PR142'], 'cache_history': ['TTLexpire'],
                'real_noncache_history': [], 'independent_multiple_uses': [],
                'cross_source_same_mechanism_support': False,
                'meaning': '两个配置任务同仓库同家族；缓存历史仅第二来源，机制/来源共变，不估独立结构因素'},
    'question_A': '同题方法配对仍可定义；收益未测，生成前正式标签未定，不外推结构因果或通用边界',
    'limitations': ['有限锚点/同助手构造/共享依赖，非独立人工真值', '公开源污染unknown/已登记暴露',
                    '无合法组织反例不证明独立，实际源文件次序非任务唯一次序'],
    'next': 'G4具体配对设计与资源下界，生成不开放',
}
with (ROOT / 'structure_records.json').open('x', encoding='utf-8') as output:
    json.dump(record, output, ensure_ascii=False, indent=2)
input_paths = ['experiments/d1_G1_task_admission_v1_20261009/task_admission_and_gaps.json',
               'experiments/d1_repository_alternative_organization_v1_20261009/actual.json',
               'experiments/d1_repository_expiry_public_oracle_v1_20261009/summary.json',
               'experiments/d1_public_cleanup_observability_feasibility_v1_20261009/public_observation_paths_first_action.json']
input_paths += [env_root + 'behavior_' + label + '.json' for label in env]
with (ROOT / 'input_evidence_hashes.json').open('x', encoding='utf-8') as output:
    json.dump({rel: hashlib.sha256((REPRO / rel).read_bytes()).hexdigest() for rel in input_paths}, output, indent=2)
print(json.dumps({'candidate_tasks': len(rows), 'sources': sources, 'bounded_candidates': 2,
                  'pending_candidates': 1, 'new_behavior_calls': 0, 'formal_labels': None}, ensure_ascii=False))
