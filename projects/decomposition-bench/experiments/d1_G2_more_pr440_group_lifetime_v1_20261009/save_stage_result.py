from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPRO = ROOT.parents[1]


def new(path, value):
    with path.open('x', encoding='utf-8') as output:
        json.dump(value, output, ensure_ascii=False, indent=2)


labels = ('parent', 'feature', 'alternative', 'late_reduction')
results = {label: json.loads((ROOT / ('behavior_' + label + '.json')).read_text(encoding='utf-8')) for label in labels}
freeze = json.loads((ROOT / 'freeze_before_execution.json').read_text(encoding='utf-8'))
summary = {
    'time': datetime.now(timezone.utc).isoformat(), 'macro_stage': 'G2-v2-limited-extension',
    'task_id': 'REPO_MORE_PR440_GROUP_LIFETIME_LIMITED',
    'source': {'repo': 'more-itertools', 'pr': 440, 'parent': '38d070c9252d2138dbd86f8f85b9970741401cb6',
               'feature': '78405e9b24d0ccdd67785136ecd56774f38ae95e', 'merged_at': '2020-07-02T01:22:37Z'},
    'results': {label: {'passed': results[label]['passed'], 'total': results[label]['total'],
                        'prediction_match': [row['passed'] for row in results[label]['cases']] == freeze['predictions'][label]}
                for label in labels},
    'distinct_public_scenarios': 3, 'worker_runs': 12, 'source_files': 8, 'source_bytes': 236482,
    'behavior_observation': 'reducefunc在外层继续推进后保留list/sum结果；无reducefunc仍为父懒组；延迟归约关键两例失败',
    'contribution': '非缓存组生命周期/回调结果连接任务；外部结果义务与内部保存方式分开',
    'organization_limit': '官方实现与独立模块各3/3，共用groupby/map且同助手构造，有限域而非独立人类真值',
    'formal_labels': None, 'split': None, 'human_reviews': 0, 'model_calls': 0,
    'upstream_tests_read': False, 'private_or_curator_read': False,
    'next': 'G3增量结构证据：把组生命周期与PR126/PR142/TTL观察并列，不能宣称三轴独立',
}
new(ROOT / 'stage_result.json', summary)
new(ROOT / 'candidate/task.json', {
    'task_id': summary['task_id'], 'status': 'research_pool_only', 'source': summary['source'],
    'parent_workspace': 'workspaces/parent', 'requirement': 'requirement.md',
    'public_cases': 'public_cases.json', 'evaluator': 'evaluate_group_lifetime.py',
    'model_visible': ['workspaces/parent', 'requirement.md', 'public_cases.json'],
    'evaluation_only': ['workspaces/feature', 'workspaces/alternative', 'workspaces/late_reduction'],
    'formal_labels': None, 'split': None, 'human_reviews': 0,
    'contamination': 'unknown；既有暴露事件保留，当前未读测试/private/curator',
})
with (ROOT / 'input_evidence_hashes.json').open('x', encoding='utf-8') as output:
    json.dump({name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
               for name in ('candidate/requirement.md', 'candidate/public_cases.json', 'freeze_before_execution.json', 'source_manifest.json',
                             'behavior_parent.json', 'behavior_feature.json', 'behavior_alternative.json', 'behavior_late_reduction.json')}, output, indent=2)
print(json.dumps({'saved': True, 'worker_runs': 12, 'feature': '3/3', 'alternative': '3/3',
                  'parent': '1/3', 'late_reduction': '1/3'}, ensure_ascii=False))
