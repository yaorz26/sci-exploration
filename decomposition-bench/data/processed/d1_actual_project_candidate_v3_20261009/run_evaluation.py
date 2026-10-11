"""用户显式指定工作区时才执行；不自动重评参考。"""
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
if args.task.endswith('ENV_OVERLAY_LIMITED') or args.task.endswith('GROUP_LIFETIME_LIMITED'):
    command += ['--cases',str(root/task['public']/'public_cases.json')]
completed = subprocess.run(command)
sys.exit(completed.returncode)
