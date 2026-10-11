"""执行两个新溯源任务；不再次执行P74参考。"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from build_input_result_tree_pair import PROJECT, WORKSPACE, COMMIT, now, save, sha, strict

P74 = PROJECT / 'experiments/d1_input_result_tree_pair_v1_20261009'
OUT = PROJECT / 'experiments/d1_value_path_version_tasks_v1_20261009'

WHOLE = '''VALUE_RESULT = __VALUE__
PATH_RESULT = __PATH__
def solve(data):
    matches = []
    def walk(v, raw_path, new_path):
        if type(v) is dict:
            out = {}
            for k, x in v.items():
                if x is None and data['drop_null']:
                    continue
                out[k] = walk(x, raw_path + [k], new_path + [k])
            return out
        if type(v) is list:
            out = []
            for i, x in enumerate(v):
                if x is None and data['drop_null']:
                    continue
                out.append(walk(x, raw_path + [i], new_path + [len(out)]))
            return out
        if type(v) is int:
            value = v * data['factor'] if VALUE_RESULT else v
            if value >= data['threshold']:
                matches.append({'path': new_path if PATH_RESULT else raw_path, 'value': value})
            return v * data['factor']
        return None
    tree = walk(data['tree'], [], [])
    return {'tree': tree, 'matches': matches}
'''

HELPERS = '''VALUE_RESULT = __VALUE__
PATH_RESULT = __PATH__
def transform_with_provenance(v, factor, drop, raw_path, new_path, records):
    if type(v) is dict:
        out = {}
        for k, x in v.items():
            if not (drop and x is None):
                out[k] = transform_with_provenance(x, factor, drop, raw_path + [k], new_path + [k], records)
        return out
    if type(v) is list:
        out = []
        for i, x in enumerate(v):
            if not (drop and x is None):
                out.append(transform_with_provenance(x, factor, drop, raw_path + [i], new_path + [len(out)], records))
        return out
    if type(v) is int:
        records.append({'raw_path': raw_path, 'new_path': new_path, 'raw_value': v, 'new_value': v * factor})
        return v * factor
    return None

def select(records, threshold):
    value_key = 'new_value' if VALUE_RESULT else 'raw_value'
    path_key = 'new_path' if PATH_RESULT else 'raw_path'
    return [{'path': r[path_key], 'value': r[value_key]} for r in records if r[value_key] >= threshold]

def solve(data):
    records = []
    tree = transform_with_provenance(data['tree'], data['factor'], data['drop_null'], [], [], records)
    return {'tree': tree, 'matches': select(records, data['threshold'])}
'''


def prepare():
    OUT.mkdir(parents=True, exist_ok=False)
    prior = json.loads((P74 / 'public_diagnostic_anchors.json').read_text(encoding='utf-8'))
    # 两种混合版本的期望是执行前手算，不拼接待测程序输出。
    raw_value_new_path = {
        'factor_one': [{'path': ['b'], 'value': 3}],
        'factor_two': [{'path': ['b'], 'value': 3}],
        'keep_null': [{'path': ['a', 1], 'value': 4}],
        'drop_null': [{'path': ['a', 0], 'value': 4}],
        'factor_zero': [{'path': ['b'], 'value': 1}],
        'factor_negative': [{'path': ['a', 1], 'value': 2}],
    }
    new_value_raw_path = {
        'factor_one': [{'path': ['b'], 'value': 3}],
        'factor_two': [{'path': ['a', 1], 'value': 4}, {'path': ['b'], 'value': 6}],
        'keep_null': [{'path': ['a', 1], 'value': 4}],
        'drop_null': [{'path': ['a', 1], 'value': 4}],
        'factor_zero': [{'path': ['a', 1], 'value': 0}, {'path': ['b'], 'value': 0}],
        'factor_negative': [{'path': ['a', 0], 'value': 6}, {'path': ['b', 'k'], 'value': 2}],
    }
    anchors = [dict(case_id=c['case_id'], payload=c['payload'], expected={
        'raw_value_new_path': {'tree': c['expected']['input']['tree'], 'matches': raw_value_new_path[c['case_id']]},
        'new_value_raw_path': {'tree': c['expected']['input']['tree'], 'matches': new_value_raw_path[c['case_id']]}})
        for c in prior]
    save(OUT / 'public_diagnostic_anchors.json', anchors)
    task_options = [
        ('raw_value_new_path', 'E_B13', False, True,
         '按原输入整数值检索并返回该原值，但path采用该整数保留在变换结果树中的位置。这是溯源值和处理后坐标，value不要求等于输出tree在path处的值。'),
        ('new_value_raw_path', 'E_B14', True, False,
         '按乘factor后的整数值检索并返回该处理值，但path采用对应整数在原输入树中的位置，用来定位修改来源；path不要求是变换结果树中的坐标。'),
    ]
    base_requirement = (P74 / 'tasks/E_B11/requirement.md').read_text(encoding='utf-8')
    old_clause = '在输入原树上检索；matches采用原树的值与路径。'
    for variant, task_id, value_result, path_result, clause in task_options:
        folder = OUT / 'tasks' / task_id
        folder.mkdir(parents=True)
        requirement = base_requirement.replace(old_clause, clause).replace(
            'path是该检索树中该叶的位置', 'path按上文规定使用原输入或变换结果树坐标')
        assert old_clause not in requirement
        (folder / 'requirement.md').write_text(requirement, encoding='utf-8')
        save(folder / 'task.json', dict(task_id=task_id, source='boltons', source_commit=COMMIT,
            source_apis=['remap', 'research'], source_snapshot='../../../d1_input_result_tree_pair_v1_20261009/source',
            license='BSD-3-Clause', family_id='nested_integer_transform_search', value_version='result' if value_result else 'input',
            path_version='result' if path_result else 'input', entrypoint='solve(data)',
            candidate_status='research_pool_only', split=None, formal_labels=None, human_reviews=0,
            published=False, requirement_file='requirement.md', private_reads=0,
            task_semantics='值与坐标分开定义的溯源适配；不是原库已有联合API',
            natural_project_demand='未验证，不以程序通过替代项目需求证据'))
        save(folder / 'public_examples.json', [dict(case_id=c['case_id'], input=c['payload'], output=c['expected'][variant]) for c in anchors])
        ref_dir = OUT / 'references' / variant
        ref_dir.mkdir(parents=True)
        for name, template in [('whole', WHOLE), ('helpers', HELPERS)]:
            (ref_dir / (name + '.py')).write_text(template.replace('__VALUE__', str(value_result)).replace('__PATH__', str(path_result)), encoding='utf-8')
    files = [p for p in OUT.rglob('*') if p.is_file()]
    save(OUT / 'execution_freeze.json', dict(created_at=now(), stage='D1-P75-value-path-version-tasks',
        seed=None, expected_solve_calls=24, unique_inputs_added=0, public_inputs_reused=6, task_diagnostic_records_added=12,
        file_sha256={p.relative_to(OUT).as_posix(): sha(p) for p in files},
        p74_summary_sha256=sha(P74 / 'summary.json'), p74_anchors_sha256=sha(P74 / 'public_diagnostic_anchors.json'),
        contract_sha256=sha(WORKSPACE / 'docs/week3/data-route/20261009/156_value_path_version_tasks_contract.md'),
        predictions=dict(each_reference_passes=6, input_mutations=0,
            raw_value_new_path={'factor_equal': True, 'drop_null_equal': False},
            new_value_raw_path={'factor_equal': False, 'drop_null_equal': True}),
        formal_labels=None, human_reviews=0, model_calls=0, private_reads=0))
    print(json.dumps({'prepared': str(OUT), 'files': len(files)}))


def run():
    frozen = json.loads((OUT / 'execution_freeze.json').read_text(encoding='utf-8'))
    assert all(sha(OUT / rel) == h for rel, h in frozen['file_sha256'].items())
    assert sha(P74 / 'summary.json') == frozen['p74_summary_sha256']
    save(OUT / 'execution_started.json', dict(started_at=now(), frozen_at=frozen['created_at'], python=sys.version,
        command='python -B -X utf8 scripts/d1/build_value_path_version_tasks.py run', p74_reference_calls=0))
    anchors = json.loads((OUT / 'public_diagnostic_anchors.json').read_text(encoding='utf-8'))
    rows = []
    with (OUT / 'raw_execution.jsonl').open('x', encoding='utf-8') as log:
        for variant in ['raw_value_new_path', 'new_value_raw_path']:
            for name in ['whole', 'helpers']:
                for c in anchors:
                    ref = OUT / 'references' / variant / (name + '.py')
                    proc = subprocess.run([sys.executable, '-B', '-I', '-S', str(PROJECT / 'scripts/d1/build_input_result_tree_pair.py'),
                        'worker', '--reference', str(ref)], input=json.dumps(c['payload']), text=True, encoding='utf-8',
                        capture_output=True, timeout=20)
                    assert len(proc.stdout.encode('utf-8')) + len(proc.stderr.encode('utf-8')) <= 1024 * 1024
                    returned = json.loads(proc.stdout) if proc.returncode == 0 else None
                    row = dict(variant=variant, reference=name, case_id=c['case_id'], returncode=proc.returncode,
                        stdout=proc.stdout, stderr=proc.stderr, returned=returned,
                        passed=bool(returned and strict(returned['output'], c['expected'][variant])),
                        input_unchanged=bool(returned and strict(returned['input_after'], c['payload'])))
                    log.write(json.dumps(row, ensure_ascii=False) + '\n'); log.flush(); rows.append(row)
    relations = []
    for variant in ['raw_value_new_path', 'new_value_raw_path']:
        for name in ['whole', 'helpers']:
            lookup = {r['case_id']: r['returned']['output']['matches'] for r in rows
                      if r['variant'] == variant and r['reference'] == name and r['returned']}
            for left, right, intervention in [('factor_one', 'factor_two', 'factor'), ('keep_null', 'drop_null', 'drop_null')]:
                expected = frozen['predictions'][variant][intervention + '_equal']
                equal = strict(lookup[left], lookup[right]) if left in lookup and right in lookup else None
                relations.append(dict(variant=variant, reference=name, intervention=intervention,
                    before=lookup.get(left), after=lookup.get(right), equal=equal, expected_equal=expected, passed=equal is expected))
    # P74的对角任务只读保存关系，零旧程序求值。
    old = json.loads((P74 / 'summary.json').read_text(encoding='utf-8'))
    evidence_matrix = []
    for variant, source_rows in [('input', old['relations']), ('raw_value_new_path', relations),
                                 ('new_value_raw_path', relations), ('result', old['relations'])]:
        relevant = [r for r in source_rows if r['variant'] == variant]
        evidence_matrix.append(dict(variant=variant, factor_changes=all(r['equal'] is False for r in relevant if r['intervention'] == 'factor'),
            drop_null_changes=all(r['equal'] is False for r in relevant if r['intervention'] == 'drop_null'),
            evidence_kind='保存的新任务输出关系，非模型效应或正式标签'))
    summary = dict(completed_at=now(), stage='D1-P75-value-path-version-tasks', unique_inputs_added=0,
        public_inputs_reused=6, task_diagnostic_records_added=12, actual_solve_calls=len(rows),
        passed=sum(r['passed'] for r in rows), input_unchanged=sum(r['input_unchanged'] for r in rows),
        by_reference={v+'/'+n: {'passed': sum(r['passed'] for r in rows if r['variant']==v and r['reference']==n), 'total': 6}
                      for v in ['raw_value_new_path', 'new_value_raw_path'] for n in ['whole', 'helpers']},
        relations=relations, relation_passed=sum(r['passed'] for r in relations), evidence_matrix=evidence_matrix,
        p74_reference_calls=0, model_calls=0, external_api_calls=0, private_reads=0, human_reviews=0,
        formal_labels=None, published=False, limitations=['新增两任务并非两个独立家族', '同一助手参考非独立真值',
            '六锚点非全域', '混合版本真实项目需求与自然性未验证', '不证明模型拆分收益'])
    save(OUT / 'summary.json', summary)
    print(json.dumps({k:summary[k] for k in ['actual_solve_calls','passed','input_unchanged','relation_passed','evidence_matrix']},ensure_ascii=False))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('action',choices=['prepare','run'])
    args=parser.parse_args()
    prepare() if args.action=='prepare' else run()
