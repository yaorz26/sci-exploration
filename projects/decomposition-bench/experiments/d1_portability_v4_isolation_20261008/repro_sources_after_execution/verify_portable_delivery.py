"""可迁移包第二遍复核：原始字节、路径补丁AST、ZIP、许可、测试一致性。"""
import ast
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import zipfile

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def functional_ast(p):
    body=ast.parse(p.read_text(encoding='utf-8')).body
    return ast.dump(ast.Module(body=[n for n in body if not (
        isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('EXPERIMENT_ROOT','SOURCE_ROOT') for t in n.targets)
        or isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='directory')],type_ignores=[]),include_attributes=False)

def main():
    root=Path(__file__).resolve().parents[2]
    source=root/'data/processed/d1_project_initial20_v5_20261008'
    out=root/'experiments/d1_candidate_delivery_v4_portable_20261008'
    dataset=out/'dataset'
    checks=[]
    def check(name,value):checks.append({'name':name,'pass':bool(value)})
    original=read(root/'experiments/d1_candidate_delivery_v2_20261008/PACKAGE_MANIFEST.json')['file_hashes']
    patches=read(out/'PORTABILITY_PATCHES.json')['patches']
    changed={p['path'].removeprefix('dataset/') for p in patches}
    check('287原始文件：285相同，仅2登记路径变化',len(original)==287 and sum(sha(dataset/r['path'])==r['sha256'] for r in original)==285 and changed=={'private/_curator/task_specs_snapshot.py','private/_curator/task_specs_expansion.py'})
    check('原始定义额外副本逐字保留',all(sha(out/p['original_copy'])==p['original_sha256']==sha(source/p['path'].removeprefix('dataset/')) for p in patches))
    check('两份定义除来源定位与搜索路径外AST不变',all(functional_ast(out/p['path'])==functional_ast(out/p['original_copy']) for p in patches))
    check('全部题面/案例/切分/评分器/参考入口和旧审计相同',all(sha(dataset/r['path'])==r['sha256'] for r in original if r['path'] not in changed))
    tasks=read(dataset/'manifest.json')['tasks']
    case_audit=[]
    for t in tasks:
        tid=t['task_id']; public=read(dataset/'public'/tid/'public_tests.json'); private=read(dataset/'private'/tid/'private_tests.json')
        combined=read(dataset/'private'/tid/'all_tests.json')
        pubspec=read(dataset/'public'/tid/'task.json')
        examples=[{'input':c['input'],**({'raises':c['expected']['error']} if 'error' in c['expected'] else {'output':c['expected']['value']})} for c in public]
        duplicate=defaultdict(list)
        for c in combined: duplicate[json.dumps(c['input'],ensure_ascii=False,allow_nan=False)].append(c)
        conflicts=[g for g in duplicate.values() if len({json.dumps(c['expected'],ensure_ascii=False,allow_nan=False) for c in g})>1]
        case_audit.append({'task_id':tid,'public_cases':len(public),'private_cases':len(private),'all_cases':len(combined),
                           'union_exact':combined==public+private,'unique_case_ids':len({c['case_id'] for c in combined})==len(combined),
                           'public_examples_match_cases':pubspec['public_examples']==examples,
                           'exact_duplicate_input_groups':[[c['case_id'] for c in g] for g in duplicate.values() if len(g)>1],
                           'conflicting_expected_same_exact_input':len(conflicts)})
    check('20题/40公开/267隐藏，合并表与分表相同',len(tasks)==20 and sum(r['public_cases'] for r in case_audit)==40 and sum(r['private_cases'] for r in case_audit)==267 and all(r['union_exact'] for r in case_audit))
    check('每题case_id唯一且同一字节输入无冲突期望',all(r['unique_case_ids'] and not r['conflicting_expected_same_exact_input'] for r in case_audit))
    check('公开题面示例与公开测试输出一致',all(r['public_examples_match_cases'] for r in case_audit))
    deps=read(out/'RUNTIME_DEPENDENCIES.json')
    check('5份运行依赖及许可已登记且源哈希一致',len(deps)==5 and all((out/d['license_file']).is_file() and all(sha(out/f['path'])==f['sha256'] for f in d['files']) for d in deps))
    check('原20题来源许可哈希不变',all(sha(dataset/'private'/t['task_id']/'UPSTREAM_LICENSE.txt')==t['source']['license_sha256'] for t in tasks))
    inventory=read(out/'PACKAGE_MANIFEST.json')['files']; external=read(out/'DELIVERY_CHECKSUMS_EXTERNAL.json'); archive=out/external['archive']
    check('清单中的全部文件哈希正确',all(sha(out/r['path'])==r['sha256'] for r in inventory))
    with zipfile.ZipFile(archive) as z:
        names=z.namelist()
        check('ZIP成员清单精确且内容正确',z.testzip() is None and set(names)=={r['path'] for r in inventory}|{'PACKAGE_MANIFEST.json'} and len(names)==len(set(names)) and all(hashlib.sha256(z.read(r['path'])).hexdigest()==r['sha256'] for r in inventory))
        check('ZIP无缓存及包外校验/评测记录',not any('__pycache__' in n or n.endswith(('.pyc','.pyo')) or n in ('DELIVERY_CHECKSUMS_EXTERNAL.json','verification.json') for n in names))
    check('包外ZIP哈希/字节/清单哈希正确',sha(archive)==external['archive_sha256'] and archive.stat().st_size==external['archive_bytes'] and sha(out/'PACKAGE_MANIFEST.json')==external['package_manifest_sha256'])
    isolation=read(root/'experiments/d1_portability_v4_isolation_20261008/summary.json')
    check('该ZIP完成40/40隔离复跑614/614案例',isolation['archive_sha256']==sha(archive) and isolation['runs']==isolation['passed_runs']==40 and isolation['case_executions']==isolation['passed_case_executions']==614)
    report={'status':'pass' if all(c['pass'] for c in checks) else 'fail','checks':checks,'case_audit':case_audit,
            'duplicate_input_group_count':sum(len(r['exact_duplicate_input_groups']) for r in case_audit),
            'reviewer':'同一助手第二遍程序复核，非独立人工','human_review_count':0,'model_calls':0,
            'scope':'字节与执行一致性；不证明完整语义覆盖、结构标注可靠、新颖性或模型效果',
            'correction':'v1复核脚本误将公开异常例子字段raises当error；修复脚本，原始题面/测试正确，无数据改动，旧报告保留'}
    path=out/'portable_delivery_verification_v2.json'
    if path.exists():raise FileExistsError('不覆盖既存复核结果')
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('checks','case_audit')},ensure_ascii=False))
    if report['status']!='pass':raise SystemExit(1)

if __name__=='__main__':main()
