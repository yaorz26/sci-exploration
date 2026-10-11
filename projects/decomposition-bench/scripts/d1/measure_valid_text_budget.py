"""已有正确代码的可容纳文本方案；不把给定文本计量写成模型生成花费。"""
import ast
import copy
import hashlib
import io
import json
from pathlib import Path
import tokenize
from native_tokenizer import NativeTokenizer, render_chatml
from measure_prompt_crowding import WHOLE, PLAN


def read(p):
    return json.loads(p.read_text(encoding='utf-8'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


class AlphaRename(ast.NodeTransformer):
    def visit_Name(self, node):
        if node.id == 'p':
            node.id = 'payload'
        return node

    def visit_arg(self, node):
        if node.arg == 'p':
            node.arg = 'payload'
        return node


def canonical_entry(source):
    tree = ast.parse(source)
    roots = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'solve']
    assert len(roots) == 1 and [a.arg for a in roots[0].args.args] == ['p']
    assert not any(isinstance(n, ast.Name) and n.id == 'payload' or isinstance(n, ast.arg) and n.arg == 'payload' for n in ast.walk(tree))
    assert [n for n in ast.walk(tree) if isinstance(n, ast.arg) and n.arg == 'p'] == roots[0].args.args
    assert not any(isinstance(n, ast.Name) and n.id == 'p' and isinstance(n.ctx, ast.Store) for n in ast.walk(tree))
    lines = source.splitlines(keepends=True); offsets = []; total = 0
    for line in lines:
        offsets.append(total); total += len(line)
    spans = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.NAME and token.string == 'p':
            spans.append((offsets[token.start[0]-1]+token.start[1], offsets[token.end[0]-1]+token.end[1]))
    result = source
    for start, end in reversed(spans):
        result = result[:start]+'payload'+result[end:]
    assert ast.dump(AlphaRename().visit(copy.deepcopy(tree)), include_attributes=False) == ast.dump(ast.parse(result), include_attributes=False)
    return result, len(spans)


def code_chunks(source):
    nodes = [n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)]
    parts = {n.name: ast.get_source_segment(source, n)+'\n' for n in nodes}
    assert ast.dump(ast.parse('\n\n'.join(parts.values())), include_attributes=False) == ast.dump(ast.parse(source), include_attributes=False)
    return nodes, parts


def main():
    root = Path(__file__).resolve().parents[2]
    source_dir = root/'experiments/d1_local_composition_v1_20261008'
    dataset = root/'data/processed/d1_project_initial20_v5_20261008'
    out = root/'experiments/d1_valid_text_budget_v1_20261008'; out.mkdir(exist_ok=False)
    freeze = read(source_dir/'code_freeze.json'); old_results = read(source_dir/'summary.json')['results']
    programs = {}; prepared = []
    for row in freeze['programs']:
        if row['artificial_mutant']:
            continue
        source_path = source_dir/Path(row['path']).name
        assert sha(source_path) == row['sha256']
        old = next(r for r in old_results if r['task_id'] == row['task_id'] and r['program'] == row['program'])
        assert old['all_pass'] and old['manual_integration']['all_pass']
        code, changes = canonical_entry(source_path.read_text(encoding='utf-8'))
        nodes, chunks = code_chunks(code)
        saved_path = out/source_path.name; saved_path.write_text(code,encoding='utf-8',newline='\n')
        record = {'task_id':row['task_id'],'program':row['program'],'source_sha256':row['sha256'],
                  'alpha_renamed_name_tokens':changes,'alpha_ast_equivalent':True,'normalized_sha256':sha(saved_path),
                  'normalized_file':saved_path.name,'top_level_functions':[n.name for n in nodes]}
        prepared.append(record); programs[(row['task_id'],row['program'])] = (code,nodes,chunks)
    contracts = {
        '_transform':'输入node、factor、drop_null；递归变换数值但不变布尔；按规则删除null并保持顺序，返回新树、不修改输入。',
        '_select':'输入已经变换的tree和threshold；返回数值达阈值的path/value，路径使用该树索引与顺序、不修改输入。',
        '_call_key':'输入整数args与kwargs；返回完整位置参数tuple及排序关键词tuple，不混同参数来源、键名和顺序。',
        '_compute':'输入整数args与kwargs，返回两者全部值之和，不修改输入。',
    }
    tokenizer = NativeTokenizer('D:/yaorz/tools/ollamaModels/blobs/sha256-60e05f2100071479f596b964f89f510f057ce397ea22f2833a0cfe029bfc2463','D:/yaorz/tools/ollama/lib/ollama')
    rows = []; prompts = []; output_audit = []
    try:
        identity = tokenizer.identity()
        for task_id in ('D1_B05','D1_C03'):
            task = read(dataset/'public'/task_id/'task.json')
            code, nodes, chunks = programs[(task_id,'staged_correct')]
            helpers = [n for n in nodes if n.name != 'solve']; previous = []; plans = []
            for n in helpers:
                referenced = {x.id for x in ast.walk(n) if isinstance(x,ast.Name) and isinstance(x.ctx,ast.Load)}
                dependencies = [x for x in previous if x in referenced]
                plans.append({'name':n.name,'signature':chunks[n.name].splitlines()[0],
                              'contract':contracts[n.name],'depends_on':dependencies})
                previous.append(n.name)
            plan = {'helpers':plans}; plan_output = json.dumps(plan,ensure_ascii=False)
            for fmt in ('pretty','compact'):
                serialized = json.dumps(task,ensure_ascii=False,indent=2) if fmt == 'pretty' else json.dumps(task,ensure_ascii=False,separators=(',',':'))
                assert json.loads(serialized) == task
                base = '你要编写Python代码。仅使用标准库，内部结构自由。任务需求与公开例子：\n'+serialized+'\n'
                for program in ('staged_correct', 'fused_correct' if task_id=='D1_B05' else 'records_correct'):
                    whole_code = programs[(task_id,program)][0]; prompt = render_chatml(base+WHOLE)
                    inp = tokenizer.count(prompt); text_tokens = tokenizer.count(whole_code)
                    rows.append({'task_id':task_id,'format':fmt,'arm':'M0','representation':program,
                                 'input_tokens':inp,'visible_output_text_tokens':text_tokens,
                                 'visible_text_total':inp+text_tokens,'remaining_at6500':6500-inp-text_tokens,
                                 'smoke_whole512_text_fits':text_tokens<=512})
                    prompts.append({'task_id':task_id,'format':fmt,'arm':'M0','representation':program,
                                    'calls':[{'stage':'whole','prompt':prompt,'given_output_text':whole_code}]})
                for context in ('all_previous','only_referenced_symbols'):
                    calls = [{'stage':'plan','prompt':render_chatml(base+PLAN),'given_output_text':plan_output}]; previous = {}
                    for helper in plans:
                        context_names = list(previous) if context=='all_previous' else helper['depends_on']
                        given_context = '\n\n'.join(previous[name] for name in context_names)
                        suffix = '固定计划：\n'+json.dumps(plan,ensure_ascii=False)+'\n已实现函数：\n'+given_context+'\n仅实现以下函数，签名保持一致，可以添加标准库import，禁止定义其他顶层函数：\n'+json.dumps(helper,ensure_ascii=False)
                        calls.append({'stage':helper['name'],'prompt':render_chatml(base+suffix),
                                      'given_output_text':chunks[helper['name']],'previous_code_names':context_names})
                        previous[helper['name']] = chunks[helper['name']]
                    suffix = '固定计划：\n'+json.dumps(plan,ensure_ascii=False)+'\n固定函数：\n'+'\n\n'.join(previous.values())+'\n仅实现solve(payload)，调用固定辅助函数，不能定义其他顶层函数。只输出代码。'
                    calls.append({'stage':'entry','prompt':render_chatml(base+suffix),'given_output_text':chunks['solve']})
                    for c in calls:
                        c['input_tokens'] = tokenizer.count(c['prompt'])
                        c['visible_output_text_tokens'] = tokenizer.count(c['given_output_text'])
                        limit = 256 if c['stage']!='entry' else 512
                        c['P9_smoke_output_cap'] = limit
                        c['visible_text_fits_smoke_cap'] = c['visible_output_text_tokens'] <= limit
                    inp = sum(c['input_tokens'] for c in calls); text_tokens = sum(c['visible_output_text_tokens'] for c in calls)
                    rows.append({'task_id':task_id,'format':fmt,'arm':'M2','representation':'staged_correct','context':context,
                                 'calls':len(calls),'input_tokens':inp,'visible_output_text_tokens':text_tokens,
                                 'visible_text_total':inp+text_tokens,'remaining_at6500':6500-inp-text_tokens,
                                 'each_text_fits_P9_smoke_cap':all(c['visible_text_fits_smoke_cap'] for c in calls),
                                 'each_input_plus_text_within8192':all(c['input_tokens']+c['visible_output_text_tokens']<=8192 for c in calls),
                                 'stage_counts':[{k:c[k] for k in ('stage','input_tokens','visible_output_text_tokens','P9_smoke_output_cap','visible_text_fits_smoke_cap')} for c in calls]})
                    prompts.append({'task_id':task_id,'format':fmt,'arm':'M2','context':context,'plan':plan,'calls':calls})
        old_calls = read(root/'experiments/d1_allin_native_pair_b03_v1_20261008/call_ledger.json')
        for c in old_calls:
            response_path = Path(c['request_directory'])/c['response']['path']
            assert sha(response_path) == c['response']['sha256']
            response = read(response_path); visible = tokenizer.count(response['response'])
            output_audit.append({'arm':c['arm'],'stage':c['stage'],'response_sha256':sha(response_path),
                                 'visible_response_text_tokens':visible,'API_eval_count':response['eval_count'],
                                 'API_minus_visible_text':response['eval_count']-visible,
                                 'done_reason':response['done_reason'],'source':'P9保存原始响应，非新API调用'})
        savings = []
        for task_id,fmt in [('D1_B05','pretty'),('D1_B05','compact'),('D1_C03','pretty'),('D1_C03','compact')]:
            pair = [r for r in rows if r['task_id']==task_id and r['format']==fmt and r['arm']=='M2']
            full = next(r for r in pair if r['context']=='all_previous'); minimal = next(r for r in pair if r['context']=='only_referenced_symbols')
            savings.append({'task_id':task_id,'format':fmt,'saved_input_tokens':full['input_tokens']-minimal['input_tokens'],
                            'given_output_text_identical':full['visible_output_text_tokens']==minimal['visible_output_text_tokens']})
        summary = {'status':'measured_given_correct_text_blueprints','tasks':2,'correct_source_programs':4,'rows':len(rows),
                   'M2_rows':sum(r['arm']=='M2' for r in rows),'M2_visible_text_under6500':sum(r['arm']=='M2' and r['visible_text_total']<=6500 for r in rows),
                   'M2_all_previous_rows':[r for r in rows if r['arm']=='M2' and r['context']=='all_previous'],
                   'only_referenced_symbol_savings':savings,'saved_P9_output_audit':output_audit,
                   'prepared_code':prepared,'tokenizer':identity,'model_calls':0,'API_calls':0,'human_reviewers':0,
                   'executor_changed':False,'script_sha256':sha(Path(__file__)),'P13_freeze_sha256':sha(source_dir/'code_freeze.json'),
                   'scope':'人工给定合法代码/计划的可见文本构造计量，非API实际新花费、模型产出概率、全域最短代码、相同模型成绩或正式预算配置'}
        for name,value in [('rows.json',rows),('summary.json',summary),('given_transcripts.json',prompts),('P9_saved_output_audit.json',output_audit)]:
            (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({k:summary[k] for k in ('status','M2_all_previous_rows','only_referenced_symbol_savings','saved_P9_output_audit','model_calls')},ensure_ascii=False))
    finally:
        tokenizer.close()


if __name__=='__main__':
    main()
