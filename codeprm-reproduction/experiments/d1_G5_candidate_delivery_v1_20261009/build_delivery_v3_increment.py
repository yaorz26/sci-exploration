from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

REPRO = Path(__file__).resolve().parents[2]
OLD = REPRO / 'data/processed/d1_actual_project_candidate_v2_20261009'
DEST = REPRO / 'data/processed/d1_actual_project_candidate_v3_20261009'
SRC = REPRO / 'experiments/d1_G2_more_pr440_group_lifetime_v1_20261009'
DEST.mkdir(parents=True, exist_ok=True)
shutil.copytree(OLD, DEST, dirs_exist_ok=True)

def copy_file(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

public = DEST / 'public/REPO_MORE_PR440_GROUP_LIFETIME_LIMITED'
source_parent = SRC / 'candidate/workspaces/parent'
for path in sorted(source_parent.rglob('*.py')):
    copy_file(path, public / 'parent' / path.relative_to(source_parent))
copy_file(source_parent / 'LICENSE', public / 'parent/LICENSE')
for name in ('requirement.md', 'public_cases.json'):
    copy_file(SRC / ('candidate/' + name), public / name)
source = json.loads((SRC / 'official_pr_metadata.json').read_text(encoding='utf-8'))
(public / 'source.json').write_text(json.dumps({**source, 'visibility': '公开PR/父上下文；标题groupfunc与实际reducefunc差异已记录'}, ensure_ascii=False, indent=2), encoding='utf-8')

evaluation = DEST / 'evaluation/REPO_MORE_PR440_GROUP_LIFETIME_LIMITED'
evaluation.mkdir(parents=True, exist_ok=True)
copy_file(SRC / 'candidate/evaluate_group_lifetime.py', evaluation / 'evaluate_group_lifetime.py')
for label in ('feature', 'alternative', 'late_reduction'):
    source_workspace = SRC / ('candidate/workspaces/' + label)
    for path in sorted(source_workspace.rglob('*.py')):
        copy_file(path, evaluation / 'programs' / label / path.relative_to(source_workspace))
    copy_file(source_workspace / 'LICENSE', evaluation / 'programs' / label / 'LICENSE')
for name in ('behavior_parent.json', 'behavior_feature.json', 'behavior_alternative.json', 'behavior_late_reduction.json', 'stage_result.json'):
    copy_file(SRC / name, evaluation / 'saved_results' / name)

manifest = json.loads((DEST / 'manifest.json').read_text(encoding='utf-8'))
manifest['created_at'] = datetime.now(timezone.utc).isoformat()
manifest['version'] = 'research_candidate_v3_increment_pr440'
manifest['tasks'].append({'task_id': 'REPO_MORE_PR440_GROUP_LIFETIME_LIMITED',
                          'public': 'public/REPO_MORE_PR440_GROUP_LIFETIME_LIMITED',
                          'evaluator': 'evaluation/REPO_MORE_PR440_GROUP_LIFETIME_LIMITED/evaluate_group_lifetime.py',
                          'source': 'more-itertools', 'scope': '有限公开组生命周期行为候选',
                          'formal_labels': None, 'split': None, 'human_reviews': 0})
manifest['usable_finite_tasks'] = 3
manifest['usable_sources'] = ['confuse', 'more-itertools']
manifest['managed_candidates'] = 4
manifest['managed_sources'] = ['confuse', 'cachetools', 'more-itertools']
manifest['incremental_from'] = 'd1_actual_project_candidate_v2_20261009'
manifest['new_behavior_worker_runs_this_cycle'] = 0
manifest['files_sha256'] = {str(path.relative_to(DEST)).replace('\\', '/'): digest(path)
                             for path in sorted(DEST.rglob('*')) if path.is_file() and path.name != 'manifest.json'}
manifest_path = DEST / 'manifest.json'
if manifest_path.exists():
    manifest_path.replace(DEST / 'inherited_manifest_v2.json')
with manifest_path.open('x', encoding='utf-8') as output:
    json.dump(manifest, output, ensure_ascii=False, indent=2)

readme = (DEST / 'README.md').read_text(encoding='utf-8')
readme += '''\n\n## v3增量：PR440\n\n在v2基础上新增一项more-itertools PR440有限任务：`groupby_transform(..., reducefunc=...)`在外层推进后保留已归约组结果，同时无`reducefunc`保持父懒组行为。三个场景×四工作区共12worker的原始结果在本次evaluation目录，官方合并/独立组织3/3，延迟归约控制1/3，父1/3。该任务补K2非缓存组生命周期义务；它仍是research_pool_only，不是正式结构标签、人工真值或模型效果。v2全部文件和结果不变，cache仍pending。\n'''
(DEST / 'README.md').write_text(readme, encoding='utf-8')
runner = (DEST / 'run_evaluation.py').read_text(encoding='utf-8')
runner = runner.replace("if args.task.endswith('ENV_OVERLAY_LIMITED'):\n    command += ['--cases',str(root/task['public']/'public_cases.json')]",
                    "if args.task.endswith('ENV_OVERLAY_LIMITED') or args.task.endswith('GROUP_LIFETIME_LIMITED'):\n    command += ['--cases',str(root/task['public']/'public_cases.json')]")
(DEST / 'run_evaluation.py').write_text(runner, encoding='utf-8')

with (Path(__file__).resolve().parent / 'delivery_v3_increment_result.json').open('x', encoding='utf-8') as output:
    json.dump({'time': manifest['created_at'], 'directory': str(DEST), 'incremental_from': str(OLD),
               'new_task': 'REPO_MORE_PR440_GROUP_LIFETIME_LIMITED', 'usable_finite_tasks': 3,
               'managed_candidates': 4, 'pending': manifest['pending'], 'new_behavior_runs': 0,
               'v2_unchanged': True}, output, ensure_ascii=False, indent=2)
print(json.dumps({'directory': str(DEST), 'new_task': 'REPO_MORE_PR440_GROUP_LIFETIME_LIMITED',
                  'usable_finite_tasks': 3, 'managed_candidates': 4, 'new_behavior_runs': 0}, ensure_ascii=False))



