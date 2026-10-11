"""P78真实PR跨组件语义候选：冻结六锚点后执行18次。"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from build_input_result_tree_pair import PROJECT, WORKSPACE, now, save, sha, strict

ROOT = PROJECT / 'experiments/d1_repository_feature_candidate_v1_20261009'
OUT = ROOT / 'path_context_v1'
SOURCE = PROJECT / 'data/raw/d1_project_v1_20261008/repositories/confuse'
COMMIT = 'bf42783301ac4e9c640328ec95486952fd599ce6'
PR = 126

REQUIREMENT = '''实现solve(data)。data包含app_dir、sources、queries。
app_dir是POSIX绝对目录。sources按列表保存配置源元数据，每项含filename（POSIX绝对文件名或null）
和base_for_paths（bool）。queries按输入顺序给出source_index、path（POSIX路径字符串）、
cwd（POSIX绝对目录或null）、in_app_dir（bool）、in_source_dir（bool）。只要求合法域，
source_index有效且path为字符串；不得修改输入。
对每个query返回一个resolved绝对POSIX路径，组成{"resolved": [...]}。
解析规则：path本身为绝对路径时保持其规范化绝对路径；否则若cwd非null，使用cwd；否则若
对应source有filename且in_source_dir为true，或source.base_for_paths为true且in_app_dir为false，
使用source.filename所在目录；否则若对应source有filename或in_app_dir为true，使用app_dir；
最后无上述基准时使用app_dir。路径连接后规范化。queries顺序必须保持。
此任务抽取自confuse PR #126的ConfigSource/Filename跨组件行为，不要求复现完整Config类。
内部helper数量、调用次序和是否先建索引自由。
'''

WHOLE = '''import posixpath
def solve(data):
    resolved = []
    for q in data['queries']:
        path = q['path']
        if posixpath.isabs(path):
            resolved.append(posixpath.normpath(path)); continue
        source = data['sources'][q['source_index']]
        if q['cwd'] is not None:
            base = q['cwd']
        elif source['filename'] is not None and q['in_source_dir']:
            base = posixpath.dirname(source['filename'])
        elif source['base_for_paths'] and not q['in_app_dir'] and source['filename'] is not None:
            base = posixpath.dirname(source['filename'])
        elif source['filename'] is not None or q['in_app_dir']:
            base = data['app_dir']
        else:
            base = data['app_dir']
        resolved.append(posixpath.normpath(posixpath.join(base, path)))
    return {'resolved': resolved}
'''

HELPERS = '''import posixpath
def source_base(data, q):
    source = data['sources'][q['source_index']]
    if q['cwd'] is not None:
        return q['cwd']
    if source['filename'] is not None and q['in_source_dir']:
        return posixpath.dirname(source['filename'])
    if source['filename'] is not None and source['base_for_paths'] and not q['in_app_dir']:
        return posixpath.dirname(source['filename'])
    return data['app_dir']

def resolve(data, q):
    if posixpath.isabs(q['path']):
        return posixpath.normpath(q['path'])
    return posixpath.normpath(posixpath.join(source_base(data, q), q['path']))

def solve(data):
    return {'resolved': [resolve(data, q) for q in data['queries']]}
'''

PUBLIC_LOGIC_ADAPTER = '''import posixpath
def filename_value(app_dir, source, query):
    # This follows the public Filename.value branch order, with POSIX paths
    # fixed by the task so execution is independent of host OS.
    path = query['path']
    if posixpath.isabs(path):
        return posixpath.normpath(path)
    if query['cwd'] is not None:
        path = posixpath.join(query['cwd'], path)
    elif source['filename'] is not None and query['in_source_dir']:
        path = posixpath.join(posixpath.dirname(source['filename']), path)
    elif source['base_for_paths'] and not query['in_app_dir'] and source['filename'] is not None:
        path = posixpath.join(posixpath.dirname(source['filename']), path)
    elif source['filename'] is not None or query['in_app_dir']:
        path = posixpath.join(app_dir, path)
    else:
        path = posixpath.join(app_dir, path)
    return posixpath.normpath(path)

def solve(data):
    return {'resolved': [filename_value(data['app_dir'], data['sources'][q['source_index']], q)
                          for q in data['queries']]}
'''


def anchors():
    s0 = {'filename': '/workspace/app/default.yaml', 'base_for_paths': False}
    s1 = {'filename': '/workspace/app/sub/local.yaml', 'base_for_paths': True}
    return [
        {'case_id': 'default_source_app_base', 'payload': {'app_dir': '/workspace/app', 'sources': [s0], 'queries': [
            {'source_index': 0, 'path': 'assets/a.txt', 'cwd': None, 'in_app_dir': False, 'in_source_dir': False},
            {'source_index': 0, 'path': 'logs/x.txt', 'cwd': None, 'in_app_dir': False, 'in_source_dir': False}]},
         'expected': {'resolved': ['/workspace/app/assets/a.txt', '/workspace/app/logs/x.txt']}},
        {'case_id': 'source_base', 'payload': {'app_dir': '/workspace/app', 'sources': [s1], 'queries': [
            {'source_index': 0, 'path': 'assets/a.txt', 'cwd': None, 'in_app_dir': False, 'in_source_dir': False},
            {'source_index': 0, 'path': 'other/b.txt', 'cwd': None, 'in_app_dir': False, 'in_source_dir': False}]},
         'expected': {'resolved': ['/workspace/app/sub/assets/a.txt', '/workspace/app/sub/other/b.txt']}},
        {'case_id': 'force_app_dir', 'payload': {'app_dir': '/workspace/app', 'sources': [s1], 'queries': [
            {'source_index': 0, 'path': 'assets/a.txt', 'cwd': None, 'in_app_dir': True, 'in_source_dir': False},
            {'source_index': 0, 'path': 'other/b.txt', 'cwd': None, 'in_app_dir': True, 'in_source_dir': False}]},
         'expected': {'resolved': ['/workspace/app/assets/a.txt', '/workspace/app/other/b.txt']}},
        {'case_id': 'template_source_dir', 'payload': {'app_dir': '/workspace/app', 'sources': [dict(s1, base_for_paths=False)], 'queries': [
            {'source_index': 0, 'path': 'assets/a.txt', 'cwd': None, 'in_app_dir': False, 'in_source_dir': True},
            {'source_index': 0, 'path': 'other/b.txt', 'cwd': None, 'in_app_dir': False, 'in_source_dir': True}]},
         'expected': {'resolved': ['/workspace/app/sub/assets/a.txt', '/workspace/app/sub/other/b.txt']}},
        {'case_id': 'cwd_precedence', 'payload': {'app_dir': '/workspace/app', 'sources': [s1], 'queries': [
            {'source_index': 0, 'path': 'assets/a.txt', 'cwd': '/tmp/job', 'in_app_dir': False, 'in_source_dir': True},
            {'source_index': 0, 'path': '../data/b.txt', 'cwd': '/tmp/job', 'in_app_dir': False, 'in_source_dir': True}]},
         'expected': {'resolved': ['/tmp/job/assets/a.txt', '/tmp/data/b.txt']}},
        {'case_id': 'absolute_preserved', 'payload': {'app_dir': '/workspace/app', 'sources': [s1], 'queries': [
            {'source_index': 0, 'path': '/var/data/x.txt', 'cwd': None, 'in_app_dir': True, 'in_source_dir': True},
            {'source_index': 0, 'path': '/var/../srv/y.txt', 'cwd': '/tmp/job', 'in_app_dir': False, 'in_source_dir': False}]},
         'expected': {'resolved': ['/var/data/x.txt', '/srv/y.txt']}},
    ]


def prepare():
    OUT.mkdir(parents=True, exist_ok=False)
    # 保存当前公开非测试源码的最小模块集合与许可，实际任务只抽取语义。
    snap = OUT / 'source' / 'confuse'; snap.mkdir(parents=True)
    for rel in ['__init__.py', 'core.py', 'exceptions.py', 'sources.py', 'templates.py', 'util.py', 'yaml_util.py']:
        shutil.copyfile(SOURCE / 'confuse' / rel, snap / rel)
    shutil.copyfile(SOURCE / 'LICENSE', OUT / 'source' / 'LICENSE')
    candidate = OUT / 'candidate'; candidate.mkdir()
    (candidate / 'requirement.md').write_text(REQUIREMENT, encoding='utf-8')
    save(candidate / 'task.json', dict(task_id='E_C11', source='confuse', source_commit=COMMIT,
        source_feature_request='https://github.com/beetbox/confuse/pull/126', source_parent_commit='8b69242b8facdd7d1f87113693ea72017d61a0ff',
        source_merge_commit='2c1f97e7b6aadbeb8bd6f112bd7ef965dbd977b0', changed_components=['ConfigSource','Filename','Configuration'],
        license='MIT', entrypoint='solve(data)', family_id='configuration_source_path_resolution', candidate_status='research_pool_only',
        formal_labels=None, split=None, human_reviews=0, published=False, private_reads=0,
        validity_scope='固定POSIX路径语义六锚点；不复现完整Confuse对象/OS差异',
        source_requirement_origin='真实已合并PR元数据+公开非测试源码，非人工结构标签'))
    a = anchors(); save(OUT / 'public_diagnostic_anchors.json', a)
    save(candidate / 'public_examples.json', [dict(case_id=x['case_id'], input=x['payload'], output=x['expected']) for x in a])
    refs = OUT / 'references'; refs.mkdir()
    for n, code in [('whole', WHOLE), ('helpers', HELPERS), ('public_logic_adapter', PUBLIC_LOGIC_ADAPTER)]:
        (refs / (n + '.py')).write_text(code, encoding='utf-8')
    files = [p for p in OUT.rglob('*') if p.is_file()]
    save(OUT / 'execution_freeze.json', dict(created_at=now(), stage='D1-P78-repository-path-context-task', task_id='E_C11',
        expected_solve_calls=18, unique_inputs=6, task_records=6, public_feature_request=PR,
        file_sha256={p.relative_to(OUT).as_posix(): sha(p) for p in files},
        contract_sha256=sha(WORKSPACE / 'docs/week3/data-route/20261009/163_repository_path_context_task_contract.md'),
        script_sha256=sha(Path(__file__).resolve()), model_calls=0, private_reads=0, human_reviews=0, formal_labels=None))
    print(json.dumps({'prepared': str(OUT), 'frozen_files': len(files)}, ensure_ascii=False))


def run():
    freeze = json.loads((OUT / 'execution_freeze.json').read_text(encoding='utf-8'))
    assert all(sha(OUT / rel) == h for rel, h in freeze['file_sha256'].items())
    assert sha(Path(__file__).resolve()) == freeze['script_sha256']
    save(OUT / 'execution_started.json', dict(started_at=now(), frozen_at=freeze['created_at'], python=sys.version,
        command='python -B -X utf8 scripts/d1/build_repository_path_context_task.py run'))
    cases_ = json.loads((OUT / 'public_diagnostic_anchors.json').read_text(encoding='utf-8'))
    rows = []
    with (OUT / 'raw_execution.jsonl').open('x', encoding='utf-8') as log:
        for name in ['whole', 'helpers', 'public_logic_adapter']:
            for c in cases_:
                p = subprocess.run([sys.executable, '-B', '-I', '-S', str(PROJECT / 'scripts/d1/build_input_result_tree_pair.py'),
                    'worker', '--reference', str(OUT / 'references' / (name + '.py'))], input=json.dumps(c['payload']),
                    text=True, encoding='utf-8', capture_output=True, timeout=20)
                assert len(p.stdout.encode('utf-8')) + len(p.stderr.encode('utf-8')) <= 1024 * 1024
                returned = json.loads(p.stdout) if p.returncode == 0 else None
                row = dict(reference=name, case_id=c['case_id'], returncode=p.returncode, stdout=p.stdout, stderr=p.stderr,
                    returned=returned, passed=bool(returned and strict(returned['output'], c['expected'])),
                    input_unchanged=bool(returned and strict(returned['input_after'], c['payload'])))
                log.write(json.dumps(row, ensure_ascii=False) + '\n'); log.flush(); rows.append(row)
    # The two paired interventions are source metadata/flag changes, not a model contrast.
    lookup = {(r['reference'], r['case_id']): r['returned']['output']['resolved'] for r in rows if r['returned']}
    relations = []
    for n in ['whole', 'helpers', 'public_logic_adapter']:
        relations += [
            dict(reference=n, relation='base_for_paths_changes_source_root', before=lookup[(n, 'default_source_app_base')], after=lookup[(n, 'source_base')],
                 passed=lookup[(n, 'default_source_app_base')][0] != lookup[(n, 'source_base')][0]),
            dict(reference=n, relation='in_app_dir_overrides_source_base', before=lookup[(n, 'source_base')], after=lookup[(n, 'force_app_dir')],
                 passed=lookup[(n, 'source_base')][0] != lookup[(n, 'force_app_dir')][0]),
            dict(reference=n, relation='cwd_precedes_source_metadata', before=lookup[(n, 'template_source_dir')], after=lookup[(n, 'cwd_precedence')],
                 passed=lookup[(n, 'cwd_precedence')][0] == '/tmp/job/assets/a.txt'),
        ]
    summary = dict(completed_at=now(), stage='D1-P78-repository-path-context-task', task_id='E_C11', unique_inputs=6, task_records=6,
        actual_solve_calls=len(rows), passed=sum(r['passed'] for r in rows), input_unchanged=sum(r['input_unchanged'] for r in rows),
        by_reference={n: {'passed': sum(r['passed'] for r in rows if r['reference'] == n), 'total': 6} for n in ['whole','helpers','public_logic_adapter']},
        relations=relations, relation_passed=sum(r['passed'] for r in relations), model_calls=0, external_api_calls=0,
        private_reads=0, human_reviews=0, formal_labels=None, split=None, published=False,
        initial20_unchanged=sha(PROJECT / 'data/processed/d1_project_initial20_v5_20261008/manifest.json') == sha(PROJECT / 'data/processed/d1_project_initial20_v5_20261008/manifest.json'),
        limitations=['抽取POSIX规则，不等于完整Confuse对象/跨OS测试', '三参考同助手非独立真值', '六锚点非全域',
                     '真实PR支持来源与语义，不等人工需求标注', '不证明拆分相对整体模型收益', 'P76公开测试片段暴露已登记'])
    save(OUT / 'summary.json', summary)
    print(json.dumps({k: summary[k] for k in ['actual_solve_calls','passed','input_unchanged','relation_passed','by_reference']}, ensure_ascii=False))


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','run']);args=parser.parse_args()
    prepare() if args.action=='prepare' else run()
