import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

out = Path(__file__).resolve().parent
patterns = {
    'direct_yaml_constructor': re.compile(r'def __init__\(self, filename=None.*'),
    'base_state_assignment': re.compile(r'base_for_paths'),
    'set_file_entry': re.compile(r'def set_file\(self, filename'),
    'set_file_yaml_call': re.compile(r'YamlSource\(filename'),
    'filename_value': re.compile(r'def value\(self, view'),
    'filename_source_first': re.compile(r'view\.first\('),
}
records = {}
for name in ('control', 'complete', 'alternative'):
    ws = out / 'workspaces' / name / 'confuse'
    rows = []
    for rel in ('sources.py', 'core.py', 'templates.py'):
        path = ws / rel
        lines = path.read_text(encoding='utf-8').splitlines()
        hits = []
        for label, pattern in patterns.items():
            found = [i + 1 for i, line in enumerate(lines) if pattern.search(line)]
            if found:
                hits.append({'evidence': label, 'lines': found})
        rows.append({'file': str(path.relative_to(out)),
                     'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'hits': hits})
    records[name] = rows

def line_set(name, label):
    return [(row['file'], hit['lines']) for row in records[name]
            for hit in row['hits'] if hit['evidence'] == label]

result = {
    'created_at': datetime.now(timezone.utc).isoformat(),
    'question': 'PR126直接入口是接口覆盖条件还是结构变量？',
    'source_kind': 'read_only_source_line_mapping',
    'records': records,
    'cross_workspace_observation': {
        'external_direct_yaml_obligation': 'observed_by_219_result',
        'set_file_and_direct_entry': 'both_public_entries_exist_or_are_tested_in_complete/alternative; control intentionally splits them',
        'common_parse_observation': 'all three route a source object to Filename.value in the inspected files; exact state ownership remains unknown',
    },
    'conclusion': '该反例首先证明接口覆盖缺口；现有源码映射不足以把多入口编码成阶段依赖或共享状态轴。结构字段保留unknown，PR126新增锚点标为外部API验收条件。',
    'excluded_claims': ['因果结构效应', '所有合法实现共享同一内部链路', '全域API完备', '模型或人工效果'],
    'model_calls': 0, 'behavior_calls': 0, 'human_reviews': 0,
    'formal_labels': None, 'split': None,
}
with (out / 'api_structure_mapping.json').open('x', encoding='utf-8') as handle:
    json.dump(result, handle, ensure_ascii=False, indent=2)
print(json.dumps({'workspaces': list(records), 'behavior_calls': 0,
                  'conclusion': result['conclusion']}, ensure_ascii=False))
