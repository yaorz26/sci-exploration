"""一次只读题面—诊断映射；不是全域覆盖证明。"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
V2 = 'data/processed/d1_actual_project_candidate_v2_20261009'
ENV = 'experiments/d1_G2_confuse_pr142_env_source_v1_20261009/candidate'
GRP = 'experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/candidate'
paths = {
    'path_requirement': f'{V2}/public/REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS/requirement.md',
    'path_evaluator': f'{V2}/evaluation/REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS/evaluate.py',
    'env_requirement': f'{ENV}/requirement.md', 'env_evaluator': f'{ENV}/evaluate_env_source.py',
    'env_cases': f'{ENV}/public_cases.json',
    'group_requirement': f'{GRP}/requirement.md', 'group_evaluator': f'{GRP}/evaluate_group_lifetime.py',
    'group_cases': f'{GRP}/public_cases.json',
    'cache_requirement': f'{V2}/pending/REPO_CACHETOOLS_EXPIRED_REPORT/original_requirement.md',
}
texts = {key: (ROOT / value).read_text(encoding='utf-8') for key, value in paths.items()}

def evidence(key, fragment):
    lines = texts[key].splitlines()
    match = [i + 1 for i, line in enumerate(lines) if fragment in line]
    if not match:
        raise ValueError((key, fragment))
    return {'path': paths[key], 'lines': match, 'fragment': fragment}

def row(task, obligation, state, requirement_key, clause, note, evaluator_key=None, anchor=None):
    result = {'task': task, 'obligation': obligation, 'observation_state': state,
              'requirement_evidence': evidence(requirement_key, clause), 'interpretation': note}
    if evaluator_key:
        result['observation_evidence'] = evidence(evaluator_key, anchor)
    return result

rows = [
    row('PR126', 'ConfigSource文件基准及标志', 'observed_in_named_cases', 'path_requirement',
        'ConfigSource 和 YamlSource', 'ConfigSource直接构造已测；不能据此推每个来源入口完整。',
        'path_evaluator', 'config.add(confuse.ConfigSource'),
    row('PR126', 'YamlSource直接构造支持base_for_paths', 'not_directly_observed', 'path_requirement',
        'ConfigSource 和 YamlSource', 'set_file可能间接调用YamlSource；直接构造的参数支持没有单独观测，不等于该类完全未执行。',
        'path_evaluator', 'if api == "set_file"'),
    row('PR126', 'Configuration.set_file支持base_for_paths', 'observed_in_named_cases', 'path_requirement',
        'Configuration.set_file', 'file_loader_flag覆盖指定入口一次。', 'path_evaluator', 'file_loader_flag'),
    row('PR126', '模板in_source_dir及in_app_dir', 'observed_in_named_cases', 'path_requirement',
        'Filename 增加可选参数', 'template_flag/app_over_source_flag是有限观察，不是全部优先级组合。',
        'path_evaluator', 'template_flag'),
    row('PR126', 'cwd、无filename及绝对路径', 'observed_in_named_cases', 'path_requirement',
        '绝对路径保持不变', '各有公开场景；未观察relative_to与新标志交叉条件。',
        'path_evaluator', 'absolute_preserved'),
    row('PR126', 'relative_to保持既有行为', 'not_explicitly_observed', 'path_requirement',
        'relative_to', '未显式提供relative_to；记录缺口，禁止自动扩该旁支。'),
    row('PR142', '前缀/小写/嵌套/标量转换', 'observed_in_named_cases', 'env_requirement',
        '匹配前缀的变量', 'prefixed_scalar及nested场景提供有限观察；并非所有有效YAML标量。',
        'env_cases', 'prefixed_scalar'),
    row('PR142', '优先级与较低来源回退', 'observed_in_named_cases', 'env_requirement',
        '具有更高优先级', 'nested_overlay_and_fallback同时观察冲突host和缺省timeout。',
        'env_cases', 'nested_overlay_and_fallback'),
    row('PR142', '构造时不默认加入环境源', 'not_observed', 'env_requirement',
        '不在构造配置对象时默认加入', '所有场景都显式调用set_env；未调用前的配置观察缺失。',
        'env_evaluator', "config.set_env(prefix='D1APP_')"),
    row('PR142', '无匹配环境变量保持配置', 'observed_in_named_cases', 'env_requirement',
        '没有匹配环境变量', '一次无匹配场景。', 'env_cases', 'no_matching_environment'),
    row('PR142', 'set_env最高优先级入口', 'explicit_constructor_constraint', 'env_requirement',
        '任务构建者固定的外部调用入口', '明示构建者调用约束，固定公开入口但不固定helper/内部类/文件。'),
    row('PR440', '相邻组归约与已返回值保留', 'observed_in_named_cases', 'group_requirement',
        'reducefunc完成的list/数值结果', 'retained_lists_after_outer_exhaustion和group_sums覆盖有限域。',
        'group_cases', 'retained_lists_after_outer_exhaustion'),
    row('PR440', '不归约时共享惰性组', 'observed_in_named_cases', 'group_requirement',
        '保留父API的懒组', '一次外层前进后旧组变空的场景；不证明内存/效率。',
        'group_cases', 'no_reducer_keeps_parent_lazy_groups'),
    row('PR440', 'keyfunc/valuefunc省略的默认行为', 'not_observed', 'group_requirement',
        'keyfunc/valuefunc未提供时', '评价器每次均提供两回调；不自动补默认组合网格。',
        'group_evaluator', "kwargs = {'keyfunc': keyfunc, 'valuefunc': valuefunc}"),
    row('PR440', '有限list/sum域及内部自由', 'explicit_scope_and_internal_freedom', 'group_requirement',
        '有限合法域', '有限域是任务范围，不是要求使用某一种内部实现；不外推任意惰性归约。'),
    row('CACHE', '物理删除与容量在返回前完成', 'pending_known_observability_gap', 'cache_requirement',
        '调用返回之前必须完成', '沿用已知待解状态，不重跑时点或访问旧源码/评价；不能作为当前完整合格任务。'),
]
result = {
    'created_at': datetime.now(timezone.utc).isoformat(),
    'question': '明示外部义务是否超出当前公开诊断观察范围？',
    'phase': 'G3-contract-integrity', 'kind': 'exploratory_read_only_support',
    'records': rows, 'tasks_managed': 4, 'finite_tasks_read': 3,
    'selected_followup': 'PR126直接YamlSource入口可能可独立遗漏；另三审后只做一个最小反例',
    'not_selected': ['PR142自动加入控制', 'PR440默认回调网格', 'cache时点重试', '全域覆盖百分比'],
    'result_limit': '静态未观测不证明假通过；需行为反例。三任务均有明示但未直接诊断条款，当前观察不能支持全域验收。',
    'model_calls': 0, 'behavior_calls': 0, 'human_reviews': 0,
    'formal_labels': None, 'split': None,
    'input_hashes': {key: {'path': value, 'sha256': hashlib.sha256((ROOT/value).read_bytes()).hexdigest()}
                     for key, value in paths.items()},
}
with (OUT/'contract_observation_audit.json').open('x', encoding='utf-8') as handle:
    json.dump(result, handle, ensure_ascii=False, indent=2)
print(json.dumps({'finite_tasks_read': 3, 'behavior_calls': 0, 'selected_followup': result['selected_followup']}, ensure_ascii=False))
