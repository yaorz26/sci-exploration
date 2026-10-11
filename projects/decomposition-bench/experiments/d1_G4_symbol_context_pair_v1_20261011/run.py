"""冻结父API完整上下文，以事前严格计量执行原G4开发烟测。"""
from __future__ import annotations
import argparse
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parent
REPO = BASE.parents[1]
WORK = REPO.parent
sys.path.insert(0, str(REPO / 'scripts/d1'))
from budgeted_generation import BudgetedClient, BudgetRefusal, ProtocolFailure
from repository_patch_entry import prepare_patch, tree_hashes
from tokenizers import Tokenizer

MODEL = 'qwen2.5-coder:7b'
TOKENIZER_FILE = REPO / 'models/Qwen2.5-Coder-7B-Instruct/tokenizer.json'
TOK = Tokenizer.from_file(str(TOKENIZER_FILE))
B = 6500
CTX = 8192
SEED = 20261011
SYSTEM = 'You are Qwen, created by Alibaba Cloud. You are a helpful assistant.'
PUBLIC = REPO / 'data/processed/d1_actual_project_candidate_v2_20261009/public'
EVALUATION = REPO / 'data/processed/d1_actual_project_candidate_v2_20261009/evaluation'
MORE = REPO / 'experiments/d1_G2_more_pr440_group_lifetime_v1_20261009/candidate'
TASKS = [
    {'id':'REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS','package':'confuse',
     'parent':PUBLIC/'REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS/parent',
     'requirement':PUBLIC/'REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS/requirement.md',
     'cases':None,
     'symbols':{'confuse/sources.py':['ConfigSource','YamlSource'],
                'confuse/templates.py':['Filename'],
                'confuse/core.py':['Configuration.set_file','RootView.set']},
     'evaluator':EVALUATION/'REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS/evaluate.py',
     'direct':REPO/'experiments/d1_G3_pr126_entry_gap_v1_20261009/evaluate_direct_yaml.py'},
    {'id':'REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED','package':'confuse',
     'parent':PUBLIC/'REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED/parent',
     'requirement':PUBLIC/'REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED/requirement.md',
     'cases':PUBLIC/'REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED/public_cases.json',
     'symbols':{'confuse/core.py':['Configuration.set_file','RootView.set'],
                'confuse/sources.py':['ConfigSource.__init__'],
                'confuse/yaml_util.py':['Loader'],
                'confuse/__init__.py':[]},
     'evaluator':EVALUATION/'REPO_CONFUSE_PR142_ENV_OVERLAY_LIMITED/evaluate_env_source.py'},
    {'id':'REPO_MORE_PR440_GROUP_LIFETIME_LIMITED','package':'more_itertools',
     'parent':MORE/'workspaces/parent','requirement':MORE/'requirement.md','cases':MORE/'public_cases.json',
     'symbols':{'more_itertools/more.py':['groupby_transform'],
                'more_itertools/__init__.py':[]},
     'evaluator':MORE/'evaluate_group_lifetime.py'},
]

def now():
    return datetime.now(timezone.utc).isoformat()

def save(path, obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as h:
        json.dump(obj,h,ensure_ascii=False,indent=2)

def text(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as h:
        h.write(value)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def chat(prompt):
    return '<|im_start|>system\n'+SYSTEM+'<|im_end|>\n<|im_start|>user\n'+prompt+'<|im_end|>\n<|im_start|>assistant\n'

def count(prompt):
    return len(TOK.encode(chat(prompt)).ids)

def api(endpoint, data=None):
    req=Request('http://127.0.0.1:11434/api/'+endpoint,
                data=json.dumps(data).encode('utf-8') if data is not None else None,
                headers={'Content-Type':'application/json'})
    with urlopen(req,timeout=900) as h:
        return json.load(h)

def transport(payload):
    # 显式raw ChatML，模板不隐式变动；成本逐次与词表比较。
    rendered=dict(payload)
    rendered['prompt']=chat(payload['prompt'])
    rendered['raw']=True
    result=api('generate',rendered)
    if result.get('prompt_eval_count') != count(payload['prompt']):
        # 先交回原始响应使BudgetedClient保存，再由调用点标记失配。
        result['local_count_mismatch']=True
    return result

def find_node(tree,symbol):
    body=tree.body
    node=None
    for name in symbol.split('.'):
        node=next(n for n in body if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name)
        body=getattr(node,'body',[])
    return node

def source_pool(task):
    pool={}
    inventory=[]
    selection=[]
    for rel,symbols in task['symbols'].items():
        file=task['parent']/rel
        source=file.read_text(encoding='utf-8')
        tree=ast.parse(source)
        lines=source.splitlines()
        nodes=[n for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom))]
        # 常量也取父事实；不会导入feature或评价材料。
        nodes += [n for n in tree.body if isinstance(n,(ast.Assign,ast.AnnAssign)) and getattr(n,'lineno',9999)<70]
        if not symbols:
            nodes=list(tree.body)
        else:
            nodes += [find_node(tree,symbol) for symbol in symbols]
        blocks=[]
        seen=set()
        for n in nodes:
            key=(n.lineno,n.end_lineno)
            if key in seen:
                continue
            seen.add(key)
            blocks.append(f'父文件 {rel} 原行 {n.lineno}—{n.end_lineno}（下一片段不连续，不得合并当完整文件）\n'+
                          '\n'.join(lines[n.lineno-1:n.end_lineno]))
        pool[rel]='\n\n'.join(blocks)
        selection.append({'file':rel,'sha256':sha(file),'symbols':symbols,'ranges':[list(x) for x in sorted(seen)]})
        for symbol in symbols:
            node=find_node(tree,symbol)
            if isinstance(node,ast.ClassDef):
                sigs=[ast.unparse(n).split('\n')[0] for n in node.body if isinstance(n,ast.FunctionDef)]
                inventory.append(f'{rel}: class {node.name}; '+'; '.join(sigs))
            else:
                inventory.append(f'{rel}: '+ast.unparse(node).split('\n')[0])
    return pool,'\n'.join(inventory),selection

def public_text(task):
    s=task['requirement'].read_text(encoding='utf-8')
    if task.get('cases'):
        s+='\n公开案例：\n'+task['cases'].read_text(encoding='utf-8')
    return s

DIFF_RULE='''只返回完成指定工作所需的最小unified diff。文件头为--- a/包/文件.py和+++ b/包/文件.py，新文件用--- /dev/null。hunk坐标使用原文件真实行号，old/new行数逐行数清；空行也带空格/加/减前缀。不要拷整份未修改代码、不要解释。只能改指定包内.py。不得用评价器、参考答案或测试。完整父文件存在，但你只能看到冻结片段；若缺信息，不要臆造原行。'''

def normalize_diff(answer):
    s=answer.strip()
    fence=re.fullmatch(r'```(?:diff)?\s*\n([\s\S]*?)\n```',s)
    if fence:
        s=fence[1]
    # 标准git元信息不改变hunk；精确行号/原行/计数仍由原解析器判。
    s='\n'.join(line for line in s.splitlines() if not line.startswith(('diff --git ','index ')))
    return s+'\n'

def candidate(task, arm, answer):
    normalized=normalize_diff(answer)
    text(arm/'normalized.patch',normalized)
    try:
        changes=prepare_patch(task['parent'],normalized,task['package'])
        workspace=arm/'workspace'
        shutil.copytree(task['parent'],workspace)
        for rel,content in changes.items():
            file=workspace/rel
            file.parent.mkdir(parents=True,exist_ok=True)
            file.write_text(content,encoding='utf-8',newline='\n')
        return {'ok':True,'workspace':str(workspace),'changes':list(changes),'hashes':tree_hashes(workspace)}
    except Exception as exc:
        return {'ok':False,'error':f'{type(exc).__name__}: {exc}'}

def request_step(client,arm,stage,prompt,cap):
    n=count(prompt)
    text(arm/f'{stage}_prompt.txt',prompt)
    save(arm/f'{stage}_preflight.json',{'time':now(),'input_tokens':n,'spent_before':client.spent,
                                     'requested_output_cap':cap,'remaining':B-client.spent-n,'ctx':CTX})
    answer=client.request(prompt,MODEL,{'seed':SEED,'temperature':0.2,'num_ctx':CTX},n,cap,stage,raw=True,context_limit=CTX)
    text(arm/f'{stage}_answer.txt',answer)
    row=client.calls[-1]
    if row['prompt_tokens']!=n:
        client.blocked=True
        row['status']='failed'
        row['error']='输入词表与服务端计数失配'
        client._snapshot()
        raise ProtocolFailure(row['error'])
    return answer

def extract_plan(answer,pool):
    value=answer.strip()
    fence=re.fullmatch(r'```(?:json)?\s*\n([\s\S]*?)\n```',value)
    if fence:
        value=fence[1]
    plan=json.loads(value)
    if not isinstance(plan,dict) or len(plan.get('components',[]))!=2:
        raise ValueError('计划必须恰有两个组件')
    for component in plan['components']:
        if not isinstance(component,dict) or not component.get('contract'):
            raise ValueError('计划缺组件契约')
        files=component.get('files')
        if not isinstance(files,list) or not files or any(f not in pool for f in files):
            raise ValueError('计划必须声明冻结父信息池内文件；不能臆造父文件')
    return plan

def generate(task,task_dir,pool,inventory,method):
    arm=task_dir/method
    arm.mkdir()
    client=BudgetedClient(arm/'requests',B,1 if method=='M0' else 4,transport)
    row={'task_id':task['id'],'method':method,'status':'running','candidate':None,'behavior':None}
    need=public_text(task)
    all_source='\n\n'.join(pool.values())
    try:
        if method=='M0':
            prompt=need+'\n父源码完整API片段：\n'+all_source+'\n'+DIFF_RULE
            final=request_step(client,arm,'whole',prompt,2400)
        else:
            # 规划只读公开接口与文件清单；后续检索自己声明的冻结文件。
            prompt=need+'\n可检索的父API/文件：\n'+inventory+'''\n将功能分为两个实现组件，内部拆法自己决定。只输出JSON，例：{"components":[{"name":"c1","files":["包/文件.py"],"contract":"职责与对外约定"},{"name":"c2","files":["包/文件.py"],"contract":"职责与对外约定"}]}。必须选择上述现有父文件，两组件可以共享文件；不要输出代码。'''
            plan_raw=request_step(client,arm,'plan',prompt,350)
            plan=extract_plan(plan_raw,pool)
            save(arm/'plan.json',plan)
            helpers=[]
            for i,comp in enumerate(plan['components'],1):
                sources='\n\n'.join(pool[f] for f in comp['files'])
                prompt=need+'\n实现以下一个组件，其他职责留给组装：\n'+json.dumps(comp,ensure_ascii=False)+'\n父文件：\n'+sources+'\n'+DIFF_RULE
                helpers.append(request_step(client,arm,f'helper{i}',prompt,700))
            prompt=need+'\n父源码：\n'+all_source+'\n计划：\n'+plan_raw
            prompt+='\n组件1回答：\n'+helpers[0]+'\n组件2回答：\n'+helpers[1]
            prompt+='\n组装两个组件，实现全部需求。输出直接针对父快照的一个完整补丁；修接口可以，但不要将组件补丁重复应用。\n'+DIFF_RULE
            final=request_step(client,arm,'assembly',prompt,1600)
        row['candidate']=candidate(task,arm,final)
        row['status']='candidate' if row['candidate']['ok'] else 'patch_failure'
    except BudgetRefusal as exc:
        row.update(status='budget_refusal',error=str(exc))
    except ProtocolFailure as exc:
        row.update(status='measurement_failure',error=str(exc))
    except (ValueError,KeyError) as exc:
        row.update(status='plan_failure',error=f'{type(exc).__name__}: {exc}')
    except Exception as exc:
        row.update(status='infrastructure_failure',error=f'{type(exc).__name__}: {exc}')
    row.update(spent=client.spent,requests_sent=len(client.calls),refusals=client.refusals,
               cost_known=all(c.get('cost_status')=='known' for c in client.calls),budget_compliant=not client.blocked and client.spent<=B)
    save(arm/'generation.json',row)
    print(json.dumps({'time':now(),'task':task['id'],'method':method,'status':row['status'],'spent':client.spent,'requests':len(client.calls)},ensure_ascii=False),flush=True)
    return row

def evaluate(task,row,task_dir):
    if not (row.get('candidate') or {}).get('ok'):
        return {'status':'not_run','conditional_behavior':None,'reason':row['status']}
    workspace=Path(row['candidate']['workspace'])
    dest=task_dir/row['method']
    cmd=[sys.executable,'-B','-X','utf8',str(task['evaluator']),'--workspace',str(workspace),'--output',str(dest/'behavior.json')]
    if task.get('cases'):
        cmd.extend(['--cases',str(task['cases'])])
    result=subprocess.run(cmd,cwd=workspace,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
    save(dest/'evaluation_process.json',{'command':cmd,'returncode':result.returncode,'stdout':result.stdout[-4000:],'stderr':result.stderr[-4000:]})
    behavior=json.loads((dest/'behavior.json').read_text(encoding='utf-8')) if (dest/'behavior.json').exists() else {'status':'evaluation_failed'}
    if task.get('direct'):
        command=[sys.executable,'-B','-X','utf8',str(task['direct']),'--workspace',str(workspace),'--output',str(dest/'direct_yaml.json')]
        proc=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=60)
        save(dest/'direct_yaml_process.json',{'command':command,'returncode':proc.returncode,'stdout':proc.stdout[-4000:],'stderr':proc.stderr[-4000:]})
        behavior['direct_yaml']=json.loads((dest/'direct_yaml.json').read_text(encoding='utf-8')) if (dest/'direct_yaml.json').exists() else {'status':'evaluation_failed'}
    return behavior

def prepare():
    if (BASE/'inputs').exists():
        raise RuntimeError('已有冻结输入，禁止覆盖')
    (BASE/'inputs').mkdir()
    all_freeze=[]
    for task in TASKS:
        pool,inventory,selection=source_pool(task)
        folder=BASE/'inputs'/task['id']
        folder.mkdir()
        save(folder/'pool.json',pool)
        text(folder/'public.txt',public_text(task))
        text(folder/'inventory.txt',inventory)
        save(folder/'manifest.json',{'id':task['id'],'selection':selection,'parent_hashes':tree_hashes(task['parent']),
                                    'requirement_sha256':sha(task['requirement']),'public_cases_sha256':sha(task['cases']) if task.get('cases') else None,
                                    'formal_labels':None,'split':None,'human_reviews':0})
        all_freeze.append({'id':task['id'],'files':list(pool),'body_tokens':len(TOK.encode('\n'.join(pool.values())).ids),'public_tokens':len(TOK.encode(public_text(task)).ids)})
    tags=api('tags')
    show=api('show',{'model':MODEL})
    save(BASE/'model_identity.json',{'model':MODEL,'tags':tags,'show':show,'tokenizer_path':str(TOKENIZER_FILE),'tokenizer_sha256':sha(TOKENIZER_FILE),'runner_sha256':sha(Path(__file__))})
    save(BASE/'prepared.json',{'time':now(),'task_ids':[t['id'] for t in TASKS],'token_limit_per_arm':B,'total_request_cap':15,'freeze':all_freeze,'macro_plan_sha256':sha(REPO/'.research-state/RESEARCH_PLAN.md')})
    print(json.dumps(all_freeze,ensure_ascii=False,indent=2))

def run():
    frozen=json.loads((BASE/'prepared.json').read_text(encoding='utf-8'))
    if frozen['macro_plan_sha256']!=sha(REPO/'.research-state/RESEARCH_PLAN.md'):
        raise RuntimeError('宏观计划变动，停止执行')
    if (BASE/'candidates_frozen.json').exists():
        raise RuntimeError('已有候选冻结，禁止重跑')
    rows=[]
    for task in TASKS:
        folder=BASE/task['id']
        folder.mkdir(exist_ok=False)
        input_dir=BASE/'inputs'/task['id']
        pool=json.loads((input_dir/'pool.json').read_text(encoding='utf-8'))
        inventory=(input_dir/'inventory.txt').read_text(encoding='utf-8')
        for method in ('M0','M2'):
            row=generate(task,folder,pool,inventory,method)
            rows.append(row)
            if not row['cost_known'] or row['status']=='measurement_failure':
                save(BASE/'measurement_abort.json',{'time':now(),'rows':rows})
                raise RuntimeError('测量/成本不明，中止全部后续请求')
    save(BASE/'candidates_frozen.json',{'time':now(),'rows':rows})
    for row in rows:
        task=next(t for t in TASKS if t['id']==row['task_id'])
        row['behavior']=evaluate(task,row,BASE/task['id'])
    save(BASE/'summary.json',{'time':now(),'scope':'research_pool_only_development_smoke','rows':rows,
                             'model':MODEL,'seed':SEED,'request_count':sum(r['requests_sent'] for r in rows),'total_known_tokens':sum(r['spent'] for r in rows),
                             'formal_labels':None,'split':None,'human_reviews':0,'macro_plan_unchanged':sha(REPO/'.research-state/RESEARCH_PLAN.md')==frozen['macro_plan_sha256']})
    print('本批候选冻结与公开评价完成',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--prepare',action='store_true')
    args=parser.parse_args()
    prepare() if args.prepare else run()
