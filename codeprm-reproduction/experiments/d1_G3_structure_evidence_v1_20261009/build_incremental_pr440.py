from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPRO = ROOT.parents[1]
old = json.loads((ROOT / 'structure_records.json').read_text(encoding='utf-8'))
pr = json.loads((REPRO / 'experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/stage_result.json').read_text(encoding='utf-8'))
row = {
    'id': 'REPO_MORE_PR440_GROUP_LIFETIME_LIMITED', 'source': 'more-itertools',
    'mechanism_family': '非缓存组生命周期/回调归约', 'status': '有限行为候选',
    'external_entities': ['iterable', '相邻groupby组', 'keyfunc/valuefunc/reducefunc回调', '外层结果迭代器'],
    'legal_domain': '有限输入；list或sum等调用时完整消费组的回调；无界流/效率未纳入',
    'operation_history': '外层推进后，已返回归约值是否仍可读取；无reducefunc保留父懒行为',
    'task_obligation': 'reducefunc在组有效期内变换/归约，外层继续后已返回值保留；相邻组不合并',
    'interface_condition': 'groupby_transform实际reducefunc入口；标题正文groupfunc与源码名称差异已记录',
    'state_scope_evidence': '父/合并共享groupby底层迭代器；合法组织可在回调内保存结果，不指定列表/缓冲所有权',
    'testability_opportunity': '正常归约、外层推进后旧值、无reducefunc保持三种公开结果；不是多用途独立证明',
    'control_results': pr['results'],
    'organization': '官方合并与独立模块各3/3；延迟归约1/3；同助手/共用groupby-map有限观察',
    'unsupported_inference': ['不证明任意惰性回调永久有效', '不证明物化/缓存时间是唯一拆法', '不证明内存/效率或跨来源独立轴'],
    'evidence': ['experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/official_pr_metadata.json',
                 'experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/source_manifest.json',
                 'experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/behavior_feature.json',
                 'experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/behavior_late_reduction.json'],
    'formal_labels': None, 'split': None, 'human_reviews': 0, 'model_effect': None,
}
record = dict(old)
record['time'] = datetime.now(timezone.utc).isoformat()
record['records'] = old['records'] + [row]
record['candidate_tasks'] = 4
record['sources'] = ['cachetools', 'confuse', 'more-itertools']
record['bounded_behavior_candidates'] = 3
record['unresolved_strong_obligation_candidates'] = 1
record['new_behavior_calls'] = 0
record['incremental_from'] = str(ROOT / 'structure_records.json')
record['new_evidence_conclusion'] = 'PR440补充非缓存生命周期义务；任务外部结果可见，但组保存组织仍自由；四候选/三来源仍不足估计三轴关联'
record['support']['real_noncache_history'] = ['REPO_MORE_PR440_GROUP_LIFETIME_LIMITED']
record['support']['configuration_connection'] = ['PR126', 'PR142']
record['support']['cross_source_same_mechanism_support'] = False
record['next'] = 'G4仅更新资源下界/可比清单；不重跑行为或重建首轮交付'
with (ROOT / 'structure_records_v2.json').open('x', encoding='utf-8') as output:
    json.dump(record, output, ensure_ascii=False, indent=2)
with (ROOT / 'incremental_input_hashes.json').open('x', encoding='utf-8') as output:
    json.dump({'old_structure_records': hashlib.sha256((ROOT / 'structure_records.json').read_bytes()).hexdigest(),
               'PR440_stage_result': hashlib.sha256((REPRO / 'experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/stage_result.json').read_bytes()).hexdigest()}, output, indent=2)
print(json.dumps({'old_records': len(old['records']), 'new_records': len(record['records']),
                  'sources': record['sources'], 'new_behavior_calls': 0, 'formal_labels': None}, ensure_ascii=False))
