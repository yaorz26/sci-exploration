import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
root = repo.parent
out = Path(__file__).resolve().parent
files = [
    root / 'docs/week3/data-route/20261009/218_pr126_direct_entry_counterexample_plan.md',
    repo / 'data/processed/d1_actual_project_candidate_v2_20261009/public/REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS/requirement.md',
    repo / 'experiments/d1_G3_pr126_entry_gap_v1_20261009/evaluate_legacy.py',
    repo / 'experiments/d1_G3_pr126_entry_gap_v1_20261009/evaluate_direct_yaml.py',
]
workspaces = {}
for name in ('control', 'complete', 'alternative'):
    path = out / 'workspaces' / name
    workspaces[name] = {
        'path': str(path),
        'files': [
            {'path': str(file.relative_to(out)),
             'sha256': hashlib.sha256(file.read_bytes()).hexdigest()}
            for file in sorted(path.rglob('*')) if file.is_file()
        ],
    }
data = {
    'created_at': datetime.now(timezone.utc).isoformat(),
    'question': '旧PR126评价是否误收遗漏直接YamlSource参数的项目实现？',
    'plan_sha256': hashlib.sha256(files[0].read_bytes()).hexdigest(),
    'input_files': [{'path': str(f), 'sha256': hashlib.sha256(f.read_bytes()).hexdigest()} for f in files],
    'workspaces': workspaces,
    'frozen_before_execution': True,
    'allowed_calls': {'legacy_control': 1, 'direct_yaml_each': 1, 'model': 0, 'human': 0},
    'expected_pattern': {'control_legacy': '8/8', 'control_direct': '0/1',
                         'complete_direct': '1/1', 'alternative_direct': '1/1'},
    'formal_labels': None, 'split': None,
}
with (out / 'freeze_before_execution.json').open('x', encoding='utf-8') as h:
    json.dump(data, h, ensure_ascii=False, indent=2)
print(json.dumps({'workspaces': list(workspaces), 'frozen_before_execution': True}, ensure_ascii=False))
