from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
REPRO = ROOT.parents[1]
DEST = REPRO / 'data/processed/d1_actual_project_candidate_v2_20261009'
DEST.mkdir(exist_ok=False)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_file(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def copy_workspace(source, target):
    # 只复制confuse包.py及原LICENSE，不取测试/管理/字节码。
    for path in sorted((source / 'confuse').rglob('*.py')):
        copy_file(path, target / path.relative_to(source))
    license_path = source / 'LICENSE'
    if not license_path.exists():
        license_path = REPRO / 'experiments/d1_repository_feature_candidate_v1_20261009/actual_project_v1/parent/LICENSE'
    copy_file(license_path, target / 'LICENSE')


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


path_root = REPRO / 'experiments/d1_runnable_repository_task_v2_20261009'
env_root = REPRO / 'experiments/d1_G2_confuse_pr142_env_source_v1_20261009'
path_id = 'REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS'
env_id = 'REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED'
path_parent = Path(load(path_root / 'parent_actual.json')['workspace'])
env_parent = env_root / 'candidate/workspaces/parent'
registry = []
for task_id, task_root, parent in ((path_id, path_root, path_parent), (env_id, env_root, env_parent)):
    public = DEST / 'public' / task_id
    copy_workspace(parent, public / 'parent')
    copy_file(task_root / 'candidate/requirement.md', public / 'requirement.md')
    metadata_path = REPRO / 'experiments/d1_repository_feature_candidate_v1_20261009' / ('confuse_pr126_metadata.json' if task_id == path_id else 'confuse_pr142_metadata.json')
    metadata = load(metadata_path)
    source = {key: metadata[key] for key in ('number', 'title', 'body', 'html_url', 'merged', 'merge_commit_sha', 'merged_at')}
    source['visibility'] = '公开来源说明不等模型可见内部答案；任务有限域另见requirement'
    (public / 'source.json').write_text(json.dumps(source, ensure_ascii=False, indent=2), encoding='utf-8')
    evaluation = DEST / 'evaluation' / task_id
    evaluation.mkdir(parents=True)
    evaluator_name = 'evaluate.py' if task_id == path_id else 'evaluate_env_source.py'
    copy_file(task_root / 'candidate' / evaluator_name, evaluation / evaluator_name)
    if task_id == env_id:
        copy_file(task_root / 'candidate/public_cases.json', public / 'public_cases.json')
        programs = {'feature': env_root / 'candidate/workspaces/feature',
                    'alternative': env_root / 'candidate/workspaces/alternative',
                    'priority_omission': env_root / 'candidate/workspaces/priority_omission'}
        results = [env_root / ('behavior_' + label + '.json') for label in ('parent', 'feature', 'alternative', 'priority_omission')]
    else:
        programs = {label: Path(load(path_root / (label + '_actual.json'))['workspace'])
                    for label in ('complete', 'source_only', 'core_omission')}
        alternate = REPRO / 'experiments/d1_repository_alternative_organization_v1_20261009'
        programs['alternative'] = Path(load(alternate / 'actual.json')['workspace'])
        results = [path_root / (label + '_actual.json') for label in ('parent', 'complete', 'source_only', 'core_omission')]
        copy_file(alternate / 'actual.json', evaluation / 'saved_results/alternative_actual.json')
    for label, program in programs.items():
        copy_workspace(program, evaluation / 'programs' / label)
    for result in results:
        copy_file(result, evaluation / 'saved_results' / result.name)
    registry.append({'task_id': task_id, 'public': 'public/' + task_id,
                     'evaluator': 'evaluation/' + task_id + '/' + evaluator_name,
                     'source': 'confuse', 'scope': '有限公开项目行为候选',
                     'formal_labels': None, 'split': None, 'human_reviews': 0})
    # 父工作区交付一致检查是文件接线，非新增语义/模型评测。
    for original in sorted((parent / 'confuse').rglob('*.py')):
        copied = public / 'parent' / original.relative_to(parent)
        assert digest(original) == digest(copied)
pending = DEST / 'pending/REPO_CACHETOOLS_EXPIRED_REPORT'
pending.mkdir(parents=True)
copy_file(REPRO / 'experiments/d1_repository_expiry_public_oracle_v1_20261009/candidate/requirement.md', pending / 'original_requirement.md')
(pending / 'STATUS.md').write_text('缓存候选未纳入可用任务清单。原物理完成时点条款保留；公开读取会补清理，无法证明先前物理时点。原requirement提evaluate_timing.py而该交付目录缺少脚本，缺口未修复。现有完整/委托5/5是有限公开行为，不代表强条款已验收。源码/许可/原始结果仍在项目experiments/d1_repository_expiry_public_oracle_v1_20261009及G1纳入表。正式标签/split null、人类0、模型0。\n', encoding='utf-8')
for source, name in (
    (REPRO / 'experiments/d1_G3_structure_evidence_v1_20261009/structure_records.json', 'structure_records.json'),
    (REPRO / 'experiments/d1_G4_pair_design_v1_20261009/paired_design_v2.json', 'paired_design.json'),
    (REPRO / 'experiments/d1_G4_pair_design_v1_20261009/resource_boundary.md', 'resource_boundary.md'),
    (REPRO / 'experiments/d1_G2_more_itertools_cursor_v1_20261009/accidental_exposure.json', 'more_cursor_exposure.json'),
    (REPRO / 'experiments/d1_G2_boltons_reverse_jsonl_v1_20261009/accidental_public_test_exposure.json', 'boltons_metadata_exposure.json'),
    (REPRO / 'experiments/d1_G2_boltons_stream_reuse_v1_20261009/official_pr_metadata.json', 'boltons_pr466_unmerged.json'),
):
    copy_file(source, DEST / 'evidence' / name)
runner = '''"""用户显式指定工作区时才执行；不自动重评参考。"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--list', action='store_true')
parser.add_argument('--task')
parser.add_argument('--workspace', type=Path)
parser.add_argument('--output', type=Path)
args = parser.parse_args()
manifest = json.loads((root/'manifest.json').read_text(encoding='utf-8'))
if args.list:
    print(json.dumps({'tasks': manifest['tasks'], 'pending': manifest['pending'], 'scope': manifest['status']}, ensure_ascii=False, indent=2))
    sys.exit(0)
if not args.task or args.workspace is None or args.output is None:
    parser.error('须指定--task、--workspace和新的--output；--list只列清单')
task = next((row for row in manifest['tasks'] if row['task_id'] == args.task), None)
if task is None:
    parser.error('任务不存在或尚待解决，不能运行')
if args.output.exists():
    parser.error('输出必须为新路径，不覆盖旧结果')
command = [sys.executable,'-B','-X','utf8',str(root/task['evaluator']),
           '--workspace',str(args.workspace.resolve()),'--output',str(args.output.resolve())]
if args.task.endswith('ENV_OVERLAY_LIMITED'):
    command += ['--cases',str(root/task['public']/'public_cases.json')]
completed = subprocess.run(command)
sys.exit(completed.returncode)
'''
(DEST / 'run_evaluation.py').write_text(runner, encoding='utf-8')
(DEST / 'README.md').write_text('''# D1真实项目功能任务研究候选成果

题目：面向项目功能级代码生成的任务分解评测数据集构建与适用边界研究。

本版本交付两项具有有限公开行为证据的confuse项目包任务：PR126来源相对路径、PR142环境变量配置叠加。cache过期报告任务在pending，强时点/交付条款未解决。两项可用候选同仓库同配置家族，不是跨来源验证；三项管理候选/两来源，不是三项正式验收。原initial20的20题/307记录/11开发9储备未改、未装入本版本。

新实质产出是PR142有限功能任务及区分来源解析和项目整合的证据：三个公开场景×四组织共12worker，父0/3（缺入口），官方合并/独立模块各3/3，优先级遗漏2/3（冲突时错读文件host）。PR126既有完整/单模块替代8/8、source-only5/8/core遗漏7/8为保存结果，没有本轮重跑。

结构证据支持“行为连接义务不规定唯一内部拆法”。cache公开len/currsize可补清理，结果符合不能倒推返回前物理状态；正式结构标签/split null，人工双审0，主A模型收益关联未测。当前真实非缓存历史和不同独立用途缺口未填，公开源污染unknown，已登记偶然暴露不能抹去。

目录边界：public只有父包、有限需求和公开案例/来源。evaluation包含评价器、完整/替代/功能遗漏实现和旧机器结果；这些不向生成模型提供。pending保留未验收cache；evidence含结构、配对设计、资源和失败/暴露。各confuse父/参考包保留原MIT LICENSE。需求不规定helper数量/文件布局；任务是实际包API调用，不是JSON solve重写。并非完整Git仓库/完整PR/无污染/正式冻结版本。

依赖为本次Python3.13.7、PyYAML6.0.3；仅Windows本地已有证据，没有新的跨平台验证。列清单不执行评分：

```powershell
python -B -X utf8 run_evaluation.py --list
```

评价一个新的候选工作区，输出必须新建：

```powershell
python -B -X utf8 run_evaluation.py --task REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED --workspace <父包修改后的工作区> --output <新结果>.json
```

G4设计显示原M0+M2一题一seed需5—6请求；两有限题需10—12请求，B=6500每臂示例共26000token上限（非实际用量/费用，另需校准与烟测）。旧剩约2、DLL身份不符、真实人类0、任务/标签/协议未冻，当前不启动生成。M2项目适配/上下文尚未正式验证；不能以给定patch或手写通过补主A。

G2负结果：more游标重复已有公开M03且父恢复失败；boltons PR466公开merged=false/merged_at null，与本地CHANGELOG的fixed不同，不据非空merge_commit_sha造任务。保留全部失败/原分母。此目录是一次交付支撑；文件数/哈希/入口通过不是研究贡献或方法效果。未发布、未训练/RL、未新增付费或模型调用。
''', encoding='utf-8')
manifest = {'created_at': datetime.now(timezone.utc).isoformat(), 'version': 'research_candidate_v2',
            'status': 'research_pool_only，非正式冻结/发布', 'tasks': registry,
            'pending': ['REPO_CACHETOOLS_EXPIRED_REPORT'],
            'usable_finite_tasks': 2, 'usable_sources': ['confuse'],
            'managed_candidates': 3, 'managed_sources': ['confuse', 'cachetools'],
            'formal_labels': None, 'split': None, 'human_reviews': 0, 'model_calls_this_cycle': 0,
            'new_behavior_worker_runs_this_cycle': 12, 'original_initial20_unchanged': True,
            'files_sha256': {str(path.relative_to(DEST)).replace('\\','/'): digest(path)
                             for path in sorted(DEST.rglob('*')) if path.is_file()}}
with (DEST / 'manifest.json').open('x', encoding='utf-8') as output:
    json.dump(manifest, output, ensure_ascii=False, indent=2)
with (ROOT / 'delivery_result.json').open('x', encoding='utf-8') as output:
    json.dump({'time': manifest['created_at'], 'directory': str(DEST),
               'usable_finite_tasks': 2, 'managed_candidates': 3, 'pending': 1,
               'copied_parent_hashes_match': True, 'new_evaluator_runs': 0,
               'scope': '一次交付接线支撑；语义成绩引用旧原始结果，非新重评'}, output, ensure_ascii=False, indent=2)
print(json.dumps({'directory': str(DEST), 'usable_finite_tasks': 2, 'pending': 1,
                  'parent_hashes_match': True, 'new_behavior_runs': 0}, ensure_ascii=False))
