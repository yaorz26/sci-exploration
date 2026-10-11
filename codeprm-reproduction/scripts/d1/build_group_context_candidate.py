"""组上下文候选：六个手算公开锚点，冻结后执行18次。"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from build_input_result_tree_pair import PROJECT, WORKSPACE, now, save, sha, strict

ROOT = PROJECT / 'experiments/d1_group_context_candidate_v1_20261009'
OUT = ROOT / 'execution_v1'
SOURCE = PROJECT / 'data/raw/d1_project_v1_20261008/repositories/more_itertools'
COMMIT = '81c21a8db1c922260cd673841257fb9b112c1318'

REQUIREMENT = '''实现solve(data)。data包含items和threshold。items是按输入順序给出的
{group,value}列表，group是字符串，value是精确int，不含bool；长度≤16，整数绝对值≤32。
threshold是[-16,64]精确整数。只要求合法域，不得改变输入。
按group首次出现顺序分组。每组取本组最小值base，对原序每个值计算normalized=value-base，
再计算total=sum(normalized)。只保留total≥threshold的组。
输出恰含groups字段，groups为保留组记录列表，每条恰含group、normalized、total。
保留重复项及组内顺序，空输入返回{"groups":[]}。内部结构、helper与执行次序自由。
这是基于公开map_reduce聚合功能的研究适配，未声称上游已有这一联合需求。
'''

WHOLE = '''def solve(data):
    buckets = {}
    for item in data['items']:
        buckets.setdefault(item['group'], []).append(item['value'])
    groups = []
    for name, values in buckets.items():
        base = min(values)
        normalized = [v - base for v in values]
        total = sum(normalized)
        if total >= data['threshold']:
            groups.append({'group': name, 'normalized': normalized, 'total': total})
    return {'groups': groups}
'''

HELPERS = '''def group_values(items):
    groups = {}
    for item in items:
        groups.setdefault(item['group'], []).append(item['value'])
    return groups

def normalize(values):
    base = min(values)
    output = [v - base for v in values]
    return output, sum(output)

def solve(data):
    result = []
    for name, values in group_values(data['items']).items():
        normalized, total = normalize(values)
        if total >= data['threshold']:
            result.append({'group': name, 'normalized': normalized, 'total': total})
    return {'groups': result}
'''

SOURCE_ADAPTER = '''from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'source'))
from more_itertools import more
API_CALLS = {'map_reduce': 0}
_map_reduce = more.map_reduce
def counted_map_reduce(*args, **kwargs):
    API_CALLS['map_reduce'] += 1
    return _map_reduce(*args, **kwargs)
more.map_reduce = counted_map_reduce

def solve(data):
    def reduce(values):
        base = min(values)
        normalized = [v - base for v in values]
        return normalized, sum(normalized)
    reduced = more.map_reduce(data['items'], keyfunc=lambda x: x['group'],
                              valuefunc=lambda x: x['value'], reducefunc=reduce)
    # 顺序来自新任务要求，显式从输入获取，不依赖原API未声明的返回顺序。
    order = list(dict.fromkeys(x['group'] for x in data['items']))
    return {'groups': [{'group': key, 'normalized': reduced[key][0], 'total': reduced[key][1]}
                       for key in order if reduced[key][1] >= data['threshold']]}
'''


def anchors():
    items = [{'group': 'a', 'value': 3}, {'group': 'b', 'value': 7},
             {'group': 'a', 'value': 5}, {'group': 'b', 'value': 9}]
    changed = [{'group': 'a', 'value': 1}, {'group': 'b', 'value': 7},
               {'group': 'a', 'value': 5}, {'group': 'b', 'value': 9}]
    a2 = {'group': 'a', 'normalized': [0, 2], 'total': 2}
    a4 = {'group': 'a', 'normalized': [0, 4], 'total': 4}
    b2 = {'group': 'b', 'normalized': [0, 2], 'total': 2}
    return [
        {'case_id': 'baseline_visible', 'payload': {'items': items, 'threshold': 0}, 'expected': {'groups': [a2, b2]}},
        {'case_id': 'same_group_changed', 'payload': {'items': changed, 'threshold': 0}, 'expected': {'groups': [a4, b2]}},
        {'case_id': 'baseline_filtered', 'payload': {'items': items, 'threshold': 3}, 'expected': {'groups': []}},
        {'case_id': 'same_group_filtered', 'payload': {'items': changed, 'threshold': 3}, 'expected': {'groups': [a4]}},
        {'case_id': 'empty', 'payload': {'items': [], 'threshold': 3}, 'expected': {'groups': []}},
        {'case_id': 'negative_duplicate', 'payload': {'items': [{'group': 'z', 'value': -2}, {'group': 'z', 'value': -2}],
          'threshold': 0}, 'expected': {'groups': [{'group': 'z', 'normalized': [0, 0], 'total': 0}]}},
    ]


def prepare():
    OUT.mkdir(parents=True, exist_ok=False)
    snap = OUT / 'source'; (snap / 'more_itertools').mkdir(parents=True)
    source_manifest = json.loads((PROJECT / 'data/raw/d1_project_v1_20261008/manifests/more_itertools.json').read_text(encoding='utf-8'))
    assert source_manifest['commit'] == COMMIT
    for rel in ['more_itertools/__init__.py', 'more_itertools/more.py', 'more_itertools/recipes.py', 'LICENSE']:
        shutil.copyfile(SOURCE / rel, snap / rel)
        assert sha(snap / rel) == source_manifest['source_hashes'][rel]
    candidate = OUT / 'candidate'; candidate.mkdir()
    (candidate / 'requirement.md').write_text(REQUIREMENT, encoding='utf-8')
    save(candidate / 'task.json', dict(task_id='E_M08', source='more_itertools', source_commit=COMMIT,
        source_api='map_reduce', license='MIT', entrypoint='solve(data)', family_id='group_context_normalization',
        related_family='D1_M04分桶功能相关但无操作脚本；不假定独立', candidate_status='research_pool_only',
        formal_labels=None, split=None, human_reviews=0, published=False, private_reads=0,
        validity_scope='合法整数列表；六锚点有限验证，轻量功能适配',
        source_requirement_origin='本研究构造，不是上游真实issue或已有联合API'))
    save(OUT / 'public_diagnostic_anchors.json', anchors())
    save(candidate / 'public_examples.json', [dict(case_id=c['case_id'], input=c['payload'], output=c['expected']) for c in anchors()])
    refs = OUT / 'references'; refs.mkdir()
    for name, code in [('whole', WHOLE), ('helpers', HELPERS), ('source_adapter', SOURCE_ADAPTER)]:
        (refs / (name + '.py')).write_text(code, encoding='utf-8')
    files = [p for p in OUT.rglob('*') if p.is_file()]
    save(OUT / 'execution_freeze.json', dict(created_at=now(), stage='D1-P76-group-context-candidate', seed=None,
        expected_solve_calls=18, unique_inputs=6, task_records=6, predictions={'each_reference_passes': 6,
        'same_group_unchanged_item': [2, 4], 'other_group_equal': True, 'threshold_selection_changes': True},
        file_sha256={p.relative_to(OUT).as_posix(): sha(p) for p in files},
        contract_sha256=sha(WORKSPACE / 'docs/week3/data-route/20261009/159_group_context_execution_contract.md'),
        script_sha256=sha(Path(__file__).resolve()),
        initial20_sha256=sha(PROJECT / 'data/processed/d1_project_initial20_v5_20261008/manifest.json'),
        model_calls=0, private_reads=0, human_reviews=0, formal_labels=None))
    print(json.dumps({'prepared': str(OUT), 'frozen_files': len(files)}, ensure_ascii=False))


def run():
    freeze = json.loads((OUT / 'execution_freeze.json').read_text(encoding='utf-8'))
    assert all(sha(OUT / rel) == h for rel, h in freeze['file_sha256'].items())
    assert sha(Path(__file__).resolve()) == freeze['script_sha256']
    save(OUT / 'execution_started.json', dict(started_at=now(), frozen_at=freeze['created_at'], python=sys.version,
        command='python -B -X utf8 scripts/d1/build_group_context_candidate.py run'))
    public = json.loads((OUT / 'public_diagnostic_anchors.json').read_text(encoding='utf-8'))
    rows = []
    with (OUT / 'raw_execution.jsonl').open('x', encoding='utf-8') as log:
        for name in ['whole', 'helpers', 'source_adapter']:
            for c in public:
                p = subprocess.run([sys.executable, '-B', '-I', '-S', str(PROJECT / 'scripts/d1/build_input_result_tree_pair.py'),
                    'worker', '--reference', str(OUT / 'references' / (name + '.py'))], input=json.dumps(c['payload']),
                    text=True, encoding='utf-8', capture_output=True, timeout=20)
                assert len(p.stdout.encode('utf-8')) + len(p.stderr.encode('utf-8')) <= 1024 * 1024
                returned = json.loads(p.stdout) if p.returncode == 0 else None
                row = dict(reference=name, case_id=c['case_id'], returncode=p.returncode, stdout=p.stdout, stderr=p.stderr,
                    returned=returned, passed=bool(returned and strict(returned['output'], c['expected'])),
                    input_unchanged=bool(returned and strict(returned['input_after'], c['payload'])))
                log.write(json.dumps(row, ensure_ascii=False) + '\n'); log.flush(); rows.append(row)
    relations = []
    for name in ['whole', 'helpers', 'source_adapter']:
        lookup = {r['case_id']: r['returned']['output'] for r in rows if r['reference'] == name and r['returned']}
        before = lookup.get('baseline_visible', {}).get('groups', [])
        after = lookup.get('same_group_changed', {}).get('groups', [])
        b = {r['group']: r for r in before}; a = {r['group']: r for r in after}
        observed = [b.get('a', {}).get('normalized', [None, None])[1], a.get('a', {}).get('normalized', [None, None])[1]]
        relations.append(dict(reference=name, relation='same_group_unchanged_item_changes', observed=observed, passed=observed == [2, 4]))
        equal = strict(b['b'], a['b']) if 'b' in b and 'b' in a else None
        relations.append(dict(reference=name, relation='other_group_invariant', before=b.get('b'), after=a.get('b'), passed=equal is True))
        filtered_before = lookup.get('baseline_filtered', {}).get('groups')
        filtered_after = lookup.get('same_group_filtered', {}).get('groups')
        selected = bool(filtered_before == [] and filtered_after and [r['group'] for r in filtered_after] == ['a'])
        relations.append(dict(reference=name, relation='threshold_selection_changes', before=filtered_before, after=filtered_after, passed=selected))
    old_manifest = PROJECT / 'data/processed/d1_project_initial20_v5_20261008/manifest.json'
    summary = dict(completed_at=now(), stage='D1-P76-group-context-candidate', task_id='E_M08', unique_inputs=6,
        task_records=6, actual_solve_calls=len(rows), passed=sum(r['passed'] for r in rows),
        input_unchanged=sum(r['input_unchanged'] for r in rows),
        by_reference={n: {'passed': sum(r['passed'] for r in rows if r['reference'] == n), 'total': 6} for n in ['whole', 'helpers', 'source_adapter']},
        source_api_calls={'map_reduce': sum(r['returned']['api_calls'].get('map_reduce', 0) for r in rows if r['returned'])},
        relations=relations, relation_passed=sum(r['passed'] for r in relations),
        initial20_unchanged=sha(old_manifest) == freeze['initial20_sha256'], model_calls=0, private_reads=0, human_reviews=0,
        formal_labels=None, split=None, published=False,
        limitations=['六锚点非全域', '同助手三参考非独立真值', '本研究构造需求非上游真实功能请求',
                     '内部多函数不是模型拆分效果', '轻量库功能适配非完整项目集成', '不假定相关家族独立'])
    save(OUT / 'summary.json', summary)
    print(json.dumps({k: summary[k] for k in ['actual_solve_calls', 'passed', 'input_unchanged', 'source_api_calls', 'relation_passed']}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('action', choices=['prepare', 'run'])
    args = parser.parse_args()
    prepare() if args.action == 'prepare' else run()
