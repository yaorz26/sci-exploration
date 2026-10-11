import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
CANDIDATE = ROOT / 'candidate'


def new(path, obj):
    with path.open('x', encoding='utf-8') as output:
        json.dump(obj, output, ensure_ascii=False, indent=2)


cases = [
    {'id': 'retained_lists_after_outer_exhaustion', 'mode': 'retain_after_advance',
     'items': [['a', 1], ['a', 2], ['b', 3], ['a', 4]], 'factor': 10, 'reducefunc': 'list',
     'expected': [['a', [10, 20]], ['b', [30]], ['a', [40]]]},
    {'id': 'group_sums', 'mode': 'normal',
     'items': [[0, 2], [0, 4], [1, 1], [1, 3]], 'factor': 1, 'reducefunc': 'sum',
     'expected': [[0, 6], [1, 4]]},
    {'id': 'no_reducer_keeps_parent_lazy_groups', 'mode': 'baseline_lazy',
     'items': [['a', 1], ['a', 2], ['b', 3]], 'factor': 1,
     'expected': {'first_key': 'a', 'first_after_advance': [], 'second_key': 'b', 'second_now': [3]}},
]
new(CANDIDATE / 'public_cases.json', {'expected_origin': '公开组生命周期义务与手算；不从feature执行取期望', 'cases': cases})
new(ROOT / 'freeze_before_execution.json', {
    'time': datetime.now(timezone.utc).isoformat(), 'macro_plan': 'v2限定扩展/208号顺序三审已完成',
    'requirement_sha256': hashlib.sha256((CANDIDATE / 'requirement.md').read_bytes()).hexdigest(),
    'cases_sha256': hashlib.sha256((CANDIDATE / 'public_cases.json').read_bytes()).hexdigest(),
    'source_manifest_sha256': hashlib.sha256((ROOT / 'source_manifest.json').read_bytes()).hexdigest(),
    'api_name_correction': 'PR标题groupfunc；合并公开API reducefunc，使用后者，原元数据保留',
    'predictions': {'parent': [False, False, True], 'feature': [True, True, True],
                    'alternative': [True, True, True], 'late_reduction': [False, False, True]},
    'maximum_worker_runs': 12, 'distinct_public_cases': 3,
    'direction_check': '真实API回调与源组有效期连接；不是存储布局/参数覆盖',
    'formal_labels': None, 'split': None, 'human_reviews': 0, 'model_calls': 0,
    'upstream_tests_read': False, 'prior_exposure': '既有两暴露保留，不声称项目零暴露',
})
workspaces = CANDIDATE / 'workspaces'
workspaces.mkdir()
shutil.copytree(ROOT / 'parent', workspaces / 'parent')
shutil.copytree(ROOT / 'feature', workspaces / 'feature')


def replace_function(workspace, implementation):
    path = workspace / 'more_itertools/more.py'
    source = path.read_text(encoding='utf-8')
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'groupby_transform')
    lines = source.splitlines(keepends=True)
    path.write_text(''.join(lines[:node.lineno-1]) + implementation + '\n\n' + ''.join(lines[node.end_lineno:]), encoding='utf-8')


shutil.copytree(ROOT / 'parent', workspaces / 'alternative')
helper = '''"""手写的独立模块组织；组变换在当前组有效期间完成。"""
from itertools import groupby

def transform_groups(iterable, keyfunc=None, valuefunc=None, reducefunc=None):
    for key, group in groupby(iterable, keyfunc):
        values = map(valuefunc, group) if valuefunc else group
        yield key, reducefunc(values) if reducefunc else values
'''
(workspaces / 'alternative/more_itertools/group_transform.py').write_text(helper, encoding='utf-8')
replace_function(workspaces / 'alternative', '''def groupby_transform(iterable, keyfunc=None, valuefunc=None, reducefunc=None):
    from .group_transform import transform_groups
    return transform_groups(iterable, keyfunc, valuefunc, reducefunc)
''')
shutil.copytree(ROOT / 'parent', workspaces / 'late_reduction')
replace_function(workspaces / 'late_reduction', '''def groupby_transform(iterable, keyfunc=None, valuefunc=None, reducefunc=None):
    ret = groupby(iterable, keyfunc)
    if valuefunc:
        ret = ((key, map(valuefunc, group)) for key, group in ret)
    if reducefunc is None:
        return ret
    saved_group_handles = list(ret)
    # 错误控制：先推进外层至耗尽，再消费已失效的源组；不故意破坏导入。
    return iter((key, reducefunc(group)) for key, group in saved_group_handles)
''')
new(ROOT / 'constructed_workspaces.json', {
    'time': datetime.now(timezone.utc).isoformat(), 'behavior_runs': 0,
    'alternative': '父包公开入口委托新模块，立即变换当前组；无私有状态约束',
    'late_reduction': '父包支持新签名但先保存懒组句柄，推进外层后才归约，保无reducer旧行为',
    'shared_dependency': '两正确组织共用itertools.groupby/map，非独立oracle；同助手构造',
    'workspace_hashes': {str(p.relative_to(CANDIDATE)): hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in workspaces.rglob('*.py')},
})
print(json.dumps({'frozen': True, 'scenarios': 3, 'workspaces': 4, 'behavior_runs': 0}, ensure_ascii=False))
