"""构建并执行新研究候选；期望值手写，旧测试不参与，输出只追加。"""
import argparse
import copy
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

PROJECT = Path(__file__).resolve().parents[2]
WORKSPACE = PROJECT.parent
OUT = PROJECT / 'experiments/d1_input_result_tree_pair_v1_20261009'
SOURCE = PROJECT / 'data/raw/d1_project_v1_20261008/repositories/boltons'
COMMIT = '4e5faa3d7e4008d89e0d8bf1ea87b6d9a061a16d'


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, obj):
    with path.open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')


def match(path, value):
    return {'path': path, 'value': value}


def cases():
    # 锚点来自契约154的事前手算，不调用待测参考。
    raw = [
        ('factor_one', {'a': [None, 2, -1], 'b': 3}, 1, True, 3,
         {'a': [2, -1], 'b': 3}, [match(['b'], 3)], [match(['b'], 3)]),
        ('factor_two', {'a': [None, 2, -1], 'b': 3}, 2, True, 3,
         {'a': [4, -2], 'b': 6}, [match(['b'], 3)], [match(['a', 0], 4), match(['b'], 6)]),
        ('keep_null', {'a': [None, 4], 'b': [1]}, 1, False, 3,
         {'a': [None, 4], 'b': [1]}, [match(['a', 1], 4)], [match(['a', 1], 4)]),
        ('drop_null', {'a': [None, 4], 'b': [1]}, 1, True, 3,
         {'a': [4], 'b': [1]}, [match(['a', 1], 4)], [match(['a', 0], 4)]),
        ('factor_zero', {'a': [None, -2], 'b': 1}, 0, True, 0,
         {'a': [0], 'b': 0}, [match(['b'], 1)], [match(['a', 0], 0), match(['b'], 0)]),
        ('factor_negative', {'a': [-3, 2], 'b': {'z': None, 'k': -1}}, -2, True, 2,
         {'a': [6, -4], 'b': {'k': 2}}, [match(['a', 1], 2)],
         [match(['a', 0], 6), match(['b', 'k'], 2)]),
    ]
    return [dict(case_id=i, payload=dict(tree=t, factor=f, drop_null=d, threshold=h),
                 expected={
                     'input': {'tree': out, 'matches': inp},
                     'result': {'tree': out, 'matches': res}})
            for i, t, f, d, h, out, inp, res in raw]


WHOLE = '''SEARCH_RESULT = __FLAG__
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
            transformed = v * data['factor']
            selected = transformed if SEARCH_RESULT else v
            if selected >= data['threshold']:
                matches.append({'path': new_path if SEARCH_RESULT else raw_path,
                                'value': selected})
            return transformed
        return None
    tree = walk(data['tree'], [], [])
    return {'tree': tree, 'matches': matches}
'''

HELPERS = '''SEARCH_RESULT = __FLAG__
def transform(v, factor, drop):
    if type(v) is dict:
        return {k: transform(x, factor, drop) for k, x in v.items()
                if not (drop and x is None)}
    if type(v) is list:
        return [transform(x, factor, drop) for x in v if not (drop and x is None)]
    return v * factor if type(v) is int else None

def scan(v, threshold, path, found):
    if type(v) is dict:
        for k, x in v.items():
            scan(x, threshold, path + [k], found)
    elif type(v) is list:
        for i, x in enumerate(v):
            scan(x, threshold, path + [i], found)
    elif type(v) is int and v >= threshold:
        found.append({'path': path, 'value': v})

def solve(data):
    tree = transform(data['tree'], data['factor'], data['drop_null'])
    found = []
    scan(tree if SEARCH_RESULT else data['tree'], data['threshold'], [], found)
    return {'tree': tree, 'matches': found}
'''

SOURCE_ADAPTER = '''from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'source'))
from boltons import iterutils
SEARCH_RESULT = __FLAG__
API_CALLS = {'remap': 0, 'research': 0}
_remap, _research = iterutils.remap, iterutils.research
def counted_remap(*args, **kwargs):
    API_CALLS['remap'] += 1
    return _remap(*args, **kwargs)
def counted_research(*args, **kwargs):
    API_CALLS['research'] += 1
    return _research(*args, **kwargs)
iterutils.remap = counted_remap
iterutils.research = counted_research

def solve(data):
    def visit(path, key, value):
        if value is None and data['drop_null']:
            return False
        if type(value) is int:
            return key, value * data['factor']
        return key, value
    tree = iterutils.remap(data['tree'], visit=visit)
    found = iterutils.research(
        tree if SEARCH_RESULT else data['tree'],
        query=lambda p, k, v: type(v) is int and v >= data['threshold'],
        reraise=True)
    return {'tree': tree, 'matches': [{'path': list(p), 'value': v} for p, v in found]}
'''


COMMON_REQUIREMENT = '''实现solve(data)。data包含tree、factor、drop_null、threshold。
合法域：tree根为dict或list；dict键为字符串；叶仅为精确整数或null，不含bool；
根深度0，最大深度4，含容器节点最多64，原整数绝对值≤64。
factor为[-3,3]整数，threshold为[-32,32]整数，drop_null为bool。只要求合法输入域。
输出恰含tree、matches两字段。tree是把每个整数叶乘factor、按drop_null删除null项后
得到的新树；删除列表元素后下标连续，保留dict顺序和空容器。不得改变输入。
__SEARCH_CLAUSE__
matches为按dict插入顺序和list下标顺序进行深度优先遍历得到的整数叶记录，
每条恰含path和value：value≥threshold，path是该检索树中该叶的位置，
包含字符串键和整数下标。不强制内部函数数量、接口、遍历次数或执行顺序。
'''


def prepare():
    OUT.mkdir(parents=True, exist_ok=False)
    snap = OUT / 'source'
    (snap / 'boltons').mkdir(parents=True)
    for rel in ['boltons/iterutils.py', 'boltons/__init__.py', 'LICENSE']:
        shutil.copyfile(SOURCE / rel, snap / rel)
    source_manifest = json.loads((PROJECT / 'data/raw/d1_project_v1_20261008/manifests/boltons.json').read_text(encoding='utf-8'))
    assert source_manifest['commit'] == COMMIT
    for rel in ['boltons/iterutils.py', 'boltons/__init__.py', 'LICENSE']:
        assert sha(snap / rel) == source_manifest['source_hashes'][rel]
    anchors = cases()
    save(OUT / 'public_diagnostic_anchors.json', anchors)
    for variant, task_id in [('input', 'E_B11'), ('result', 'E_B12')]:
        folder = OUT / 'tasks' / task_id
        folder.mkdir(parents=True)
        clause = ('在输入原树上检索；matches采用原树的值与路径。' if variant == 'input'
                  else '在变换结果树上检索；matches采用结果树的值与路径。')
        requirement = COMMON_REQUIREMENT.replace('__SEARCH_CLAUSE__', clause)
        (folder / 'requirement.md').write_text(requirement, encoding='utf-8')
        save(folder / 'task.json', dict(task_id=task_id, source='boltons', source_commit=COMMIT,
             source_apis=['remap', 'research'], license='BSD-3-Clause', family_id='nested_integer_transform_search',
             search_version=variant, entrypoint='solve(data)', candidate_status='research_pool_only',
             split=None, formal_labels=None, human_reviews=0, published=False,
             validity_scope='公开整数树合法域；六锚点不是全域证明', requirement_file='requirement.md',
             model_prompt_exposure='未向模型发送', private_reads=0))
        save(folder / 'public_examples.json', [dict(case_id=c['case_id'], input=c['payload'],
                                                   output=c['expected'][variant]) for c in anchors])
        ref_dir = OUT / 'references' / variant
        ref_dir.mkdir(parents=True)
        for name, template in [('whole', WHOLE), ('helpers', HELPERS), ('source_adapter', SOURCE_ADAPTER)]:
            (ref_dir / (name + '.py')).write_text(template.replace('__FLAG__', str(variant == 'result')), encoding='utf-8')
    files = [p for p in OUT.rglob('*') if p.is_file()]
    freeze = dict(created_at=now(), stage='D1-P74-input-result-tree-pair', seed=None,
                  unique_input_count=6, task_diagnostic_records=12, expected_solve_calls=36,
                  references_authorship='同一助手；非独立审查', formal_labels=None, human_reviews=0,
                  file_sha256={p.relative_to(OUT).as_posix(): sha(p) for p in files},
                  contract_sha256=sha(WORKSPACE / 'docs/week3/data-route/20261009/154_input_result_tree_pair_contract.md'),
                  initial20_sha256=sha(PROJECT / 'data/processed/d1_project_initial20_v5_20261008/manifest.json'),
                  predictions=dict(each_reference_passes=6, input_mutations=0,
                    input_intervention_invariances=2, result_intervention_changes=2,
                    variant_different_cases=4), model_calls=0, private_reads=0)
    save(OUT / 'execution_freeze.json', freeze)
    print(json.dumps({'prepared': str(OUT), 'frozen_files': len(files), 'created_at': freeze['created_at']}))


def strict(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return list(a) == list(b) and all(strict(a[k], b[k]) for k in a)
    if type(a) is list:
        return len(a) == len(b) and all(strict(x, y) for x, y in zip(a, b))
    return a == b


def worker(path):
    data = json.load(sys.stdin)
    spec = importlib.util.spec_from_file_location('candidate_reference', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    value = module.solve(data)
    print(json.dumps(dict(output=value, input_after=data, api_calls=getattr(module, 'API_CALLS', {}))))


def run():
    freeze = json.loads((OUT / 'execution_freeze.json').read_text(encoding='utf-8'))
    assert all(sha(OUT / rel) == expected for rel, expected in freeze['file_sha256'].items())
    old_manifest = PROJECT / 'data/processed/d1_project_initial20_v5_20261008/manifest.json'
    assert sha(old_manifest) == freeze['initial20_sha256']
    save(OUT / 'execution_started.json', dict(started_at=now(), frozen_at=freeze['created_at'],
                                              python=sys.version, command='python -B -X utf8 scripts/d1/build_input_result_tree_pair.py run'))
    anchors = json.loads((OUT / 'public_diagnostic_anchors.json').read_text(encoding='utf-8'))
    rows = []
    with (OUT / 'raw_execution.jsonl').open('x', encoding='utf-8') as log:
        for variant in ['input', 'result']:
            for name in ['whole', 'helpers', 'source_adapter']:
                path = OUT / 'references' / variant / (name + '.py')
                for c in anchors:
                    completed = subprocess.run([sys.executable, '-B', '-I', '-S', str(Path(__file__).resolve()),
                        'worker', '--reference', str(path)], input=json.dumps(c['payload']), text=True,
                        encoding='utf-8', capture_output=True, timeout=20)
                    assert len(completed.stdout.encode('utf-8')) + len(completed.stderr.encode('utf-8')) <= 1024 * 1024
                    returned = json.loads(completed.stdout) if completed.returncode == 0 else None
                    row = dict(variant=variant, reference=name, case_id=c['case_id'],
                               returncode=completed.returncode, stdout=completed.stdout, stderr=completed.stderr,
                               returned=returned,
                               passed=bool(returned is not None and strict(returned['output'], c['expected'][variant])),
                               input_unchanged=bool(returned is not None and strict(returned['input_after'], c['payload'])))
                    log.write(json.dumps(row, ensure_ascii=False) + '\n')
                    log.flush()
                    rows.append(row)
    relations = []
    for name in ['whole', 'helpers', 'source_adapter']:
        for variant in ['input', 'result']:
            lookup = {r['case_id']: r['returned']['output']['matches'] for r in rows
                      if r['variant'] == variant and r['reference'] == name and r['returned'] is not None}
            for left, right, intervention in [('factor_one', 'factor_two', 'factor'), ('keep_null', 'drop_null', 'drop_null')]:
                equal = strict(lookup[left], lookup[right]) if left in lookup and right in lookup else None
                relations.append(dict(reference=name, variant=variant, intervention=intervention,
                                      before=lookup.get(left), after=lookup.get(right), equal=equal,
                                      predicted_equal=(variant == 'input'), passed=(equal is (variant == 'input'))))
    variant_differences = {}
    for name in ['whole', 'helpers', 'source_adapter']:
        by_variant = {v: {r['case_id']: r['returned']['output'] for r in rows if r['reference'] == name
                      and r['variant'] == v and r['returned'] is not None} for v in ['input', 'result']}
        variant_differences[name] = [c['case_id'] for c in anchors if c['case_id'] in by_variant['input']
               and c['case_id'] in by_variant['result'] and not strict(by_variant['input'][c['case_id']], by_variant['result'][c['case_id']])]
    summary = dict(completed_at=now(), stage='D1-P74-input-result-tree-pair', unique_input_count=len(anchors),
        task_diagnostic_records=12, actual_solve_calls=len(rows), passed=sum(r['passed'] for r in rows),
        input_unchanged=sum(r['input_unchanged'] for r in rows),
        by_reference={v + '/' + n: {'passed': sum(r['passed'] for r in rows if r['variant'] == v and r['reference'] == n), 'total': 6}
                      for v in ['input', 'result'] for n in ['whole', 'helpers', 'source_adapter']},
        source_api_calls={key: sum(r['returned']['api_calls'].get(key, 0) for r in rows if r['returned']) for key in ['remap', 'research']},
        source_api_count_scope='插桩实际函数入口；research内调用remap也计入，非任务要求的调用数',
        relations=relations, relation_passed=sum(r['passed'] for r in relations),
        variant_differences=variant_differences, formal_labels=None, human_reviews=0,
        initial20_unchanged=sha(old_manifest) == freeze['initial20_sha256'],
        model_calls=0, external_api_calls=0, private_reads=0, published=False,
        limitations=['六锚点非全域证明', '三参考同一助手，不冒称独立真值',
                     '同一家族，不冒称两个独立样本', '值和路径版本一起改变，非单轴因果实验',
                     '不提供拆分相对整体模型效果', '功能适配，不等于完整项目集成'])
    save(OUT / 'summary.json', summary)
    print(json.dumps({k: summary[k] for k in ['actual_solve_calls', 'passed', 'input_unchanged',
                                             'source_api_calls', 'relation_passed', 'variant_differences']}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'run', 'worker'])
    parser.add_argument('--reference', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare()
    elif args.action == 'run':
        run()
    else:
        worker(args.reference)
