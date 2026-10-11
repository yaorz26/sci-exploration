"""冻结最小公开需求/锚点后构造四个评价工作区；不执行行为。"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
CANDIDATE = ROOT / 'candidate'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_new(path, value):
    with path.open('x', encoding='utf-8') as output:
        json.dump(value, output, ensure_ascii=False, indent=2)


cases = [
    {'id': 'no_matching_environment', 'environment': {}, 'yaml_file': 'port: 11\n',
     'queries': {'port': {'path': ['port'], 'kind': 'int'}},
     'expected': {'port': {'value': 11, 'type': 'int'}}},
    {'id': 'prefixed_scalar', 'environment': {'D1APP_PORT': '42', 'D1OTHER_NOISE': '99'},
     'yaml_file': '{}\n',
     'queries': {'port': {'path': ['port'], 'kind': 'int'},
                 'excluded': {'path': ['noise'], 'kind': 'exists'}},
     'expected': {'port': {'value': 42, 'type': 'int'}, 'excluded': False}},
    {'id': 'nested_overlay_and_fallback', 'environment': {'D1APP_DB__HOST': 'env.local'},
     'yaml_file': 'db:\n  host: file.local\n  timeout: 7\n',
     'queries': {'host': {'path': ['db', 'host'], 'kind': 'str'},
                 'timeout': {'path': ['db', 'timeout'], 'kind': 'int'}},
     'expected': {'host': {'value': 'env.local', 'type': 'str'},
                  'timeout': {'value': 7, 'type': 'int'}}},
]
save_new(CANDIDATE / 'public_cases.json', {'expected_origin': '公开PR义务与手算，未调用合并版本取得答案', 'cases': cases})
freeze = {
    'frozen_at': datetime.now(timezone.utc).isoformat(), 'plan': '196_G2_confuse_pr142_env_source_plan.md',
    'requirement_sha256': sha(CANDIDATE / 'requirement.md'),
    'public_cases_sha256': sha(CANDIDATE / 'public_cases.json'),
    'evaluator_sha256': sha(CANDIDATE / 'evaluate_env_source.py'),
    'source_manifest_sha256': sha(ROOT / 'non_test_source_manifest.json'),
    'distinct_scenarios': 3, 'workspaces': 4, 'maximum_worker_runs': 12,
    'predictions': {'parent': [False, False, False], 'feature': [True, True, True],
                    'alternative': [True, True, True], 'priority_omission': [True, True, False]},
    'direction_check': '检验环境来源进入真实配置读取、优先级和下层回退；属于G2-K1，不扩参数矩阵。',
    'construction_constraint': 'set_env公开入口为构建者固定，内部EnvSource/helper/module组织不固定。',
    'scope_limit': 'PR142有限子范围；列表、全YAML、reload和冲突键均未纳入。',
    'formal_labels': None, 'split': None, 'human_reviews': 0, 'model_calls': 0,
    'upstream_tests_read': False, 'D1_private_read_for_this_candidate': False,
    'prior_accidental_exposure': '../d1_G2_more_itertools_cursor_v1_20261009/accidental_exposure.json',
}
save_new(ROOT / 'freeze_before_execution.json', freeze)
workspaces = CANDIDATE / 'workspaces'
workspaces.mkdir()
shutil.copytree(ROOT / 'parent', workspaces / 'parent')
shutil.copytree(ROOT / 'merge', workspaces / 'feature')
shutil.copytree(ROOT / 'parent', workspaces / 'alternative')
helper = '''"""手写的有限域替代组织；不使用PR142工具函数。"""
import os
import yaml
from . import yaml_util
from .sources import ConfigSource

def apply_environment(config, prefix=None, sep='__'):
    prefix = prefix if prefix is not None else config.appname.upper() + '_'
    overlay = {}
    for name, raw in os.environ.items():
        if not name.startswith(prefix):
            continue
        path = name[len(prefix):].lower().split(sep) if sep else [name[len(prefix):].lower()]
        node = overlay
        for part in path[:-1]:
            node = node.setdefault(part, {})
        node[path[-1]] = yaml.load(raw, Loader=config.loader)
    config.set(ConfigSource(overlay))
'''
alternative = workspaces / 'alternative' / 'confuse'
(alternative / 'env_overlay.py').write_text(helper, encoding='utf-8')
core = alternative / 'core.py'
body = core.read_text(encoding='utf-8')
anchor = '    def set_file(self, filename, base_for_paths=False):'
assert body.count(anchor) == 1
method = '''    def set_env(self, prefix=None, sep='__'):
        from .env_overlay import apply_environment
        apply_environment(self, prefix, sep)

'''
core.write_text(body.replace(anchor, method + anchor), encoding='utf-8')
shutil.copytree(workspaces / 'alternative', workspaces / 'priority_omission')
omission = workspaces / 'priority_omission' / 'confuse' / 'env_overlay.py'
omission.write_text(helper.replace('config.set(ConfigSource(overlay))', 'config.add(ConfigSource(overlay))'), encoding='utf-8')
save_new(ROOT / 'constructed_workspaces.json', {
    'constructed_at': datetime.now(timezone.utc).isoformat(),
    'parent': '官方父提交包源码', 'feature': '官方合并提交包源码',
    'alternative': '父源码 + 独立env_overlay模块 + core公开入口；有限合法输入域',
    'priority_omission': '替代组织中把最高优先set改为最低优先add；不破坏导入',
    'reference_dependency': '两个正确组织使用同一既有YAML Loader；非完全独立oracle',
    'hashes': {str(p.relative_to(CANDIDATE)): sha(p) for p in workspaces.rglob('*.py')},
})
print(json.dumps({'frozen': True, 'scenarios': 3, 'workspaces': 4, 'behavior_runs': 0}, ensure_ascii=False))
