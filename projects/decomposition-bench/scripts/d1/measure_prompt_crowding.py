"""公开输入的精确构造情景计量；无模型/预检API，不推断代码正确率。"""
import hashlib
import json
from pathlib import Path
import statistics
from native_tokenizer import NativeTokenizer, render_chatml

WHOLE='直接完整实现solve(payload)，可自行使用辅助函数。只输出Python代码。'
PLAN='自主分解为2至3个辅助函数，按依赖先后排列。只输出JSON：{"helpers":[{"name":"_name","signature":"def _name(args):","contract":"输入输出及状态修改规则","depends_on":[]}]}。solve入口另外生成，不在helpers中。'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    root=Path(__file__).resolve().parents[2];dataset=root/'data/processed/d1_project_initial20_v5_20261008'
    out=root/'experiments/d1_prompt_crowding_v1_20261008';out.mkdir(exist_ok=False)
    manifest=json.loads((dataset/'manifest.json').read_text(encoding='utf-8'));rows=[];whole=[];raw=[]
    tokenizer=NativeTokenizer('D:/yaorz/tools/ollamaModels/blobs/sha256-60e05f2100071479f596b964f89f510f057ce397ea22f2833a0cfe029bfc2463','D:/yaorz/tools/ollama/lib/ollama')
    try:
        identity=tokenizer.identity()
        for meta in manifest['tasks']:
            tid=meta['task_id'];path=dataset/'public'/tid/'task.json';task=json.loads(path.read_text(encoding='utf-8'))
            for fmt in ('pretty','compact'):
                serialized=json.dumps(task,ensure_ascii=False,indent=2) if fmt=='pretty' else json.dumps(task,ensure_ascii=False,separators=(',',':'))
                assert json.loads(serialized)==task
                base='你要编写Python代码。仅使用标准库，内部结构自由。任务需求与公开例子：\n'+serialized+'\n'
                full=render_chatml(base+WHOLE);single=tokenizer.count(full)
                info={'task_id':tid,'split':meta['split'],'repository':meta['source']['repository'],'author_state':meta['structure_v2']['cross_operation_state'],
                      'author_testability':meta['structure_v2']['separate_behavior_testability'],'format':fmt,'public_task_sha256':sha(path),
                      'base_prompt_tokens':tokenizer.count(render_chatml(base)),'M0_input_tokens':single,'M0_max_output_remainder_at6500':6500-single}
                whole.append(info);raw.append({'scenario':tid+'_'+fmt+'_M0','calls':[{'stage':'whole','prompt':full,'input_tokens':single}]})
                for count in (2,3):
                    plan={'helpers':[{'name':'_h'+str(i+1),'signature':'def _h'+str(i+1)+'(payload):','contract':'输入为payload JSON对象；返回该阶段JSON结果；不修改输入。',
                                      'depends_on':[] if i==0 else ['_h'+str(i)]} for i in range(count)]}
                    for comment_lines in (0,128):
                        calls=[{'stage':'plan','prompt':render_chatml(base+PLAN)}];chunks=[]
                        for i,helper in enumerate(plan['helpers']):
                            suffix='固定计划：\n'+json.dumps(plan,ensure_ascii=False)+'\n已实现函数：\n'+'\n\n'.join(chunks)+'\n仅实现以下函数，签名保持一致，可以添加标准库import，禁止定义其他顶层函数：\n'+json.dumps(helper,ensure_ascii=False)
                            calls.append({'stage':'helper_'+str(i+1),'prompt':render_chatml(base+suffix)})
                            chunks.append(helper['signature']+'\n'+('    # 仅作长度情景占位，不代表实际算法\n'*comment_lines)+'    return payload')
                        suffix='固定计划：\n'+json.dumps(plan,ensure_ascii=False)+'\n固定函数：\n'+'\n\n'.join(chunks)+'\n仅实现solve(payload)，调用固定辅助函数，不能定义其他顶层函数。只输出代码。'
                        calls.append({'stage':'entry','prompt':render_chatml(base+suffix)})
                        for call in calls:call['input_tokens']=tokenizer.count(call['prompt'])
                        total=sum(call['input_tokens'] for call in calls);scenario=tid+'_'+fmt+'_h'+str(count)+'_comments'+str(comment_lines)
                        raw.append({'scenario':scenario,'plan':plan,'synthetic_helper_code':chunks,'calls':calls})
                        rows.append({**info,'scenario':scenario,'helper_count':count,'synthetic_comment_lines_per_helper':comment_lines,
                                     'calls':len(calls),'stage_input_tokens':[{'stage':c['stage'],'input_tokens':c['input_tokens']} for c in calls],
                                     'M2_total_input_tokens':total,'M2_max_output_remainder_at6500':6500-total,
                                     'input_only_exceeds6500':total>6500,'single_input_exceeds8192':any(c['input_tokens']>8192 for c in calls),
                                     'input_ratio_M2_over_M0':total/single})
        groups=[]
        for fmt in ('pretty','compact'):
            for h in (2,3):
                for padding in (0,128):
                    chosen=[r for r in rows if r['format']==fmt and r['helper_count']==h and r['synthetic_comment_lines_per_helper']==padding]
                    groups.append({'format':fmt,'helpers':h,'comment_lines':padding,'tasks':len(chosen),
                                   'input_min':min(r['M2_total_input_tokens'] for r in chosen),'input_median':statistics.median(r['M2_total_input_tokens'] for r in chosen),'input_max':max(r['M2_total_input_tokens'] for r in chosen),
                                   'over6500':sum(r['input_only_exceeds6500'] for r in chosen),
                                   'remaining_output_min':min(r['M2_max_output_remainder_at6500'] for r in chosen),
                                   'remaining_output_median':statistics.median(r['M2_max_output_remainder_at6500'] for r in chosen),
                                   'ratio_median':statistics.median(r['input_ratio_M2_over_M0'] for r in chosen)})
        savings=[]
        for tid in [t['task_id'] for t in manifest['tasks']]:
            a=next(r for r in rows if r['task_id']==tid and r['format']=='pretty' and r['helper_count']==2 and r['synthetic_comment_lines_per_helper']==0)
            b=next(r for r in rows if r['task_id']==tid and r['format']=='compact' and r['helper_count']==2 and r['synthetic_comment_lines_per_helper']==0)
            savings.append({'task_id':tid,'same_semantic_fields':True,'M0_input_saving':a['M0_input_tokens']-b['M0_input_tokens'],
                            'M2_input_saving':a['M2_total_input_tokens']-b['M2_total_input_tokens'],
                            'M2_saving_fraction':(a['M2_total_input_tokens']-b['M2_total_input_tokens'])/a['M2_total_input_tokens']})
        by_state=[]
        for label in ('none','operation_sequence'):
            r=[x for x in rows if x['author_state']==label and x['format']=='pretty' and x['helper_count']==2 and x['synthetic_comment_lines_per_helper']==0]
            by_state.append({'author_state':label,'tasks':len(r),'M0_input_median':statistics.median(x['M0_input_tokens'] for x in r),
                             'M2_input_median':statistics.median(x['M2_total_input_tokens'] for x in r),
                             'M2_max_output_remainder_median':statistics.median(x['M2_max_output_remainder_at6500'] for x in r)})
        summary={'status':'measured_constructed_scenarios','tasks':20,'M0_rows':len(whole),'M2_scenarios':len(rows),'model_calls':0,'API_calls':0,
                 'groups':groups,'same_fields_compaction_savings':savings,'author_state_descriptive':by_state,'tokenizer':identity,
                 'public_manifest_sha256':sha(dataset/'manifest.json'),'executor_template_source_sha256':sha(root/'scripts/d1/run_allin_pipeline.py'),
                 'script_sha256':sha(Path(__file__)),'scope':'占位计划/长度情景的精确输入token，不是模型实际计划、代码正确性、所有可能计划最低成本、预算违例或效果；余额忽略输出，仅为情景上界'}
        for name,data in [('summary.json',summary),('rows.json',rows),('M0_rows.json',whole)]:
            (out/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        with (out/'constructed_prompts.jsonl').open('w',encoding='utf-8') as f:
            for record in raw:f.write(json.dumps(record,ensure_ascii=False)+'\n')
        print(json.dumps({'status':summary['status'],'groups':groups,'state_descriptive':by_state,'median_M2_compaction_saving':statistics.median(x['M2_input_saving'] for x in savings),'model_calls':0},ensure_ascii=False))
    finally:tokenizer.close()

if __name__=='__main__':main()
