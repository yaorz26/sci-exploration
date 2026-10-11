from pathlib import Path
import ast
import difflib
import hashlib
import json

ROOT = Path('experiments/d1_repository_feature_candidate_v1_20261009/actual_project_v1')
FILES = ['confuse/sources.py', 'confuse/templates.py', 'confuse/core.py']

def methods(path):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append(node.name)
    return sorted(set(out))

def hits(path, terms):
    text = path.read_text(encoding='utf-8')
    return {term: [i for i, line in enumerate(text.splitlines(), 1) if term in line] for term in terms}

rows=[]
for rel in FILES:
    parent=ROOT/'parent'/rel; merge=ROOT/'merge'/rel
    parent_text=parent.read_text(encoding='utf-8').splitlines(keepends=True)
    merge_text=merge.read_text(encoding='utf-8').splitlines(keepends=True)
    diff=list(difflib.unified_diff(parent_text,merge_text,fromfile='parent/'+rel,tofile='merge/'+rel,n=0))
    rows.append({'file':rel,'parent_sha256':hashlib.sha256(parent.read_bytes()).hexdigest(),'merge_sha256':hashlib.sha256(merge.read_bytes()).hexdigest(),'parent_methods':methods(parent),'merge_methods':methods(merge),'changed_hunks':len([x for x in diff if x.startswith('@@')]),'added_lines':len([x for x in diff if x.startswith('+') and not x.startswith('+++')]),'removed_lines':len([x for x in diff if x.startswith('-') and not x.startswith('---')]),'merge_term_lines':hits(merge,['base_for_paths','in_source_dir','in_app_dir','set_file'])})
result={
 'candidate':'REPO_CONFUSE_PR126_SOURCE_RELATIVE_PATHS',
 'source':'actual_project_v1/{parent,merge}',
 'evidence_rows':rows,
 'interpretation':{
   'stage_dependency':{'status':'observed_candidate','description':'ConfigSource/YamlSource construction stores source metadata; Filename.value later consumes it when resolving a path. This is an ordered data path across sources.py, core.py, and templates.py.','formal_label':None},
   'shared_state':{'status':'observed_object_local','description':'base_for_paths persists on each ConfigSource object between construction and later template evaluation; no process-global or cross-request state was observed in these files.','formal_label':None},
   'independent_checkability':{'status':'behaviorally_observable','description':'The saved API diagnostics distinguish app-directory, source-directory, override, absolute-path, and unsupported-parent behavior; oracle is researcher-derived and has no human double review.','formal_label':None}
 },
 'competing_explanations':[
   '新增字段只是两个独立API开关，后续模板不依赖源对象元数据',
   '源对象元数据只在一次调用内传递，不构成跨阶段状态',
   '行为输出可测，但结构归因仍可能被多个实现路径混淆'
 ],
 'scope':'static source evidence plus saved public API diagnostics; no upstream tests, hidden D1 data, model calls, or formal labels'
}
out=ROOT/'structure_evidence_v1.json'; out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(result,ensure_ascii=False,indent=2))
